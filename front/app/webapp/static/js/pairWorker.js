/**
 * Web Worker for incremental pair processing.
 * Fetches the gzipped NDJSON batch stream and builds indexes incrementally.
 */

const IMG_REGEX = /^(wit\d+_[a-z]{3}(\d+)_(\d+))(?:_([\d,]+))?\.jpg$/;
// const weights = { 1: 1.0, 2: 0.5, 3: 0.125, 4: -1.0, 5: 0.125 };
const weights = { 0: 1, 1: 1, 2: 1.5, 3: 1.25, 4: -1.0, 5: 1.25 };
const pairKey = ({ digit_1: a, digit_2: b }) => a < b ? `${a}-${b}` : `${b}-${a}`;

let state = null;

self.onmessage = async ({ data: { url } }) => {
    state = createState();
    try {
        const res = await fetch(url);
        if (!res.ok) throw new Error((await res.json().catch(() => ({}))).error || `HTTP ${res.status}`);

        const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
        let buffer = "";
        for (let chunk; !(chunk = await reader.read()).done;) {
            const lines = (buffer + chunk.value).split("\n");
            buffer = lines.pop();
            for (const line of lines) processBatch(...JSON.parse(line));
        }
        finalize();
    } catch (err) {
        self.postMessage({ type: 'error', message: err.message });
    }
};

function createState() {
    return {
        names: [],
        pairs: [],
        imageMap: new Map(),
        index: {
            byImage: new Map(),
            byDocPair: new Map(),
            // byDoc: new Map(),
        },
        categories: {},
        exactPairs: [],
        manualPairs: [],
        realScoreSum: 0,
        realScoreCount: 0,
        maxWeightedScore: 0, // TODO check if you can do better
    };
}

function processBatch(newNames, flat) {
    const { names, pairs, index, categories } = state;
    for (const name of newNames) names.push(name);

    for (let i = 0; i < flat.length; i += 5) {
        const id1 = flat[i], id2 = flat[i + 1], score = flat[i + 2], cat = flat[i + 3], userMatch = flat[i + 4];

        if (cat === 4) continue;

        categories[cat] = (categories[cat] || 0) + 1;
        if (userMatch) categories[5] = (categories[5] || 0) + 1;

        const w = weights[cat || (userMatch && 5)] || 0;
        const hasScore = score != null;
        const weightedScore = hasScore ? Math.max(0.01, score * w) : 0;

        const img1 = getOrAddImage(names[id1]);
        const img2 = getOrAddImage(names[id2]);

        const processedPair = {
            // indexes in `names`, replaced by image ids on the main thread
            id_1: id1,
            id_2: id2,
            digit_1: img1.digit,
            digit_2: img2.digit,
            page_1: img1.canvas,
            page_2: img2.canvas,
            score,
            weightedScore,
            category: cat,
            // similarity_type: p.similarity_type,
            rank_1: 0,
            rank_2: 0,
            // doc_rank_1: 0,
            // doc_rank_2: 0
        };

        pairs.push(processedPair);
        if (hasScore) {
            state.realScoreSum += weightedScore; // could use score
            state.realScoreCount++;
            if (weightedScore > state.maxWeightedScore) state.maxWeightedScore = weightedScore;
        } else {
            state.manualPairs.push({ pair: processedPair, w });
        }
        if (cat === 1) state.exactPairs.push(processedPair);

        pushToMap(index.byDocPair, pairKey(processedPair), processedPair);
        pushToMap(index.byImage, id1, processedPair);
        pushToMap(index.byImage, id2, processedPair);
        // pushToMap(index.byDoc, digit1, processedPair);
        // pushToMap(index.byDoc, digit2, processedPair);
    }

    self.postMessage({ type: 'progress', count: pairs.length });
}

