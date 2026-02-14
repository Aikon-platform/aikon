import {derived, writable, get} from "svelte/store";
import {extractNb, generateColor} from "../utils.js";
import { streamPairsToWorker } from "./pairStreamReader.js";

import {appUrl} from "../constants.js";

// TO DELETE
// const appUrl = "https://vhs.huma-num.fr";
// TO DELETE

const createWorker = () => new Worker(
    "/static/js/pairWorker.js",
    { type: "module" }
);

export function createDocumentSetStore(documentSetId) {
    const error = writable(null);
    const loading = writable(false);
    const loadingProgress = writable({ loaded: 0, done: false });

    const selectedCategories = writable([]);
    const selectedRegions = writable(new Set());
    const selectedNodes = writable([]);

    const scoreFilter = writable(true);
    const threshold = writable(0.5);
    const topK = writable(3);
    const mutualTopK = writable(true);
    const scoreMode = writable("topk");
    const onlyExactMatches = derived(selectedCategories, $cats =>
        $cats.length === 1 && $cats[0] === 1
    );

    const allPairs = writable([]);
    const regionsMetadata = writable(new Map());

    // web worker for processing pairs
    let worker;
    let abortController = null;

    const pairIndex = writable({
        byImage: new Map(),
        byDocPair: new Map(),
        byDoc: new Map(),
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

        if (worker) worker.terminate() && (worker = null);
        if (abortController) abortController.abort();
        abortController = new AbortController();

        // TO DELETE
        // const documentSetId = 413; // histoire naturelle
        // const documentSetId = 414; // nicolas
        // const documentSetId = 437; // physiologus
        // const documentSetId = 416; // de materia medica
        // const documentSetId = 417; // traité de géométrie
        // const documentSetId = 418; // encyclopédie mathématique
        // const documentSetId = 436; // Jombert complet
        // const documentSetId = 432; // Jombert incomplet
        // const documentSetId = 408;
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

                        if (type === "progress") {
                            loadingProgress.set({ loaded: e.data.count, done: false });
                            return;
                        }

                        if (type !== "complete") return;

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

                        const digitIds = Array.from(stats.documentStats.scoreCount.keys());

                        if (get(selectedRegions).size === 0) {
                            selectedRegions.set(new Set(digitIds));
                        }

                        const results = await Promise.all(
                            digitIds.map(id => getDigitInfo(id).then(info => ({ id, info })))
                        );

                        const metaMap = new Map();
                        results.forEach(({ id, info }) => metaMap.set(id, info));
                        regionsMetadata.set(metaMap);

                        const docMap = new Map();
                        digitIds.forEach((id, index) => {
                            const info = metaMap.get(id) || {};
                            docMap.set(id, {
                                id,
                                title: info.title || `Digitization ${id}`,
                                color: info.color || generateColor(index),
                                images: [],
                                ...info
                            });
                        });

                        imgMap.forEach(img => {
                            const doc = docMap.get(img.digit);
                            if (doc) {
                                img.color = doc.color;
                                img.title = `${doc.title} | Page ${img.canvas}`;
                                doc.images.push(img);
                            }
                        });

                        // TODO add normalizedScore = totalScore / images.length

                        docMap.forEach(doc => {
                            doc.images.sort((a, b) => {
                                if (a.canvas !== b.canvas) return a.canvas - b.canvas;
                                return (parseInt(a.xywh?.[1]) || 0) - (parseInt(b.xywh?.[1]) || 0);
                            })
                            return doc;
                        });

                        imageNodes.set(imgMap);
                        documentNodes.set(docMap);

                        docSetNumber.set({
                            documents: digitIds.length,
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

                    const url = `${appUrl}/document-set/${documentSetId}/pairs/stream?category=${$cats.join(",")}`;

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
                    if (e.name === "AbortError") {
                        console.log("Request aborted");
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

    async function getDigitInfo(digitId) {
        try {
            const response = await fetch(`${appUrl}/search/digitization/?id=${digitId}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const { results } = await response.json();
            if (!results?.length) return { title: `Digitization ${digitId}` };

            const digit = results[0];
            const [, ...titleParts] = (digit.title || "").split(" | ");

            return {
                title: titleParts.join(" | ") || digit.title,
                ref: digit.ref,
                witnessId: digit.witness_id,
                zeros: digit.zeros,
                img_nb: digit.img_nb,
                url: digit.url
            };
        } catch (e) {
            error.set(`Error fetching digitization #${digitId}: ${e.message}`);
            return { title: `Digitization ${digitId}` };
        }
    }

    const filteredPairs = derived(
        [allPairs, threshold, topK, mutualTopK, selectedRegions, scoreFilter],
        ([$pairs, $threshold, $topK, $mutual, $regions, $scoreFilter]) => {
            if (!$pairs) return [];
            const result = [];

            const $mode = get(scoreMode);

            for (let i = 0; i < $pairs.length; i++) {
                const p = $pairs[i];

                if ($mode === "threshold" && $scoreFilter) {
                    if (p.weightedScore < $threshold) break;
                }

                if (!$regions.has(p.digit_1) || !$regions.has(p.digit_2)) continue;

                if ($mode === "topk" && $topK !== null && $scoreFilter) {
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
                activeDocIds.add(p.digit_1);
                activeDocIds.add(p.digit_2);
            }

            const docs = [];
            activeDocIds.forEach(id => {
                const doc = $docNodes.get(id);
                if (doc) docs.push(doc);
            });

            return docs.sort((a, b) => b.id - a.id);
        }
    );

    const filteredDocPairStats = derived(filteredPairs, ($pairs) => {
        const scoreCount = new Map();
        if (!$pairs?.length) return {scoreCount, scoreRange: {min: 0, max: 0, range: 0}};

        let min = Infinity, max = -Infinity;
        for (const p of $pairs) {
            const key = p.digit_1 < p.digit_2
                ? `${p.digit_1}-${p.digit_2}`
                : `${p.digit_2}-${p.digit_1}`;
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
            for (const did of [p.digit_1, p.digit_2]) {
                const entry = scoreCount.get(did) || {score: 0, count: 0};
                entry.score += p.weightedScore || 0;
                entry.count++;
                scoreCount.set(did, entry);
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
                    label: `Digitization: ${nodeData.digit}\nPage: ${nodeData.canvas}\nConnections: ${count}\nTotal score: ${score.toFixed(2)}`
                });
            }
        }

        return { nodes, links };
    });

    const documentNetwork = derived([filteredDocs], ([$docNodes]) => {
        if (!$docNodes.length) return { nodes: [], links: [] };

        const $docStats = get(filteredDocStats);
        const $docPairStats = get(filteredDocPairStats);

        const nodes = $docNodes.map(n => {
            const stats = $docStats.scoreCount?.get(n.id);
            const { count = 0, score = 0 } = stats || {};

            return {
                ...n,
                radius: normalizeRadius(count, $docStats.countRange),
                label: `${n.title}\nImages: ${count}\nTotal score: ${score.toFixed(2)}`,
            };
        });

        const links = Array.from($docPairStats.scoreCount.entries()).map(([key, pairStat]) => {
            const [source, target] = key.split("-").map(Number);
            const {strength, distance, width} = calculateLinkProps(pairStat.score, $docPairStats.scoreRange);
            return {
                source, target, strength, distance, width
            };
        });


        return { nodes, links };
    });

    function buildAlignedImageMatrix(orderedSelection) {
        if (!orderedSelection.length) return {regions: [], rows: []};

        const $documentNodes = get(documentNodes);
        const $pairIndex = get(pairIndex);
        const $onlyExactMatches = get(onlyExactMatches);

        const firstDigitId = orderedSelection[0];

        const firstDoc = $documentNodes.get(firstDigitId);
        if (!firstDoc?.images) return {regions: orderedSelection, rows: []};
        const firstImages = firstDoc.images;

        const findPairs = (imgId, sourceDigitId, targetDigitId) => {
            const pairKey = sourceDigitId < targetDigitId
                ? `${sourceDigitId}-${targetDigitId}`
                : `${targetDigitId}-${sourceDigitId}`;
            const pairs = $pairIndex.byDocPair.get(pairKey) || [];

            return pairs
                .filter(p =>
                    (p.id_1 === imgId && p.digit_1 === sourceDigitId) ||
                    (p.id_2 === imgId && p.digit_2 === sourceDigitId)
                )
                .map(p => {
                    const isFirst = p.id_1 === imgId;
                    return {
                        id: isFirst ? p.id_2 : p.id_1,
                        page: isFirst ? p.page_2 : p.page_1,
                        rank: isFirst ? p.rank_1 : p.rank_2,
                        otherRank: isFirst ? p.rank_2 : p.rank_1,
                        score: p.weightedScore
                    };
                });
        };

        const findBestMatch = (imgId, sourceDigitId, targetDigitId) => {
            const pairs = findPairs(imgId, sourceDigitId, targetDigitId);
            if (!pairs.length) return null;

            const mutualTop1 = pairs.find(p => p.rank <= 1 && p.otherRank <= 1);
            if (mutualTop1) return {id: mutualTop1.id, page: mutualTop1.page};

            const mutualTop2 = pairs.find(p => p.rank <= 2 && p.otherRank <= 2);
            if (mutualTop2) return {id: mutualTop2.id, page: mutualTop2.page};

            return null;
        };

        if (!$onlyExactMatches) {
            const rows = [];
            for (const firstImg of firstImages) {
                const row = {[firstDigitId]: {id: firstImg.id, page: firstImg.canvas}};

                for (let colIdx = 1; colIdx < orderedSelection.length; colIdx++) {
                    const targetDigitId = orderedSelection[colIdx];
                    const best = findBestMatch(firstImg.id, firstDigitId, targetDigitId);
                    if (best) row[targetDigitId] = best;
                }

                rows.push(row);
            }
            return {regions: orderedSelection, rows};
        }

        const allRows = [];

        for (const firstImg of firstImages) {
            let currentRows = [{[firstDigitId]: {id: firstImg.id, page: firstImg.canvas}}];

            for (let colIdx = 1; colIdx < orderedSelection.length; colIdx++) {
                const targetDigitId = orderedSelection[colIdx];
                const nextRows = [];

                for (const row of currentRows) {
                    const allPairsFound = [];

                    for (let srcIdx = 0; srcIdx < colIdx; srcIdx++) {
                        const sourceDigitId = orderedSelection[srcIdx];
                        if (row[sourceDigitId]) {
                            const pairs = findPairs(row[sourceDigitId].id, sourceDigitId, targetDigitId);
                            allPairsFound.push(...pairs);
                        }
                    }

                    if (allPairsFound.length === 0) {
                        nextRows.push(row);
                    } else {
                        const uniquePairs = new Map();
                        allPairsFound.forEach(p => {
                            if (!uniquePairs.has(p.id)) {
                                uniquePairs.set(p.id, {id: p.id, page: p.page});
                            }
                        });

                        for (const pair of uniquePairs.values()) {
                            const newRow = {...row, [targetDigitId]: pair};
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
            const key = orderedSelection.map(did => row[did]?.id || "").join("|");
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
        }
    }

    const normalizeByImages = writable(true);

    const visiblePairIds = derived(filteredPairs, ($pairs) => {
        const set = new Set();
        for (const p of $pairs) {
            set.add(`${p.id_1}-${p.id_2}`);
        }
        return set;
    });

    const imageCountMap = derived(documentNodes, ($docs) => {
        const map = new Map();
        for (const [id, doc] of $docs) {
            map.set(id, Math.max(1, doc.images?.length || doc.img_nb || 1));
        }
        return map;
    });

    return {
        documentSetId,
        docSetId: documentSetId,

        error,
        loadingProgress,
        cancelLoading: () => {
            if (abortController) {
                abortController.abort();
                loading.set(false);
            }
        },

        allPairs,
        visiblePairs: filteredPairs,
        pairIndex,
        documentNodes,
        imageNodes,
        fetchPairs,
        imageNetwork,
        documentNetwork,
        selectedCategories,
        onlyExactMatches,
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
        scoreFilter,
        setScoreFilter: (b) => scoreFilter.set(b),

        filteredDocPairStats,
        filteredDocStats,

        normalizeByImages,
        imageCountMap,
        visiblePairIds,
    };
}
