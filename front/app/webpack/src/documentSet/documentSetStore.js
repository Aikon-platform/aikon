import {derived, writable} from 'svelte/store';
import {refToIIIF} from "../utils.js";

const BASE_URL = "https://iscd.huma-num.fr/";
const urlTemplate = "vhs/witness/{witnessId}/regions/pairs?regionsIds={regionIds}&category={category}&excludeSelf=true";

const corpusDefinitions = {
    "Natural History": {
        buffon: {
            23: {witnessId: 23, regionId: 23},
            24: {witnessId: 24, regionId: 24},
            25: {witnessId: 25, regionId: 25},
            26: {witnessId: 26, regionId: 26},
            27: {witnessId: 27, regionId: 27},
            28: {witnessId: 28, regionId: 28},
            30: {witnessId: 30, regionId: 30},
            31: {witnessId: 31, regionId: 31},
            32: {witnessId: 32, regionId: 32},
            2335: {witnessId: 2335, regionId: 2348},
            2336: {witnessId: 2336, regionId: 2350},
            2337: {witnessId: 2337, regionId: 2349}
        },
        encyclo_animal: {
            248: {witnessId: 248, regionId: 248}
        },
        fajardo: {
            2284: {witnessId: 2284, regionId: 2288},
            2285: {witnessId: 2285, regionId: 2289},
            2286: {witnessId: 2286, regionId: 2297},
            2287: {witnessId: 2287, regionId: 2296},
            2288: {witnessId: 2288, regionId: 2295},
            2289: {witnessId: 2289, regionId: 2298},
            2290: {witnessId: 2290, regionId: 2293},
            2291: {witnessId: 2291, regionId: 2292},
            2292: {witnessId: 2292, regionId: 2291},
            2293: {witnessId: 2293, regionId: 2299},
            2297: {witnessId: 2297, regionId: 2294}
        },
        bewick: {
            2339: {witnessId: 2339, regionId: 2353}
        }
    },
    "Geometry": {
        geometry: {
            2282: {witnessId: 2282, regionId: 2290},
            2309: {witnessId: 2309, regionId: 2312},
            2310: {witnessId: 2310, regionId: 2310},
            2312: {witnessId: 2312, regionId: 2313},
            2314: {witnessId: 2314, regionId: 2318}
        }
    },
    "Mathematics": {
        lexicon_technikum: {
            77: {witnessId: 77, regionId: 2320},
            2325: {witnessId: 2325, regionId: 2321}
        },
        chambers: {
            75: {witnessId: 75, regionId: 75},
            76: {witnessId: 76, regionId: 76}
        },
        encyclo_math: {
            247: {witnessId: 247, regionId: 247}
        },
        wolff: {
            116: {witnessId: 116, regionId: 116},
            117: {witnessId: 117, regionId: 117},
            118: {witnessId: 118, regionId: 118},
            119: {witnessId: 119, regionId: 119},
            120: {witnessId: 120, regionId: 120}
        }
    },
    "Weddigen": {
        weddingen: {
            2185: {witnessId: 2185, regionId: 2126},
            2242: {witnessId: 2242, regionId: 2186},
            2239: {witnessId: 2239, regionId: 2181},
            2243: {witnessId: 2243, regionId: 2182},
            2259: {witnessId: 2259, regionId: 2234}
        }
    },
    "Physiologus": {
        physiologus: {
            845: {witnessId: 845, regionId: 845},
            847: {witnessId: 847, regionId: 2190},
            849: {witnessId: 849, regionId: 849},
            853: {witnessId: 853, regionId: 853},
            1728: {witnessId: 1728, regionId: 1679}
        }
    },
    "Hygin": {
        hygin: {
            870: {witnessId: 870, regionId: 2196},
            913: {witnessId: 913, regionId: 913},
            914: {witnessId: 914, regionId: 914},
            973: {witnessId: 973, regionId: 973},
            975: {witnessId: 975, regionId: 975}
        }
    },
    "Phaenomena": {
        draelants: {
            933: {witnessId: 933, regionId: 933},
            935: {witnessId: 935, regionId: 2346},
            925: {witnessId: 925, regionId: 2347},
            926: {witnessId: 926, regionId: 926},
            996: {witnessId: 996, regionId: 996}
        }
    },
    "Dioscorides": {
        dioscorides: {
            1001: {witnessId: 1001, regionId: 1001},
            1003: {witnessId: 1003, regionId: 1003},
            1006: {witnessId: 1006, regionId: 1006},
            1008: {witnessId: 1008, regionId: 1008},
            1012: {witnessId: 1012, regionId: 1012},
            1013: {witnessId: 1013, regionId: 1013}
        }
    }
};

// function imageToIiif(imgName) {
//     const parts = imgName.split('_');
//     const coords = parts[parts.length - 1].replace('.jpg', '');
//     const base = parts.slice(0, -1).join('_');
//     return `${BASE_URL}iiif/2/${base}.jpg/${coords}/full/0/default.jpg`;
// }

function imageToPage(imgName) {
    const parts = imgName.split('_');
    return parseInt(parts[parts.length - 2]);
}

