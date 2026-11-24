import {derived, writable, get} from "svelte/store";

import {appUrl, aiiinotateUrl} from "../constants.js";

// TO DELETE
// import {aiiinotateUrl} from "../constants.js";
// const appUrl = "https://vhs.huma-num.fr";
// TO DELETE

const createWorker = () => new Worker(
    "/static/js/pairWorker.js",
    { type: "module" }
);

/** categories of a pair, the user match of the current user counting as category 5 */
export const pairCats = p => p.userMatch ? [p.category, 5] : [p.category];

const NO_RANK = 65535, NO_CAT = 255;
const rankOf = r => r === NO_RANK ? Infinity : r;

/** pairs kept as the worker's typed columns, pair objects being built on demand by pairAt */
function pairTable(columns, names, docDigits, imgMap) {
    return {
        ...columns,
        names,
        n: columns.id1.length,
        imgs: names.map(name => imgMap.get(name)),
        nameIdx: new Map(names.map((name, j) => [name, j])),
        docIdx: new Map(docDigits.map((d, k) => [d, k])),
        D: docDigits.length,
        removed: new Uint8Array(names.length),
    };
}

function makePair(t, i) {
    const a = t.imgs[t.id1[i]], b = t.imgs[t.id2[i]];
    return {
        id_1: a.id,
        id_2: b.id,
        digit_1: a.digit,
        digit_2: b.digit,
        page_1: a.canvas,
        page_2: b.canvas,
        score: isNaN(t.score[i]) ? null : Math.round(t.score[i] * 1e4) / 1e4,
        weightedScore: t.w[i],
        category: t.cat[i] === NO_CAT ? null : t.cat[i],
        userMatch: !!t.um[i],
        similarityType: t.st[i],
        rank_1: rankOf(t.rank1[i]),
        rank_2: rankOf(t.rank2[i]),
    };
}

/** indices of the pairs whose images are both kept by imgOk (Uint8Array by image index), in score order */
function* orderedPairs(t, imgOk) {
    for (let k = 0; k < t.n; k++) {
        const i = t.order[k];
        if (imgOk[t.id1[i]] && imgOk[t.id2[i]]) yield i;
    }
}

