import { writable } from 'svelte/store';

function createTabStore() {
    const initialTab = new URLSearchParams(window.location.search).get("tab") ?? "all";
    const { subscribe, set } = writable(initialTab);

    return {
        subscribe,
        change: (tab) => {
            set(tab);
            const url = new URL(window.location);
            url.searchParams.set("tab", tab);
            window.history.pushState({}, "", url);
        },
        init: () => {
            const tab = new URLSearchParams(window.location.search).get("tab") ?? "all";
            set(tab);
        }
    };
}

export const activeLayout = createTabStore();
