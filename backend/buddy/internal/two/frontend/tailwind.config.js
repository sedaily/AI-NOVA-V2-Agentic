/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Claude color palette (CSS 변수 사용)
        "always-white": "hsl(var(--always-white))",
        "always-black": "hsl(var(--always-black))",

        bg: {
          "000": "hsl(var(--bg-000))",
          100: "hsl(var(--bg-100))",
          200: "hsl(var(--bg-200))",
          300: "hsl(var(--bg-300))",
          400: "hsl(var(--bg-400))",
          500: "hsl(var(--bg-500))",
        },
        text: {
          "000": "hsl(var(--text-000))",
          100: "hsl(var(--text-100))",
          200: "hsl(var(--text-200))",
          300: "hsl(var(--text-300))",
          400: "hsl(var(--text-400))",
          500: "hsl(var(--text-500))",
        },
        border: {
          100: "hsl(var(--border-100))",
          200: "hsl(var(--border-200))",
          300: "hsl(var(--border-300))",
          400: "hsl(var(--border-400))",
          "300-15": "hsl(var(--border-300)/0.15)",
          "300-35": "hsla(var(--border-300)/35%)",
        },
        accent: {
          brand: "hsl(var(--accent-brand))",
          main: {
            "000": "hsl(var(--accent-main-000))",
            100: "hsl(var(--accent-main-100))",
            200: "hsl(var(--accent-main-200))",
            900: "hsl(var(--accent-main-900))",
          },
          pro: {
            "000": "hsl(var(--accent-pro-000))",
            100: "hsl(var(--accent-pro-100))",
            200: "hsl(var(--accent-pro-200))",
            900: "hsl(var(--accent-pro-900))",
          },
          secondary: {
            "000": "hsl(var(--accent-secondary-000))",
            100: "hsl(var(--accent-secondary-100))",
            200: "hsl(var(--accent-secondary-200))",
            900: "hsl(var(--accent-secondary-900))",
          },
        },
        danger: {
          "000": "hsl(var(--danger-000))",
          100: "hsl(var(--danger-100))",
          200: "hsl(var(--danger-200))",
          900: "hsl(var(--danger-900))",
        },
        oncolor: {
          100: "hsl(var(--oncolor-100))",
          200: "hsl(var(--oncolor-200))",
          300: "hsl(var(--oncolor-300))",
        },
      },
      fontFamily: {
        ui: ["Inter", "system-ui", "sans-serif"],
        "ui-serif": ["Georgia", "Times New Roman", "Times", "serif"],
        heading: ["Inter", "system-ui", "sans-serif"],
        "claude-response": ["Georgia", "Times New Roman", "Times", "serif"],
        base: ["Inter", "system-ui", "sans-serif"],
        small: ["Inter", "system-ui", "sans-serif"],
        serif: ["Georgia", "Times New Roman", "Times", "serif"],
        "sans-serif": ["Inter", "system-ui", "sans-serif"],
        system: [
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
      fontSize: {
        xs: ["0.75rem", { lineHeight: "1rem" }],
        sm: ["0.875rem", { lineHeight: "1.25rem" }],
        base: ["1rem", { lineHeight: "1.5rem" }],
        large: ["1.125rem", { lineHeight: "1.75rem" }],
        small: ["0.875rem", { lineHeight: "1.25rem" }],
      },
      fontWeight: {
        "base-bold": "600",
      },
      spacing: {
        0.5: "0.125rem",
        1.5: "0.375rem",
        2.5: "0.625rem",
        3.5: "0.875rem",
      },
      borderRadius: {
        lg: "0.5rem",
        xl: "0.75rem",
        "2xl": "1rem",
      },
      borderWidth: {
        0.5: "0.5px",
      },
      animation: {
        "fade-in": "fadeIn 0.2s ease-in-out",
        "slide-in": "slideIn 0.3s cubic-bezier(0.165, 0.85, 0.45, 1)",
        "scale-in": "scaleIn 0.2s ease-in-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideIn: {
          "0%": {
            opacity: "0",
            transform: "translateX(-0.5rem)",
          },
          "100%": {
            opacity: "1",
            transform: "translateX(0)",
          },
        },
        scaleIn: {
          "0%": {
            opacity: "0",
            transform: "scale(0.95)",
          },
          "100%": {
            opacity: "1",
            transform: "scale(1)",
          },
        },
      },
      transitionTimingFunction: {
        claude: "cubic-bezier(0.165, 0.85, 0.45, 1)",
      },
    },
  },
  plugins: [],
};
