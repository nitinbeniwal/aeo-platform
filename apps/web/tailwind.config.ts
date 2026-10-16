import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0b0f19",
        panel: "#141a2b",
        accent: "#6366f1",
      },
    },
  },
  plugins: [],
};

export default config;
