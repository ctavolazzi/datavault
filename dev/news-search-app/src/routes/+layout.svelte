<script>
  import '../styles/main.css';
  import Navbar from '$lib/components/Navbar.svelte';
</script>

<div class="min-h-screen bg-gray-100 dark:bg-dark text-gray-900 dark:text-gray-100">
  <header class="bg-white dark:bg-dark-lighter border-b border-gray-200 dark:border-gray-700">
    <Navbar />
  </header>

  <main class="container mx-auto px-4 py-8">
    <slot />
  </main>

  <footer class="mt-auto py-6 bg-white dark:bg-dark-lighter border-t border-gray-200 dark:border-gray-700">
    <div class="container mx-auto px-4 text-center text-gray-600 dark:text-gray-400">
      <p>© {new Date().getFullYear()} News Search App. All rights reserved.</p>
    </div>
  </footer>
</div>