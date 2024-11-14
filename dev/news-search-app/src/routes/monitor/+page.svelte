<script>
  import { onMount } from 'svelte';
  import { Chart } from 'chart.js/auto';

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  let stats = null;
  let healthStatus = null;
  let hitMissChart;
  let responseTimeChart;

  async function fetchData() {
    try {
      const [statsRes, healthRes, sizeRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/cache/stats`),
        fetch(`${API_BASE_URL}/api/cache/health`),
        fetch(`${API_BASE_URL}/api/cache/size`)
      ]);

      stats = await statsRes.json();
      healthStatus = await healthRes.json();
      const sizeInfo = await sizeRes.json();

      updateCharts(stats.data);
      updateSizeInfo(sizeInfo.data);
    } catch (error) {
      console.error('Failed to fetch monitoring data:', error);
    }
  }

  function updateCharts(data) {
    if (hitMissChart) {
      hitMissChart.data.datasets[0].data = [data.hits, data.misses];
      hitMissChart.update();
    }

    if (responseTimeChart) {
      responseTimeChart.data.datasets[0].data = [data.avg_response_ms];
      responseTimeChart.update();
    }
  }

  async function handleClearCache() {
    await fetch(`${API_BASE_URL}/api/cache/clear`, { method: 'DELETE' });
    fetchData();
  }

  async function handleOptimize() {
    await fetch(`${API_BASE_URL}/api/cache/optimize`, { method: 'POST' });
    fetchData();
  }

  async function handlePreload() {
    await fetch(`${API_BASE_URL}/api/cache/preload`, { method: 'POST' });
    fetchData();
  }

  function createNewsCard(article) {
    const timeAgo = new Date(article.publishedAt).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });

    return `
      <div class="news-card">
        <div class="news-card__image-container">
          <img
            src="${article.urlToImage || '/placeholder-news.jpg'}"
            alt="${article.title}"
            class="news-card__image"
            loading="lazy"
            onerror="this.src='/placeholder-news.jpg'"
          />
          <div class="news-card__source">${article.source.name}</div>
        </div>
        <div class="news-card__content">
          <h3 class="news-card__title">${article.title}</h3>
          <p class="news-card__description">${article.description || ''}</p>
          <div class="news-card__footer">
            <span class="news-card__date">${timeAgo}</span>
            <a href="${article.url}" target="_blank" class="news-card__link">Read More</a>
          </div>
        </div>
      </div>
    `;
  }

  onMount(() => {
    // Initialize charts
    const hitMissCtx = document.getElementById('hitMissChart');
    hitMissChart = new Chart(hitMissCtx, {
      type: 'doughnut',
      data: {
        labels: ['Hits', 'Misses'],
        datasets: [{
          data: [0, 0],
          backgroundColor: ['#10B981', '#EF4444']
        }]
      }
    });

    const responseTimeCtx = document.getElementById('responseTimeChart');
    responseTimeChart = new Chart(responseTimeCtx, {
      type: 'bar',
      data: {
        labels: ['Response Time (ms)'],
        datasets: [{
          data: [0],
          backgroundColor: '#3B82F6'
        }]
      }
    });

    // Start polling
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  });
</script>

<div class="container mx-auto px-4 py-8">
  <h1 class="text-3xl font-bold mb-8">Cache Monitor</h1>

  <!-- Stats Grid -->
  <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
    <div class="bg-white p-6 rounded-lg shadow">
      <h3 class="text-lg font-semibold mb-4">Cache Stats</h3>
      {#if stats?.data}
        <div class="space-y-2">
          <p>Hit Ratio: {stats.data.hit_ratio_percent.toFixed(1)}%</p>
          <p>Total Requests: {stats.data.total_requests}</p>
          <p>Avg Response: {stats.data.avg_response_ms.toFixed(1)}ms</p>
        </div>
      {/if}
    </div>

    <div class="bg-white p-6 rounded-lg shadow">
      <h3 class="text-lg font-semibold mb-4">Health Status</h3>
      {#if healthStatus?.data}
        <div class="flex items-center">
          <span class={healthStatus.data.status === 'healthy' ? 'text-green-500' : 'text-red-500'}>
            ● {healthStatus.data.status}
          </span>
        </div>
      {/if}
    </div>

    <div class="bg-white p-6 rounded-lg shadow">
      <h3 class="text-lg font-semibold mb-4">Actions</h3>
      <div class="space-x-2">
        <button
          on:click={handleClearCache}
          class="bg-red-500 text-white px-4 py-2 rounded">
          Clear Cache
        </button>
        <button
          on:click={handleOptimize}
          class="bg-green-500 text-white px-4 py-2 rounded">
          Optimize
        </button>
        <button
          on:click={handlePreload}
          class="bg-blue-500 text-white px-4 py-2 rounded">
          Preload
        </button>
      </div>
    </div>
  </div>

  <!-- Charts -->
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <div class="bg-white p-6 rounded-lg shadow">
      <h3 class="text-lg font-semibold mb-4">Hit/Miss Ratio</h3>
      <canvas id="hitMissChart"></canvas>
    </div>
    <div class="bg-white p-6 rounded-lg shadow">
      <h3 class="text-lg font-semibold mb-4">Response Time</h3>
      <canvas id="responseTimeChart"></canvas>
    </div>
  </div>
</div>

<style>
  :global(body) {
    background-color: #f3f4f6;
  }
</style>