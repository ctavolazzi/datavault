import { writable } from 'svelte/store';

function createSearchStore() {
    // Initialize with session storage if available
    const initialState = {
        history: [],
        loading: false,
        error: null
    };

    if (typeof window !== 'undefined') {
        const sessionHistory = sessionStorage.getItem('searchHistory');
        if (sessionHistory) {
            initialState.history = JSON.parse(sessionHistory);
        }
    }

    const { subscribe, set, update } = writable(initialState);

    return {
        subscribe,
        addSearch: (query) => {
            update(state => {
                const newHistory = [
                    {
                        query,
                        timestamp: new Date().toISOString()
                    },
                    ...state.history
                ].slice(0, 10);

                if (typeof window !== 'undefined') {
                    sessionStorage.setItem('searchHistory', JSON.stringify(newHistory));
                }

                return {
                    ...state,
                    history: newHistory
                };
            });
        },
        clearHistory: () => {
            if (typeof window !== 'undefined') {
                sessionStorage.removeItem('searchHistory');
            }
            update(state => ({ ...state, history: [] }));
        }
    };
}

export const searchStore = createSearchStore();