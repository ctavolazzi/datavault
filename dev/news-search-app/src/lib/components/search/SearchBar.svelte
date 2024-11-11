<script>
    import { searchStore } from '$lib/stores/searchStore';

    export let onSearch;
    let searchQuery = '';
    let showHistory = false;

    function formatDate(dateString) {
        return new Date(dateString).toLocaleString();
    }

    async function handleSubmit() {
        if (!searchQuery.trim()) return;
        showHistory = false;
        await searchStore.addSearch(searchQuery.trim());
        onSearch(searchQuery.trim());
    }

    function handleHistoryClick(query) {
        searchQuery = query;
        showHistory = false;
        onSearch(query);
    }

    function handleClearHistory() {
        searchStore.clearHistory();
        showHistory = false;
    }
</script>

<div class="search-wrapper">
    <div class="search-container">
        <input
            type="text"
            class="search-input"
            bind:value={searchQuery}
            placeholder="Search for news..."
            on:focus={() => showHistory = true}
            on:keydown={(e) => e.key === 'Enter' && handleSubmit()}
        />
        <button
            class="search-button"
            on:click={handleSubmit}
            disabled={$searchStore.loading || !searchQuery.trim()}
        >
            {$searchStore.loading ? 'Loading...' : 'Search'}
        </button>
    </div>

    {#if showHistory && $searchStore.history.length > 0}
        <div class="search-history-dropdown">
            <div class="history-header">
                <h3>Recent Searches</h3>
                <button class="clear-button" on:click={handleClearHistory}>
                    Clear History
                </button>
            </div>
            <ul>
                {#each $searchStore.history as {query, timestamp}}
                    <li>
                        <button on:click={() => handleHistoryClick(query)}>
                            <span class="query">{query}</span>
                            <span class="timestamp">{formatDate(timestamp)}</span>
                        </button>
                    </li>
                {/each}
            </ul>
        </div>
    {/if}
</div>

<style>
    .search-wrapper {
        position: relative;
        width: 100%;
    }

    .search-history-dropdown {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        border: 1px solid #ddd;
        border-top: none;
        border-radius: 0 0 4px 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        z-index: 1000;
        max-height: 300px;
        overflow-y: auto;
    }

    .history-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px;
        border-bottom: 1px solid #eee;
    }

    .history-header h3 {
        margin: 0;
        font-size: 0.9rem;
        color: #666;
    }

    .clear-button {
        background: none;
        border: none;
        color: #ef4444;
        font-size: 0.8rem;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: 4px;
    }

    .clear-button:hover {
        background-color: #fee2e2;
    }

    .search-history-dropdown ul {
        list-style: none;
        margin: 0;
        padding: 0;
    }

    .search-history-dropdown li {
        border-bottom: 1px solid #eee;
    }

    .search-history-dropdown li:last-child {
        border-bottom: none;
    }

    .search-history-dropdown li button {
        width: 100%;
        padding: 10px;
        text-align: left;
        background: none;
        border: none;
        display: flex;
        justify-content: space-between;
        align-items: center;
        cursor: pointer;
    }

    .search-history-dropdown li button:hover {
        background-color: #f5f5f5;
    }

    .query {
        color: #4d9eff;
    }

    .timestamp {
        color: #666;
        font-size: 0.9rem;
    }
</style>