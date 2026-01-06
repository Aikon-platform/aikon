const regionsType = "region";
const IMG_REGEX = /^(.+)_(\d+)_([\d,]+)\.jpg$/;

self.onmessage = (e) => {
    const { rawPairs, selectedCategories } = e.data;
    const results = processPairs(rawPairs);
    self.postMessage(results);
};

function processPairs(data) {
    const pairs = [];
    const imageMap = new Map(); // imgId -> imgNode

    const index = {
        byImage: new Map(),   // imgId -> [pairs]
        byDocPair: new Map(), // "r1-r2" -> [pairs]
        byDoc: new Map(),     // rid -> [pairs]
    };

    const pStats = createStatsObject();
    const docStats = createStatsObject();
    const imgStats = createStatsObject();
    const docPStats = createStatsObject();

    const weights = {1: 1.0, 2: 0.5, 3: 0.125, 4: -1.0, 5: 0.125};

    const len = data.length;
    for (let i = 0; i < len; i++) {
        const p = data[i];

        if (p.category === 4) continue;

        const w = weights[p.category] || 0;
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
            weightedScore: weightedScore,
            category: p.category,
            is_manual: p.is_manual,

            // Rank for topk filtering
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

    pairs.sort((a, b) => b.weightedScore - a.weightedScore);

    // TOP-K
    for (const [imgId, imgPairs] of index.byImage) {
        // Sort image pairs by descending score
        imgPairs.sort((a, b) => b.weightedScore - a.weightedScore);

        for (let k = 0; k < imgPairs.length; k++) {
            const pair = imgPairs[k];
            if (pair.id_1 === imgId) {
                pair.rank_1 = k + 1; // Rang 1-based
            } else {
                pair.rank_2 = k + 1;
            }
        }
    }

    finalizeStats(pStats, pairs.length);
    finalizeStats(docStats, docStats.scoreCount.size);
    finalizeStats(imgStats, imgStats.scoreCount.size);
    finalizeStats(docPStats, docPStats.scoreCount.size);

    computeDensity(docStats);
    computeDensity(imgStats);
    computeDensity(docPStats);

    return {
        allPairs: pairs,
        imageNodes: imageMap,
        pairIndex: index,
        stats: {
            pairStats: pStats,
            documentStats: docStats,
            imageStats: imgStats,
            docPairStats: docPStats
        }
    };
}

function getOrAddImage(imgKey, rid, map, imgStats, docStats, score) {
    const imgId = `${rid}_${imgKey}`;
    let imgData = map.get(imgId);

    if (!imgData) {
        let page = 0;
        let ref = imgKey;
        let coords = null; // string "x,y,w,h"

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
            ref: ref,
            canvas: page,
            xywh: coords ? coords.split(',') : null,
            type: regionsType,
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
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(value);
}

function createStatsObject() {
    return {
        count: 0,
        totalScore: 0,
        scoreCount: new Map(), // key -> { score, count }
        scoreRange: { min: Infinity, max: -Infinity, range: 0 },
        countRange: { min: Infinity, max: -Infinity, range: 0 },
        links: 0,
        density: 0
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
        stats.count++; // Number of unique keys
    }

    entry.score += score;
    entry.count += 1;
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
        stats.scoreRange.min = 0;
        stats.scoreRange.max = 0;
        stats.countRange.min = 0;
        stats.countRange.max = 0;
    }

    stats.scoreRange.range = stats.scoreRange.max - stats.scoreRange.min;
    stats.countRange.range = stats.countRange.max - stats.countRange.min;
}

function computeDensity(stats) {
    if (stats.count <= 1) {
        stats.density = 0;
        return;
    }
    // Undirected graph density 2 * E / (V * (V-1))
    stats.density = (2 * stats.links) / (stats.count * (stats.count - 1));
}
