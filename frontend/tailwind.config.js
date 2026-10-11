/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          bg: "#080c14",
          surface: "#111827",
          card: "#161f30",
          border: "rgba(255, 255, 255, 0.08)",
          accent: "#00d2ff",
          bullish: "#10b981",
          bearish: "#ef4444",
          gold: "#f59e0b",
        }
      }
    },
  },
  plugins: [],
}
