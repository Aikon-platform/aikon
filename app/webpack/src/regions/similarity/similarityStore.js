import {csrfToken} from '../../constants';
import {derived, get, writable} from 'svelte/store';

function createSimilarityStore() {
    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const pageLength = 50;

    const currentPage = writable(1);
    const comparedRegions = writable({});
    const selectedRegions = writable(JSON.parse(localStorage.getItem("selectedRegions")) || {});
    const qImgs = writable([]);
    /**
     * List of query images (i.e. current regions in first column) for the current page
     */
    const pageQImgs = writable([]);
    /**
     * List of similar images (i.e. for compared regions) for the current page
     */
    const pageSImgs = writable({});

    /**
     * Fetches all query images and regions that were compared to current regions on load
     * @type {Promise<any>}
     */
    const fetchSimilarity = (async () => {
        const regions = await fetch(
            `${baseUrl}similar-regions`
        ).then(response => response.json()
        ).then(data => {
            comparedRegions.set(data);
            return data;
        }).catch(
            error => console.error('Error:', error)
        );

        const imgs = await fetch(
            `${baseUrl}query-images`,
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

        // pageQImgs and pageSImgs are derived from currentPage update
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

    const setPageSImgs = derived(selectedRegions, ($selectedRegions) =>
        // todo make setPageSImgs reactive on page change
        (async () => await fetchPageSImgs($selectedRegions))()
    );

    function updatePageQImgs(pageNb) {
        const start = (pageNb - 1) * pageLength;
        const end = start + pageLength;
        const currentQImgs = get(qImgs).slice(start, end)
        pageQImgs.set(currentQImgs);
        return currentQImgs;
    }

    const fetchPageSImgs = async (selectedRegions) => {
        const response = await fetch(
            `${baseUrl}similarity-page`,
            {
                method: "POST",
                body: JSON.stringify({
                    regionsIds: Object.values(selectedRegions).map(r => r.id),
                    pageImgs: get(pageQImgs),
                    topk: 10, // TODO retrieve this value from the user
                    excludedCategories: [] // TODO retrieve this value from the toolbar
                }),
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
            }
        );
        const data = await response.json();
        pageSImgs.set(data);
        return data;
    };

    // const fetchQSimilarity = async (qImg) => {
    //     const response = await fetch(
    //         `${baseUrl}similarity-page`,
    //         {
    //             method: "POST",
    //             body: JSON.stringify({
    //                 regionsIds: Object.values(get(selectedRegions)).map(r => r.id),
    //                 qImg: qImg,
    //             }),
    //             headers: {
    //                 'Content-Type': 'application/json',
    //                 'X-CSRFToken': csrfToken
    //             },
    //         }
    //     );
    //     return await response.json()
    // };

    function addSimilarity(qImg, sImg) {
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

    function getSimilarImgs(qImg) {
        const currentSImgs = get(pageSImgs);
        return currentSImgs.hasOwnProperty(qImg) ? currentSImgs[qImg] : [];
    }

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
        qImgs,
        pageQImgs,
        pageSImgs,
        selectedRegions,
        fetchSimilarity,
        setPageQImgs,
        setPageSImgs,
        getSimilarImgs,
        getRegionsInfo,
        handlePageUpdate,
        unselect,
        select,
        isSelected,
    };
}

export const similarityStore = createSimilarityStore();