function formatData(data) {
    return data.map(pair => ({
        ...pair,
        page_1: imageToPage(pair.img_1),
        img_1: refToIIIF(pair.img_1),
        page_2: imageToPage(pair.img_2),
        img_2: refToIIIF(pair.img_2)
    }));
}

async function getWitnessTitle(witnessId) {
    try {
        const response = await fetch(`${BASE_URL}search/regions/?id=${witnessId}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();

        if (data.hasOwnProperty("results") && data.results.length > 0) {
            let title = data.results[0].title.split(" | ");
            title.shift();
            return title.join(" | ") || `Region Extraction ${witnessId}`;
        }
        return `Region Extraction #${witnessId}`;
    } catch (e) {
        console.error(`Error fetching title for witness ${witnessId}:`, e);
        return `Region Extraction #${witnessId}`;
    }
}

async function enrichCorpusWithTitles(corpus, regionMetadataMap) {
    const witnessIds = new Set();

    for (const subcorpus of Object.values(corpus)) {
        for (const witness of Object.values(subcorpus)) {
            witnessIds.add(witness.regionId);
        }
    }

    const titlePromises = Array.from(witnessIds).map(async witnessId => {
        const title = await getWitnessTitle(witnessId);
        return [witnessId, title];
    });

    const titles = await Promise.all(titlePromises);
    const titleMap = Object.fromEntries(titles);

    for (const subcorpus of Object.values(corpus)) {
        for (const witness of Object.values(subcorpus)) {
            witness.witTitle = titleMap[witness.regionId];
            regionMetadataMap.set(witness.regionId, {
                witnessId: witness.witnessId,
                witTitle: witness.witTitle,
                regionId: witness.regionId
            });
        }
    }
}

async function fetchCorpusData(corpus) {
    const regionIds = [];
    let witnessId;

    for (const subcorpus of Object.values(corpus)) {
        for (const witness of Object.values(subcorpus)) {
            witnessId = witness.witnessId;
            regionIds.push(witness.regionId);
        }
    }

    const regionIdsStr = regionIds.join(",");
    const url = BASE_URL + urlTemplate
        .replace("{witnessId}", witnessId)
        .replace("{regionIds}", regionIdsStr)
        .replace("{category}", 1);

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (e) {
        console.error(`Error fetching corpus data:`, e);
        return null;
    }
}

export function createDocumentSetStore() {
    const selectedCorpus = writable("");
    const currentData = writable(null);
    const currentCorpus = writable(null);
    const loading = writable(false);
    const error = writable(null);
    const regionMetadata = writable(new Map());

    const corpusStats = derived(
        [currentData, currentCorpus],
        ([$data, $corpus]) => {
            if (!$data || !$corpus) return null;

            const nodeCount = new Set([
                ...$data.map(d => d.img_1),
                ...$data.map(d => d.img_2)
            ]).size;

            return {
                nodeCount,
                linkCount: $data.length,
                subCorpusCount: Object.keys($corpus).length,
                docCount: Object.values($corpus).reduce(
                    (count, wit) => count + Object.keys(wit).length, 0
                )
            };
        }
    );

    const availableCorpora = derived([], () => Object.keys(corpusDefinitions));

    async function loadCorpus(corpusName) {
        if (!corpusName) {
            selectedCorpus.set("");
            currentData.set(null);
            currentCorpus.set(null);
            error.set(null);
            return;
        }

        loading.set(true);
        error.set(null);

        try {
            const corpus = corpusDefinitions[corpusName];
            if (!corpus) {
                throw new Error(`Corpus "${corpusName}" not found`);
            }

            const metadata = new Map();
            await enrichCorpusWithTitles(corpus, metadata);

            const data = await fetchCorpusData(corpus);

            if (data && !data.hasOwnProperty("message") && !data.hasOwnProperty("error")) {
                const formattedData = formatData(data);

                selectedCorpus.set(corpusName);
                currentData.set(formattedData);
                currentCorpus.set(corpus);
                regionMetadata.set(metadata);
            } else {
                throw new Error("Failed to load corpus data");
            }
        } catch (e) {
            console.error("Error loading corpus:", e);
            error.set(e.message);
            currentData.set(null);
            currentCorpus.set(null);
        } finally {
            loading.set(false);
        }
    }

    function reset() {
        selectedCorpus.set("");
        currentData.set(null);
        currentCorpus.set(null);
        error.set(null);
        regionMetadata.set(new Map());
    }

    return {
        subscribe: derived(
            [selectedCorpus, currentData, currentCorpus, loading, error, corpusStats, regionMetadata],
            ([$selectedCorpus, $currentData, $currentCorpus, $loading, $error, $corpusStats, $regionMetadata]) => ({
                selectedCorpus: $selectedCorpus,
                data: $currentData,
                corpus: $currentCorpus,
                loading: $loading,
                error: $error,
                stats: $corpusStats,
                metadata: $regionMetadata
            })
        ).subscribe,
        loadCorpus,
        reset,
        availableCorpora,
        regionMetadata
    };
}
