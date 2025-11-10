import {derived, writable} from 'svelte/store';
import {extractNb, refToIIIF} from "../utils.js";
import {appUrl, regionsType} from "../constants.js";

function imageToPage(imgName) {
    return parseInt(imgName.split('_').at(-2));
}

function generateColor(index) {
    const goldenAngle = 137.5;
    const saturations = [85, 70, 60];
    const lightnesses = [50, 65, 40];
    const hue = (index * goldenAngle) % 360;
    const saturation = saturations[index % saturations.length];
    const lightness = lightnesses[Math.floor(index / saturations.length) % lightnesses.length];
    return `hsl(${Math.floor(hue)}, ${saturation}%, ${lightness}%)`;
}

function processPair(pair) {
    const result = {...pair};
    for (const key of ['1', '2']) {
        const pairImg = pair[`img_${key}`];
        const imgParts = pairImg.split("_");
        result[`img_${key}`] = refToIIIF(pairImg); // TODO find a way to remove the need of reffToIIIF since it is basically the same as ref+coord
        result[`id_${key}`] = pairImg;
        result[`page_${key}`] = imageToPage(pairImg);
        result[`ref_${key}`] = `${imgParts.slice(0,3).join("_").replace(".jpg", "")}.jpg`;
        result[`coord_${key}`] = imgParts.slice(3).join("_").replace(".jpg", "");
    }
    return result;
}

function computeNetworkStats(pairs, regionsInfo) {
    const imageNodes = new Map();
    const documentNodes = new Map();
    const imageScoreSums = new Map();
    const documentPairs = new Map();
    const imageDegrees = new Map();

    let minScore = Infinity;
    let maxScore = -Infinity;
    let totalScore = 0;
    let scoredCount = 0;
    const categories = {};

    // NOTE third loop on pairs
    pairs.forEach(pair => {
        const {img_1, img_2, regions_id_1: r1, regions_id_2: r2, score, category} = pair;

        if (score != null) {
            if (score < minScore) minScore = score;
            if (score > maxScore) maxScore = score;
            totalScore += score;
            scoredCount++;

            imageScoreSums.set(img_1, (imageScoreSums.get(img_1) || 0) + score);
            imageScoreSums.set(img_2, (imageScoreSums.get(img_2) || 0) + score);
        }

        imageDegrees.set(img_1, (imageDegrees.get(img_1) || 0) + 1);
        imageDegrees.set(img_2, (imageDegrees.get(img_2) || 0) + 1);

        categories[category ?? 0] = (categories[category ?? 0] || 0) + 1;

        for (const [img, rid, key] of [[img_1, r1, '1'], [img_2, r2, '2']]) {
            if (!imageNodes.has(img)) {
                imageNodes.set(img, {
                    id: img,
                    img: pair[`ref_${key}`],
                    regionId: rid,
                    canvas: pair[`page_${key}`],
                    color: regionsInfo[rid]?.color || "#888888",
                    ref: pair[`id_${key}`],
                    type: regionsType,
                    xywh: pair[`coord_${key}`].split(",")
                });
            }

            if (!documentNodes.has(rid)) {
                documentNodes.set(rid, []);
            }
            documentNodes.get(rid).push({img, canvas: pair[`page_${key}`], pair});
            // NOTE regionsInfo could be set here
        }

        const key = r1 < r2 ? `${r1}-${r2}` : `${r2}-${r1}`;
        const existing = documentPairs.get(key);
        documentPairs.set(key, {
            count: (existing?.count || 0) + 1,
            score: (existing?.score || 0) + (score ?? 0)
        });
    });

    const scoreSums = Array.from(imageScoreSums.values());
    const minScoreSum = Math.min(...scoreSums);
    const maxScoreSum = Math.max(...scoreSums);

    return {
        imageNodes,
        documentNodes,
        documentPairs,
        imageScoreSums,
        imageDegrees,
        scoreRange: {min: minScore, max: maxScore},
        scoreSumRange: {min: minScoreSum, max: maxScoreSum},
        avgScore: scoredCount > 0 ? totalScore / scoredCount : null,
        categories
    };
}

