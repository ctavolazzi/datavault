<script>
  import { onMount } from 'svelte';
  import { searchStore } from '$lib/stores/searchStore';
  import SearchBar from '$lib/components/search/SearchBar.svelte';

  let articles = [];
  let loading = false;
  let error = null;

  async function fetchTopHeadlines() {
    loading = true;
    try {
      const response = await fetch('http://localhost:8000/api/top-headlines');
      if (!response.ok) throw new Error('Failed to fetch top headlines');

      const data = await response.json();
      articles = data.articles || [];
    } catch (err) {
      error = err.message;
      articles = [];
    } finally {
      loading = false;
    }
  }

  async function handleSearch(query) {
    loading = true;
    error = null;

    try {
      const response = await fetch('http://localhost:8000/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query })
      });

      if (!response.ok) throw new Error('Failed to fetch news');

      const data = await response.json();
      articles = data.articles || [];
    } catch (err) {
      error = err.message;
      articles = [];
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    fetchTopHeadlines();
    searchStore.loadHistory();
  });
</script>

<main>
  <h1 class="page-title">News Search</h1>

  <SearchBar onSearch={handleSearch} />

  {#if error}
    <div class="error-message">{error}</div>
  {/if}

  {#if loading}
    <div class="loading-message">Loading...</div>
  {:else}
    <div class="news-grid">
      {#each articles as article}
        <div class="news-card">
          {#if article.urlToImage}
            <img
              src={article.urlToImage}
              alt={article.title}
              class="news-card__image"
              on:error={(e) => e.target.style.display = 'none'}
            />
          {/if}
          <div class="news-card__content">
            <h2 class="news-card__title">{article.title}</h2>
            <p class="news-card__description">{article.description || 'No description available'}</p>
            <a href={article.url} target="_blank" rel="noopener noreferrer">Read more</a>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</main>