const imgMask = (t, digits) => t.imgs.map((img, j) => img && !t.removed[j] && digits.has(img.digit) ? 1 : 0);

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
    // documentSetId = 627; // Set gros
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

    /** pairTable of the loaded pairs */
    const allPairs = writable(null);
    let table = null;
    allPairs.subscribe(t => table = t);
    /** Map<pair index, pair> of the current filteredPairs, so that pairAt returns the same objects */
    let visible = new Map();
    const pairAt = i => visible.get(i) ?? makePair(table, i);

    // web worker for processing pairs
    let worker;

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

    const regionCounts = writable(new Map());
    dsInfoPromise.then(info => Promise.all(
        Object.values(info?.Digitization || {}).map(({id, ref}) =>
            fetch(`${aiiinotateUrl}/annotations/2/count?manifestShortId=${ref}`)
                .then(r => r.ok ? r.json() : Promise.reject(r.statusText))
                .then(({count}) => [id, count])
                .catch(e => { console.error(`Error fetching region count for ${ref}`, e); return [id, null]; })
        )
    )).then(entries => regionCounts.set(new Map(entries)));

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

        worker?.terminate();

        const loadPromise = new Promise((resolve, reject) => {
            loading.set(true);
            loadingProgress.set({ loaded: 0, done: false });
            error.set(null);

            worker = createWorker();

            worker.onmessage = async (e) => {
                const { type } = e.data;

                if (type === "progress") {
                    loadingProgress.set({ loaded: e.data.count, done: false });
                    return;
                }

                if (type === "error") return worker.onerror(e.data);

                if (type !== "complete") return;

                const {
                    columns,
                    docDigits,
                    imageIds,
                    imageNodes: imgMap,
                    categories: cats,
                    stats
                } = e.data;
                const t = pairTable(columns, imageIds, docDigits, imgMap);

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
                    pairs: t.n,
                    images: imgMap.size,
                    categories: cats
                });

                allPairs.set(t);
                catOverrides.clear();
                pairCat.set(findCategory);

                loading.set(false);
                loadingProgress.set({ loaded: t.n, done: true });

                worker.terminate();
                worker = null;
                resolve(t.n);
            };

            worker.onerror = (err) => {
                console.error("Worker error", err);
                error.set(`Worker error: ${err.message}`);
                loading.set(false);
                reject(err);
            };

            worker.postMessage({ url: `${appUrl}/document-set/${documentSetId}/pairs/stream?category=${$cats.join(",")}` });
        });

        set(loadPromise);
    });

    const filteredPairs = derived(
        [allPairs, threshold, topK, mutualTopK, selectedDocuments, scoreFilter],
        ([t, $threshold, $topK, $mutual, $regions, $scoreFilter]) => {
            visible = new Map();
            if (!t) return [];
            const result = [];

            const $mode = get(scoreMode);
            const imgOk = imgMask(t, $regions);

            for (let k = 0; k < t.n; k++) {
                const i = t.order[k];

                if ($mode === "threshold" && $scoreFilter) {
                    if (t.w[i] < $threshold) break;
                }

                if (!imgOk[t.id1[i]] || !imgOk[t.id2[i]]) continue;

                if ($mode === "topk" && $topK !== null && $scoreFilter) {
                    const r1Rank = rankOf(t.rank1[i]);
                    const r2Rank = rankOf(t.rank2[i]);

                    if ($mutual) {
                        if (r1Rank > $topK || r2Rank > $topK) continue;
                    } else {
                        if (r1Rank > $topK && r2Rank > $topK) continue;
                    }
                }

                const p = makePair(t, i);
                visible.set(i, p);
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
        const used = new Set();
        for (const p of $pairs) {
            const key = p.digit_1 < p.digit_2
                ? `${p.digit_1}-${p.digit_2}`
                : `${p.digit_2}-${p.digit_1}`;
            const entry = scoreCount.get(key) || {score: 0, count: 0, matchScore: 0, matchCount: 0};
            entry.score += p.weightedScore || 0;
            entry.count++;
            const u1 = `${key}:${p.id_1}`, u2 = `${key}:${p.id_2}`;
            if (!used.has(u1) && !used.has(u2)) {
                used.add(u1).add(u2);
                entry.matchScore += p.weightedScore || 0;
                entry.matchCount++;
            }
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

    const hideEmpty = writable(false);
    const visibleDocuments = derived(
        [sortedDocumentNodes, selectedDocuments, hideEmpty, filteredPairs],
        ([$nodes, $selected, $hide, $pairs]) => {
            const linked = new Set();
            if ($hide) for (const p of $pairs) if (p.digit_1 !== p.digit_2) linked.add(p.digit_1).add(p.digit_2);
            return $nodes
                .map(([, meta]) => meta)
                .filter(d => $selected.has(d.id) && (!$hide || linked.has(d.id)));
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
        const t = table;
        const a = t?.docIdx.get(doc1Id), b = t?.docIdx.get(doc2Id);
        if (a == null || b == null) return [];
        const k = Math.min(a, b) * t.D + Math.max(a, b);
        const pairs = [];
        for (const i of t.byDocPair.subarray(t.dpStart[k], t.dpStart[k + 1])) {
            const p = visible.size > 0 ? visible.get(i) : pairAt(i);
            if (p) pairs.push(p);
        }
        return pairs;
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
                    if (!entry.byTargetDoc.has(targetDoc.id)) entry.byTargetDoc.set(targetDoc.id, new Map());
                    entry.byTargetDoc.get(targetDoc.id).set(target.image.id, target.image);
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
                    const images = onlyOneMatch ? [entry.image] : [...entry.values()];
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
            if (!byDoc.has(target.doc.id)) byDoc.set(target.doc.id, { doc: target.doc, matches: new Map() });
            const matches = byDoc.get(target.doc.id).matches;
            const existing = matches.get(target.image.id);
            if (!existing || target.score > existing.score) matches.set(target.image.id, target);
        }

        const targets = [...byDoc.values()].map(({ doc, matches }) => {
            const sorted = [...matches.values()].sort((a, b) => b.score - a.score);
            return { doc, images: sorted.map(m => m.image), bestImageId: sorted[0].image.id };
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

    function buildNetworkMatches({ baseDocId, docIds, imageIds }) {
        const imgNodes = get(imageNodes);
        const docNodes = get(documentNodes);
        const baseDoc = docNodes.get(baseDocId);
        if (!baseDoc) return { matches: [], columns: [] };

        const byDoc = new Map();
        for (const id of imageIds) {
            const img = imgNodes.get(id);
            if (!img) continue;
            if (!byDoc.has(img.digit)) byDoc.set(img.digit, []);
            byDoc.get(img.digit).push(img);
        }

        const targets = [...docIds]
            .filter(id => id !== baseDocId && byDoc.has(id))
            .map(id => ({ doc: docNodes.get(id), images: byDoc.get(id) }))
            .filter(t => t.doc);

        const row = [
            { images: byDoc.get(baseDocId) || [], doc: baseDoc },
            ...targets,
        ];
        const columns = [{ doc: baseDoc }, ...targets.map(t => ({ doc: t.doc }))];
        return assignIndices({ matches: [row], columns });
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

    function toggleAllDocuments(select = true) {
        selectedDocuments.set(new Set(select ? get(documentNodes).keys() : []));
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

    /** Map<pair index, pair> of the visible pairs */
    const visiblePairIds = derived(filteredPairs, () => visible);

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

    const imageCountMap = derived([documentNodes, regionCounts], ([$docs, $counts]) =>
        new Map([...$docs].map(([id, doc]) => [id, Math.max(1, $counts.get(id) ?? 0, doc.images.length)]))
    );

    /** index of the pair (a, b) */
    const findPair = (a, b) => {
        const t = table, j = t?.nameIdx.get(a), k = t?.nameIdx.get(b);
        if (j == null || k == null) return null;
        for (let s = t.start[j]; s < t.start[j + 1]; s++) {
            const i = t.byImage[s];
            if (t.id1[i] === k || t.id2[i] === k) return i;
        }
        return null;
    };
    const categoryOf = i => i == null || table.cat[i] === NO_CAT ? null : table.cat[i];
    const catKey = (a, b) => a < b ? `${a}-${b}` : `${b}-${a}`;
    /** Map<"id1-id2", category> of categories patched for pairs that are not loaded */
    const catOverrides = new Map();
    const findCategory = (a, b) => categoryOf(findPair(a, b)) ?? catOverrides.get(catKey(a, b)) ?? null;
    /** (img1, img2) => category; re-set (functions always notify subscribers) on load and by patchPairs */
    const pairCat = writable(findCategory);

    /**
     * Light refresh: patch already-loaded pairs in place and re-emit without re-streaming from the worker
     * `updates`: [{img_1, img_2, category}]
     * // TODO make more versatile => allow to remove pairs
     */
    const patchPairs = (updates) => {
        for (const { img_1, img_2, category } of updates) {
            const i = findPair(img_1, img_2);
            if (i == null) {
                catOverrides.set(catKey(img_1, img_2), category);
                continue;
            }
            table.cat[i] = category ?? NO_CAT;
            const p = visible.get(i);
            if (p) p.category = category;
        }
        pairCat.set(findCategory);
    };

    /** pairs whose documents are both in digits, in score order */
    const pairsOfDocuments = digits => table ? Array.from(orderedPairs(table, imgMask(table, digits)), i => pairAt(i)) : [];

    const removeImages = (ids) => {
        const t = table;
        for (const id of ids) {
            const j = t.nameIdx.get(id);
            if (j != null) t.removed[j] = 1;
        }
        const keptIdx = new Uint8Array(t.names.length);
        let pairs = 0;
        for (let i = 0; i < t.n; i++) {
            if (t.removed[t.id1[i]] || t.removed[t.id2[i]]) continue;
            keptIdx[t.id1[i]] = keptIdx[t.id2[i]] = 1;
            pairs++;
        }
        const kept = new Set(t.names.filter((_, j) => keptIdx[j]));
        imageNodes.update(m => (m.forEach((_, id) => kept.has(id) || m.delete(id)), m));
        documentNodes.update(m => (m.forEach(d => d.images = d.images.filter(i => kept.has(i.id))), m));
        docSetNumber.update(n => ({...n, pairs, images: kept.size}));
        allPairs.set(t);
    };


    return {
        documentSetId,
        docSetId: documentSetId,

        error,
        loadingProgress,

        allPairs,
        pairsOfDocuments,
        visiblePairs: filteredPairs,
        visibleDocuments,
        pairCat,
        imageNodes,
        documentNodes,
        witnessNodes,
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
        removeImages,
        toggleCategory,
        toggleDoc,
        toggleAllDocuments,
        getFilteredPairsForDocPair,
        buildMatchesForAnchor,
        buildFriezeMatches,
        buildClusterMatches,
        buildNetworkMatches,
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
        regionCounts,
        imageCountMap,
        visiblePairIds,
        coverageData,
        hideEmpty,
        setHideEmpty: (b) => hideEmpty.set(b),
    };
}
