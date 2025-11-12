import {derived, writable} from 'svelte/store';
import {extractNb, refToIIIFRoot, imageToPage, generateColor} from "../utils.js";
// import {appUrl, regionsType} from "../constants.js";
// TO DELETE
import {regionsType} from "../constants.js";
const appUrl = "https://vhs.huma-num.fr";
// TO DELETE

export function createDocumentSetStore(documentSetId) {
    const error = writable(null);

    const selectedCategories = writable([1]);

    const selectedNodes = writable([]);

    const selectedRegions = writable(new Set());

    const threshold = 0.5;

    /**
     * All RegionsPair objects loaded in the current context
     *      // todo improve by indexing pairs by ids  Map<pairId, pairData>
     */
    const allPairs = writable([]);

    /**
     * Image pair index: Map<imgId, [pairs containing this imgId]>
     *     // todo improve by referencing pairs by id only Map<imgId, [pairIds]>
     */
    const imagePairIndex = writable(new Map());

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
            scoreRange: {min: Infinity, max: -Infinity},
            countRange: {min: Infinity, max: -Infinity},
            links: 0,
            clusters: 0,
            connectivity: 0
        };
    }

    const pairStats = writable({});
    const documentStats = writable({});
    const imageStats = writable({});
    const docPairStats = writable({});
    const docSetNumber = writable({
        regions: 0,
        pairs: 0,
        images: 0,
        categories: {}
    });

    const fetchPairs = derived(selectedCategories, ($selectedCategories, set) => {
        (async () => {
            try {
                const cats = $selectedCategories.join(',');

                // TO DELETE
                const documentSetId = 413; // 414;
                // TO DELETE

                const response = await fetch(`${appUrl}/document-set/${documentSetId}/pairs?category=${cats}`);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);

                const data = await response.json();

                const imgPairIdx = new Map();
                const documentMap = new Map();
                const imageMap = new Map();

                const pStats = emptyStats();
                const docStats = emptyStats();
                const imgStats = emptyStats();
                const docPStats = emptyStats();
                const categories = {};

                const context = {
                    imgPairIdx,
                    documentMap,
                    imageMap,
                    pStats,
                    docStats,
                    imgStats,
                    docPStats,
                    categories
                };

                const pairs = data.map(pair => {
                    if (pair.category === 4) {
                        return null;
                    }
                    const score = pair.score ?? null;
                    if (score == null && pair.is_manual !== true) {
                        return null;
                    }
                    if ($selectedCategories.includes(0) && pair.category === 0 && score < threshold) {
                        return null;
                    }
                    return processPair(pair, context)
                });

                pStats.avgScore = pStats.count > 0 ? pStats.totalScore / pStats.count : 0;
                docStats.links = docStats.scoreCount.size;
                imgStats.links = imgStats.scoreCount.size;
                docPStats.links = docPStats.scoreCount.size;

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

                docSetNumber.set({
                    regions: regionIds.length,
                    pairs: pairs.length,
                    images: imgStats.count,
                    categories
                });

                imagePairIndex.set(imgPairIdx);
                pairStats.set(pStats);
                documentStats.set(docStats);
                imageStats.set(imgStats);
                docPairStats.set(docPStats);
                selectedRegions.set(new Set(regionIds));
                documentNodes.set(documentMap);
                imageNodes.set(imageMap);
                allPairs.set(pairs.filter(Boolean)); // todo find a way to be more efficient than this

                set(true)
            } catch (e) {
                error.set(`Error processing pairs: ${e.message}`);
                set(false);
            }
        })();
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
        const {imgPairIdx, documentMap, imageMap, pStats, docStats, imgStats, docPStats, categories} = context;

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
                    xywh: imgCoord.split(","),
                });
            }

            if (!documentMap.has(rid)) {
                documentMap.set(rid, {
                    id: rid,
                    imageCount: 0, // todo delete that because it is stored in docStats
                    images: [], // TODO maybe remove complete pairs and only add reference to pair
                });
            }
            documentMap.get(rid).images.push({id: imgId, canvas: imgPage, pair})
            documentMap.get(rid).imageCount++;

            if (!imgPairIdx.has(imgId)) imgPairIdx.set(imgId, []);
            imgPairIdx.get(imgId).push(pair);

            addToStats(imgStats, imgId, weightedScore);
            addToStats(docStats, rid, weightedScore);
        }

        const {regions_id_1: r1, regions_id_2: r2} = pair;
        const pairKey = r1 < r2 ? `${r1}-${r2}` : `${r2}-${r1}`;
        addToStats(docPStats, pairKey, weightedScore);

        return pair;
    }

    function calculateWeightedScore(score, category) {
        const baseScore = score ?? 0;
        if (category === 1) return baseScore + 1.0;
        if (category === 2) return baseScore + 0.5;
        if (category === 3 || category === 5) return baseScore + 0.125;
        if (category === 4) return Math.max(0.01, baseScore - 1.0);
        return Math.max(0.01, baseScore);
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

    function calculateLinkProps(link, range) {
        const {min, max} = range;
        const score = link.score ?? 0;
        const strength = max > min ? (score - min) / (max - min) : 0.5;
        const distance = 30 + (2 - strength) * 100;
        const width = 1 + strength * 4;
        return {strength, distance, width};
    }

    function normalizeRadius(score, range, minRadius = 10, maxRadius = 75) {
        const {min, max} = range;
        if (max === min) return (minRadius + maxRadius) / 2;
        return minRadius + ((score - min) / (max - min)) * (maxRadius - minRadius);
    }

    const imageNetwork = derived([allPairs, imageNodes, imageStats], ([$pairs, $imageNodes, $stats]) => {
        const nodes = Array.from($imageNodes.values()).map(n => {
            const imgStats = $stats.scoreCount.get(n.id);
            const {count, score} = imgStats;
            const label =  `Region: ${n.regionId}\nPage: ${n.canvas}\nConnections: ${count}\nTotal score: ${score}`;
            return {
                ...n, // todo do we need to duplicate all image data here?
                radius: normalizeRadius(imgStats.score, $stats.countRange),
                label,
            };
        });

        const links = $pairs.map(pair => {
            const {strength, distance, width} = calculateLinkProps(pair, $stats.scoreRange);
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

    const filteredImageNetwork = derived([imageNetwork, selectedRegions], ([$network, $active]) => {
        // TODO recompute stats?
        const nodes = $network.nodes.filter(n => $active.has(n.regionId));
        const nodeIds = new Set(nodes.map(n => n.id));
        const links = $network.links.filter(l =>
            nodeIds.has(l.source.id || l.source) &&
            nodeIds.has(l.target.id || l.target)
        );

        return {...$network, nodes, links};
    });

    const documentNetwork = derived([docPairStats, documentNodes, documentStats], ([$docPairStats, $docNodes, $stats]) => {
        const nodes = Array.from($docNodes.values()).map(n => {
            const docStats = $stats.scoreCount.get(n.id);
            const {count, score} = docStats;
            const label =  `${n.title}\nPage: ${n.page}\nImage: ${count}\nTotal score: ${score}`;
            return {
                ...n, // todo do we need to duplicate all document data here?
                radius: normalizeRadius(docStats.count, $stats.countRange),
                label,
            };
        });

        const links = Array.from($docPairStats.scoreCount.entries()).map(([key, pairStat]) => {
            const [source, target] = key.split('-').map(Number);
            const {strength, distance, width} = calculateLinkProps(pairStat.score, $stats.scoreRange);
            return {
                source, target, strength, distance, width
            };
        });

        return { nodes, links };
    });

    const filteredDocumentNetwork = derived([documentNetwork, selectedRegions], ([$network, $active]) => {
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
        selectedRegions.update(regions => {
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
        buildAlignedImageMatrix
    };
}
