/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./templates/**/*.html", "./apps/**/*.py", "./static/js/**/*.js"],
  theme: {
    extend: {
      colors: {
        surface: "rgb(var(--surface) / <alpha-value>)",
        accent: {
          DEFAULT: "rgb(var(--accent) / <alpha-value>)",
          soft: "rgb(var(--accent-soft) / <alpha-value>)",
        },
      },
      fontFamily: {
        heading: ["Space Grotesk", "sans-serif"],
        body: ["Space Grotesk", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
      boxShadow: {
        soft: "0 12px 30px -12px rgba(15, 23, 42, 0.2)",
      },
      transitionDuration: {
        theme: "320ms",
      },
    },
  },
  plugins: [require("@tailwindcss/forms")],
};
