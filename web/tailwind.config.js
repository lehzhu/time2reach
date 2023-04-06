/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index1.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    inset: {
      '0': 0,
      '1/2': '50%',
    },
    extend: {},
  },
  plugins: [],
}