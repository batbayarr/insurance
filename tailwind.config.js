/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./core/templates/**/*.html",
    "./core/static/js/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        'accounting-blue': '#1e40af',
        'accounting-green': '#059669',
        'accounting-red': '#dc2626',
      },
    },
  },
  plugins: [],
}