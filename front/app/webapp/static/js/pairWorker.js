/**
 * Web Worker for incremental pair processing.
 * Receives batches via postMessage and builds indexes incrementally.
 */

const IMG_REGEX = /^(.+)_(\d+)_([\d,]+)\.jpg$/;

// Persistent state across batches
let state = null;

self.onmessage = (e) => {
    const { type, pairs, isLast } = e.data;

    switch (type) {
        case 'init':
            state = createState();
            break;

        case 'batch':
            if (!state) state = createState();
            processBatch(pairs);
            if (isLast) finalize();
            break;

        case 'done':
            if (state) {
                finalize();
            } else {
                // if received 'done' without any data, send empty result
                self.postMessage({
                    type: 'complete',
                    allPairs: [],
                    imageNodes: new Map(),
                    pairIndex: { byImage: new Map(), byDocPair: new Map(), byDoc: new Map() },
                    categories: {},
                    stats: {
                        pairStats: createStatsObject(true),
                        documentStats: createStatsObject(true),
                        imageStats: createStatsObject(true),
                        docPairStats: createStatsObject(true)
                    }
                });
            }
            break;

        // Legacy: full array mode (for backward compat)
        default:
            if (e.data.rawPairs) {
                state = createState();
                processBatch(e.data.rawPairs);
                finalize();
            }
    }
};

function createState() {
    return {
        pairs: [],
        imageMap: new Map(),
        index: {
            byImage: new Map(),
            byDocPair: new Map(),
            byDoc: new Map(),
        },
        categories: {},
        pStats: createStatsObject(),
        docStats: createStatsObject(),
        imgStats: createStatsObject(),
        docPStats: createStatsObject(),
        weights: { 1: 1.0, 2: 0.5, 3: 0.125, 4: -1.0, 5: 0.125 }
    };
}

function processBatch(batch) {
    const { pairs, imageMap, index, categories, weights, pStats, docStats, imgStats, docPStats } = state;

    for (let i = 0; i < batch.length; i++) {
        const p = batch[i];
        const cat = p.category || 0;

        if (cat === 4) continue;

        categories[cat] = (categories[cat] || 0) + 1;

        const w = weights[cat] || 0;
        const baseScore = p.score ?? w;
        const weightedScore = Math.max(0.01, baseScore + baseScore * w);

        const img1 = getOrAddImage(p.img_1, p.regions_id_1, imageMap, imgStats, docStats, weightedScore);
        const img2 = getOrAddImage(p.img_2, p.regions_id_2, imageMap, imgStats, docStats, weightedScore);

        const processedPair = {
            id_1: img1.id,
            id_2: img2.id,
            regions_id_1: p.regions_id_1,
            regions_id_2: p.regions_id_2,
            page_1: img1.canvas,
            page_2: img2.canvas,
            score: p.score,
            weightedScore,
            category: cat,
            similarity_type: p.similarity_type,
            rank_1: 0,
            rank_2: 0
        };

        pairs.push(processedPair);
        updateStats(pStats, null, weightedScore);

        const pairKey = p.regions_id_1 < p.regions_id_2
            ? `${p.regions_id_1}-${p.regions_id_2}`
            : `${p.regions_id_2}-${p.regions_id_1}`;

        pushToMap(index.byDocPair, pairKey, processedPair);
        updateStats(docPStats, pairKey, weightedScore);

        pushToMap(index.byImage, img1.id, processedPair);
        pushToMap(index.byImage, img2.id, processedPair);
        pushToMap(index.byDoc, p.regions_id_1, processedPair);
        pushToMap(index.byDoc, p.regions_id_2, processedPair);
    }

    // Progress update (optional - can throttle if needed)
    self.postMessage({ type: 'progress', count: pairs.length });
}

