import { writable, get } from 'svelte/store';
import {initPagination, pageUpdate} from "../utils.js";

function createRecordsStore() {
    const currentPage = writable(1);
    const pageRecords = writable([]);
    const resultNumber = writable(0);
    const searchParams = writable(new URLSearchParams(window.location.search));

    initPagination(currentPage, "p");

    async function fetchPage() {
        const params = get(searchParams);
        params.set('p', `${get(currentPage)}`);

        try {
            const response = await fetch(`${window.location.origin}/search/witness/?${params.toString()}`);
            const data = await response.json();
            pageRecords.set(data.results);
            resultNumber.set(data.count);
            currentPage.set(data.current_page);

            params.set('p', String(get(currentPage)));
            const newUrl = `${window.location.pathname}?${params.toString()}`;
            history.pushState(null, '', newUrl);

            return data;
        } catch (error) {
            console.error("Error fetching page:", error);
            throw error;
        }
    }

    let resultPage = fetchPage();
    function handlePageUpdate(pageNb) {
        pageUpdate(pageNb, currentPage, "p");
        resultPage = fetchPage();
    }

    function recordSearch(formData) {
        const queryParams = new URLSearchParams(formData);
        searchParams.set(queryParams);
        handlePageUpdate(1);
    }

    function remove(recordId) {
        // todo add deletion feature
    }

    return {
        currentPage,
        pageRecords,
        resultPage,
        resultNumber,
        fetchPage,
        handlePageUpdate,
        recordSearch,
    };
}

export const recordsStore = createRecordsStore();
