<script>
  import { searchStore } from '$lib/stores/searchStore';
  export let onHistoryItemClick;

  function formatDate(dateString) {
      return new Date(dateString).toLocaleString();
  }
</script>

<div class="search-history">
  <h3>Recent Searches</h3>
  {#if $searchStore.history.length > 0}
      <ul>
          {#each $searchStore.history as {query, timestamp}}
              <li>
                  <button on:click={() => onHistoryItemClick(query)}>
                      {query}
                  </button>
                  <span class="timestamp">{formatDate(timestamp)}</span>
              </li>
          {/each}
      </ul>
  {:else}
      <p>No recent searches</p>
  {/if}
</div>

<style>
  .search-history {
      margin-top: 2rem;
      padding: 1rem;
      background-color: #f8f9fa;
      border-radius: 4px;
  }

  h3 {
      margin: 0 0 1rem 0;
      font-size: 1.1rem;
  }

  ul {
      list-style: none;
      padding: 0;
      margin: 0;
  }

  li {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0.5rem 0;
      border-bottom: 1px solid #eee;
  }

  button {
      background: none;
      border: none;
      color: #4d9eff;
      cursor: pointer;
      padding: 0;
  }

  .timestamp {
      color: #666;
      font-size: 0.9rem;
  }
</style>