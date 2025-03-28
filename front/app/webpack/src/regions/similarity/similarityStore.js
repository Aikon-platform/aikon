import { derived, get, writable } from 'svelte/store';
import { errorMsg, initPagination, loading, pageUpdate } from "../../utils.js";
import { csrfToken } from "../../constants.js";

/**
 * @typedef { Object.<number, RegionsType> } SelectedRegionsType
 *  selected regions are witness Ids mapped to all the region extractions
 *  against with which RegionPairs have been evaluated
 */
/**
 * @typedef {Object.<number, undefined>} EmptyRegionsType:
 *  like the above SelectedRegionsType, but there is no RegionsType
 */
/**
 * @typedef RegionsType
 *  a regions extraction
 * @type {object}
 * @property {Number} id
 * @property {String} ref
 * @property {String} url: IIIF URL to the extracted image regions
 * @property {"Regions"} type
 * @property {"Regions"} class: python  class
 * @property {String} title
 * @property {Number} zeros,
 * @property {Number} img_nb: number of extracted images
 */
/**
 * @typedef PropagateParamsType
 * @property {Number[]} recursionDepth
 * @property {boolean} filterByRegions
 */
/**
 * @typedef SimilarityParamsType
 * @type {object}
 * @property {Number[]} excludedCategories
 * @property {SelectedRegionsType} regions
 * @property {Number} similarityScoreCutoff
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

    /** @type {Number} the current witness' ID */
    const currentPageId = window.location.pathname.match(/\d+/g).join('-');

    /** @type {EmptyRegionsType}  */
    const emptySelection = { [currentPageId]: {} };

    const allowedPropagateDepthRange = [2,6];

    const currentPage = writable(1);

    // todo empty selected regions if not in compared regions
    /** @type {RegionsType} */
    const comparedRegions = writable({});

    /** @type {SelectedRegionsType} */
    const selectedRegions = writable(JSON.parse(localStorage.getItem("selectedRegions")) || emptySelection);
    selectedRegions.subscribe((value) => localStorage.setItem("selectedRegions", JSON.stringify(value)));

    /** @type {Number[]} */
    const excludedCategories = writable(JSON.parse(localStorage.getItem("excludedCategories")) || []);
    excludedCategories.subscribe((value) => localStorage.setItem("excludedCategories", JSON.stringify(value)));

    /** @type {Number?} RegionPairs below this score will be hidden from the user */
    const similarityScoreCutoff = writable(JSON.parse(localStorage.getItem("similarityScoreCutoff")) || undefined);
    similarityScoreCutoff.subscribe((value) => {
        // since the 1st value is undefined, we need to ensure we're not writing this to localStorage
        if (value!=null) localStorage.setItem("similarityScoreCutoff", JSON.stringify(value))
    });

    /** @type {Number[]} */
    const propagateRecursionDepth = writable(JSON.parse(localStorage.getItem("propagateRecursionDepth")) || allowedPropagateDepthRange);
    propagateRecursionDepth.subscribe((value) => localStorage.setItem("propagateRecursionDepth", JSON.stringify(value)));

    /** @type {Boolean} */
    const propagateFilterByRegions = writable(JSON.parse(localStorage.getItem("propagateFilterByRegions")) || false);
    propagateFilterByRegions.subscribe((value) => localStorage.setItem("propagateFilterByRegions", JSON.stringify(value)));

    /** @type {PropagateParamsType} no localStorage syncing since individual stores are aldready synced */
    const propagateParams = derived([propagateRecursionDepth, propagateFilterByRegions], ([$propagateRecursionDepth, $propagateFilterByRegions]) => ({
        propagateRecursionDepth: $propagateRecursionDepth,
        propagateFilterByRegions: $propagateFilterByRegions
    }));

    /** @type {SimilarityParamsType} no localStorage syncing since individual stores are aldready synced */
    const similarityParams = derived([excludedCategories, selectedRegions, similarityScoreCutoff], ([$excludedCategories, $selectedRegions, $similarityScoreCutoff]) => ({
        excludedCategories: $excludedCategories,
        regions: $selectedRegions,
        similarityScoreCutoff: $similarityScoreCutoff
    }));

    /** @type {SimilarityToolbarParamsType} no localStorage syncing since individual stores are aldready synced */
    const similarityToolbarParams = derived([propagateParams, similarityParams], ([$propagateParams, $similarityParams]) => ({
        propagate: $propagateParams,
        similarity: $similarityParams
    }));

    /** @type {String[]|[]} query image names for the current witness */
    const qImgs = writable([]);
    const pageQImgs = writable([]);

    /**
     * On load, fetches all query images and regions that were compared to current regions
     * @type {Promise<any>}
     */
    async function fetchSimilarity() {
        loading.set(true);
        try {
            const regionsResponse = await fetch(`${baseUrl}compared-regions`);
            const regionsData = await regionsResponse.json();
            comparedRegions.set(regionsData);

            const imgsResponse = await fetch(`${baseUrl}query-images`);
            const imgsData = await imgsResponse.json();
            if (imgsData.length > 0) {
                qImgs.set(imgsData);
                handlePageUpdate(initCurrentPage());
            }
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
            store(updatedSelection)
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
        (async () => updatePageQImgs($currentPage, $qImgs))()
    );

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
        propagateFilterByRegions,
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
