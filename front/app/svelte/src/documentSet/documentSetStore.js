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

    // TO DELETE
    // const documentSetId = 413; // histoire naturelle
    // const documentSetId = 414; // nicolas
    // const documentSetId = 437; // physiologus
    // const documentSetId = 416; // de materia medica
    // const documentSetId = 417; // traité de géométrie
    // const documentSetId = 418; // encyclopédie mathématique
    // const documentSetId = 436; // Jombert complet
    // const documentSetId = 432; // Jombert incomplet
    // documentSetId = 455; // Set benchmark
    // TO DELETE

    const error = writable(null);
    const loading = writable(false);
    const loadingProgress = writable({ loaded: 0, done: false });

    const selectedCategories = writable([]);
    const selectedDocuments = writable(new Set());
    const selectedNodes = writable([]);

    const scoreFilter = writable(true);
    const threshold = writable(0.5);
    const topK = writable(3);
    const mutualTopK = writable(true);
    const scoreMode = writable("topk");
    const onlyOneSelectedCategory = derived(selectedCategories, $cats =>
        $cats.length === 1
    );

    const allPairs = writable([]);

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
     * Document nodes: Map<digitizationId, digitizationData>
     */
    const documentNodes = writable(new Map());
    const witnessNodes = writable(new Map());
    const seriesNodes = writable(new Map());

    /**
     * {
     *     "Digitization": { "id", "color", "title", "min_date", "max_date", "Witness": [serId], "Series": [serId] }
     *     "Witness":      { "id", "color", "title", "min_date", "max_date", "Digitization": [digitIds], "Series": [serId] }
     *     "Series":       { "id", "color", "title", "min_date", "max_date", "Digitization": [digitIds], "Witness": [witIds] }
     * }
     * @type {Promise<any>}
     */
    const dsInfoPromise = fetch(`${appUrl}/document-set/${documentSetId}/info`)
        .then(r => r.ok ? r.json() : Promise.reject(r.statusText))
        .catch(e => { error.set(`Error fetching document set info: ${e}`); return null; });

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

                        const dsInfo = await dsInfoPromise;
                        const digits = dsInfo?.Digitization || {};

                        const digitIds = Object.keys(digits).map(Number);
                        if (get(selectedDocuments).size === 0) {
                            selectedDocuments.set(new Set(digitIds));
                        }

                        const docMap = new Map();
                        digitIds.forEach(id => {
                            docMap.set(id, {
                                images: [],
                                title: `Digitization ${id}`,
                                color: "hsl(0, 0%, 50%)",
                                ...digits[id] || {},
                            });
                        });

                        docMap.forEach(doc => {
                            const range = [doc.min_date, doc.max_date].filter(Boolean);
                            if (range.length) doc.title += ` (${[...new Set(range)].join("–")})`;
                        });

                        if (dsInfo) {
                            witnessNodes.set(new Map(Object.values(dsInfo.Witness).map(w => [w.id, w])));
                            seriesNodes.set(new Map(Object.values(dsInfo.Series).map(s => [s.id, s])));
                        }

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

    const filteredPairs = derived(
        [allPairs, threshold, topK, mutualTopK, selectedDocuments, scoreFilter],
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

    const docSort = writable("title");
    const sortWith = {
        id:        (a, b) => a[0] - b[0],
        witnessId: (a, b) => (a[1].witness_id || 0) - (b[1].witness_id || 0),
        title:     (a, b) => (a[1].title || "").localeCompare(b[1].title || ""),
        date:      (a, b) => (a[1].min_date || 0) - (b[1].min_date || 0),
    };
    const sortedDocumentNodes = derived(
        [documentNodes, docSort],
        ([$nodes, $sort]) => Array.from($nodes).sort(sortWith[$sort])
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

    function getFilteredPairsForDocPair(doc1Id, doc2Id) {
        const $pairIndex = get(pairIndex);
        const $visibleIds = get(visiblePairIds);
        const key = doc1Id < doc2Id ? `${doc1Id}-${doc2Id}` : `${doc2Id}-${doc1Id}`;
        const pairs = $pairIndex.byDocPair.get(key) || [];
        return $visibleIds.size > 0
            ? pairs.filter(p => $visibleIds.has(`${p.id_1}-${p.id_2}`))
            : pairs;
    }

    function otherSide(pair, anchorDocId, anchorImgId, imgNodes, docNodes) {
        const isFrom1 = pair.digit_1 === anchorDocId && (anchorImgId == null || pair.id_1 === anchorImgId);
        const isFrom2 = pair.digit_2 === anchorDocId && (anchorImgId == null || pair.id_2 === anchorImgId);
        if (!isFrom1 && !isFrom2) return null;
        const targetId = isFrom1 ? pair.id_2 : pair.id_1;
        const targetDocId = isFrom1 ? pair.digit_2 : pair.digit_1;
        const image = imgNodes.get(targetId);
        const doc = docNodes.get(targetDocId);
        return image && doc ? { image, doc, score: pair.weightedScore } : null;
    }

    function assignIndices(data) {
        let idx = 0;
        for (const row of data.matches) {
            for (const cell of row) {
                if (!cell) continue;
                cell.indices = cell.images.map(() => idx++);
            }
        }
        return data;
    }

    function buildMatchesForAnchor(anchorDoc, targetDocs, anchorImageIds = null, onlyOneMatch = false, onlyAnchorWithMatches = false) {
        const byAnchor = new Map();
        const imgNodes = get(imageNodes);
        const docNodes = get(documentNodes);

        const anchorImages = anchorImageIds
            ? (anchorDoc.images || []).filter(img => anchorImageIds.has(img.id))
            : (anchorDoc.images || []);

        for (const img of anchorImages) {
            byAnchor.set(img.id, { anchor: img, byTargetDoc: new Map() });
        }

        for (const targetDoc of targetDocs) {
            if (targetDoc.id === anchorDoc.id) continue;
            const pairs = getFilteredPairsForDocPair(anchorDoc.id, targetDoc.id);
            for (const p of pairs) {
                const anchorOnSide1 = p.digit_1 === anchorDoc.id;
                const anchorId = anchorOnSide1 ? p.id_1 : p.id_2;
                const target = otherSide(p, anchorDoc.id, anchorId, imgNodes, docNodes);
                const entry = byAnchor.get(anchorId);
                if (!entry || !target) continue;

                if (onlyOneMatch) {
                    const existing = entry.byTargetDoc.get(targetDoc.id);
                    if (!existing || p.weightedScore > existing.score) {
                        entry.byTargetDoc.set(targetDoc.id, { image: target.image, score: p.weightedScore });
                    }
                } else {
                    if (!entry.byTargetDoc.has(targetDoc.id)) entry.byTargetDoc.set(targetDoc.id, []);
                    entry.byTargetDoc.get(targetDoc.id).push(target.image);
                }
            }
        }

        const rows = Array.from(byAnchor.values())
            .sort((a, b) => (a.anchor.canvas ?? Infinity) - (b.anchor.canvas ?? Infinity))
            .map(({ anchor, byTargetDoc }) => [
                { images: [anchor], doc: anchorDoc },
                ...targetDocs.map(td => {
                    const entry = byTargetDoc.get(td.id);
                    if (!entry) return null;
                    const images = onlyOneMatch ? [entry.image] : entry;
                    return { images, doc: td };
                }),
            ]).filter(row => onlyAnchorWithMatches ? row.slice(1).some(c => c) : row);

        const columns = [{ doc: anchorDoc }, ...targetDocs.map(d => ({ doc: d }))];
        return assignIndices({ matches: rows, columns });
    }

    function buildFriezeMatches(frieze, pairs) {
        const imgNodes = get(imageNodes);
        const docNodes = get(documentNodes);
        const baseDoc = docNodes.get(frieze.baseDocId);
        const sourceImage = imgNodes.get(frieze.imageId);
        if (!baseDoc || !sourceImage) return { matches: [], columns: [] };

        const byDoc = new Map();
        for (const p of pairs) {
            const target = otherSide(p, frieze.baseDocId, frieze.imageId, imgNodes, docNodes);
            if (!target || target.doc.id === frieze.baseDocId) continue;
            if (!byDoc.has(target.doc.id)) byDoc.set(target.doc.id, { doc: target.doc, matches: [] });
            byDoc.get(target.doc.id).matches.push(target);
        }

        const targets = [...byDoc.values()].map(({ doc, matches }) => {
            matches.sort((a, b) => b.score - a.score);
            return { doc, images: matches.map(m => m.image), bestImageId: matches[0].image.id };
        });

        const row = [
            { images: [sourceImage], doc: baseDoc, bestImageId: sourceImage.id },
            ...targets,
        ];
        const columns = [{ doc: baseDoc }, ...targets.map(t => ({ doc: t.doc }))];
        return assignIndices({ matches: [row], columns });
    }

    function buildClusterMatches({ baseDocId, docIds, imageIds }) {
        const docNodes = get(documentNodes);
        const baseDoc = docNodes.get(baseDocId);
        if (!baseDoc) return { matches: [], columns: [] };
        const targetDocs = [...docIds].map(id => docNodes.get(id)).filter(Boolean);
        const data = buildMatchesForAnchor(baseDoc, targetDocs, imageIds, true, targetDocs.length > 0);
        if (!targetDocs.length && data.matches.length) {
            const allImages = data.matches.flatMap(row => row[0]?.images ?? []);
            return {
                matches: [[{ images: allImages, doc: baseDoc, indices: allImages.map((_, i) => i) }]],
                columns: [{ doc: baseDoc }],
            };
        }
        return data;
    }

    function toggleCategory(categoryId) {
        selectedCategories.update(cats => {
            const index = cats.indexOf(categoryId);
            return index > -1
                ? cats.filter(c => c !== categoryId)
                : [...cats, categoryId].sort((a, b) => a - b);
        });
    }

    function toggleDoc(docId) {
        selectedDocuments.update(docs => {
            const newDocs = new Set(docs);
            newDocs.has(docId) ? newDocs.delete(docId) : newDocs.add(docId);
            return newDocs;
        });
    }

    function selectAllDocuments() {
        const allIds = Array.from(get(documentNodes).keys());
        selectedDocuments.set(new Set(allIds));
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

    const coverageData = derived(filteredPairs, ($pairs) => {
        const map = new Map();
        for (const p of $pairs) {
            const k1 = `${p.digit_1}-${p.digit_2}`;
            const k2 = `${p.digit_2}-${p.digit_1}`;
            if (!map.has(k1)) map.set(k1, new Set());
            if (!map.has(k2)) map.set(k2, new Set());
            map.get(k1).add(p.id_1);
            map.get(k2).add(p.id_2);
        }
        return map;
    });

    const imageCountMap = derived(documentNodes, ($docs) => {
        const map = new Map();
        for (const [id, doc] of $docs) {
            map.set(id, Math.max(1, doc.images?.length || doc.img_nb || 1));
        }
        return map;
    });

    const hideEmpty = writable(false);

    /**
     * Light refresh: patch already-loaded pairs in place and re-emit without re-streaming from the worker
     * `updates`: [{img_1, img_2, category}]
     * // TODO make more versatile => allow to remove pairs
     */
    const patchPairs = (updates) => {
        const map = new Map(updates.map(u => [`${u.img_1}-${u.img_2}`, u.category]));
        allPairs.update($pairs => {
            for (const p of $pairs) {
                const cat = map.get(`${p.id_1}-${p.id_2}`) ?? map.get(`${p.id_2}-${p.id_1}`);
                if (cat !== undefined) p.category = cat;
            }
            return $pairs;
        });
    };

    /** Map<"id1-id2", category> of visible pairs, for category selection state */
    const pairCat = derived(filteredPairs, $pairs =>
        new Map($pairs.map(p => [`${p.id_1}-${p.id_2}`, p.category]))
    );

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
        pairCat,
        pairIndex,
        imageNodes,
        documentNodes,
        docSort,
        sortedDocumentNodes,
        fetchPairs,
        imageNetwork,
        documentNetwork,
        selectedCategories,
        onlyOneSelectedCategory,
        pairStats,
        documentStats,
        imageStats,
        docPairStats,
        docSetNumber,
        selectedNodes,
        selectedDocuments,
        updateSelectedNodes: (nodes) => selectedNodes.set(nodes),
        toggleCategory,
        toggleDoc,
        selectAllDocuments,
        getFilteredPairsForDocPair,
        buildMatchesForAnchor,
        buildFriezeMatches,
        buildClusterMatches,
        patchPairs,

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
        coverageData,
        hideEmpty,
        setHideEmpty: (b) => hideEmpty.set(b),
    };
}
