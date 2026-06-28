import type { Config } from "tailwindcss"
import defaultTheme from "tailwindcss/defaultTheme"
// eslint-disable-next-line @typescript-eslint/no-require-imports
const animatePlugin = require("tailwindcss-animate")

export default {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        base: "#0a0a0f",
        surface: "#111118",
        card: "#13131a",
        border: "#1e1e2e",
        accent: "#6366f1",
        muted: "#64748b",
        primary: "#e2e8f0",
      },
      fontFamily: {
        sans: ["var(--font-sans)", ...defaultTheme.fontFamily.sans],
      },
    },
  },
  plugins: [animatePlugin],
} satisfies Config
