/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'trader-bg': '#0f172a',
        'trader-card': '#1e293b',
        'trader-border': '#334155',
        'trader-green': '#22c55e',
        'trader-red': '#ef4444',
        'trader-yellow': '#eab308',
        'trader-blue': '#3b82f6',
        'trader-text': '#f1f5f9',
        'trader-muted': '#94a3b8',
      },
    },
  },
  plugins: [],
}
