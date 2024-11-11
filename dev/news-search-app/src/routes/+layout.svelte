<script>
  import '../styles/main.css';
  import Navbar from '$lib/components/Navbar.svelte';
</script>

<div class="min-h-screen flex flex-col">
  <header class="bg-white dark:bg-gray-800 shadow-sm">
    <Navbar />
  </header>

  <slot />

  <footer class="mt-auto bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
    <div class="container mx-auto px-4 py-3 text-center text-gray-600 dark:text-gray-400">
      <p>© {new Date().getFullYear()} News Search App. All rights reserved.</p>
    </div>
  </footer>
</div>