function finalize() {
    const { pairs, imageMap, index, categories, pStats, docStats, imgStats, docPStats } = state;

    // Sort all pairs by score
    pairs.sort((a, b) => b.weightedScore - a.weightedScore);

    // TOP-K
    for (const [imgId, imgPairs] of index.byImage) {
        imgPairs.sort((a, b) => b.weightedScore - a.weightedScore);
        for (let k = 0; k < imgPairs.length; k++) {
            const pair = imgPairs[k];
            if (pair.id_1 === imgId) pair.rank_1 = k + 1;
            else pair.rank_2 = k + 1;
        }
    }

    finalizeStats(pStats, pairs.length);
    finalizeStats(docStats, docStats.scoreCount.size);
    finalizeStats(imgStats, imgStats.scoreCount.size);
    finalizeStats(docPStats, docPStats.scoreCount.size);

    computeDensity(docStats);
    computeDensity(imgStats);
    computeDensity(docPStats);

    // Send final result
    self.postMessage({
        type: 'complete',
        allPairs: pairs,
        imageNodes: imageMap,
        pairIndex: index,
        categories,
        stats: {
            pairStats: pStats,
            documentStats: docStats,
            imageStats: imgStats,
            docPairStats: docPStats
        }
    });

    // Clear state for next use
    state = null;
}

function getOrAddImage(imgKey, rid, map, imgStats, docStats, score) {
    const imgId = `${rid}_${imgKey}`;
    let imgData = map.get(imgId);

    if (!imgData) {
        let page = 0, ref = imgKey, coords = null;

        const match = imgKey.match(IMG_REGEX);
        if (match) {
            ref = `${match[1]}_${match[2]}.jpg`;
            page = parseInt(match[2], 10);
            coords = match[3];
        } else {
            const parts = imgKey.split('_');
            if (parts.length >= 2) {
                page = parseInt(parts[parts.length - 2], 10) || 0;
            }
        }

        imgData = {
            id: imgId,
            regionId: rid,
            ref,
            canvas: page,
            xywh: coords ? coords.split(',') : null,
            type: "regions",
            // to be initialized in the main thread
            color: null
        };
        map.set(imgId, imgData);
    }

    updateStats(imgStats, imgId, score);
    updateStats(docStats, rid, score);

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

function createStatsObject(isEmpty = false) {
    const min = isEmpty ? 0 : Infinity;
    const max = isEmpty ? 0 : -Infinity;
    return {
        count: 0,
        totalScore: 0,
        scoreCount: new Map(),
        scoreRange: { min: min, max: max, range: 0 },
        countRange: { min: min, max: max, range: 0 },
        links: 0,
        density: 0,
        avgScore: 0
    };
}

function updateStats(stats, key, score) {
    if (key === null) {
        stats.count++;
        stats.totalScore += score;
        updateMinMax(stats.scoreRange, score);
        return;
    }

    let entry = stats.scoreCount.get(key);
    if (!entry) {
        entry = { score: 0, count: 0 };
        stats.scoreCount.set(key, entry);
        stats.count++;
    }
    entry.score += score;
    entry.count++;
}

function updateMinMax(rangeObj, val) {
    if (val < rangeObj.min) rangeObj.min = val;
    if (val > rangeObj.max) rangeObj.max = val;
}

function finalizeStats(stats, linkCount) {
    stats.links = linkCount;
    stats.avgScore = stats.count > 0 ? stats.totalScore / stats.count : 0;

    if (stats.scoreCount.size > 0) {
        for (const val of stats.scoreCount.values()) {
            updateMinMax(stats.scoreRange, val.score);
            updateMinMax(stats.countRange, val.count);
        }
    } else if (stats.scoreRange.min === Infinity) {
        stats.scoreRange.min = stats.scoreRange.max = 0;
        stats.countRange.min = stats.countRange.max = 0;
    }

    stats.scoreRange.range = stats.scoreRange.max - stats.scoreRange.min;
    stats.countRange.range = stats.countRange.max - stats.countRange.min;
}

function computeDensity(stats) {
    if (stats.count <= 1) {
        stats.density = 0;
        return;
    }
    stats.density = (2 * stats.links) / (stats.count * (stats.count - 1));
}
