import { writable } from 'svelte/store';

function createTabStore(defaultTab = "all") {
    const initialTab = new URLSearchParams(window.location.search).get("tab") ?? defaultTab;
    const { subscribe, set } = writable(initialTab);

    return {
        subscribe,
        change: (tab) => {
            set(tab);
            const url = new URL(window.location);
            url.searchParams.set("tab", tab);
            window.history.pushState({}, "", url);
        },
        init: (fallback = defaultTab) => {
            const tab = new URLSearchParams(window.location.search).get("tab") ?? fallback;
            set(tab);
        }
    };
}

export const activeLayout = createTabStore();
