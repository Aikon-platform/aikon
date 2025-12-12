import { imageToPage } from "../utils.js";
import { regionsType } from "../constants.js";

const IMG_REGEX = /^(.+)_(\d+)_([\d,]+)\.jpg$/;

self.onmessage = (e) => {
    const { rawPairs, categories } = e.data;
    const results = processPairs(rawPairs, categories);
    // send processing results back to main thread
    self.postMessage(results);
};

function processPairs(data, categories) {
    const imageMap = new Map();    // imgId -> imgNode (cache)
    const docMap = new Map();      // regionId -> docNode
    const pairIndex = {
        byImage: new Map(),
        byDocPair: new Map(),
        byDoc: new Map(),
    };

    const stats = {
        global: { minScore: Infinity, maxScore: -Infinity, totalPairs: 0, categories: {} },
        p: createEmptyStats(), doc: createEmptyStats(), img: createEmptyStats(), docP: createEmptyStats()
    };

    const validPairs = [];
    const len = data.length;

    // weights per category
    const weights = {1: 1.0, 2: 0.5, 3: 0.125, 4: -1.0, 5: 0.125};

    for (let i = 0; i < len; i++) {
        const rawPair = data[i];

        if (rawPair.category === 4) continue;
        const rawScore = rawPair.score ?? 0;

        if (!rawPair.is_manual) continue;

        const w = weights[rawPair.category] || 0;
        const finalScore = Math.max(0.01, rawScore + rawScore * w);

        const newPair = {
            s: finalScore, // score
            c: rawPair.category, // category
            r1: rawPair.regions_id_1, // region 1
            r2: rawPair.regions_id_2, // region 2
            m: rawPair.is_manual || false // manual
        };

        processImg(rawPair, '1', newPair, imageMap, docMap, pairIndex, stats.img, stats.doc, finalScore);
        processImg(rawPair, '2', newPair, imageMap, docMap, pairIndex, stats.img, stats.doc, finalScore);

        validPairs.push(newPair);
        updateStat(stats.p, null, finalScore);
        stats.global.categories[newPair.c] = (stats.global.categories[newPair.c] || 0) + 1;
        if (finalScore < stats.global.minScore) stats.global.minScore = finalScore;
        if (finalScore > stats.global.maxScore) stats.global.maxScore = finalScore;

        // Stats Doc-Pair
        const r1 = newPair.r1;
        const r2 = newPair.r2;
        const pairKey = r1 < r2 ? `${r1}-${r2}` : `${r2}-${r1}`;
        updateStat(stats.docP, pairKey, finalScore);
        pushMap(pairIndex.byDocPair, pairKey, newPair);
    }

    stats.global.totalPairs = validPairs.length;
    finalizeStats(stats, validPairs.length); // min/max counts

    return {
        allPairs: validPairs,
        imageNodes: imageMap,
        documentNodes: docMap,
        pairIndex: pairIndex,
        stats: stats
    };
}


function processImg(rawPair, suffix, newPair, imageMap, docMap, pairIndex, imgStats, docStats, score) {
    const imgKey = rawPair[`img_${suffix}`]; // Eg: 'wit1001_img1001_0144_642,73,1075,2032.jpg'
    const rid = rawPair[`regions_id_${suffix}`];
    const imgId = `${rid}_${imgKey}`;

    let imgData = imageMap.get(imgId);

    if (!imgData) {
        const match = imgKey.match(IMG_REGEX);
        let page = 0;
        let coords = [];
        let ref = imgKey;

        if (match) {
            ref = `${match[1]}_${match[2]}.jpg`;
            page = parseInt(match[2], 10);
            coords = match[3].split(',');
        } else {
            page = imageToPage(imgKey);
        }

        imgData = {
            id: imgId,
            rid: rid,
            canvas: page,
            xywh: coords,
            ref: ref,
            type: regionsType,
            color: null, // will be assigned in the main thread
            class: 'Cluster'
        };
        imageMap.set(imgId, imgData);

        let docNode = docMap.get(rid);
        if (!docNode) {
            docNode = { id: rid, images: [], links: 0, title: null };
            docMap.set(rid, docNode);
        }
        docNode.images.push({ id: imgId, canvas: page });

        pushMap(pairIndex.byDoc, rid, newPair);

    }

    // lightweight pair for the UI
    newPair[`i${suffix}`] = imgData;

    updateStat(imgStats, imgId, score);
    updateStat(docStats, rid, score);
    pushMap(pairIndex.byImage, imgId, newPair);
}

function createEmptyStats() {
    return {
        count: 0,
        scoreCount: new Map(),
        minScore: Infinity, maxScore: -Infinity,
        minCount: Infinity, maxCount: -Infinity,
        totalScore: 0,
        links: 0,
        density: 0,
        rangeScore: 0, rangeCount: 0
    };
}

function updateStat(statObj, key, val) {
    statObj.count++;
    statObj.totalScore += val;

    if (val < statObj.minScore) statObj.minScore = val;
    if (val > statObj.maxScore) statObj.maxScore = val;

    if (key !== null) {
        let entry = statObj.scoreCount.get(key);
        if (!entry) {
            entry = { score: 0, count: 0 };
            statObj.scoreCount.set(key, entry);
        }
        entry.score += val;
        entry.count += 1;
    }
}

function finalizeStats(statsWrapper, totalPairs) {
    const finalize = (s) => {
        if (s.count === 0) return;
        s.rangeScore = s.maxScore - s.minScore;

        if (s.scoreCount.size > 0) {
            s.minCount = Infinity; s.maxCount = -Infinity;
            for (const val of s.scoreCount.values()) {
                if (val.count < s.minCount) s.minCount = val.count;
                if (val.count > s.maxCount) s.maxCount = val.count;
            }
            s.rangeCount = s.maxCount - s.minCount;
        }
    };

    finalize(statsWrapper.p);
    finalize(statsWrapper.doc);
    finalize(statsWrapper.img);
    finalize(statsWrapper.docP);

    statsWrapper.p.links = totalPairs;
    statsWrapper.docP.links = statsWrapper.docP.scoreCount.size;
}

function pushMap(map, key, item) {
    let arr = map.get(key);
    if (!arr) {
        arr = [];
        map.set(key, arr);
    }
    arr.push(item);
}
