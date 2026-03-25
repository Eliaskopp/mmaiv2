# ADR-003: i18n Progressive Delivery

## Status

Accepted

## Context

MMAi V2 targets global users across Melbourne, European, and Asian markets. We needed multilingual support without blocking the core AI chat feature deployment. The solution had to be lightweight, frontend-only, and decoupled from backend schema changes.

## Decision

We chose a client-side `react-i18next` implementation backed by standard JSON locale files. This avoids heavy SSR translation infrastructure and database enum constraints.

The rollout followed a progressive delivery strategy:

1. **Infrastructure first (PR #8):** Wired up `i18next` with `LanguageDetector`, added English (`en`) and Dutch (`nl`) locales, and built language selectors into `LoginPage` and `ProfilePage`. Verified end-to-end before merging.
2. **Content expansion (branch `feature/i18n-es-de-th`):** Added Spanish (`es`), German (`de`), and Thai (`th`) in a completely isolated follow-up branch. No logic changes — only new JSON files, imports, and `<option>` elements.

The backend `language_code` column is a loose `String(10)` field with no enum validation, so new languages require zero backend changes or migrations.

## Consequences

### Positive

- **Zero backend risk.** The `String(10)` column accepts any language code. No migrations, no enum updates, no deployment coordination.
- **Zero new network calls.** App-wide language sync piggybacks on the existing `ProtectedRoute` profile fetch, which already reads `language_code` and calls `i18n.changeLanguage()`. Adding languages added no requests to the critical path.
- **Isolated rollout.** Infrastructure and content were shipped in separate branches. A broken translation file cannot regress authentication, chat, or profile logic.
- **Simple contribution model.** Adding a new language is a single JSON file + three lines of wiring (import, resource entry, `<option>`). No specialist tooling required.

### Negative / Trade-offs

- **Bundle size.** All locale JSON files are statically imported and bundled into the client JS. This is negligible for 5 languages (~2 KB each) but will need `i18next-http-backend` or dynamic `import()` if we scale beyond ~20 languages.
- **No server-side rendering.** Initial HTML is always in the fallback language (`en`) until React hydrates and `LanguageDetector` resolves the user's preference. Acceptable for an SPA, but would need SSR integration if we add SEO-sensitive public pages.
- **Translation quality.** Current translations were AI-generated and should be reviewed by native speakers before targeting production marketing in those locales.
