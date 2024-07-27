import { writable, derived, get } from 'svelte/store';
import {initPagination, pageUpdate} from "../utils.js";

function createRecordsStore() {
    const currentPage = writable(1);
    const pageRecords = writable([]);
    const resultNumber = writable(0);

    initPagination(currentPage, "p");

    function handlePageUpdate(pageNb) {
        pageUpdate(pageNb, currentPage, "p");
    }

    // const fetchPage = derived(currentPage, ($currentPage) =>
    //     (async () => {
    //         const response = await fetch(`${window.location.origin}/search/witness/?p=${$currentPage}`);
    //         const data = await response.json();
    //         pageRecords.set(data);
    //         return data;
    //     })());
    async function fetchPage(queryString = null) {
        if (!queryString) {
            queryString = `p=${get(currentPage)}`;
        }
        try {
            const response = await fetch(`${window.location.origin}/search/witness/?${queryString}`);
            const data = await response.json();
            pageRecords.set(data.results);
            resultNumber.set(data.count);
            currentPage.set(data.current_page);
            return data;
        } catch (error) {
            console.error("Error fetching page:", error);
            throw error;
        }
    }

    let resultPage = fetchPage();

    function remove(recordId) {
        // todo
    }

    return {
        currentPage,
        pageRecords,
        resultPage,
        fetchPage,
        handlePageUpdate,
    };
}

export const recordsStore = createRecordsStore();
