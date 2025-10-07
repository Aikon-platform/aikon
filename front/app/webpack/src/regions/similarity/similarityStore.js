import { derived, get, writable } from 'svelte/store';
import { errorMsg, initPagination, loading, pageUpdate } from "../../utils.js";
import { csrfToken } from "../../constants.js";

/**
 * @typedef { Object.<number, Object.<string, RegionsType>> } SelectedRegionsType
 *  { <witness id>: { <regions ref>: RegionsType }
 */
/**
 * @typedef {Object.<number, undefined|>} EmptyRegionsType:
 *  like the above SelectedRegionsType, but there is no RegionsType
 */
/**
 * @typedef RegionsType
 *  a regions extraction
 * @type {object}
 * @property {number} id
 * @property {string} ref
 * @property {string} url: IIIF URL to the extracted image regions
 * @property {"Regions"} type
 * @property {"Regions"} class: python  class
 * @property {string} title
 * @property {number} zeros,
 * @property {number} img_nb: number of extracted images
 */
/**
 * @typedef { Object.<string, RegionsType> } ComparedRegionsType
 *  { <regions ref>: RegionsType }
 */
/**
 * @typedef PropagateParamsType
 * @property {number} propagateRecursionDepth
 * @property {boolean} propagateFilterByRegionExtraction
 */
/**
 * @typedef SimilarityParamsType
 * @type {object}
 * @property {number[]} excludedCategories
 * @property {SelectedRegionsType} regions
 * @property {number} similarityScoreCutoff
 */
/**
 * @typedef SimilarityToolbarParamsType
 *      all params defined in SimilarityToolbar
 * @type {object}
 * @property {PropagateParamsType} propagate
 * @property {SimilarityParamsType} similarity
 */


