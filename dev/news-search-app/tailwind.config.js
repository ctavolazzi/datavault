/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  darkMode: 'class', // Enable dark mode
  theme: {
    extend: {
      colors: {
        primary: '#00ff00',
        dark: {
          DEFAULT: '#1a1a1a',
          lighter: '#2a2a2a'
        }
      }
    },
  },
  plugins: [],
}