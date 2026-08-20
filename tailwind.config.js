/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0f172a', // slate-900
        surface: '#1e293b', // slate-800
        primary: '#3b82f6', // blue-500
        secondary: '#8b5cf6', // violet-500
        accent: '#10b981', // emerald-500
        danger: '#ef4444', // red-500
        textMain: '#f8fafc', // slate-50
        textMuted: '#94a3b8', // slate-400
        borderLight: '#334155', // slate-700
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}
