import {derived, get, writable} from 'svelte/store';

function createSimilarityStore() {
    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const pageLength = 50;

    const currentPage = writable(1);
    const comparedRegions = writable({});
    const qImgs = writable([]);
    /**
     * List of query images (i.e. current regions in first column) for the current page
     */
    const pageQImgs = writable([]);
    /**
     * List of similar images (i.e. for compared regions) for the current page
     */
    const pageSImgs = writable({});

    const selectedRegions = writable(JSON.parse(localStorage.getItem("selectedRegions")) || {});

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
        // const currentQImgs = get(pageQImgs);
        const response = await fetch(
            `${baseUrl}similarity-page`,
            {
                method: "POST",
                body: JSON.stringify({
                    regionsIds: Object.values(selectedRegions).map(r => r.id),
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

    function addCategory(regionRef, category) {
        /*
        if (event.target.name === 'category' && event.target.id !== 'category5') {
                form.querySelectorAll('input[name="category"]:not(#category5):checked').forEach((checkbox) => {
                    if (checkbox !== event.target) checkbox.checked = false;
                });
            }
            let img_1 = form.querySelector('.img_1').value;
            let img_2 = form.querySelector('.img_2').value;
            let regions_ref_1 = form.querySelector('.regions_ref_1').value;
            let regions_ref_2 = form.querySelector('.regions_ref_2').value;
            let category = form.querySelector('input[name="category"]:not(#category5):checked');
            let category_x = form.querySelector('#category5:checked');
            form.querySelectorAll('input[name="category"]').forEach((checkbox) => {
                checkbox.disabled = true;
            });
            let data = {
                'img_1': img_1,
                'img_2': img_2,
                'regions_ref_1': regions_ref_1,
                'regions_ref_2': regions_ref_2,
                'category': category ? category.value : null,
                'category_x': category_x ? category_x.value : null,
            };
            fetch(`/${APP_NAME}/save-category/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN
                },
                body: JSON.stringify(data)
            }).then(response => response.json())
            .then(data => {
				form.querySelectorAll('input[name="category"]').forEach((checkbox) => {
					checkbox.disabled = false;
				});
			});
        */
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
        addCategory
    };
}

export const similarityStore = createSimilarityStore();
