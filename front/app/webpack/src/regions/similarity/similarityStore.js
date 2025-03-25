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

    /** EmptyRegionsType:  */
    const emptySelection = { [currentPageId]: {} };

    const currentPage = writable(1);

    // todo empty selected regions if not in compared regions
    /** @type {RegionsType} */
    const comparedRegions = writable({});

    // TODO to delete very soon
    /** @type {SelectedRegionsType} */
    let storedSelection = JSON.parse(localStorage.getItem("selectedRegions"));
    if (storedSelection && !storedSelection.hasOwnProperty(currentPageId)) {
        storedSelection = emptySelection;
    }

    /** @type {SelectedRegionsType} */
    const selectedRegions = writable(storedSelection || emptySelection);
    // TODO replace with this line
    // const selectedRegions = writable(JSON.parse(localStorage.getItem("selectedRegions")) || emptySelection);

    /** @type {Number[]} */
    const excludedCategories = writable(JSON.parse(localStorage.getItem("excludedCategories")) || []);

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

    /** @type {Number[]} min/max scores for the currently selected regions */
    const similarityScoreRange = writable([])
    /** @type {Number?} RegionPairs below this score will be hidden from the user */
    const similarityScoreCutoff = writable()

    /** @param {Array<int>} to_rid: rid of regions to filter by */
    async function fetchSimilarityScoreRange(to_rid=[]) {
        loading.set(true)
        fetch(`${baseUrl}similarity-score-range`,  {
            method: "POST",
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ to_rid: to_rid })
        })
        .then(response => response.json())
        .then(data => similarityScoreRange.set([data.min, data.max]))
        .catch(err => {
            console.error("Error on fetchSimilarityScoreRange:", err);
            errorMsg.set(err.message);
        })
        .finally(() => loading.set(false))
    }


    const allowedPropagateDepthRange = [2,6];

    /** @type {PropagateParamsType} */
    const propagateParams = writable({
        recursionDepth: allowedPropagateDepthRange,
        filterByRegions: false
    })
    /** @type {SimilarityParamsType} */
    const similarityParams = derived([excludedCategories, selectedRegions, similarityScoreCutoff], ([$excludedCategories, $selectedRegions, $similarityScoreCutoff]) => ({
        excludedCategories: $excludedCategories,
        regions: $selectedRegions,
        similarityScoreCutoff: $similarityScoreCutoff  // @writable similarityScoreCutoff
    }))
    /** @type {SimilarityToolbarParamsType} */
    const similarityToolbarParams = derived([propagateParams, similarityParams], ([$propagateParams, $similarityParams]) => ({
        propagate: $propagateParams,
        similarity: $similarityParams
    }))

    function store(selection) {
        localStorage.setItem("selectedRegions", JSON.stringify(selection));
    }

    // TODO see if `select` and `unselect` are still needed, since the modifications of
    // `selectedRegions` has been moved to `similarityRegions.setComparedRegions`.
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

    // const setPageQImgs = derived(currentPage, ($currentPage) =>
    //     (async () => updatePageQImgs($currentPage))()
    // );

    // function updatePageQImgs(pageNb) {
    //     const start = (pageNb - 1) * pageLength;
    //     const end = start + pageLength;
    //     const currentQImgs = get(qImgs).slice(start, end)
    //     pageQImgs.set(currentQImgs);
    //     return currentQImgs;
    // }

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
        fetchSimilarity,
        similarityScoreRange,
        fetchSimilarityScoreRange,
        setPageQImgs,
        getRegionsInfo,
        handlePageUpdate,
        unselect,
        select,
        addComparedRegions,
        isSelected,
        pageLength,
        similarityToolbarParams,
        propagateParams,
        allowedPropagateDepthRange,
        similarityScoreCutoff,
    };
}

export const similarityStore = createSimilarityStore();
