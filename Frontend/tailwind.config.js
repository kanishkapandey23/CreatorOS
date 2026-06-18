/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "hsl(var(--background))",
        ink: "hsl(var(--foreground))",
        "ink-muted": "hsl(var(--muted-foreground))",
        "ink-subtle": "hsl(240 4% 65%)",
        line: "hsl(var(--border))",
        brand: "hsl(var(--ring))",
        "brand-soft": "hsl(var(--ring) / 0.1)",
        secondary: "hsl(var(--secondary))",
        violet: "hsl(262 83% 58%)",
        "violet-soft": "hsl(262 83% 58% / 0.1)",
        success: "hsl(142 72% 29%)",
        "success-soft": "hsl(142 72% 29% / 0.1)",
        danger: "hsl(var(--destructive))",
        "danger-soft": "hsl(var(--destructive) / 0.1)",
        card: "hsl(var(--card))",
        "card-foreground": "hsl(var(--card-foreground))",
      },
      fontFamily: {
        display: ["var(--font-sora)", "system-ui", "sans-serif"],
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05)",
        soft: "0 4px 6px -1px rgba(0, 0, 0, 0.03), 0 2px 4px -2px rgba(0, 0, 0, 0.03)",
        pop: "0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -4px rgba(0, 0, 0, 0.05)",
      }
    },
  },
  plugins: [],
}
