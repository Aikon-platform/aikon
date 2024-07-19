import {csrfToken} from '../../constants';
import {derived, get, writable} from 'svelte/store';

function createSimilarityStore() {
    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const pageLength = 50;

    const currentPage = writable(1);
    const comparedRegions = writable({});
    const selectedRegions = writable(JSON.parse(localStorage.getItem("selectedRegions")) || {});
    const excludedCategories = writable(JSON.parse(localStorage.getItem("excludedCategories")) || []);
    const qImgs = writable([]);
    const pageQImgs = writable([]);

    /**
     * Fetches all query images and regions that were compared to current regions on load
     * @type {Promise<any>}
     */
    const fetchSimilarity = (async () => {
        const regions = await fetch(
            `${baseUrl}compared-regions`
        ).then(response => response.json()
        ).then(data => {
            comparedRegions.set(data);
            return data;
        }).catch(
            error => console.error('Error:', error)
        );

        const imgs = await fetch(
            `${baseUrl}query-regions`,
        ).then(response => response.json()
        ).then(data => {
            if (data.length === 0 || !data) {
                return null;
            }
            qImgs.set(data);
            return data;
        }).catch(
            error => console.error('Error:', error)
        );

        // pageQImgs is derived from currentPage update
        handlePageUpdate(initCurrentPage());
        return imgs;
    })();

    const initCurrentPage = () => {
        if (typeof window !== 'undefined') {
            const urlPage = parseInt(new URLSearchParams(window.location.search).get("sp"));
            if (!isNaN(urlPage)) {
                currentPage.set(urlPage);
                return urlPage;
            }
        }
        currentPage.set(1);
        return 1;
    }

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

    function addSimilarRegion(qImg, sImg) {
        // TODO send request to add region pair record
        // TODO django side, check if region ref is correctly formatted + correspond to existing wit+digit
        // TODO django side, check if region pair already exists
        // TODO django side, check if digit has already regions, if not create one?
        // TODO django side, create region pair record (if 2 images has been paired, add user id to category x)
        // TODO if successful add region to comparedRegions (if not already the case)
        // TODO if successful select region in selectedRegions (if not already the case)
        // TODO if successful display new similar regions
        // TODO if unsuccessful display error message + do not show new similar regions
    }

    function handlePageUpdate(pageNb) {
        currentPage.set(pageNb);
        if (typeof window !== 'undefined') {
            const url = new URL(window.location.href);
            url.searchParams.set("sp", pageNb);
            window.history.pushState({}, '', url);
        }
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
        isSelected,
    };
}

export const similarityStore = createSimilarityStore();
