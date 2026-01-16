import {derived, writable, get} from 'svelte/store';
import {extractNb, generateColor} from "../utils.js";
import { streamPairsToWorker } from "./pairStreamReader.js";

import {appUrl} from "../constants.js";

// TO DELETE
// const appUrl = "https://vhs.huma-num.fr";
// TO DELETE

const createWorker = () => new Worker(
   '/static/js/pairWorker.js',
   //  './pairWorker.js',
    { type: 'module' }
);

export function createDocumentSetStore(documentSetId) {
    const error = writable(null);
    const loading = writable(false);
    const loadingProgress = writable({ loaded: 0, done: false });

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
    let abortController = null;

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

        // Cleanup previous
        if (worker) worker.terminate() && (worker = null);
        if (abortController) abortController.abort();
        abortController = new AbortController();

        // TO DELETE
        // const documentSetId = 413; // histoire naturelle
        // const documentSetId = 414; // nicolas
        // const documentSetId = 437; // physiologus
        // const documentSetId = 416; // de materia medica
        // const documentSetId = 417; // traité de géométrie
        // const documentSetId = 436; // Jombert complet
        // const documentSetId = 432; // Jombert incomplet
        // TO DELETE

        const loadPromise = new Promise((resolve, reject) => {
            loading.set(true);
            loadingProgress.set({ loaded: 0, done: false });
            error.set(null);

            const run = async () => {
                try {
                    worker = createWorker();

                    worker.onmessage = async (e) => {
                        const { type } = e.data;

                        if (type === 'progress') {
                            loadingProgress.set({ loaded: e.data.count, done: false });
                            return;
                        }

                        if (type !== 'complete') return;

                        // Process complete - same as before
                        const {
                            allPairs: sorted,
                            imageNodes: imgMap,
                            pairIndex: idx,
                            categories: cats,
                            stats
                        } = e.data;

                        pairIndex.set(idx);
                        pairStats.set(stats.pairStats);
                        applyDefaultThreshold();
                        documentStats.set(stats.documentStats);
                        imageStats.set(stats.imageStats);
                        docPairStats.set(stats.docPairStats);

                        const regionIds = Array.from(stats.documentStats.scoreCount.keys());

                        if (get(selectedRegions).size === 0) {
                            selectedRegions.set(new Set(regionIds));
                        }

                        const results = await Promise.all(
                            regionIds.map(id => getRegionsInfo(id).then(info => ({ id, info })))
                        );

                        const metaMap = new Map();
                        results.forEach(({ id, info }) => metaMap.set(id, info));
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

                        // TODO: sort images by coord (from top to bottom only)
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

                        loading.set(false);
                        loadingProgress.set({ loaded: sorted.length, done: true });

                        worker.terminate();
                        worker = null;
                        resolve(sorted.length);
                    };

                    worker.onerror = (err) => {
                        console.error("Worker error", err);
                        error.set(`Worker error: ${err.message}`);
                        loading.set(false);
                        reject(err);
                    };

                    const url = `${appUrl}/document-set/${documentSetId}/pairs/stream?category=${$cats.join(',')}`;

                    await streamPairsToWorker(url, worker, {
                        signal: abortController.signal,
                        onProgress: (loaded, done) => {
                            loadingProgress.set({ loaded, done });
                        },
                        onError: (err) => {
                            error.set(`Stream error: ${err.message}`);
                        }
                    });

                } catch (e) {
                    if (e.name === 'AbortError') {
                        console.log('Request aborted');
                        return;
                    }
                    error.set(`Fetch error: ${e.message}`);
                    loading.set(false);
                    reject(e);
                }
            };

            run();
        });

        set(loadPromise);
    });

    async function getRegionsInfo(regionId) {
        try {
            const response = await fetch(`${appUrl}/search/regions/?id=${regionId}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const { results } = await response.json();
            if (!results?.length) return { title: `Region Extraction ${regionId}` };

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
            return { title: `Region Extraction ${regionId}` };
        }
    }

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

    function selectAllRegions() {
        const allIds = Array.from(get(documentNodes).keys());
        selectedRegions.set(new Set(allIds));
    }

    function applyDefaultThreshold() {
        if (!get(selectedCategories).includes(0)) return;

        const { min, max } = get(pairStats).scoreRange || {};
        if (min == null || max == null) return;

        if (get(threshold) === min) {
            threshold.set((min + max) / 2);
            // scoreMode.set('topk');
            // topK.set(2);
            // mutualTopK.set(true);
        }
    }

    const matrixMode = writable('filtered'); // 'all' | 'filtered'
    const normalizeByPages = writable(false);

    const visiblePairIds = derived(filteredPairs, ($pairs) => {
        const set = new Set();
        for (const p of $pairs) {
            set.add(`${p.id_1}-${p.id_2}`);
        }
        return set;
    });

    const filteredDocPairStats = derived(filteredPairs, ($pairs) => {
        const scoreCount = new Map();
        if (!$pairs?.length) return {scoreCount, scoreRange: {min: 0, max: 0, range: 0}};

        let min = Infinity, max = -Infinity;
        for (const p of $pairs) {
            const key = p.regions_id_1 < p.regions_id_2
                ? `${p.regions_id_1}-${p.regions_id_2}`
                : `${p.regions_id_2}-${p.regions_id_1}`;
            const entry = scoreCount.get(key) || {score: 0, count: 0};
            entry.score += p.weightedScore || 0;
            entry.count++;
            scoreCount.set(key, entry);
        }

        for (const {score} of scoreCount.values()) {
            if (score < min) min = score;
            if (score > max) max = score;
        }
        if (min === Infinity) min = max = 0;

        return {scoreCount, scoreRange: {min, max, range: max - min}};
    });

    const filteredDocStats = derived(filteredPairs, ($pairs) => {
        const scoreCount = new Map();
        if (!$pairs?.length) return {scoreCount, countRange: {min: 0, max: 0, range: 0}};

        for (const p of $pairs) {
            for (const rid of [p.regions_id_1, p.regions_id_2]) {
                const entry = scoreCount.get(rid) || {score: 0, count: 0};
                entry.score += p.weightedScore || 0;
                entry.count++;
                scoreCount.set(rid, entry);
            }
        }

        let min = Infinity, max = -Infinity;
        for (const {count} of scoreCount.values()) {
            if (count < min) min = count;
            if (count > max) max = count;
        }
        if (min === Infinity) min = max = 0;

        return {scoreCount, countRange: {min, max, range: max - min}};
    });

    const activeDocPairStats = derived(
        [matrixMode, docPairStats, filteredDocPairStats],
        ([$mode, $all, $filtered]) => $mode === 'filtered' ? $filtered : $all
    );

    const activeDocStats = derived(
        [matrixMode, documentStats, filteredDocStats],
        ([$mode, $all, $filtered]) => $mode === 'filtered' ? $filtered : $all
    );

    // Page counts per document (for normalization)
    const pageCountMap = derived(documentNodes, ($docs) => {
        const map = new Map();
        for (const [id, doc] of $docs) {
            map.set(id, Math.max(1, doc.images?.length || doc.img_nb || 1));
        }
        return map;
    });

    return {
        error,
        loadingProgress,
        cancelLoading: () => {
            if (abortController) {
                abortController.abort();
                loading.set(false);
            }
        },

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
        selectAllRegions,
        buildAlignedImageMatrix,

        threshold,
        setThreshold: (t) => threshold.set(t),
        topK,
        setTopK: (k) => topK.set(k),
        mutualTopK,
        setMutualTopK: (b) => mutualTopK.set(b),
        scoreMode,
        setScoreMode: (m) => scoreMode.set(m),

        matrixMode,
        setMatrixMode: (m) => matrixMode.set(m),
        normalizeByPages,
        setNormalizeByPages: (b) => normalizeByPages.set(b),
        activeDocPairStats,
        activeDocStats,
        pageCountMap,
        visiblePairIds,
    };
}
