/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-noto)', 'Noto Sans SC', '"PingFang SC"', '"Microsoft YaHei"', 'sans-serif'],
        display: ['var(--font-noto)', 'Noto Serif SC', 'STSong', 'serif'],
        mono: ['"Noto Sans Mono"', '"Source Han Mono"', 'monospace'],
      },
      colors: {
        ink: {
          50: '#f7f6f3',
          100: '#eeeae2',
          200: '#ddd6c8',
          300: '#c8bda8',
          400: '#b0a08a',
          500: '#9c8a72',
          600: '#8a7660',
          700: '#726050',
          800: '#5e4f44',
          900: '#4e4139',
          950: '#2a2219',
        },
        vermillion: {
          50: '#fff3f0',
          100: '#ffe4de',
          200: '#ffccc2',
          300: '#ffa898',
          400: '#ff7a63',
          500: '#f7523a',
          600: '#e4341d',
          700: '#c02715',
          800: '#9e2314',
          900: '#832417',
          950: '#470e06',
        },
        indigo: {
          50: '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
          950: '#1e1b4b',
        },
        paper: {
          DEFAULT: '#f5f0e8',
          dark: '#1a1714',
        },
      },
      backgroundImage: {
        'noise': "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.05'/%3E%3C/svg%3E\")",
        'paper-texture': 'radial-gradient(ellipse at 20% 50%, rgba(99, 102, 241, 0.05) 0%, transparent 60%), radial-gradient(ellipse at 80% 20%, rgba(247, 82, 58, 0.03) 0%, transparent 50%)',
      },
      animation: {
        'fade-up': 'fadeUp 0.5s ease forwards',
        'fade-in': 'fadeIn 0.4s ease forwards',
        'shimmer': 'shimmer 1.5s infinite',
        'float': 'float 6s ease-in-out infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-8px)' },
        },
      },
      boxShadow: {
        'card': '0 2px 8px rgba(42, 34, 25, 0.08), 0 0 0 1px rgba(42, 34, 25, 0.05)',
        'card-hover': '0 8px 24px rgba(42, 34, 25, 0.12), 0 0 0 1px rgba(99, 102, 241, 0.2)',
        'glow': '0 0 20px rgba(99, 102, 241, 0.3)',
        'glow-sm': '0 0 10px rgba(99, 102, 241, 0.2)',
      },
    },
  },
  plugins: [],
};
