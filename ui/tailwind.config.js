/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bizon: {
          bg: '#020817',
          surface: '#0B1220',
          primary: '#006CFF',
          success: '#4CCB7F',
          danger: '#EF4444',
          warning: '#FFB34D',
          border: '#1E293B',
          muted: '#64748B',
          text: '#F8FAFC',
          textSecondary: '#94A3B8',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      borderRadius: {
        pill: '9999px',
      },
    },
  },
  plugins: [],
}
