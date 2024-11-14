<script>
  let isMenuOpen = false;

  function toggleMenu() {
    isMenuOpen = !isMenuOpen;
  }
</script>

<nav class="bg-gray-900 border-b border-green-500">
  <div class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
    <a href="/" class="text-xl font-bold no-underline flex items-center gap-1">
      <span class="text-green-500">News</span>
      <span class="text-gray-300">Vault</span>
    </a>

    <!-- Desktop Navigation -->
    <ul class="hidden md:flex items-center space-x-6">
      <li><a href="/" class="nav-link">Home</a></li>
      <li><a href="/monitor" class="nav-link">Monitor</a></li>
      <li><a href="/search" class="nav-link">Search</a></li>
    </ul>

    <!-- Mobile Menu Button -->
    <button
      class="md:hidden text-green-500 hover:text-green-400 transition-colors"
      on:click={toggleMenu}
      aria-label="Toggle menu"
    >
      <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        {#if isMenuOpen}
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        {:else}
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        {/if}
      </svg>
    </button>
  </div>

  <!-- Mobile Menu -->
  {#if isMenuOpen}
    <div class="md:hidden bg-gray-800">
      <a href="/" class="mobile-nav-link">Home</a>
      <a href="/monitor" class="mobile-nav-link">Monitor</a>
      <a href="/search" class="mobile-nav-link">Search</a>
    </div>
  {/if}
</nav>

<style lang="postcss">
  .nav-link {
    @apply text-gray-300 hover:text-green-500 transition-colors duration-200;
  }

  .mobile-nav-link {
    @apply block text-gray-300 hover:text-green-500 hover:bg-gray-700 px-4 py-2 transition-colors duration-200;
  }
</style>
