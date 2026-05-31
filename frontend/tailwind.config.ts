import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        base: "#f4f2ea",
        ink: "#1f1b16",
        card: "#fffdf7",
        accent: "#c95f2d",
        accentDark: "#9d431b",
        muted: "#6a655e"
      },
      fontFamily: {
        display: ["'DM Serif Display'", "serif"],
        body: ["'Space Grotesk'", "sans-serif"]
      },
      boxShadow: {
        panel: "0 16px 40px rgba(31, 27, 22, 0.08)"
      }
    }
  },
  plugins: []
};

export default config;
