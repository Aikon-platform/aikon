import {derived, writable, get} from 'svelte/store';
import {extractNb, refToIIIFRoot, imageToPage, generateColor, initPagination, pageUpdate} from "../utils.js";
import {appUrl, regionsType} from "../constants.js";
// // TO DELETE
// import {regionsType} from "../constants.js";
// const appUrl = "https://vhs.huma-num.fr";
// // TO DELETE

export function createDocumentSetStore(documentSetId) {
    const error = writable(null);

    const selectedCategories = writable([1]);

    const selectedNodes = writable([]);

    const selectedRegions = writable(new Set());

    const threshold = writable(0.5);

    /**
     * All RegionsPair objects loaded in the current context
     */
    const allPairs = writable([]);

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

    function emptyStats() {
        return {
            count: 0,
            scoreCount: new Map(),
            scoreRange: {min: Infinity, max: -Infinity, range: null},
            countRange: {min: Infinity, max: -Infinity, range: null},
            links: 0,
            clusters: 0,
            density: 0
        };
    }

    const pairStats = writable({});
    const documentStats = writable({});
    const imageStats = writable({});
    const docPairStats = writable({});
    const docSetNumber = writable({
        documents: 0,
        pairs: 0,
        images: 0,
        categories: {}
    });

    const fetchPairs = derived(selectedCategories, ($selectedCategories, set) => {
        const promise = (async () => {
            try {
                // // TO DELETE
                // // const documentSetId = 413; // histoire naturelle
                // // const documentSetId = 414; // nicolas
                // const documentSetId = 415; // physiologus
                // // const documentSetId = 416; // de materia medica
                // // const documentSetId = 417; // traité de géométrie
                // // TO DELETE

                const response = await fetch(`${appUrl}/document-set/${documentSetId}/pairs?category=${$selectedCategories.join(',')}`);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);

                const data = await response.json();

                const index = { byImage: new Map(), byDocPair: new Map(), byDoc: new Map(), }
                const documentMap = new Map();
                const imageMap = new Map();

                const pStats = emptyStats();
                const docStats = emptyStats();
                const imgStats = emptyStats();
                const docPStats = emptyStats();
                const categories = {};
                // MARKER
                const imgToRegionsMap = new Map();

                const context = {
                    index,
                    documentMap,
                    imageMap,
                    imgToRegionsMap,
                    pStats,
                    docStats,
                    imgStats,
                    docPStats,
                    categories
                };

                const pairs = data.reduce((acc, pair) => {
                    if (pair.category === 4) {
                        return acc;
                    }
                    const score = pair.score ?? null;
                    if (score == null && pair.is_manual !== true) {
                        return acc;
                    }
                    if ($selectedCategories.includes(0) && pair.category === 0) {
                        if (pair.is_manual !== true && score < threshold) {
                            return acc;
                        }
                    }
                    acc.push(processPair(pair, context));
                    return acc;
                }, []);

                pStats.avgScore = pStats.count > 0 ? pStats.totalScore / pStats.count : 0;
                docStats.links = Array.from(docPStats.scoreCount.entries()).length;
                imgStats.links = pairs.length;
                docPStats.links = docPStats.scoreCount.size;

                computeDensity(docStats);
                computeDensity(imgStats);
                computeDensity(docPStats);

                computeRange(pStats);
                computeRange(docStats);
                computeRange(imgStats);
                computeRange(docPStats);

                const regionIds = Array.from(documentMap.keys());
                await Promise.all(
                    regionIds.map(async (rid, i) => {
                        const info = await getRegionsInfo(rid);
                        const color = generateColor(i);

                        const node = documentMap.get(rid);
                        Object.assign(node, {
                            title: info.title,
                            ref: info.ref,
                            witnessId: info.witnessId,
                            digitizationRef: info.digitizationRef,
                            zeros: info.zeros,
                            img_nb: info.img_nb,
                            url: info.url,
                            color
                        });
                    })
                );

                imageMap.forEach(imgData => {
                    const doc = documentMap.get(imgData.regionId);
                    imgData.class = 'Cluster';
                    imgData.color = doc?.color;
                    imgData.title = (doc?.title || `Region ${imgData.regionId}`) + `<br>Page ${imgData.canvas}`;
                });

                docSetNumber.set({
                    documents: regionIds.length,
                    pairs: pairs.length,
                    images: imgStats.count,
                    clusters: null,
                    categories
                });

                pairIndex.set(index);
                pairStats.set(pStats);
                documentStats.set(docStats);
                imageStats.set(imgStats);
                docPairStats.set(docPStats);
                selectedRegions.set(new Set(regionIds));
                documentNodes.set(documentMap);
                imageNodes.set(imageMap);
                allPairs.set(pairs.filter(Boolean)); // todo find a way to be more efficient than this
            } catch (e) {
                error.set(`Error processing pairs: ${e.message}`);
            }
        })();
        set(promise)
    });

    /**
     * param pair : similarity pair to update
     * {
     *      "img_1": "wit<id>_<digit><id>_<canvas_nb>_<coord>.jpg",
     *      "img_2": "wit<id>_<digit><id>_<canvas_nb>_<coord>.jpg",
     *      "regions_id_1": 1,
     *      "regions_id_2": 2,
     *      "score": 0.123,
     *      "category": 1,
     *      "category_x": [],
     *      "is_manual": false,
     *      "similarity_type": 1
     * }
     *
     * returns { pair } with added fields:
     *  {
     *      "id_1": "<region_id>_wit<id>_<digit><id>_<canvas_nb>_<coord>.jpg",
     *      "id_2": "<region_id>_wit<id>_<digit><id>_<canvas_nb>_<coord>.jpg",
     *      "regions_id_1": 1,
     *      "regions_id_2": 2,
     *      "img_1": "iiif url",
     *      "img_2": "iiif url",
     *      "page_1": <canvas_nb>,
     *      "page_2": <canvas_nb>,
     *      "ref_1": "wit<id>_<digit><id>_<canvas_nb>.jpg",
     *      "ref_2": "wit<id>_<digit><id>_<canvas_nb>.jpg",
     *      "coord_1": "<coord>",
     *      "coord_2": "<coord>",
     *      "score": 0.123,
     *      "category": 1,
     *      "category_x": [],
     *      "is_manual": false,
     *      "similarity_type": 1
     * }
     */
    function processPair(pair, context) {
        const {index, documentMap, imageMap, imgToRegionsMap, pStats, docStats, imgStats, docPStats, categories} = context;

        const score = pair.score ?? null;
        const category = pair.category ?? 0;
        const weightedScore = calculateWeightedScore(score, category);

        pair.weightedScore = weightedScore;
        addToScores(pStats, weightedScore);

        pStats.count++;
        pStats.totalScore += weightedScore;
        categories[category] = (categories[category] || 0) + 1;

        for (const key of ['1', '2']) {
            const imgKey = pair[`img_${key}`];
            const rid = pair[`regions_id_${key}`];
            const imgParts = imgKey.split("_");
            const imgRef = `${imgParts.slice(0,3).join("_").replace(".jpg", "")}.jpg`;
            const imgCoord = imgParts.slice(3).join("_").replace(".jpg", "");
            const imgPage = imageToPage(imgKey);

            // MARKER
            if (imgToRegionsMap.has(imgKey)) {
                const previousRid = imgToRegionsMap.get(imgKey);
                if (previousRid !== rid) {
                    console.warn(`⚠️ INCONSISTENCY DETECTED: Image "${imgKey}" used with different regions_id: ${previousRid} and ${rid}`);
                }
            } else {
                imgToRegionsMap.set(imgKey, rid);
            }

            pair[`id_${key}`] = imgKey;
            pair[`img_${key}`] = `${refToIIIFRoot(imgKey)}/${imgCoord}/full/0/default.jpg`;
            pair[`page_${key}`] = imgPage;
            pair[`ref_${key}`] = imgRef;
            pair[`coord_${key}`] = imgCoord;

            if (!imageMap.has(imgKey)) {
                imageMap.set(imgKey, {
                    id: imgKey,
                    img: imgRef,
                    regionId: rid,
                    canvas: imgPage,
                    color: null,
                    ref: imgRef,
                    type: regionsType,
                    xywh: imgCoord.split(","),
                });
            }

            if (!documentMap.has(rid)) {
                documentMap.set(rid, {
                    id: rid,
                    images: [],
                });
            }
            documentMap.get(rid).images.push({id: imgKey, canvas: imgPage})

            addToStats(imgStats, imgKey, weightedScore);
            addToStats(docStats, rid, weightedScore);
            addToIndex(index.byImage, imgKey, pair);
            addToIndex(index.byDoc, rid, pair);
        }

        const {regions_id_1: r1, regions_id_2: r2} = pair;
        const pairKey = r1 < r2 ? `${r1}-${r2}` : `${r2}-${r1}`;
        addToStats(docPStats, pairKey, weightedScore);
        addToIndex(index.byDocPair, pairKey, pair);

        return pair;
    }

    function calculateWeightedScore(score, category, categoryWeights = {1: 1.0, 2: 0.5, 3: 0.125, 4: -1.0, 5: 0.125}) {
        const baseScore = score ?? 0;
        const weight = categoryWeights[category] ?? 0;
        return Math.max(0.01, baseScore + baseScore * weight);
    }

    function computeRange(stats) {
        stats.scoreRange.range = stats.scoreRange.max - stats.scoreRange.min;
        stats.countRange.range = stats.countRange.max - stats.countRange.min;
    }

    function computeDensity(stats) {
        if (stats.links <= 0) return 0;
        stats.density = (2 * stats.links) / (stats.count * (stats.count - 1));
    }

    function addToStats(stats, key, score) {
        const existing = stats.scoreCount.get(key);
        if (!existing) { stats.count++; }

        // TODO is it better to check at each pass or compute min/max at the end?
        const accumulatedScore = (existing?.score || 0) + score;
        addToScores(stats, accumulatedScore);

        const count = (existing?.count || 0) + 1;
        if (count < stats.countRange.min) stats.countRange.min = count;
        if (count > stats.countRange.max) stats.countRange.max = count;

        stats.scoreCount.set(key, {
            score: accumulatedScore,
            count: count,
        });
    }

    function addToIndex(index, key, pair) {
        if (!index.has(key)) index.set(key, []);
        index.get(key).push(pair);
    }

    function addToScores(stats, score) {
        if (score == null) return;
        if (score < stats.scoreRange.min) stats.scoreRange.min = score;
        if (score > stats.scoreRange.max) stats.scoreRange.max = score;
    }

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

    function calculateLinkProps(score, scoreRange, minDistance = 10, maxDistance = 200, minWidth = 2, maxWidth = 25) {
        const {min, _, range} = scoreRange;
        const strength = range === 0 ? 0.5 : (score - min) / range;
        const distance = maxDistance - strength * (maxDistance - minDistance);
        const width = minWidth + strength * (maxWidth - minWidth);
        return {strength, distance, width};
    }

    function normalizeRadius(count, countRange, minRadius = 10, maxRadius = 60) {
        const {min, _, range} = countRange;
        if (range === 0) return (minRadius + maxRadius) / 2;
        return minRadius + ((count - min) / range) * (maxRadius - minRadius);
    }

    const imageNetwork = derived(allPairs, ($pairs) => {
        const $imageNodes = get(imageNodes);
        const $stats = get(imageStats);
        const $pairStats = get(pairStats)

        const nodes = Array.from($imageNodes.values()).map(n => {
            const imgStats = $stats.scoreCount.get(n.id);
            const {count, score} = imgStats;
            const label = `Region: ${n.regionId}\nPage: ${n.canvas}\nConnections: ${count}\nTotal score: ${score}`;
            return {
                ...n,
                radius: normalizeRadius(score, $stats.scoreRange), // normalizeRadius(count, $stats.countRange)
                label,
            };
        });

        const links = $pairs.map(pair => {
            const {strength, distance, width} = calculateLinkProps(pair.weightedScore, $pairStats.scoreRange);
            return {
                source: pair.id_1,
                target: pair.id_2,
                strength,
                distance,
                width
            }
        });

        return { nodes, links };
    });

    function filterNetwork(network, activeRegions, keyRid="id") {
        // TODO recompute stats?
        if (activeRegions.size === network.nodes.length) {
            return network;
        }

        const nodeIds = new Set()
        const nodes = network.nodes.filter(n => {
            if (activeRegions.has(n[keyRid])){
                nodeIds.add(n.id);
                return true;
            }
            return false;
        });
        const links = network.links.filter(l => {
            const srcId = l.source?.id ?? l.source;
            const tgtId = l.target?.id ?? l.target;
            return nodeIds.has(srcId) && nodeIds.has(tgtId);
        });

        return {...network, nodes, links};
    }

    const filteredImageNetwork = derived([imageNetwork, selectedRegions], ([$network, $active]) => {
        return filterNetwork($network, $active, "regionId");
    });

    const documentNetwork = derived([documentNodes], ([$docNodes]) => {
        const $docPairStats = get(docPairStats);
        const $stats = get(documentStats)

        const nodes = Array.from($docNodes.values()).map(n => {
            const docStats = $stats.scoreCount.get(n.id);
            const {count, score} = docStats;
            const label =  `${n.title}\nImage: ${count}\nTotal score: ${score}`;
            return {
                ...n, // todo do we need to duplicate all document data here?
                radius: normalizeRadius(docStats.count, $stats.countRange),
                label,
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

    const filteredDocumentNetwork = derived([documentNetwork, selectedRegions], ([$network, $active]) => {
        return filterNetwork($network, $active);
    });

    /**
     * returns {
     *      regions: [regionId1, regionId2 ...],           // ordered list of selected regions ids
     *      rows: [                                        // images contained in the same pairs across regions
     *          { regionId1: {id: img_id, page: page_nb}, regionId2: {id: img_id, page: page_nb} },
     *          { regionId1: {id: img_id, page: page_nb} },
     *          { regionId1: {id: img_id, page: page_nb}, regionsId3: {id: img_id, page: page_nb} },
     *      ]
     * }
     */
    function buildAlignedImageMatrix(orderedSelection) {
        if (!orderedSelection.length) return {regions: [], rows: []};

        const $documentNodes = get(documentNodes);
        const $pairIndex = get(pairIndex);

        const firstRegionId = orderedSelection[0];
        const firstDoc = $documentNodes.get(firstRegionId);
        if (!firstDoc?.images) return {regions: orderedSelection, rows: []};

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

        const firstImages = [...firstDoc.images].sort((a, b) => a.canvas - b.canvas);
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
        allPairs,
        pairIndex,
        documentNodes,
        imageNodes,
        fetchPairs,
        imageNetwork: filteredImageNetwork,
        documentNetwork: filteredDocumentNetwork,
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
    };
}
