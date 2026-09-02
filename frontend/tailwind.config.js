/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Surface / base scale (light theme — white → light grey)
        base: {
          950: '#F8FAF9',
          900: '#EFF6F1',
          850: '#E8F0EA',
          800: '#DDE8DF',
          700: '#C8DDD0',
          600: '#AECFB8',
        },
        // Ink / text scale
        ink: {
          100: '#0F1A12',
          200: '#1C2E20',
          300: '#2E4A35',
          400: '#4A6B53',
          500: '#6B8F74',
          600: '#8DAF96',
        },
        // Accent
        crimson: {
          500: '#DC2626',
          600: '#B91C1C',
        },
      },
      fontSize: {
        micro: ['10px', { lineHeight: '1.4', letterSpacing: '0.08em' }],
      },
    },
  },
  plugins: [],
}
