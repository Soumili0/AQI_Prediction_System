/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary:   { DEFAULT: '#1e3a5f', 50: '#eff6ff', 100: '#dbeafe', 500: '#1e3a5f', 600: '#162d4a', 700: '#0f2035' },
        secondary: { DEFAULT: '#2d6a4f', 50: '#f0fdf4', 500: '#2d6a4f', 600: '#235c43' },
        aqi: {
          good:      '#00e400',
          moderate:  '#ffff00',
          sensitive: '#ff7e00',
          unhealthy: '#ff0000',
          very:      '#8f3f97',
          hazardous: '#7e0023',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        card:  '0 4px 6px -1px rgba(0,0,0,.07), 0 2px 4px -1px rgba(0,0,0,.05)',
        hover: '0 10px 15px -3px rgba(0,0,0,.1), 0 4px 6px -2px rgba(0,0,0,.05)',
      },
      animation: {
        'fade-in':    'fadeIn .3s ease-in-out',
        'slide-up':   'slideUp .4s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(.4,0,.6,1) infinite',
      },
      keyframes: {
        fadeIn:  { '0%': { opacity: 0 },              '100%': { opacity: 1 } },
        slideUp: { '0%': { opacity: 0, transform: 'translateY(16px)' }, '100%': { opacity: 1, transform: 'translateY(0)' } },
      },
    },
  },
  plugins: [],
};
