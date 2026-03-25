# Frontend — Claude Code Instructions

## React Code Style

- Functional components with hooks — no class components
- **Chakra UI v2** (NOT v3) — v3 has a different API
- TypeScript strict mode (enabled in `tsconfig.app.json`)
- Semantic tokens defined in `src/theme.ts` for all theming
- `fontVariantNumeric` is not a direct Chakra style prop — use `sx={{ fontVariantNumeric: 'tabular-nums' }}`

## Data Layer

- React Query for all data fetching, custom hooks in `src/hooks/`
- Axios client at `src/services/api-client.ts` with JWT refresh interceptor (queue pattern)
- Token storage: `access_token` / `refresh_token` in localStorage

## Vite Config

- Dev server: port `5173`, proxy `/api` → `localhost:8001`
- Vendor chunk splitting configured (React, Chakra, data, charts, markdown)

## Commands

```bash
npm run dev          # Start dev server on :5173
npm run build        # tsc -b && vite build → frontend/dist/
npm run lint         # ESLint check
npm run preview      # Preview production build
npm run format       # Prettier check
npm run format:fix   # Prettier auto-fix
```
