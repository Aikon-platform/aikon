import {derived, get, writable} from 'svelte/store';
import {initPagination, pageUpdate} from "../../utils.js";

function createVectorizationStore() {
    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const pageLength = 49;

    const currentPage = writable(1);
    const vectImgs = writable([]);
    const pageVectImgs = writable([]);

    /**
     * Fetches all query images and regions that were compared to current regions on load
     * @type {Promise<any>}
     */
    const fetchVectorization = (async () => {
        const vecto = await fetch(
            `${baseUrl}vectorized-images`
        ).then(response => response.json()
        ).then(data => {
            vectImgs.set(data);
            return data;
        }).catch(
            error => console.error('Error:', error)
        );

        // pageVectImgs is derived from currentPage update
        handlePageUpdate(initCurrentPage());
        return vecto;
    })();

    const initCurrentPage = () => initPagination(currentPage, "vp");

    const setPageVectImgs = derived(currentPage, ($currentPage) =>
        (async () => updatePageVectImgs($currentPage))()
    );

    function updatePageVectImgs(pageNb) {
        const start = (pageNb - 1) * pageLength;
        const end = start + pageLength;
        const currentVectImgs = get(vectImgs).slice(start, end)
        pageVectImgs.set(currentVectImgs);
        return currentVectImgs;
    }

    function handlePageUpdate(pageNb) {
        pageUpdate(pageNb, currentPage, "vp");
    }

    return {
        currentPage,
        pageLength,
        vectImgs,
        fetchVectorization,
        setPageVectImgs,
        pageVectImgs,
        handlePageUpdate,
    };
}

export const vectorizationStore= createVectorizationStore();
