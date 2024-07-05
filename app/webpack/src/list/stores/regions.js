import { writable, derived } from 'svelte/store';

function createRegionsStore() {
    const currentPage = writable(1);
    const allRegions = writable({});
    const pageRegions = writable({});
    const baseUrl = `${window.location.origin}${window.location.pathname}`;

    if (typeof window !== 'undefined') {
        const urlPage = new URLSearchParams(window.location.search).get("p");
        if (urlPage) {
            currentPage.set(parseInt(urlPage));
        }
    }

    const fetchAll = (async () => {
        const response = await fetch(`${baseUrl}canvas`);
        const data = await response.json();
        let regions = {};
        Object.values(data).forEach(canvases => {
            Object.entries(canvases).forEach(([k, v]) => {
                regions[k] = v;
            })
        })

        allRegions.set(regions);
        return data;
    })();

    const fetchPages = derived(currentPage, ($currentPage) =>
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

    function removeRegion(regionId) {
        allRegions.update(regions => {
            delete regions[regionId];
            return { ...regions };
        });
        // todo update paginated regions as well
    }

    return {
        currentPage,
        pageRegions,
        allRegions,
        fetchPages,
        fetchAll,
        handlePageUpdate,
        updatePageRegions
    };
}

export const regionsStore = createRegionsStore();
