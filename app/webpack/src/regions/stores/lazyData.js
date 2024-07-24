import { writable } from 'svelte/store';

function createLazyDataStore() {
    const { subscribe, set, update } = writable({
        items: {},
        loading: false,
        error: null,
        currentPage: 1,
        totalPages: 1
    });

    return {
        subscribe,
        loadMore: async (baseUrl, pageSize = 20) => {
            update(state => ({ ...state, loading: true, error: null }));
            try {
                const response = await fetch(`${baseUrl}?page=${state.currentPage}&pageSize=${pageSize}`);
                if (!response.ok) throw new Error('Failed to fetch data');
                const data = await response.json();

                update(state => ({
                    items: { ...state.items, ...data.items },
                    currentPage: state.currentPage + 1,
                    totalPages: data.totalPages,
                    loading: false
                }));
            } catch (error) {
                update(state => ({ ...state, error, loading: false }));
            }
        },
        reset: () => set({ items: {}, loading: false, error: null, currentPage: 1, totalPages: 1 })
    };
}

export const lazyData = createLazyDataStore();
