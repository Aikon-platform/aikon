import {derived, get, writable} from 'svelte/store';
import {errorMsg, initPagination, loading, pageUpdate} from "../../utils.js";

function createSimilarityStore() {
    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const pageLength = 25;

    const currentPage = writable(1);
    // todo empty selected regions if not in compared regions
    const comparedRegions = writable({});
    const selectedRegions = writable(JSON.parse(localStorage.getItem("selectedRegions")) || {});
    const excludedCategories = writable(JSON.parse(localStorage.getItem("excludedCategories")) || []);
    const qImgs = writable([]);
    const pageQImgs = writable([]);

    /**
     * Fetches all query images and regions that were compared to current regions on load
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
            delete updatedSelection[regionRef];
            store(updatedSelection)
            return updatedSelection;
        });
    }
    function select(region) {
        selectedRegions.update(selection => {
            const updatedSelection = { ...selection, [region.ref]: region };
            store(updatedSelection)
            return updatedSelection;
        });
    }

    const isSelected = derived(selectedRegions, ($selectedRegions) =>
        regionRef => $selectedRegions.hasOwnProperty(regionRef)
    );

    function getRegionsInfo(ref) {
        const displayedRegions = get(comparedRegions);
        const regionRef = Object.keys(displayedRegions).filter(key => key.startsWith(ref));
        if (regionRef.length !== 1) {
            return {title: "Error"};
        }
        return displayedRegions[regionRef[0]]
    }

    return {
        currentPage,
        comparedRegions,
        excludedCategories,
        qImgs,
        pageQImgs,
        selectedRegions,
        fetchSimilarity,
        setPageQImgs,
        getRegionsInfo,
        handlePageUpdate,
        unselect,
        select,
        addComparedRegions,
        isSelected,
        pageLength
    };
}

export const similarityStore= createSimilarityStore();
