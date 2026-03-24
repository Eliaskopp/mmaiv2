import { extendTheme, type ThemeConfig } from '@chakra-ui/react'

const config: ThemeConfig = {
  initialColorMode: 'dark',
  useSystemColorMode: false,
}

const theme = extendTheme({
  config,

  semanticTokens: {
    colors: {
      'bg.canvas': { default: '#F5F0E8', _dark: '#0A1628' },
      'bg.subtle': { default: '#FAF7F2', _dark: '#0F1E35' },
      'bg.muted': { default: '#EDE7DB', _dark: '#152842' },
      'bg.panel': { default: '#D5CFC3', _dark: '#1C3250' },

      'text.primary': { default: '#1E3A5F', _dark: '#F5F0E8' },
      'text.secondary': { default: '#2A3B52', _dark: '#C4B9A8' },
      'text.muted': { default: '#6B7B8D', _dark: '#8B8178' },

      'brand.primary': { default: '#E8512D', _dark: '#E8512D' },
      'brand.subtle': { default: '#FFF1EE', _dark: 'rgba(232,81,45,0.12)' },
      'accent.blue': { default: '#3B82F6', _dark: '#60A5FA' },

      'chat.user.bg': { default: '#E8512D', _dark: '#E8512D' },
      'chat.user.text': { default: '#0A1628', _dark: '#0A1628' },
      'chat.ai.bg': { default: '#fefae4', _dark: '#fefae4' },
      'chat.ai.text': { default: '#0A1628', _dark: '#0A1628' },
    },
  },

  colors: {
    brand: {
      50: '#FFF1EE',
      100: '#FFDDD6',
      200: '#FFB8AA',
      300: '#FF927E',
      400: '#F06E52',
      500: '#E8512D',
      600: '#CC4324',
      700: '#B0351B',
      800: '#932813',
      900: '#761C0C',
    },
    navy: {
      50: '#E8EDF4',
      100: '#C4CDD9',
      200: '#8B99AD',
      300: '#5A6B83',
      400: '#2D4160',
      500: '#0A1628',
      600: '#081220',
      700: '#060E18',
      800: '#040A10',
      900: '#020608',
    },
    paper: {
      50: '#FAF7F2',
      100: '#F5F0E8',
      200: '#EDE7DB',
      300: '#F0EBE1',
      400: '#D5CFC3',
      500: '#BDB7AB',
      600: '#8B8178',
      700: '#5A5A5A',
      800: '#2D2D2D',
      900: '#1A1A1A',
    },
  },

  fonts: {
    heading: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    body: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    mono: "'JetBrains Mono', 'Fira Code', monospace",
  },

  styles: {
    global: {
      body: {
        bg: 'bg.canvas',
        color: 'text.primary',
        fontFeatureSettings: "'cv02', 'cv03', 'cv04', 'cv11'",
      },
    },
  },

  components: {
    Button: {
      defaultProps: {
        colorScheme: 'brand',
      },
    },
    Container: {
      baseStyle: {
        maxW: 'container.sm',
      },
    },
  },
})

export default theme