export function createDocumentSetStore(documentSetId) {
    const error = writable(null);
    const selectedCategories = writable([1]);
    const selectedNodes = writable([]);
    const activeRegions = writable(new Set());
    const allPairs = writable([]);
    const regionsMetadata = writable({});
    const imageIndex = writable(new Map());
    const networkStats = writable(null);

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

    const fetchPairs = derived(selectedCategories, ($selectedCategories, set) => {
        (async () => {
            try {
                const cats = $selectedCategories.join(',');
                const response = await fetch(`${appUrl}/document-set/${documentSetId}/pairs?category=${cats}`);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);

                const data = await response.json();
                // NOTE first loop on pairs
                const pairs = data.map(processPair);

                const index = new Map();
                const regionIds = new Set();

                // NOTE second loop on pairs
                pairs.forEach(pair => {
                    for (const key of ['1', '2']) {
                        const rid = pair[`regions_id_${key}`];
                        const img = pair[`img_${key}`];
                        regionIds.add(rid);
                        if (!index.has(img)) index.set(img, []);
                        index.get(img).push(pair);
                    }
                });

                const regionIdsArray = [...regionIds];
                const metadataEntries = await Promise.all(
                    regionIdsArray.map(async (rid, i) => {
                        const info = await getRegionsInfo(rid);
                        info.color = generateColor(i);
                        return [rid, info];
                    })
                );

                const metadata = Object.fromEntries(metadataEntries);
                const stats = computeNetworkStats(pairs, metadata);

                regionsMetadata.set(metadata);
                imageIndex.set(index);
                networkStats.set(stats);
                activeRegions.set(new Set(regionIdsArray));
                allPairs.set(pairs);
                set(true);
            } catch (e) {
                error.set(`Error fetching pairs: ${e.message}`);
                set(false);
            }
        })();
    });

    const regionsInfo = derived([networkStats, regionsMetadata], ([$stats, $metadata]) => {
        if (!$stats) return {};

        const info = {};
        $stats.documentNodes.forEach((imgData, rid) => {
            const images = [...new Set(imgData.map(d => d.img))];
            const pages = [...new Set(imgData.map(d => d.canvas))].sort((a,b) => a-b);

            info[rid] = {
                title: $metadata[rid]?.title || "",
                witnessId: $metadata[rid]?.witnessId || null,
                images,
                pages,
                color: $metadata[rid]?.color || null,
            };
        });
        return info;
    });

    const imageNetwork = derived([allPairs, networkStats, regionsInfo], ([$pairs, $stats]) => {
        if (!$stats) return {nodes: [], links: []};

        const links = $pairs.map(pair => ({
            source: pair.img_1,
            target: pair.img_2,
            score: pair.score,
            category: pair.category,
            width: (pair.score ?? 10) / 5
        }));

        return {
            nodes: Array.from($stats.imageNodes.values()),
            links,
            stats: {
                scoreRange: $stats.scoreRange,
                scoreSumRange: $stats.scoreSumRange,
                scoreSums: $stats.imageScoreSums,
                degrees: $stats.imageDegrees
            }
        };
    });

    const filteredImageNetwork = derived([imageNetwork, activeRegions], ([$network, $active]) => {
        const nodes = $network.nodes.filter(n => $active.has(n.regionId));
        const nodeIds = new Set(nodes.map(n => n.id));
        const links = $network.links.filter(l =>
            nodeIds.has(l.source.id || l.source) &&
            nodeIds.has(l.target.id || l.target)
        );

        return {...$network, nodes, links};
    });

    const documentNetwork = derived([networkStats, regionsInfo], ([$stats, $regionsInfo]) => {
        if (!$stats) return {nodes: [], links: [], stats: null};

        const nodes = Array.from($stats.documentNodes.keys()).map(id => ({
            id,
            title: $regionsInfo[id]?.title || `Region ${id}`,
            color: $regionsInfo[id]?.color || "#888888",
            imageCount: $stats.documentNodes.get(id).length
        }));

        const imageCounts = nodes.map(n => n.imageCount);
        const minImageCount = Math.min(...imageCounts);
        const maxImageCount = Math.max(...imageCounts);

        const scoreSums = Array.from($stats.documentPairs.values()).map(d => d.score);
        const minScoreSum = Math.min(...scoreSums);
        const maxScoreSum = Math.max(...scoreSums);

        const links = Array.from($stats.documentPairs.entries()).map(([key, {count, score}]) => {
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
        // TODO use filteredDocumentNetwork
        const nodes = $network.nodes.filter(n => $active.has(n.regionId));
        const nodeIds = new Set(nodes.map(n => n.id));
        const links = $network.links.filter(l =>
            nodeIds.has(l.source.id || l.source) &&
            nodeIds.has(l.target.id || l.target)
        );

        return {...$network, nodes, links};
    });

    const docSetStats = derived([allPairs, regionsMetadata, networkStats], ([$pairs, $metadata, $stats]) => {
        if (!$stats) return null;

        const witnesses = new Set(
            Object.values($metadata)
                .map(m => m.witnessId)
                .filter(Boolean)
        );

        return {
            regions: Object.keys($metadata).length,
            witnesses: witnesses.size,
            pairs: $pairs.length,
            avgScore: $stats.avgScore?.toFixed(2) || null,
            categories: $stats.categories,
            stats: [
                {nodes: $stats.imageNodes.size, links: $pairs.length},
                {nodes: $stats.documentNodes.size, links: $stats.documentPairs.size}
            ]
        };
    });

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

    function buildAlignedImageMatrix(selectionOrder, regionImages, data) {
        const regions = [...selectionOrder];

        const getRegionImagesMap = (regionId) => {
            const map = new Map();
            (regionImages.get(regionId) ?? []).forEach(imgData => {
                map.set(imgData.img, {page: imgData.canvas, img: imgData.img});
            });
            return map;
        };

        const regionImagesMap = new Map(regions.map(r => [r, getRegionImagesMap(r)]));
        const rows = [];
        const globalProcessed = new Map(regions.map(r => [r, new Set()]));

        const findConnectedImages = (regionId, img, targetRegion) => {
            const connected = [];
            data.forEach(pair => {
                const [r1, r2] = [pair.regions_id_1, pair.regions_id_2];
                const [i1, i2] = [pair.img_1, pair.img_2];

                if ((r1 === regionId && i1 === img && r2 === targetRegion) ||
                    (r2 === regionId && i2 === img && r1 === targetRegion)) {
                    const targetImg = r1 === targetRegion ? i1 : i2;
                    if (regionImagesMap.get(targetRegion).has(targetImg)) {
                        connected.push(regionImagesMap.get(targetRegion).get(targetImg));
                    }
                }
            });
            return connected;
        };

        const buildRowFromSeed = (seedRegion, seedImg) => {
            const visited = new Map([[seedRegion, seedImg.img]]);
            const queue = [{region: seedRegion, img: seedImg, path: {[seedRegion]: seedImg}}];
            const completedPaths = [];

            while (queue.length > 0) {
                const {region, img, path} = queue.shift();
                const currentIndex = regions.indexOf(region);

                if (currentIndex === regions.length - 1) {
                    completedPaths.push(path);
                    continue;
                }

                const nextRegion = regions[currentIndex + 1];
                const connected = findConnectedImages(region, img.img, nextRegion);

                if (connected.length > 0) {
                    connected.forEach(nextImg => {
                        queue.push({
                            region: nextRegion,
                            img: nextImg,
                            path: {...path, [nextRegion]: nextImg}
                        });
                    });
                } else if (Object.keys(path).length > 0) {
                    completedPaths.push(path);
                }
            }

            return completedPaths;
        };

        regions.forEach(regionId => {
            const images = Array.from(regionImagesMap.get(regionId).values())
                .sort((a, b) => a.page - b.page);

            images.forEach(imgData => {
                if (globalProcessed.get(regionId).has(imgData.img)) return;

                const paths = buildRowFromSeed(regionId, imgData);

                if (paths.length > 0) {
                    paths.forEach(path => {
                        Object.entries(path).forEach(([r, img]) => {
                            globalProcessed.get(Number(r)).add(img.img);
                        });
                        rows.push(path);
                    });
                } else {
                    globalProcessed.get(regionId).add(imgData.img);
                    rows.push({[regionId]: imgData});
                }
            });
        });

        return {regions, rows};
    }

    return {
        imageNetwork: filteredImageNetwork,
        documentNetwork,
        regionsInfo,
        regionsMetadata,
        docSetStats,
        allPairs,
        fetchPairs,
        error,
        selectedCategories,
        toggleCategory,
        selectedNodes,
        updateSelectedNodes: (nodes) => selectedNodes.set(nodes),
        activeRegions,
        toggleRegion,
        imageIndex,
        networkStats,
        buildAlignedImageMatrix
    };
}