function finalize() {
    const { pairs, names, imageMap, index, categories } = state;

    const meanReal = state.realScoreCount ? state.realScoreSum / state.realScoreCount : 1;
    for (const { pair, w } of state.manualPairs) pair.weightedScore = meanReal * w;

    const exactScore = (state.maxWeightedScore || 1) * 1.25;
    for (const p of state.exactPairs) p.weightedScore = exactScore;

    pairs.sort((a, b) => b.weightedScore - a.weightedScore);
    // const rankGroups = new Map();

    for (const [imgId, imgPairs] of index.byImage) {
        imgPairs.sort((a, b) => b.weightedScore - a.weightedScore);

        for (let k = 0; k < imgPairs.length; k++) {
            const pair = imgPairs[k];

            // const other = pair.id_1 === imgId ? pair.digit_2 : pair.digit_1;
            // pushToMap(rankGroups, `${imgId}|${other}`, pair);

            const isSelf = pair.digit_1 === pair.digit_2;
            const isExact = pair.category === 1
            const rank = isSelf ? Infinity : (isExact ? 1 : k + 1);
            if (pair.id_1 === imgId) {
                pair.rank_1 = rank;
            } else {
                pair.rank_2 = rank;
            }
        }
    }

    // ranking of the pair relative to the document pair (digit_1, digit_2)
    // for (const [key, group] of rankGroups) {
    //     const imgId = key.slice(0, key.lastIndexOf('|'));
    //     group.sort((a, b) => b.weightedScore - a.weightedScore);
    //     for (let k = 0; k < group.length; k++) {
    //         const pair = group[k];
    //         const rank = pair.digit_1 === pair.digit_2 ? Infinity : (pair.category === 1 ? 1 : k + 1);
    //         if (pair.id_1 === imgId) {
    //             pair.doc_rank_1 = rank;
    //         } else {
    //             pair.doc_rank_2 = rank;
    //         }
    //     }
    // }

    self.postMessage({
        type: 'complete',
        allPairs: pairs,
        imageIds: names,
        imageNodes: imageMap,
        pairIndex: {
            byImage: new Map([...index.byImage].map(([id, ps]) => [names[id], ps])),
            byDocPair: index.byDocPair,
            // byDoc: index.byDoc,
        },
        categories,
        stats: {
            pairStats: { count: pairs.length, scoreRange: range(pairs.length ? [pairs.at(-1).weightedScore, pairs[0].weightedScore] : []) },
            documentStats: groupStats(p => [p.digit_1, p.digit_2]),
            imageStats: groupStats(p => [names[p.id_1], names[p.id_2]]),
            docPairStats: groupStats(p => [pairKey(p)])
        }
    });

    state = null;
}

function getOrAddImage(imgKey) {
    let imgData = state.imageMap.get(imgKey);

    if (!imgData) {
        const [, ref, digit, page, coords] = imgKey.match(IMG_REGEX);
        imgData = {
            id: imgKey,
            digit: +digit,
            ref: `${ref}.jpg`,
            canvas: +page,
            xywh: coords ? coords.split(',') : null,
            type: "region_extraction",
            // to be initialized in the main thread
            color: null
        };
        state.imageMap.set(imgKey, imgData);
    }

    return imgData;
}

function pushToMap(map, key, value) {
    let arr = map.get(key);
    if (!arr) {
        arr = [];
        map.set(key, arr);
    }
    arr.push(value);
}

function groupStats(keysOf) {
    const scoreCount = new Map();
    for (const p of state.pairs) {
        for (const key of keysOf(p)) {
            const entry = scoreCount.get(key) ?? scoreCount.set(key, { score: 0, count: 0 }).get(key);
            entry.score += p.weightedScore;
            entry.count++;
        }
    }
    const entries = [...scoreCount.values()];
    const stats = {
        count: scoreCount.size,
        scoreCount,
        scoreRange: range(entries.map(e => e.score)),
        countRange: range(entries.map(e => e.count)),
    };
    // computeDensity(stats);
    return stats;
}

function range(values) {
    let min = Infinity, max = -Infinity;
    for (const v of values) {
        if (v < min) min = v;
        if (v > max) max = v;
    }
    return values.length ? { min, max, range: max - min } : { min: 0, max: 0, range: 0 };
}

// function computeDensity(stats) {
//     if (stats.count <= 1) {
//         stats.density = 0;
//         return;
//     }
//     stats.density = (2 * stats.links) / (stats.count * (stats.count - 1));
// }
