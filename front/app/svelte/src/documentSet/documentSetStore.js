import {derived, writable, get} from 'svelte/store';
import {extractNb, generateColor} from "../utils.js";
// import {appUrl} from "../constants.js";

// TO DELETE
const appUrl = "https://vhs.huma-num.fr";
// TO DELETE

const createWorker = () => new Worker(
   '/static/js/pairWorker.js',
   //  './pairWorker.js',
    { type: 'module' }
);

export function createDocumentSetStore(documentSetId) {
    const error = writable(null);

    const selectedCategories = writable([]);
    const selectedRegions = writable(new Set());
    const selectedNodes = writable([]);

    const threshold = writable(0);
    const topK = writable(3);
    const mutualTopK = writable(false);
    const scoreMode = writable('threshold');

    /**
     * All RegionsPair objects loaded in the current context
     */
    const allPairs = writable([]);
    const regionsMetadata = writable(new Map());

    // web worker for processing pairs
    let worker;

    const pairIndex = writable({
        byImage: new Map(),        // imgId -> [pairs]
        byDocPair: new Map(),      // "r1-r2" -> [pairs]
        byDoc: new Map(),          // regionId -> [pairs]
    });

    /**
     * Image nodes: Map<imgId, imageData>
     */
    const imageNodes = writable(new Map());
    /**
     * Document nodes: Map<regionId, regionData>
     */
    const documentNodes = writable(new Map());

    const pairStats = writable({});
    const documentStats = writable({});
    const imageStats = writable({});
    const docPairStats = writable({});
    const docSetNumber = writable({
        documents: 0,
        pairs: null,
        images: 0,
        categories: {}
    });

    const fetchPairs = derived(selectedCategories, ($cats, set) => {
        if ($cats.length === 0) {
            set(Promise.resolve(0));
            return;
        }

        if (worker) worker.terminate();

        // TO DELETE
        // const documentSetId = 413; // histoire naturelle
        const documentSetId = 414; // nicolas
        // const documentSetId = 415; // physiologus
        // const documentSetId = 416; // de materia medica
        // const documentSetId = 417; // traité de géométrie
        // const documentSetId = 436; // Jombert complet
        // TO DELETE

        const loadPromise = new Promise((resolve, reject) => {
            const load = async () => {
                try {
                    const response = await fetch(`${appUrl}/document-set/${documentSetId}/pairs?category=${$cats.join(',')}`);
                    if (!response.ok) throw new Error(`HTTP ${response.status}`);
                    const rawData = await response.json();

                    worker = createWorker();

                    worker.postMessage({
                        rawPairs: rawData,
                        selectedCategories: $cats
                    });

                    worker.onmessage = async (e) => {
                        const { allPairs: sorted, imageNodes: imgMap, pairIndex: idx, categories: cats, stats } = e.data;

                        pairIndex.set(idx);

                        pairStats.set(stats.pairStats);
                        documentStats.set(stats.documentStats);
                        imageStats.set(stats.imageStats);
                        docPairStats.set(stats.docPairStats);

                        const regionIds = Array.from(stats.documentStats.scoreCount.keys());

                        const currentRegions = get(selectedRegions);
                        if (currentRegions.size === 0) {
                            selectedRegions.set(new Set(regionIds));
                        }

                        const results = await Promise.all(
                            regionIds.map(id => getRegionsInfo(id).then(info => ({id, info})))
                        );

                        const metaMap = new Map();
                        results.forEach(({id, info}) => metaMap.set(id, info));
                        regionsMetadata.set(metaMap);

                        const docMap = new Map();
                        regionIds.forEach((id, index) => {
                            const info = metaMap.get(id) || {};
                            docMap.set(id, {
                                id,
                                title: info.title || `Region Extraction ${id}`,
                                color: info.color || generateColor(index),
                                images: [],
                                ...info
                            });
                        });

                        imgMap.forEach(img => {
                            const doc = docMap.get(img.regionId);
                            if (doc) {
                                img.color = doc.color;
                                img.title = `${doc.title} | Page ${img.canvas}`;
                                doc.images.push(img);
                            }
                        });

                        docMap.forEach(doc => doc.images.sort((a, b) => a.canvas - b.canvas));

                        imageNodes.set(imgMap);
                        documentNodes.set(docMap);

                        docSetNumber.set({
                            documents: regionIds.length,
                            pairs: sorted.length,
                            images: imgMap.size,
                            categories: cats
                        });

                        allPairs.set(sorted);

                        worker.terminate();
                        worker = null;
                        resolve(sorted.length);
                    };

                    worker.onerror = (err) => {
                        console.error("Worker error", err);
                        const errMsg = `Error processing pairs: ${err.message}`;
                        error.set(errMsg);
                        reject(new Error(errMsg));
                    };

                } catch (e) {
                    const errMsg = `Fetch error: ${e.message}`;
                    error.set(errMsg);
                    reject(new Error(errMsg));
                }
            };

            load();
        });

        set(loadPromise);
    });

    async function getRegionsInfo(regionId) {
        try {
            const response = await fetch(`${appUrl}/search/regions/?id=${regionId}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const {results} = await response.json();
            if (!results?.length) return {title: `Region Extraction ${regionId}`};

            const region = results[0];
            const [, ...titleParts] = region.title.split(" | ");
            const [wit, digit] = (region.ref || "_").split("_");

            return {
                title: titleParts.join(" | "),
                ref: region.ref,
                witnessId: extractNb(wit),
                digitizationRef: digit,
                zeros: region.zeros,
                img_nb: region.img_nb,
                url: region.url
            };
        } catch (e) {
            error.set(`Error fetching region #${regionId}: ${e.message}`);
            return {title: `Region Extraction ${regionId}`};
        }
    }

    // TODO make filtering more efficient by remembering what was filtered last time
    // TODO and only applying the delta (keep in memory last threshold, topK, regions etc)
    const filteredPairs = derived(
        [allPairs, threshold, topK, mutualTopK, selectedRegions],
        ([$pairs, $threshold, $topK, $mutual, $regions]) => {
            if (!$pairs) return [];
            const result = [];

            const $mode = get(scoreMode);

            for (let i = 0; i < $pairs.length; i++) {
                    const p = $pairs[i];

                    // 1. Score filtering
                    if ($mode === 'threshold') {
                        if (p.weightedScore < $threshold) break;
                    }

                    // 2. Region filter
                    if (!$regions.has(p.regions_id_1) || !$regions.has(p.regions_id_2)) continue;

                    // 3. TopK filtering
                    if ($mode === 'topk' && $topK !== null) {
                        const r1Rank = p.rank_1 ?? Infinity;
                        const r2Rank = p.rank_2 ?? Infinity;

                        if ($mutual) {
                            if (r1Rank > $topK || r2Rank > $topK) continue;
                        } else {
                            if (r1Rank > $topK && r2Rank > $topK) continue;
                        }
                    }

                    result.push(p);
                }

                return result;
        }
    );

    const filteredDocs = derived(
        [filteredPairs, documentNodes],
        ([$pairs, $docNodes]) => {
            if (!$pairs.length || $docNodes.size === 0) return [];

            const activeDocIds = new Set();
            for (const p of $pairs) {
                activeDocIds.add(p.regions_id_1);
                activeDocIds.add(p.regions_id_2);
            }

            const docs = [];
            activeDocIds.forEach(id => {
                const doc = $docNodes.get(id);
                if (doc) docs.push(doc);
            });

            return docs.sort((a, b) => b.id - a.id);
        }
    );

    function calculateLinkProps(score, scoreRange, minDistance = 10, maxDistance = 200, minWidth = 2, maxWidth = 25) {
        if (!scoreRange) return {strength: 0.5, distance: 100, width: 2};

        const {min, _, range} = scoreRange;
        const strength = range === 0 ? 0.5 : (score - min) / range;
        const distance = maxDistance - strength * (maxDistance - minDistance);
        const width = minWidth + strength * (maxWidth - minWidth);
        return {strength, distance, width};
    }

    function normalizeRadius(count, countRange, minRadius = 10, maxRadius = 60) {
        if (!countRange) return minRadius;

        const {min, _, range} = countRange;
        if (range === 0) return (minRadius + maxRadius) / 2;
        return minRadius + ((count - min) / range) * (maxRadius - minRadius);
    }

    /**
     * Image Network Visualization Data
     * Only processes nodes and links that are currently visible based on TopK/Threshold.
     */
    const imageNetwork = derived([filteredPairs], ([$pairs]) => {
        const $imageNodes = get(imageNodes);
        const $imgStats = get(imageStats);
        const $pairStats = get(pairStats);

        const activeNodes = new Set();
        const links = [];
        for (const pair of $pairs) {
            const {strength, distance, width} = calculateLinkProps(pair.weightedScore, $pairStats.scoreRange);
            links.push({
                source: pair.id_1,
                target: pair.id_2,
                strength,
                distance,
                width
            });

            // Mark nodes as active so we only render relevant images
            if (!activeNodes.has(pair.id_1)) activeNodes.add(pair.id_1);
            if (!activeNodes.has(pair.id_2)) activeNodes.add(pair.id_2);
        }

        const nodes = [];
        for (const imgId of activeNodes) {
            const nodeData = $imageNodes.get(imgId);
            if (nodeData) {
                const imgStats = $imgStats.scoreCount?.get(imgId);
                const {count, score} = imgStats;

                nodes.push({
                    ...nodeData,
                    radius: normalizeRadius(score, $imgStats.scoreRange),
                    label: `Region: ${nodeData.regionId}\nPage: ${nodeData.canvas}\nConnections: ${count}\nTotal score: ${score.toFixed(2)}`
                });
            }
        }

        return { nodes, links };
    });

    const documentNetwork = derived(filteredDocs, ($docNodes) => {
        const $docPairStats = get(docPairStats);
        const $docStats = get(documentStats)

        if ($docNodes.size === 0) return { nodes: [], links: [] };

        const nodes = Array.from($docNodes.values()).map(n => {
            const docStats = $docStats.scoreCount?.get(n.id);
            const {count, score} = docStats;

            return {
                ...n,
                radius: normalizeRadius(count, $docStats.countRange),
                label: `${n.title}\nImages: ${count}\nTotal score: ${score.toFixed(2)}`,
            };
        });

        const links = Array.from($docPairStats.scoreCount.entries()).map(([key, pairStat]) => {
            const [source, target] = key.split('-').map(Number);
            const {strength, distance, width} = calculateLinkProps(pairStat.score, $docPairStats.scoreRange);
            return {
                source, target, strength, distance, width
            };
        });

        return { nodes, links };
    });

    /**
     * Matrix Visualization Logic
     * returns {
     *    regions: [regionId1, regionId2 ...],           // ordered list of selected regions ids
     *    rows: [                                        // images contained in the same pairs across regions
     *       { regionId1: {id: img_id, page: page_nb}, regionId2: {id: img_id, page: page_nb} },
     *       { regionId1: {id: img_id, page: page_nb} },
     *       { regionId1: {id: img_id, page: page_nb}, regionsId3: {id: img_id, page: page_nb} },
     *    ]
     * }
     */
    function buildAlignedImageMatrix(orderedSelection) {
        if (!orderedSelection.length) return {regions: [], rows: []};

        const $documentNodes = get(documentNodes);
        const $pairIndex = get(pairIndex);

        const firstRegionId = orderedSelection[0];

        const firstDoc = $documentNodes.get(firstRegionId);
        if (!firstDoc?.images) return {regions: orderedSelection, rows: []};
        const firstImages = firstDoc.images; // already sorted by canvas in documentNodes

        const findPairs = (imgId, sourceRegionId, targetRegionId) => {
            const {r1, r2} = {r1: sourceRegionId, r2: targetRegionId};
            const pairKey = r1 < r2 ? `${r1}-${r2}` : `${r2}-${r1}`;
            const pairs = $pairIndex.byDocPair.get(pairKey) || [];

            return pairs
                .map(p => {
                    if (p.id_1 === imgId && p.regions_id_1 === sourceRegionId) {
                        return {id: p.id_2, page: p.page_2};
                    } else if (p.id_2 === imgId && p.regions_id_2 === sourceRegionId) {
                        return {id: p.id_1, page: p.page_1};
                    }
                    return null;
                })
                .filter(Boolean);
        };

        const allRows = [];

        for (const firstImg of firstImages) {
            let currentRows = [{[firstRegionId]: {id: firstImg.id, page: firstImg.canvas}}];

            for (let colIdx = 1; colIdx < orderedSelection.length; colIdx++) {
                const targetRegionId = orderedSelection[colIdx];
                const nextRows = [];

                for (const row of currentRows) {
                    const allPairsFound = [];

                    for (let srcIdx = 0; srcIdx < colIdx; srcIdx++) {
                        const sourceRegionId = orderedSelection[srcIdx];
                        if (row[sourceRegionId]) {
                            const pairs = findPairs(row[sourceRegionId].id, sourceRegionId, targetRegionId);
                            allPairsFound.push(...pairs);
                        }
                    }

                    if (allPairsFound.length === 0) {
                        nextRows.push(row);
                    } else {
                        const uniquePairs = new Map();
                        allPairsFound.forEach(p => {
                            if (!uniquePairs.has(p.id)) {
                                uniquePairs.set(p.id, p);
                            }
                        });

                        for (const pair of uniquePairs.values()) {
                            const newRow = {...row, [targetRegionId]: pair};
                            nextRows.push(newRow);
                        }
                    }
                }

                currentRows = nextRows;
            }

            allRows.push(...currentRows);
        }

        const rows = [];
        const seen = new Set();

        for (const row of allRows) {
            const key = orderedSelection.map(rid => row[rid]?.id || '').join('|');
            if (!seen.has(key)) {
                seen.add(key);
                rows.push(row);
            }
        }

        return {regions: orderedSelection, rows};
    }

    function toggleCategory(categoryId) {
        selectedCategories.update(cats => {
            const index = cats.indexOf(categoryId);
            return index > -1
                ? cats.filter(c => c !== categoryId)
                : [...cats, categoryId].sort((a, b) => a - b);
        });
    }

    function toggleRegion(regionId) {
        selectedRegions.update(regions => {
            const newRegions = new Set(regions);
            newRegions.has(regionId) ? newRegions.delete(regionId) : newRegions.add(regionId);
            return newRegions;
        });
    }

    return {
        error,
        allPairs, // Contains all pairs sorted
        visiblePairs: filteredPairs, // Optimized for visualization
        pairIndex,
        documentNodes,
        imageNodes,
        fetchPairs,
        imageNetwork,
        documentNetwork,
        selectedCategories,
        pairStats,
        documentStats,
        imageStats,
        docPairStats,
        docSetNumber,
        selectedNodes,
        selectedRegions,
        updateSelectedNodes: (nodes) => selectedNodes.set(nodes),
        toggleCategory,
        toggleRegion,
        buildAlignedImageMatrix,

        threshold,
        setThreshold: (t) => threshold.set(t),
        topK,
        setTopK: (k) => topK.set(k),
        mutualTopK,
        setMutualTopK: (b) => mutualTopK.set(b),
        scoreMode,
        setScoreMode: (m) => scoreMode.set(m),
    };
}
