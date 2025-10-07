import { writable, derived, get } from 'svelte/store';
import {initPagination, pageUpdate} from "../utils.js";

function createRegionsStore() {
    const baseUrl = `${window.location.origin}${window.location.pathname}`;

    const currentPage = writable(1);
    const allRegions = writable({});
    const pageRegionExtraction = writable({});
    const clipBoard = writable("");

    initPagination(currentPage, "p");

    function copyRef(ref) {
        clipBoard.update((cb) => {
            const itemRef = cb === ref ? "" : ref;
            // NOTE: isItemCopied stays to true if user copied another string
            navigator.clipboard.writeText(itemRef).then(r => "");
            return itemRef;
        });
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
            pageRegionExtraction.set(data);
            return data;
        })());

    function handlePageUpdate(pageNb) {
        pageUpdate(pageNb, currentPage, "p");
    }

    function remove(regionId) {
        allRegions.update(regions => {
            delete regions[regionId];
            return { ...regions };
        });
        pageRegionExtraction.update(currentPageRegions => {
            for (const canvasNb in currentPageRegions) {
                if (currentPageRegions[canvasNb][regionId]) {
                    const { [regionId]: _, ...rest } = currentPageRegions[canvasNb];
                    currentPageRegions[canvasNb] = rest;
                    return currentPageRegions;
                }
            }
            return currentPageRegions;
        });
    }

    return {
        currentPage,
        pageRegionExtraction,
        allRegions,
        fetchPages,
        fetchAll,
        handlePageUpdate,
        remove,
        clipBoard,
        copyRef,
    };
}

export const regionsStore = createRegionsStore();
