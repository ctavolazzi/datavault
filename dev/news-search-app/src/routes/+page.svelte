<script>
  import { onMount } from 'svelte';
  import { searchStore } from '$lib/stores/searchStore';
  import SearchBar from '$lib/components/search/SearchBar.svelte';

  let articles = [];
  let loading = false;
  let error = null;

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  // Filter out removed articles or those with placeholder content
  function isValidArticle(article) {
    return article.title !== '[Removed]' &&
           article.description !== '[Removed]' &&
           article.title?.trim() !== '' &&
           article.description?.trim() !== '';
  }

  // Add debounce utility
  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  async function fetchTopHeadlines() {
    loading = true;
    error = null;
    try {
      const response = await fetch(`${API_BASE_URL}/api/top-headlines`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      articles = (data.articles || []).filter(isValidArticle);
    } catch (err) {
      console.error('Error fetching headlines:', err);
      error = 'Unable to load headlines. Please try again later.';
      articles = [];
    } finally {
      loading = false;
    }
  }

  // Debounce the search handler
  const debouncedSearch = debounce(async (query) => {
    if (!query.trim()) {
      await fetchTopHeadlines();
      return;
    }

    loading = true;
    error = null;

    try {
      const response = await fetch(`${API_BASE_URL}/api/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
        credentials: 'same-origin'
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      articles = (data.articles || []).filter(isValidArticle);
    } catch (err) {
      console.error('Error searching news:', err);
      error = 'Unable to search news. Please try again later.';
      articles = [];
    } finally {
      loading = false;
    }
  }, 300); // 300ms delay

  // Update the handleSearch function to use debouncing
  function handleSearch(query) {
    debouncedSearch(query);
  }

  onMount(() => {
    const controller = new AbortController();

    // Only fetch top headlines on initial load
    fetchTopHeadlines();

    return () => {
      controller.abort();
    };
  });
</script>

<main>
  <h1 class="page-title">News Search</h1>

  <SearchBar onSearch={handleSearch} />

  {#if error}
    <div class="error-message" role="alert">
      <span>😕 {error}</span>
      <button on:click={fetchTopHeadlines}>Try Again</button>
    </div>
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
              on:error={(e) => {
                e.target.style.display = 'none';
                e.target.closest('.news-card').classList.add('no-image');
              }}
              loading="lazy"
            />
          {/if}
          <div class="news-card__content">
            <h2 class="news-card__title">{article.title}</h2>
            <p class="news-card__description">
              {article.description || 'No description available'}
            </p>
            <a href={article.url} target="_blank" rel="noopener noreferrer">Read more</a>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</main>

<style>
  .news-card.no-image {
    min-height: 200px; /* Ensure consistent height even without image */
  }
</style>