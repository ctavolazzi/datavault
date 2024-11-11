import { writable } from 'svelte/store';

function createSearchStore() {
    const { subscribe, set, update } = writable({
        history: [],
        loading: false,
        error: null
    });

    return {
        subscribe,
        addSearch: async (query) => {
            update(state => ({ ...state, loading: true, error: null }));

            try {
                // Log the search to backend
                await fetch('http://localhost:8000/api/log_search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        user_id: 'placeholder_user_id',
                        query,
                        timestamp: new Date().toISOString()
                    })
                });

                // Update local history
                update(state => ({
                    ...state,
                    history: [{
                        query,
                        timestamp: new Date().toISOString()
                    }, ...state.history]
                }));
            } catch (error) {
                update(state => ({ ...state, error: error.message }));
            } finally {
                update(state => ({ ...state, loading: false }));
            }
        },
        loadHistory: async () => {
            update(state => ({ ...state, loading: true, error: null }));

            try {
                const response = await fetch('http://localhost:8000/api/search_history/placeholder_user_id');
                if (!response.ok) throw new Error('Failed to fetch search history');

                const history = await response.json();
                update(state => ({ ...state, history }));
            } catch (error) {
                update(state => ({ ...state, error: error.message }));
            } finally {
                update(state => ({ ...state, loading: false }));
            }
        },
        clearHistory: () => {
            update(state => ({ ...state, history: [] }));
        }
    };
}

export const searchStore = createSearchStore();