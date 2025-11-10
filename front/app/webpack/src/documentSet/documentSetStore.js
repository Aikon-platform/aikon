import {derived, writable} from 'svelte/store';
import {extractNb, refToIIIFRoot, imageToPage, generateColor} from "../utils.js";
import {appUrl, regionsType} from "../constants.js";

export function createDocumentSetStore(documentSetId) {
    const error = writable(null);

    /**
     * Selected categories for filtering pairs (0=no cat, 1=exact, 2=partial, 3=semantic, 5=user match)
     * [1, 2, 3]
     * @type {Writable<number[]>}
     */
    const selectedCategories = writable([1]);

    /**
     * Selected nodes in the network graph
     * @type {Writable<*[]>}
     */
    const selectedNodes = writable([]);

    /**
     *
     * @type {Writable<Set<any>>}
     */
    const activeRegions = writable(new Set());

    /**
     * All RegionsPair objects loaded in the current context
     *      // todo improve by indexing pairs by ids  Map<pairId, pairData>
     * @type {Writable<*[]>}
     */
    const allPairs = writable([]);

    /**
     * Image pair index: Map<imgId, [pairs containing this imgId]>
     *     // todo improve by referencing pairs by id only Map<imgId, [pairIds]>
     * @type {Writable<Map<any, any>>}
     */
    const imagePairIndex = writable(new Map());

    /**
     * Computed network statistics
     * {
     *     documentStats: Map<"regionId1-regionId2", {count, score}>,
     *     imageStats: Map<imgId, {score, count}>,
     *     docPairStats: Map<"regionId1-regionId2", {count, score}>,
     *     scoreRange: {min, max},
     *     weightedScoreRange: {min, max},
     *     scoreSumRange: {min, max},
     *     totalScores: number,
     *     scoredCount: number,
     *     avgScore: number,
     *     categories: { categoryId: count, ... }
     * }
     */
    const networkStats = writable(null);

    /**
     * Image nodes: Map<imgId, imageData>
     */
    const imageNodes = writable(new Map());

    /**
     * Document nodes: Map<regionId, regionData>
     */
    const documentNodes = writable(new Map());

    function calculateWeightedScore(score, category) {
        const baseScore = score ?? 0;
        if (category === 1) return baseScore + 1.0;
        if (category === 2) return baseScore + 0.5;
        if (category === 3 || category === 5) return baseScore + 0.125;
        if (category === 4) return Math.max(0.01, baseScore - 1.0);
        return Math.max(0.01, baseScore);
    }

    const fetchPairs = derived(selectedCategories, ($selectedCategories, set) => {
        (async () => {
            try {
                const cats = $selectedCategories.join(',');
                const response = await fetch(`${appUrl}/document-set/${documentSetId}/pairs?category=${cats}`);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);

                const data = await response.json();

                const index = new Map();
                const documentMap = new Map();
                const imageMap = new Map();
                const stats = {
                    documentStats: new Map(),
                    imageStats: new Map(),
                    docPairStats: new Map(),
                    scoreRange: {min: Infinity, max: -Infinity},
                    weightedScoreRange: {min: Infinity, max: -Infinity},
                    scoreSumRange: {min: null, max: null},
                    totalScores: 0,
                    scoredCount: 0,
                    avgScore: null,
                    categories: {}
                }

                const context = {index, documentMap, imageMap, stats};
                const pairs = data.map(pair => processPair(pair, context));

                const scoreSums = Array.from(stats.imageStats.values()).map(s => s.score);
                stats.scoreSumRange = {min: Math.min(...scoreSums), max: Math.max(...scoreSums)}
                stats.avgScore = stats.scoredCount > 0 ? stats.totalScores / stats.scoredCount : null;

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
                    imgData.color = doc?.color;
                    imgData.title = (doc?.title || `Region ${imgData.regionId}`) + `<br>Page ${imgData.canvas}`;
                });

                imagePairIndex.set(index);
                networkStats.set(stats);
                activeRegions.set(new Set(regionIds));
                allPairs.set(pairs);
                documentNodes.set(documentMap);
                imageNodes.set(imageMap);

                set(true);
            } catch (e) {
                error.set(`Error fetching pairs: ${e.message}`);
                set(false);
            }
        })();
    });

    // TODO compute weighted score with category for pairs
    // TODO

    /**
     * @param pair : similarity pair to update
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
     * @param context
     *
     * @returns { pair } with added fields:
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
        const {index, documentMap, imageMap, stats} = context;
        const score = pair.score ?? null;
        const category = pair.category ?? 0;
        const weightedScore = calculateWeightedScore(score, category);

        pair.weightedScore = weightedScore;

        if (score != null) {
            if (score < stats.scoreRange.min) stats.scoreRange.min = score;
            if (score > stats.scoreRange.max) stats.scoreRange.max = score;
        }

        if (weightedScore < stats.weightedScoreRange.min) stats.weightedScoreRange.min = weightedScore;
        if (weightedScore > stats.weightedScoreRange.max) stats.weightedScoreRange.max = weightedScore;

        stats.totalScores += weightedScore;
        stats.scoredCount++;
        stats.categories[category] = (stats.categories[category] || 0) + 1;

        for (const key of ['1', '2']) {
            const imgKey = pair[`img_${key}`];
            const rid = pair[`regions_id_${key}`];
            const imgId = `${rid}_${imgKey}`;
            const imgParts = imgKey.split("_");
            const imgRef = `${imgParts.slice(0,3).join("_").replace(".jpg", "")}.jpg`;
            const imgCoord = imgParts.slice(3).join("_").replace(".jpg", "");
            const imgPage = imageToPage(imgKey);

            pair[`id_${key}`] = imgId;
            pair[`img_${key}`] = `${refToIIIFRoot(imgKey)}/${imgCoord}/full/0/default.jpg`;
            pair[`page_${key}`] = imgPage;
            pair[`ref_${key}`] = imgRef;
            pair[`coord_${key}`] = imgCoord;

            if (!imageMap.has(imgId)) {
                imageMap.set(imgId, {
                    id: imgId,
                    img: imgRef,
                    regionId: rid,
                    canvas: imgPage,
                    color: null,
                    ref: imgRef,
                    type: regionsType,
                    xywh: pair[`coord_${key}`].split(","),
                });
            }

            if (!documentMap.has(rid)) {
                documentMap.set(rid, {
                    id: rid,
                    imageCount: 0,
                    images: [],
                });
            }
            documentMap.get(rid).images.push({id: imgId, canvas: imgPage, pair})
            documentMap.get(rid).imageCount++;

            if (!index.has(imgId)) index.set(imgId, []);
            index.get(imgId).push(pair);

            const existing = stats.imageStats.get(imgId);
            stats.imageStats.set(imgId, {
                score: (existing?.score || 0) + weightedScore,
                count: (existing?.count || 0) + 1,
            })
        }

        const {regions_id_1: r1, regions_id_2: r2} = pair;
        const docKey = r1 < r2 ? `${r1}-${r2}` : `${r2}-${r1}`;
        const existingDoc = stats.documentStats.get(docKey);
        stats.documentStats.set(docKey, {
            score: (existingDoc?.score || 0) + weightedScore,
            count: (existingDoc?.count || 0) + 1,
        });

        const existingPair = stats.docPairStats.get(docKey);
        stats.docPairStats.set(docKey, {
            score: (existingPair?.score || 0) + weightedScore,
            count: (existingPair?.count || 0) + 1,
        });

        return pair;
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

    const imageNetwork = derived([allPairs, imageNodes, networkStats], ([$pairs, $imageNodes, $stats]) => {
        if (!$stats) return {nodes: [], links: [], stats: null};

        const links = $pairs.map(pair => ({
            source: pair.id_1,
            target: pair.id_2,
            score: pair.score,
            weightedScore: pair.weightedScore,
            category: pair.category,
            width: (pair.score ?? 10) / 5
        }));

        return {
            nodes: Array.from($imageNodes.values()),
            links,
            stats: {
                scoreRange: $stats.scoreRange,
                weightedScoreRange: $stats.weightedScoreRange,
                scoreSumRange: $stats.scoreSumRange,
                imageStats: $stats.imageStats
            }
        };
    });

    const filteredImageNetwork = derived([imageNetwork, activeRegions], ([$network, $active]) => {
        // TODO recompute stats?
        const nodes = $network.nodes.filter(n => $active.has(n.regionId));
        const nodeIds = new Set(nodes.map(n => n.id));
        const links = $network.links.filter(l =>
            nodeIds.has(l.source.id || l.source) &&
            nodeIds.has(l.target.id || l.target)
        );

        return {...$network, nodes, links};
    });

    const documentNetwork = derived([networkStats, documentNodes], ([$stats, $docNodes]) => {
        if (!$stats || !$docNodes) return {nodes: [], links: [], stats: null};
        const nodes = Array.from($docNodes.values());

        // TODO compute min/max imageCount directly in processPair
        const imageCounts = nodes.map(n => n.imageCount);
        const minImageCount = Math.min(...imageCounts);
        const maxImageCount = Math.max(...imageCounts);

        const scoreSums = Array.from($stats.documentStats.values()).map(d => d.score);
        const minScoreSum = Math.min(...scoreSums);
        const maxScoreSum = Math.max(...scoreSums);

        const links = Array.from($stats.documentStats.entries()).map(([key, {count, score}]) => {
            const [source, target] = key.split('-').map(Number);
            return {source, target, count, scoreSum: score};
        });

        return {
            nodes,
            links,
            stats: {
                imageCountRange: {min: minImageCount, max: maxImageCount},
                scoreSumRange: {min: minScoreSum, max: maxScoreSum}
            }
        };
    });

    const filteredDocumentNetwork = derived([documentNetwork, activeRegions], ([$network, $active]) => {
        // TODO recompute stats?
        const nodes = $network.nodes.filter(n => $active.has(n.id));
        const activeIds = new Set(nodes.map(n => n.id));
        const links = $network.links.filter(l => {
            const srcId = l.source?.id ?? l.source;
            const tgtId = l.target?.id ?? l.target;
            return activeIds.has(srcId) && activeIds.has(tgtId);
        });
        return {...$network, nodes, links};
    });

    // TODO maybe do not derive from that many stores but compute directly in fetchPairs
    const docSetStats = derived([allPairs, imageNodes, documentNodes, networkStats], ([$pairs, $imageNodes, $docNodes, $stats]) => {
        if (!$stats || !$docNodes) return null;

        const witnesses = new Set(
            Array.from($docNodes.values()).map(n => n.witnessId).filter(Boolean)
        );

        return {
            regions: $docNodes.size,
            witnesses: witnesses.size,
            pairs: $pairs.length,
            avgScore: $stats.avgScore?.toFixed(2) || null,
            categories: $stats.categories,
            stats: [
                {nodes: $imageNodes.size, links: $pairs.length},
                {nodes: $docNodes.size, links: $stats.documentStats.size}
            ]
        };
    });

    /**
     * returns {
     *      regions: [regionId1, regionId2 ...],           // ordered list of selected regions ids
     *      rows: [
     *          { regionId1: img, regionId2: img },    // images contained in the same pairs across regions
     *          { regionId1: img },
     *          { regionId1: img, regionsId3: img },
     *      ]
     * }
     */
    function buildAlignedImageMatrix(orderedSelection, documentNodes, allPairs) {
        if (!orderedSelection.length) return {regions: [], rows: []};

        const firstRegionId = orderedSelection[0];
        const firstDoc = documentNodes.get(firstRegionId);
        if (!firstDoc?.images) return {regions: orderedSelection, rows: []};

        const findPairs = (imgId, sourceRegionId, targetRegionId) => {
            const results = [];
            for (const p of allPairs) {
                if (p.id_1 === imgId && p.regions_id_1 === sourceRegionId && p.regions_id_2 === targetRegionId) {
                    results.push({id: p.id_2, page: p.page_2});
                } else if (p.id_2 === imgId && p.regions_id_2 === sourceRegionId && p.regions_id_1 === targetRegionId) {
                    results.push({id: p.id_1, page: p.page_1});
                }
            }
            return results;
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
        activeRegions.update(regions => {
            const newRegions = new Set(regions);
            newRegions.has(regionId) ? newRegions.delete(regionId) : newRegions.add(regionId);
            return newRegions;
        });
    }

    return {
        error,
        allPairs,
        documentNodes,
        imageNodes,
        fetchPairs,
        imageNetwork: filteredImageNetwork,
        documentNetwork: filteredDocumentNetwork,
        selectedCategories,
        docSetStats, // TODO check what is the difference with networkStats (merge?)
        networkStats, // TODO check what is the difference with docSetStats (merge?)
        selectedNodes,
        activeRegions,
        updateSelectedNodes: (nodes) => selectedNodes.set(nodes),
        toggleCategory,
        toggleRegion,
        buildAlignedImageMatrix
    };
}
