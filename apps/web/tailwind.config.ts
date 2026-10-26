import type { Config } from "tailwindcss";

/**
 * Design tokens taken from the LightEd Figma file.
 * navy  = primary deep blue used for sidebars / headings
 * brand = bright blue CTA colour
 * gold  = accent used on the splash screen and highlights
 * mist  = soft lavender page background
 */
const config: Config = {
  content: ["./src/app/**/*.{ts,tsx}", "./src/components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          50: "#eef3fb",
          100: "#d8e3f5",
          300: "#8ba6cf",
          500: "#3c649e",
          600: "#2a4f86",
          700: "#1D4076",
          800: "#16325c",
          900: "#0f2444",
        },
        brand: {
          50: "#eef4ff",
          100: "#dbe7ff",
          200: "#bcd2ff",
          300: "#8eb3ff",
          400: "#5b8cff",
          500: "#2F6BFF",
          600: "#1f55e6",
          700: "#1a43b8",
          800: "#193a91",
          900: "#1a3572",
        },
        gold: {
          100: "#fff4d1",
          300: "#ffdf85",
          400: "#FFC83D",
          500: "#f5b414",
        },
        mist: "#F4F6FC",
        ink: "#0F1B33",
        muted: "#6B7A99",
        line: "#E4E9F5",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
        display: ["'Plus Jakarta Sans'", "Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(16,27,51,0.04), 0 12px 32px -12px rgba(16,27,51,0.12)",
        float: "0 24px 60px -24px rgba(16,27,51,0.28)",
        ring: "0 0 0 4px rgba(47,107,255,0.12)",
      },
      borderRadius: {
        "4xl": "2rem",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.5s ease-out both",
        float: "float 6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
