/**
 * Web Worker for incremental pair processing.
 * Fetches the gzipped NDJSON batch stream and builds indexes incrementally.
 */

const IMG_REGEX = /^(wit\d+_[a-z]{3}(\d+)_(\d+))(?:_([\d,]+))?\.jpg$/;
// const weights = { 1: 1.0, 2: 0.5, 3: 0.125, 4: -1.0, 5: 0.125 };
const weights = { 0: 1, 1: 1, 2: 1.5, 3: 1.25, 4: -1.0, 5: 1.25 };
const COLS = { id1: Uint32Array, id2: Uint32Array, score: Float64Array, cat: Uint8Array, um: Uint8Array };
const pairKey = (a, b) => a < b ? `${a}-${b}` : `${b}-${a}`;

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
        imgs: [],
        imageMap: new Map(),
        categories: {},
        n: 0,
        cols: Object.fromEntries(Object.entries(COLS).map(([k, T]) => [k, new T(1 << 20)])),
    };
}

function reserve(size) {
    const { cols } = state;
    if (size <= cols.id1.length) return;
    const cap = Math.max(size, cols.id1.length * 2);
    for (const k in cols) {
        const a = new cols[k].constructor(cap);
        a.set(cols[k]);
        cols[k] = a;
    }
}

function processBatch(newNames, flat) {
    const { names, imgs, categories } = state;
    for (const name of newNames) names.push(name);

    reserve(state.n + flat.length / 5);
    const { id1, id2, score, cat, um } = state.cols;

    for (let i = 0; i < flat.length; i += 5) {
        const a = flat[i], b = flat[i + 1], c = flat[i + 3], u = flat[i + 4];
        if (c === 4) continue;

        categories[c] = (categories[c] || 0) + 1;
        if (u) categories[5] = (categories[5] || 0) + 1;

        imgs[a] ??= getOrAddImage(names[a]);
        imgs[b] ??= getOrAddImage(names[b]);

        const k = state.n++;
        id1[k] = a;
        id2[k] = b;
        score[k] = flat[i + 2] ?? NaN;
        cat[k] = c;
        um[k] = u;
    }

    self.postMessage({ type: 'progress', count: state.n });
}

function finalize() {
    const { names, imgs, imageMap, categories, n } = state;
    const { id1, id2, score, cat, um } = Object.fromEntries(
        Object.entries(state.cols).map(([k, a]) => [k, a.slice(0, n)])
    );
    const weightOf = i => weights[cat[i] || (um[i] && 5)] || 0;

    const w = new Float64Array(n);
    let sum = 0, count = 0, max = 0;
    for (let i = 0; i < n; i++) {
        if (isNaN(score[i])) continue;
        w[i] = Math.max(0.01, score[i] * weightOf(i));
        sum += w[i];
        count++;
        if (w[i] > max) max = w[i];
    }
    const meanReal = count ? sum / count : 1;
    const exactScore = (max || 1) * 1.25;
    for (let i = 0; i < n; i++) {
        if (cat[i] === 1) w[i] = exactScore;
        else if (isNaN(score[i])) w[i] = meanReal * weightOf(i);
    }

    // byImage as CSR: pairs of image j are byImage[start[j]..start[j + 1]]
    const byW = (a, b) => w[b] - w[a];
    const start = new Uint32Array(names.length + 1);
    for (let i = 0; i < n; i++) {
        start[id1[i] + 1]++;
        start[id2[i] + 1]++;
    }
    for (let j = 0; j < names.length; j++) start[j + 1] += start[j];
    const byImage = new Uint32Array(2 * n), next = start.slice(0, -1);
    for (let i = 0; i < n; i++) {
        byImage[next[id1[i]]++] = i;
        byImage[next[id2[i]]++] = i;
    }

    const rank1 = new Float32Array(n), rank2 = new Float32Array(n);
    for (let j = 0; j < names.length; j++) {
        byImage.subarray(start[j], start[j + 1]).sort(byW).forEach((i, k) => {
            const rank = cat[i] === 1 ? 1 : imgs[id1[i]].digit === imgs[id2[i]].digit ? Infinity : k + 1;
            if (id1[i] === j) rank1[i] = rank;
            else rank2[i] = rank;
        });
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

    const order = new Uint32Array(n).map((_, i) => i).sort(byW);
    const digits = i => [imgs[id1[i]].digit, imgs[id2[i]].digit];
    const columns = { id1, id2, score, cat, w, rank1, rank2, order, start, byImage };

    self.postMessage({
        type: 'complete',
        columns,
        imageIds: names,
        imageNodes: imageMap,
        categories,
        stats: {
            pairStats: { count: n, scoreRange: range(n ? [w[order[n - 1]], w[order[0]]] : []) },
            documentStats: groupStats(n, w, digits),
            imageStats: groupStats(n, w, i => [names[id1[i]], names[id2[i]]]),
            docPairStats: groupStats(n, w, i => [pairKey(...digits(i))]),
        },
    }, Object.values(columns).map(a => a.buffer));

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

function groupStats(n, w, keysOf) {
    const scoreCount = new Map();
    for (let i = 0; i < n; i++) {
        for (const key of keysOf(i)) {
            const entry = scoreCount.get(key) ?? scoreCount.set(key, { score: 0, count: 0 }).get(key);
            entry.score += w[i];
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
