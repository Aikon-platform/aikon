import {derived, get, writable} from 'svelte/store';
import {extractNb, refToIIIF} from "../utils.js";
import { appUrl } from "../constants.js";

function imageToPage(imgName) {
    const parts = imgName.split('_');
    return parseInt(parts[parts.length - 2]);
}

export function createDocumentSetStore() {
    const error = writable(null);

    const corpusStats = derived(
        [allPairs, regionsMetadata],
        ([$allPairs, $regionsMetadata]) => {
            // todo link-count, node-count, doc-count, category count
            return {};
        }
    );

    // TODO add
    //  regionsImages
    //  regions list
    //  region to color

    const allPairs = writable({});
    const regionsMetadata = writable({});
    const imageIndex = writable(new Map());

    const fetchPairs = (async () => {
        const response = await fetch(`${appUrl}/document-set/${documentSetId}/pairs`);
        const data = await response.json();
        const pairs = data.map(pair => ({
            ...pair,
            page_1: imageToPage(pair.img_1),
            img_1: refToIIIF(pair.img_1),
            page_2: imageToPage(pair.img_2),
            img_2: refToIIIF(pair.img_2)
        }));

        allPairs.set(pairs);

        const index = new Map();
        const regionIds = new Set();

        pairs.forEach(pair => {
            for (const key of ['1', '2']) {
                regionIds.add(pair[`regions_${key}`]);
                const imgKey = `img_${key}`;
                if (!index.has(pair[imgKey])) index.set(pair[imgKey], []);
                index.get(pair[imgKey]).push(pair);
            }
        });

        imageIndex.set(index);

        const regionIdsArray = [...regionIds];
        for (let i = 0; i < regionIdsArray.length; i++) {
            const info = await getRegionsInfo(regionIdsArray[i]);
            info.color = generateColor(i);
            regionsMetadata.update(m => ({...m, [regionIdsArray[i]]: info}));
        }

        return data;
    })();

    async function getRegionsInfo(regionId) {
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
            const response = await fetch(`${BASE_URL}search/regions/?id=${regionId}`);
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
            error.set(`Error fetching region extraction metadata ${regionId}: ${e}`);
        }
        return regionInfo;
    }

    const regionsInfo = derived([allPairs, regionsMetadata], ([$allPairs, $metadata]) => {
        const info = {};
        for (let pair of $allPairs) {
            for (const key of ['1', '2']) {
                const regionKey = `regions_${key}`;
                const imgKey = `img_${key}`;
                const pageKey = `page_${key}`;

                const regionsId = pair[regionKey];
                if (!info.hasOwnProperty(regionsId)) {
                    info[regionsId] = {
                        title: $metadata[regionsId]?.title || "",
                        witnessId: $metadata[regionsId]?.witnessId || null,
                        images: [pair[imgKey]],
                        pages: [pair[pageKey]],
                        color: null,
                    };
                } else {
                    if (!info[regionsId].images.includes(pair[imgKey])) {
                        info[regionsId].images.push(pair[imgKey]);
                    }
                    if (!info[regionsId].pages.includes(pair[pageKey])) {
                        info[regionsId].pages.push(pair[pageKey]);
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
                    nodes.set(pair[`img_${key}`], {
                        id: pair[`img_${key}`],
                        regionId: pair[regionKey],
                        page: pair[`page_${key}`],
                        color: $regionsInfo[pair[regionKey]]?.color || "#888888"
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
            documentImgs.get(r1).push({img: pair.img_1, page: pair.page_1, pair});
            documentImgs.get(r2).push({img: pair.img_2, page: pair.page_2, pair});

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

    return {
        imageNetwork,
        documentNetwork,
        regionsInfo,
        regionsMetadata,
        allPairs,
        fetchPairs,
        error
    };
}
