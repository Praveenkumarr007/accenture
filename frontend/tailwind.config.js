/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          900: '#f5f5f7',
          800: '#ffffff',
          700: '#fafafc',
          600: '#efeff3',
        },
        slate: {
          200: '#1d1d1f',
          300: '#3a3a3c',
          400: '#6e6e73',
          500: '#86868b',
          600: '#aeaeb2',
          700: '#d2d2d7',
          800: '#e8e8ed',
          900: '#f5f5f7',
        },
        accent: {
          DEFAULT: '#0071e3',
          light: '#0071e3',
          dark: '#0066cc',
        },
        success: '#34c759',
        danger: '#ff3b30',
        warning: '#ff9500',
      },
      fontFamily: {
        sans: ["-apple-system", "BlinkMacSystemFont", "SF Pro Text", "SF Pro Display", "Helvetica Neue", "Helvetica", "Arial", "sans-serif"],
      },
      borderRadius: {
        xl: '14px',
        '2xl': '18px',
      },
      boxShadow: {
        apple: '0 1px 3px rgba(0, 0, 0, 0.08), 0 4px 16px rgba(0, 0, 0, 0.06)',
      },
    },
  },
  plugins: [],
}