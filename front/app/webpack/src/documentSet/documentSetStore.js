import {derived, writable, get} from 'svelte/store';
import {extractNb, refToIIIFRoot, imageToPage, generateColor} from "../utils.js";
import {appUrl} from "../constants.js";
import PairWorker from './pairProcessor.worker.js?worker';

// // TO DELETE
// const appUrl = "https://vhs.huma-num.fr";
// // TO DELETE

export function createDocumentSetStore(documentSetId) {
    const error = writable(null);

    const selectedCategories = writable([1]);
    const selectedRegions = writable(new Set());
    const selectedNodes = writable([]);
    const threshold = writable(0.5);
    const topK = writable(null); // null = disabled, number = k
    const mutualTopK = writable(false);

    /**
     * All RegionsPair objects loaded in the current context
     */
    const allPairs = writable([]);

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
        pairs: 0,
        images: 0,
        categories: {}
    });

    const fetchPairs = derived(selectedCategories, ($cats, set) => {
        if (worker) worker.terminate();

        // TO DELETE
        // const documentSetId = 413; // histoire naturelle
        // const documentSetId = 414; // nicolas
        // const documentSetId = 415; // physiologus
        // const documentSetId = 416; // de materia medica
        // const documentSetId = 417; // traité de géométrie
        // TO DELETE

        const load = async () => {

            try {
                const response = await fetch(`${appUrl}/document-set/${documentSetId}/pairs?category=${$cats.join(',')}`);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                const rawData = await response.json();

                worker = new PairWorker();

                worker.postMessage({
                    rawPairs: rawData,
                    selectedCategories: $cats
                });

                worker.onmessage = (e) => {
                    const { allPairs: sorted, imageNodes: imgMap, pairIndex: idx, stats } = e.data;

                    allPairs.set(sorted);
                    imageNodes.set(imgMap);
                    pairIndex.set(idx);

                    pairStats.set(stats.pairStats);
                    documentStats.set(stats.documentStats);
                    imageStats.set(stats.imageStats);
                    docPairStats.set(stats.docPairStats);

                    const currentRegions = get(selectedRegions);
                    if (currentRegions.size === 0) {
                        selectedRegions.set(new Set(stats.documentStats.scoreCount.keys()));
                    }

                    const range = stats.pairStats.scoreRange;
                    // TODO update slider min/max

                    worker.terminate();
                    worker = null;
                };

                worker.onerror = (err) => {
                    console.error("Worker error", err);
                    error.set("Error processing pairs");
                };

            } catch (e) {
                error.set(`Fetch error: ${e.message}`);
            }
        };

        load();
        set(Promise.resolve());
    });

    const filteredPairs = derived(
        [allPairs, threshold, topK, mutualTopK],
        ([$pairs, $threshold, $topK, $mutual]) => {
            if (!$pairs) return [];

            const result = [];
            const len = $pairs.length;

            for (let i = 0; i < len; i++) {
                const p = $pairs[i];

                // Threshold on score
                if (p.weightedScore < $threshold) {
                    // stop here because pairs are sorted by score
                    // and threshold is prioritised on topK filtering
                    break;
                }

                // TopK filtering
                if ($topK !== null) {
                    const k = $topK;
                    if ($mutual) {
                        // MBoth images must be in each other's top K
                        if (p.rank_1 > k || p.rank_2 > k) continue;
                    } else {
                        // At least one image must be in top K
                        if (p.rank_1 > k && p.rank_2 > k) continue;
                    }
                }

                result.push(p);
            }
            return result;
        }
    );

    // TODO filteredDocs ?
    // TODO get regionInfo before fetching and processing pairs in order to have titles/colors from the start + populate documentNodes images

    /**
     * Reactively fetches region metadata (titles, colors) when document stats are populated by the worker.
     * This compensates for the removal of the fetch logic in the main fetchPairs function.
     */
    const metadataFetcher = derived(documentStats, async ($docStats, set) => {
        const regionIds = $docStats?.scoreCount ? Array.from($docStats.scoreCount.keys()) : [];

        if (regionIds.length === 0) {
            set(false);
            return;
        }

        try {
            const docMap = new Map();

            // Parallel fetch of region details
            await Promise.all(
                regionIds.map(async (rid, i) => {
                    const info = await getRegionsInfo(rid);
                    const color = generateColor(i);

                    docMap.set(rid, {
                        id: rid,
                        title: info.title,
                        ref: info.ref,
                        witnessId: info.witnessId,
                        digitizationRef: info.digitizationRef,
                        zeros: info.zeros,
                        img_nb: info.img_nb,
                        url: info.url,
                        color,
                        // Initialize images array (will be populated by worker logic linkage if needed,
                        // but here we primarily need metadata for the network nodes)
                        images: []
                    });
                })
            );

            // Update the writable store exposed to the UI
            documentNodes.set(docMap);

            // Also update the image nodes with the correct colors/titles now that we have them
            imageNodes.update(imgMap => {
                imgMap.forEach(img => {
                    const doc = docMap.get(img.regionId);
                    if (doc) {
                        img.color = doc.color;
                        img.title = (doc.title || `Region ${img.regionId}`) + `<br>Page ${img.canvas}`;
                    }
                });
                return imgMap;
            });

            set(true);
        } catch (e) {
            console.error("Error fetching region metadata", e);
            error.set(e.message);
            set(false);
        }
    });
    // Force subscription to ensure the side-effect runs even if the UI doesn't explicitly subscribe to this derived store
    metadataFetcher.subscribe(() => {});


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
        const $stats = get(imageStats);
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
                const imgStats = $stats.scoreCount?.get(imgId);
                const {count, score} = imgStats;

                nodes.push({
                    ...nodeData,
                    radius: normalizeRadius(score, $stats.scoreRange),
                    label: `Region: ${nodeData.regionId}\nPage: ${nodeData.canvas}\nConnections: ${count}\nTotal score: ${score.toFixed(2)}`
                });
            }
        }

        return { nodes, links };
    });

    /**
     * Helper to filter network based on active regions
     * (Kept for compatibility, though imageNetwork now handles region filtering internally for performance)
     */
    function filterNetwork(network, activeRegions, keyRid="id") {
        if (activeRegions.size === 0) return network;
        if (activeRegions.size === network.nodes.length) return network;

        const nodeIds = new Set();
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

    // const filteredImageNetwork = derived([imageNetwork, selectedRegions], ([$network, $active]) => {
    //     // Redundant filtering if imageNetwork already filters, but keeps architectural consistency
    //     return filterNetwork($network, $active, "regionId");
    // });

    const documentNetwork = derived([documentNodes], ([$docNodes]) => {
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

    const filteredDocumentNetwork = derived([documentNetwork, selectedRegions], ([$network, $active]) => {
        return filterNetwork($network, $active);
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
        const firstImages = [...firstDoc.images].sort((a, b) => a.canvas - b.canvas);

        // TODO do populate documentNodes images when processing pairs in the worker
        // // Note: The worker does not populate doc.images in the documentNodes map
        // // We need to retrieve images belonging to a document via the pairIndex.byDoc or similar
        // // However, pairIndex.byDoc gives pairs, not unique images.
        // // We can infer images from the filtered imageNodes or reconstruct it.
        // // For the matrix, we need a starting list of images for the first region.
        //
        // // Strategy: Get all images for the first region from the imageNodes store
        // const $imageNodes = get(imageNodes);
        // const firstImages = [];
        //
        // // Scan all images to find those belonging to firstRegionId
        // // This is O(N) on images, which is acceptable (<< 1M pairs)
        // $imageNodes.forEach(img => {
        //     if (img.regionId === firstRegionId) {
        //         firstImages.push(img);
        //     }
        // });
        //
        // firstImages.sort((a, b) => a.canvas - b.canvas);

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
        // to keep ?
        allPairs, // Contains all pairs sorted
        visiblePairs: filteredPairs, // Optimized for visualization
        pairIndex,
        documentNodes,
        imageNodes,
        fetchPairs,
        imageNetwork,
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
        topK,
        setTopK: (k) => topK.set(k),
        mutualTopK,
        setMutualTopK: (b) => mutualTopK.set(b),
    };
}
