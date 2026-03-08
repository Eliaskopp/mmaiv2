# MMAi Coach — Frontend

React 19 + TypeScript + Vite + Chakra UI v2.

Served at **chat.mmai.coach** (production) / `localhost:5173` (dev).

## Commands

```bash
npm install       # Install dependencies
npm run dev       # Dev server on :5173 (proxies /api → localhost:8000)
npm run build     # Production build → dist/
npm run lint      # ESLint check
npm run preview   # Preview production build locally
```

## Key files

| Path | Purpose |
|------|---------|
| `src/services/api-client.ts` | Axios client with JWT refresh interceptor |
| `src/types/auth.ts` | TypeScript interfaces for auth |
| `src/hooks/` | React Query hooks |
| `src/services/` | API service functions |
| `src/components/` | UI components |
| `vite.config.ts` | Dev proxy: `/api` → `localhost:8000` |