function createSimilarityStore() {
    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const pageLength = 25;

    /** @type {number} the current witness' ID */
    const currentPageId = window.location.pathname.match(/\d+/g).join('-');

    /** @type {EmptyRegionsType}  */
    const emptySelection = { [currentPageId]: {} };

    const allowedPropagateDepthRange = [2,6];

    const currentPage = writable(1);

    /** @type {writable<ComparedRegionsType>} */
    const comparedRegions = writable({});

    /** @type {writable<SelectedRegionsType>} */
    const selectedRegions = writable(JSON.parse(localStorage.getItem("selectedRegions")) || emptySelection);
    selectedRegions.subscribe((value) => localStorage.setItem("selectedRegions", JSON.stringify(value)));

    /** @type {writable<number[]>} */
    const excludedCategories = writable(JSON.parse(localStorage.getItem("excludedCategories")) || []);
    excludedCategories.subscribe((value) => localStorage.setItem("excludedCategories", JSON.stringify(value)));

    /** @type {writable<number?>} RegionPairs below this score will be hidden from the user */
    const similarityScoreCutoff = writable(JSON.parse(localStorage.getItem("similarityScoreCutoff")) || undefined);
    similarityScoreCutoff.subscribe((value) => {
        // since the 1st value is undefined, we need to ensure we're not writing this to localStorage
        if (value!=null) localStorage.setItem("similarityScoreCutoff", JSON.stringify(value))
    });

    /** @type {writable<number[]>} */
    const propagateRecursionDepth = writable(JSON.parse(localStorage.getItem("propagateRecursionDepth")) || allowedPropagateDepthRange[1]);
    propagateRecursionDepth.subscribe((value) => localStorage.setItem("propagateRecursionDepth", JSON.stringify(value)));

    /** @type {writable<Boolean>} */
    const propagateFilterByRegionExtraction = writable(JSON.parse(localStorage.getItem("propagateFilterByRegionExtraction")) || false);
    propagateFilterByRegionExtraction.subscribe((value) => localStorage.setItem("propagateFilterByRegionExtraction", JSON.stringify(value)));

    /** @type {writable<PropagateParamsType>} no localStorage syncing since individual stores are aldready synced */
    const propagateParams = derived([propagateRecursionDepth, propagateFilterByRegionExtraction], ([$propagateRecursionDepth, $propagateFilterByRegionExtraction]) => ({
        propagateRecursionDepth: $propagateRecursionDepth,
        propagateFilterByRegionExtraction: $propagateFilterByRegionExtraction
    }));

    /** @type {writable<SimilarityParamsType>} no localStorage syncing since individual stores are aldready synced */
    const similarityParams = derived([excludedCategories, selectedRegions, similarityScoreCutoff], ([$excludedCategories, $selectedRegions, $similarityScoreCutoff]) => ({
        excludedCategories: $excludedCategories,
        regions: $selectedRegions,
        similarityScoreCutoff: $similarityScoreCutoff
    }));

    /** @type {writable<SimilarityToolbarParamsType>} no localStorage syncing since individual stores are aldready synced */
    const similarityToolbarParams = derived([propagateParams, similarityParams], ([$propagateParams, $similarityParams]) => ({
        propagate: $propagateParams,
        similarity: $similarityParams
    }));

    /** @type {writable<string[]|[]>} query image names for the current witness */
    const qImgs = writable([]);
    const pageQImgs = writable([]);

    /**
     * On load, fetches all query images and regions that were compared to current regions
     * @type {Promise<any>}
     */
    async function fetchSimilarity() {
        const getComparedRegions = async () => {
            const regionsResponse = await fetch(`${baseUrl}compared-regions`);
            const regionsData = await regionsResponse.json();
            comparedRegions.set(regionsData);

            // from one refresh to another, in case of database changes, selectedRegions may contain regions that are not in comparedRegions => delete those
            selectedRegions.update((_selectedRegions) => {
                let currentSelectedRegions = _selectedRegions[currentPageId] || {};
                if ( Object.keys(currentSelectedRegions).length ) {
                    let filtered =
                        // `.filter().reduce()` creates a copy of `currentSelectedRegions` without the keys that are not in `regionsData`
                        Object.keys(currentSelectedRegions)
                        .filter(key => Object.keys(regionsData).includes(key))
                        .reduce((obj, key) => {
                            obj[key] = currentSelectedRegions[key];
                            return obj
                        }, {});
                        _selectedRegions[currentPageId] = filtered;
                }
                return _selectedRegions;
            });
        }
        const getQueryImages = async () => {
            const imgsResponse = await fetch(`${baseUrl}query-images`);
            const imgsData = await imgsResponse.json();
            if (imgsData.length > 0) {
                qImgs.set(imgsData);
                handlePageUpdate(initCurrentPage());
            }
        }

        loading.set(true);
        try {
            // Promise.all => parallelize async queries
            await Promise.all([ getComparedRegions(), getQueryImages() ]);
        } catch (err) {
            console.error('Error:', err);
            errorMsg.set(err.message);
        } finally {
            loading.set(false);
        }
    }

    function store(selection) {
        localStorage.setItem("selectedRegions", JSON.stringify(selection));
    }

    // TODO delete select/unselect ? unselect is only used in `_SimilarityBtn` (to be deleted), `select` is still used in `SimilarRegion`.
    function unselect(regionRef) {
        selectedRegions.update(selection => {
            const updatedSelection = { ...selection };
            delete updatedSelection[currentPageId][regionRef];
            store(updatedSelection)
            return updatedSelection;
        });
    }
    function select(region) {
        selectedRegions.update(selection => {
            const updatedSelection = {
                ...selection,
                [currentPageId]: {
                    ...(selection[currentPageId] || {}),
                    [region.ref]: region
                }
            };
            store(updatedSelection);
            return updatedSelection;
        });
    }

    const isSelected = derived(selectedRegions, ($selectedRegions) =>
        regionRef => $selectedRegions[currentPageId]?.hasOwnProperty(regionRef)
    );

    function getRegionsInfo(ref) {
        const displayedRegions = get(comparedRegions);
        const regionRef = Object.keys(displayedRegions).filter(key => key.startsWith(ref));
        if (regionRef.length !== 1) {
            return {title: "Error"};
        }
        return displayedRegions[regionRef[0]]
    }

    const initCurrentPage = () => initPagination(currentPage, "sp");

    // without `qImgs`, `setPageQImgs` may run before qImgs has been defined
    const setPageQImgs = derived([currentPage, qImgs], ([$currentPage, $qImgs]) =>
        (async () => updatePageQImgs($currentPage, $qImgs))());

    function updatePageQImgs(pageNb, _qImgs) {
        const start = (pageNb - 1) * pageLength;
        const end = start + pageLength;
        const currentQImgs = _qImgs.slice(start, end);
        pageQImgs.set(currentQImgs);
        return currentQImgs;
    }

    function handlePageUpdate(pageNb) {
        pageUpdate(pageNb, currentPage, "sp");
    }

    function addComparedRegions(region) {
        comparedRegions.update(regions => {
            return {...regions, [region.ref]: region};
        });
    }

    return {
        currentPage,
        comparedRegions,
        excludedCategories,
        qImgs,
        pageQImgs,
        selectedRegions,
        propagateRecursionDepth,
        propagateFilterByRegionExtraction,
        similarityToolbarParams,
        propagateParams,
        similarityScoreCutoff,
        allowedPropagateDepthRange,
        fetchSimilarity,
        setPageQImgs,
        getRegionsInfo,
        handlePageUpdate,
        unselect,
        select,
        addComparedRegions,
        isSelected,
        pageLength,
    };
}

export const similarityStore = createSimilarityStore();
