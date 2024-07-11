import { writable, derived } from 'svelte/store';

function createSimilarityStore() {
    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const pageLength = 50;

    const currentPage = writable(1);
    const nbOfPage = writable(0);
    const comparedRegions = writable({});
    const qImgs = writable([]);
    /**
     * List of query images (i.e. current regions in first column) for the current page
     * @type {Writable}
     */
    const pageQImgs = writable([]);
    /**
     * List of similar images (i.e. for compared regions) for the current page
     * @type {Writable}
     */
    const pageSImgs = writable({});
    const selectedRegions = writable({});

    if (typeof window !== 'undefined') {
        const urlPage = parseInt(new URLSearchParams(window.location.search).get("sp"));
        if (!isNaN(urlPage)) {
            currentPage.set(urlPage);
        } else {
            currentPage.set(1);
        }
    }

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
            {
                method: "POST",
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN
                },
                body: JSON.stringify({ regionsRefs: Object.keys(regions) })
            }
        ).then(response => response.json()
        ).then(data => {
            qImgs.set(data);
        });

        nbOfPage.set(Math.ceil(imgs.length / pageLength));

        await fetchSimilarityPage();
        return imgs;
    })();

    const fetchSimilarityPage = async () => {
        const response = await fetch(
            `${baseUrl}similarity-page`,
            {
                method: "POST",
                body: JSON.stringify({
                    regionsIds: Object.keys(get(selectedRegions)),
                    pageImgs: get(pageQImgs),
                }),
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN
                },
            }
        );
        const data = await response.json();
        pageSImgs.set(data);
        return data;
    };

    const fetchPage = derived(currentPage, ($currentPage) => async () => {
        return await fetchSimilarityPage();
    });

    function handlePageUpdate(pageNb) {
        const start = (pageNb - 1) * pageLength;
        const end = start + pageLength;
        pageQImgs.set(get(qImgs).slice(start, end))
        currentPage.set(pageNb);

        if (typeof window !== 'undefined') {
            const url = new URL(window.location.href);
            url.searchParams.set("sp", pageNb);
            window.history.pushState({}, '', url);
        }
    }

    function unselect(regionId) {
        selectedRegions.update(selection => {
            delete selection[regionId];
            return { ...selection };
        });
    }
    function select(region) {
        selectedRegions.update(selection => {
            selection[region.id] = region;
            return region;
        });
    }

    function getSimilarImg(qImg) {
        return get(pageSImgs)[qImg];
    }

    function getRegionsInfo(refs) {
        // todo: get info from comparedRegions
        return `TODO: ${refs}`
    }

    return {
        currentPage,
        nbOfPage,
        comparedRegions,
        qImgs,
        pageQImgs,
        pageSImgs,
        selectedRegions,
        fetchPage,
        fetchSimilarity,
        getSimilarImg,
        getRegionsInfo,
        handlePageUpdate,
        unselect,
        select
    };
}

export const similarityStore = createSimilarityStore();
