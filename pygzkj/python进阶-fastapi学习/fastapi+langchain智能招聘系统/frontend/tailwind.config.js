/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        sidebar: {
          DEFAULT: '#1f2d3d',
          hover: '#263445',
          active: '#409eff',
          muted: '#aeb9c7',
        },
        workspace: '#f4f6f9',
      },
      boxShadow: {
        panel: '0 1px 2px rgba(15, 23, 42, 0.06)',
      },
    },
  },
  plugins: [],
}
