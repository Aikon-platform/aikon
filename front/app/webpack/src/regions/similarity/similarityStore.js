import { derived, get, writable } from 'svelte/store';
import { errorMsg, initPagination, loading, pageUpdate } from "../../utils.js";
import { csrfToken } from "../../constants.js";


function createSimilarityStore() {
    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const currentPageId = window.location.pathname.match(/\d+/g).join('-');
    const emptySelection = { [currentPageId]: {}};
    const pageLength = 25;

    const currentPage = writable(1);
    // todo empty selected regions if not in compared regions
    const comparedRegions = writable({});

    // TODO to delete very soon
    let storedSelection = JSON.parse(localStorage.getItem("selectedRegions"));
    if (storedSelection && !storedSelection.hasOwnProperty(currentPageId)) {
        storedSelection = emptySelection;
    }
    const selectedRegions = writable(storedSelection || emptySelection);
    // TODO replace with this line
    // const selectedRegions = writable(JSON.parse(localStorage.getItem("selectedRegions")) || emptySelection);

    const excludedCategories = writable(JSON.parse(localStorage.getItem("excludedCategories")) || []);
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

    const similarityScoreRange = writable([])
    /** @param {Array<int>} to_rid: rid of regions to filter by */
    async function fetchSimilarityScoreRange(to_rid=[]) {
        loading.set(true)
        console.log(`${baseUrl}similarity-score-range`);
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

    const initCurrentPage = () => initPagination(currentPage, "sp");

    const setPageQImgs = derived(currentPage, ($currentPage) =>
        (async () => updatePageQImgs($currentPage))()
    );

    function updatePageQImgs(pageNb) {
        const start = (pageNb - 1) * pageLength;
        const end = start + pageLength;
        const currentQImgs = get(qImgs).slice(start, end)
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

    function store(selection) {
        localStorage.setItem("selectedRegions", JSON.stringify(selection));
    }

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

    const allowedPropagateDepthRange = [2,6];

    const propagateParams = writable({
        recursionDepth: allowedPropagateDepthRange,
        filterByRegion: false
    })
    const otherParams = writable({ /** TBD */ });
    const toolbarParams = derived([propagateParams, otherParams], ([$propagateParams, $otherParams]) => ({
        propagate: $propagateParams,
        other: $otherParams
    }))

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
        toolbarParams,
        propagateParams,
        allowedPropagateDepthRange,
    };
}

export const similarityStore = createSimilarityStore();
