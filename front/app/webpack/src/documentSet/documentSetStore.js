import {derived, get, writable} from 'svelte/store';
import {extractNb, refToIIIF} from "../utils.js";
import {appUrl, regionsType} from "../constants.js";

function imageToPage(imgName) {
    const parts = imgName.split('_');
    return parseInt(parts[parts.length - 2]);
}

export function createDocumentSetStore(documentSetId) {
    const error = writable(null);
    const category = writable(1);
    const selectedNodes = writable([]);

    function updateSelectedNodes(nodesArray) {
        selectedNodes.set(nodesArray);
    }

    // TODO add
    //  regionsImages
    //  regions list
    //  region to color

    /** @type {Writable<RegionItemType[]>} */
    const allPairs = writable([]);
    const regionsMetadata = writable({});
    const imageIndex = writable(new Map());

    const fetchPairs = (async () => {
        try {
            const response = await fetch(`${appUrl}/document-set/${documentSetId}/pairs?category=${get(category)}`);
            if (!response.ok) {
                error.set(`Failed to fetch document set pairs: HTTP ${response.status}`);
                return;
            }

            const data = await response.json();

            const pairs = data.map(pair => {
                for (const key of ['1', '2']) {
                    const pairImg = pair[`img_${key}`];
                    const imgParts = pairImg.split("_");
                    pair = {
                        ...pair,
                        [`img_${key}`]: refToIIIF(pairImg), // TODO improve because refToIIIF is effectively combination of ref and coord
                        [`id_${key}`]: pairImg,
                        [`page_${key}`]: imageToPage(pairImg),
                        [`ref_${key}`]: `${imgParts.slice(0,3).join("_").replace(".jpg", "")}.jpg`,
                        [`coord_${key}`]: imgParts.slice(3).join("_").replace(".jpg", ""),
                    };
                }
                return pair
            });

            allPairs.set(pairs);

            const index = new Map();
            const regionIds = new Set();

            pairs.forEach(pair => {
                for (const key of ['1', '2']) {
                    regionIds.add(pair[`regions_id_${key}`]);
                    const imgKey = `img_${key}`;
                    if (!index.has(pair[imgKey])) index.set(pair[imgKey], []);
                    index.get(pair[imgKey]).push(pair);
                }
            });

            imageIndex.set(index);

            const regionIdsArray = [...regionIds];
            const metadataPromises = regionIdsArray.map(async (regionId, i) => {
                const info = await getRegionsInfo(regionId);
                info.color = generateColor(i);
                return [regionId, info];
            });

            const metadataEntries = await Promise.all(metadataPromises);
            regionsMetadata.set(Object.fromEntries(metadataEntries));
        } catch (e) {
            error.set(`Error fetching pairs: ${e.message}`);
        }
    })();

    async function getRegionsInfo(regionId) {
        // TODO move this into regionStore
        let regionInfo = {
            title: `Region Extraction ${regionId}`,
            ref: "",
            witnessId: null,
            digitizationRef: "",
            zeros: 0,
            img_nb: 0,
            url: ""
        };
        try {
            const response = await fetch(`${appUrl}/search/regions/?id=${regionId}`);
            if (!response.ok) {
                error.set(`Failed to fetch region info: HTTP ${response.status}`);
                throw new Error(`HTTP ${response.status}`)
            }
            const data = await response.json();

            if (!data.hasOwnProperty("results") || data.results.length === 0) {
                error.set(`No Region Extraction #${regionId}`);
                return regionInfo;
            }
            const region = data.results[0];
            let title = region.title.split(" | ");
            title.shift();
            regionInfo.title = title.join(" | ");

            if (region.hasOwnProperty("ref")) {
                regionInfo.ref = region.ref;
                const [wit, digit] = region.ref.split("_");
                regionInfo.witnessId = extractNb(wit);
                regionInfo.digitizationRef = digit;
            }
            regionInfo.zeros = region.zeros;
            regionInfo.img_nb = region.img_nb;
            regionInfo.url = region.url;
        } catch (e) {
            error.set(`Error fetching region extraction metadata #${regionId}: ${e}`);
        }
        return regionInfo;
    }

    const regionsInfo = derived([allPairs, regionsMetadata], ([$allPairs, $metadata]) => {
        const info = {};
        for (let pair of $allPairs) {
            for (const key of ['1', '2']) {
                const regionKey = `regions_id_${key}`;
                const regionsId = pair[regionKey];
                if (!info.hasOwnProperty(regionsId)) {
                    info[regionsId] = {
                        title: $metadata[regionsId]?.title || "",
                        witnessId: $metadata[regionsId]?.witnessId || null,
                        images: [pair[`img_${key}`]],
                        pages: [pair[`page_${key}`]],
                        color: null,
                    };
                } else {
                    if (!info[regionsId].images.includes(pair[`img_${key}`])) {
                        info[regionsId].images.push(pair[`img_${key}`]);
                    }
                    if (!info[regionsId].pages.includes(pair[`page_${key}`])) {
                        info[regionsId].pages.push(pair[`page_${key}`]);
                    }
                }
            }
        }
        return info;
    });

    function generateColor(index) {
        const goldenAngle = 137.5;
        const saturations = [85, 70, 60];
        const lightnesses = [50, 65, 40];

        const hue = (index * goldenAngle) % 360;
        const saturation = saturations[index % saturations.length];
        const lightness = lightnesses[Math.floor(index / saturations.length) % lightnesses.length];

        return `hsl(${Math.floor(hue)}, ${saturation}%, ${lightness}%)`;
    }

    const imageNetwork = derived([allPairs, regionsInfo], ([$allPairs, $regionsInfo]) => {
        const nodes = new Map();
        const links = [];

        $allPairs.forEach(pair => {
            for (const key of ['1', '2']) {
                const regionKey = `regions_id_${key}`;
                if (!nodes.has(pair[`img_${key}`])) {
                    const regionId = pair[regionKey];
                    nodes.set(pair[`img_${key}`], {
                        id: pair[`img_${key}`],
                        img: pair[`ref_${key}`],
                        regionId: regionId,
                        canvas: pair[`page_${key}`],
                        title: `Region ${regionId}<br/>Page ${pair[`page_${key}`]}`,
                        color: $regionsInfo[regionId]?.color || "#888888",
                        ref: pair[`id_${key}`],
                        type: regionsType,
                        xywh: pair[`coord_${key}`].split(",")
                    });
                }
            }

            links.push({
                source: pair.img_1,
                target: pair.img_2,
                score: pair.score,
                category: pair.category,
                width: (pair.score ?? 10) / 5
            });
        });
        return {
            nodes: Array.from(nodes.values()),
            links,
        };
    });

    const documentNetwork = derived([allPairs, regionsInfo], ([$allPairs, $regionsInfo]) => {
        const connectedDocuments = new Map();
        const documentImgs = new Map();

        $allPairs.forEach(pair => {
            const r1 = pair.regions_id_1;
            const r2 = pair.regions_id_2;

            if (!documentImgs.has(r1)) documentImgs.set(r1, []);
            if (!documentImgs.has(r2)) documentImgs.set(r2, []);
            documentImgs.get(r1).push({img: pair.img_1, canvas: pair.page_1, pair});
            documentImgs.get(r2).push({img: pair.img_2, canvas: pair.page_2, pair});

            const key = r1 < r2 ? `${r1}-${r2}` : `${r2}-${r1}`;
            const existing = connectedDocuments.get(key);
            connectedDocuments.set(key, {
                count: (existing?.count || 0) + 1,
                score: (existing?.score || 0) + (pair.score ?? 0)
            });
        });
        const nodes = Array.from(documentImgs.keys()).map(id => ({
            id,
            title: $regionsInfo[id]?.title || `Region ${id}`,
            color: $regionsInfo[id]?.color || "#888888",
            size: documentImgs.get(id).length
        }));

        const links = [];
        let maxCount = 1;
        for (const {count} of connectedDocuments.values()) {
            if (count > maxCount) maxCount = count;
        }
        connectedDocuments.forEach(({count, score}, key) => {
            const [source, target] = key.split('-').map(Number);
            links.push({
                source,
                target,
                count,
                width: 1 + (count / maxCount) * 9,
                score: count > 0 ? score / count : 0
            });
        });
        return {
            nodes,
            links,
        };
    });

    function generateDistinctColor(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = str.charCodeAt(i) + ((hash << 5) - hash);
            hash = hash & hash;
        }

        const goldenRatio = 0.618033988749895;
        const hue = ((hash * goldenRatio) % 1) * 360;
        const saturation = 65 + (hash % 20);
        const lightness = 80 + (hash % 10);

        return `hsl(${Math.floor(hue)}, ${saturation}%, ${lightness}%)`;
    }

    function buildAlignedImageMatrix(selectionOrder, regionImages, data) {
        const regions = [...selectionOrder];

        const getRegionImagesMap = (regionId) => {
            const map = new Map();
            regionImages.get(regionId).forEach(imgData => {
                map.set(imgData.img, {page: imgData.page, img: imgData.img});
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

    const docSetStats = derived(
        [allPairs, regionsMetadata, imageNetwork, documentNetwork],
        ([$allPairs, $regionsMetadata, $imageNetwork, $documentNetwork]) => {
            const witnesses = new Set();
            const categories = {};
            let totalScore = 0;
            let scoredPairs = 0;

            $allPairs.forEach(pair => {
                Object.values($regionsMetadata).forEach(meta => {
                    if (meta.witnessId) witnesses.add(meta.witnessId);
                });

                if (pair.category) {
                    categories[pair.category] = (categories[pair.category] || 0) + 1;
                }

                if (pair.score != null) {
                    totalScore += pair.score;
                    scoredPairs++;
                }
            });

            return {
                regions: Object.keys($regionsMetadata).length,
                witnesses: witnesses.size,
                pairs: $allPairs.length,
                stats:
                [
                    {
                        nodes: $imageNetwork.nodes.length,
                        links: $imageNetwork.links.length,
                    },
                    {
                        nodes: $documentNetwork.nodes.length,
                        links: $documentNetwork.links.length,
                    }
                ],
                avgScore: scoredPairs > 0 ? (totalScore / scoredPairs).toFixed(2) : null,
                categories
            };
        }
    );

    return {
        imageNetwork,
        documentNetwork,
        regionsInfo,
        regionsMetadata,
        docSetStats,
        allPairs,
        fetchPairs,
        error,
        category,
        selectedNodes,
        updateSelectedNodes,
    };
}
