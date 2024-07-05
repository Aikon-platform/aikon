import { writable, derived } from 'svelte/store';

function createPaginatedRegions() {
    const currentPage = writable(1);
    const pageRegions = writable({});
    const baseUrl = `${window.location.origin}${window.location.pathname}`;

    if (typeof window !== 'undefined') {
        const urlPage = new URLSearchParams(window.location.search).get("p");
        if (urlPage) {
            currentPage.set(parseInt(urlPage));
        }
    }

    const fetchPages = derived(currentPage, ($currentPage, set) =>
        (async () => {
            const response = await fetch(`${baseUrl}canvas?p=${$currentPage}`);
            const data = await response.json();
            pageRegions.set(data);
            return data;
    })());

    function handlePageUpdate(pageNb) {
        currentPage.set(pageNb);
        if (typeof window !== 'undefined') {
            const url = new URL(window.location.href);
            url.searchParams.set("p", pageNb);
            window.history.pushState({}, '', url);
        }
    }

    function updatePageRegions(updateFn) {
        pageRegions.update(updateFn);
    }

    return {
        currentPage,
        pageRegions,
        fetchPages,
        handlePageUpdate,
        updatePageRegions
    };
}

export const pageStore = createPaginatedRegions();
