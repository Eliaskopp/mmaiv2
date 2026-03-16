# Frontend Context — MMAi V2

Handoff document for building the frontend UI. All 33 backend endpoints are live, tested, and ready. This file gives a Senior Frontend Architect everything needed to build the UI without guessing at API contracts, error shapes, or auth flows.

---

## 1. API Contract

All endpoints are prefixed with `/api/v1/`. The Vite dev proxy forwards `/api` to `localhost:8000`.

### Auth (8 endpoints)

| Method | Path | Request Body | Response | Auth | Rate Limit |
|--------|------|-------------|----------|------|------------|
| POST | `/auth/register` | `RegisterRequest` | `AuthResponse` (201) | No | 5/min |
| POST | `/auth/login` | `LoginRequest` | `AuthResponse` | No | 10/min |
| POST | `/auth/refresh` | `{ refresh_token: string }` | `RefreshResponse` | No | 30/min |
| GET | `/auth/me` | — | `User` | Yes | — |
| POST | `/auth/verify-email` | `{ token: string }` | `MessageResponse` | No | — |
| POST | `/auth/logout` | — | `MessageResponse` | No | — |
| POST | `/auth/forgot-password` | `{ email: string }` | `MessageResponse` | No | 3/min |
| POST | `/auth/reset-password` | `{ token: string, password: string }` | `MessageResponse` | No | — |

### Health (1 endpoint)

| Method | Path | Response | Auth |
|--------|------|----------|------|
| GET | `/health` | `HealthResponse` | No |

### Profile (3 endpoints)

| Method | Path | Request Body | Response | Auth |
|--------|------|-------------|----------|------|
| POST | `/profile` | `ProfileCreate` | `ProfileResponse` (201) | Yes |
| GET | `/profile` | — | `ProfileResponse` | Yes |
| PATCH | `/profile` | `ProfileUpdate` | `ProfileResponse` | Yes |

### Journal Sessions (5 endpoints)

| Method | Path | Request Body | Response | Auth | Query Params |
|--------|------|-------------|----------|------|-------------|
| POST | `/journal/sessions` | `SessionCreate` | `SessionResponse` (201) | Yes | — |
| GET | `/journal/sessions` | — | `SessionListResponse` | Yes | `offset`, `limit`, `date_from`, `date_to`, `session_type` |
| GET | `/journal/sessions/{session_id}` | — | `SessionResponse` | Yes | — |
| PATCH | `/journal/sessions/{session_id}` | `SessionUpdate` | `SessionResponse` | Yes | — |
| DELETE | `/journal/sessions/{session_id}` | — | `MessageResponse` | Yes | — |

### Recovery Logs (3 endpoints)

| Method | Path | Request Body | Response | Auth | Query Params |
|--------|------|-------------|----------|------|-------------|
| POST | `/recovery/logs` | `RecoveryLogCreate` | `RecoveryLogResponse` | Yes | — |
| GET | `/recovery/logs` | — | `RecoveryLogListResponse` | Yes | `offset`, `limit`, `date_from`, `date_to` |
| GET | `/recovery/logs/{log_date}` | — | `RecoveryLogResponse` | Yes | — |

Note: `POST /recovery/logs` is an **upsert** — if a log already exists for the date in `logged_for`, it updates the existing record.

### Conversations (6 endpoints)

| Method | Path | Request Body | Response | Auth | Rate Limit | Query Params |
|--------|------|-------------|----------|------|------------|-------------|
| POST | `/conversations` | `ConversationCreate` | `ConversationResponse` (201) | Yes | — | — |
| GET | `/conversations` | — | `ConversationListResponse` | Yes | — | `offset`, `limit` |
| GET | `/conversations/{id}` | — | `ConversationDetailResponse` | Yes | — | — |
| DELETE | `/conversations/{id}` | — | `MessageResponse` | Yes | — | — |
| POST | `/conversations/{id}/messages` | `MessageCreate` | `MessageResponse[]` (201) | Yes | 20/min | — |
| GET | `/conversations/{id}/messages` | — | `MessageListResponse` | Yes | — | `offset`, `limit` |

Note: `POST .../messages` returns an **array of two messages** — the user message and the AI assistant response. A background task also runs AI note extraction on the assistant's response.

### Notes (5 endpoints)

| Method | Path | Request Body | Response | Auth | Query Params |
|--------|------|-------------|----------|------|-------------|
| POST | `/notes` | `NoteCreate` | `NoteResponse` (201) | Yes | — |
| GET | `/notes` | — | `NoteListResponse` | Yes | `offset`, `limit`, `type`, `status`, `pinned` |
| GET | `/notes/{note_id}` | — | `NoteResponse` | Yes | — |
| PATCH | `/notes/{note_id}` | `NoteUpdate` | `NoteResponse` | Yes | — |
| DELETE | `/notes/{note_id}` | — | `MessageResponse` | Yes | — |

### Stats (2 endpoints)

| Method | Path | Response | Auth | Query Params |
|--------|------|----------|------|-------------|
| GET | `/stats/acwr` | `ACWRResponse` | Yes | — |
| GET | `/stats/volume` | `DailyVolumePoint[]` | Yes | `days` (default 30, max 365) |

---

## 2. TypeScript Interfaces

All types are defined in `frontend/src/types/` and re-exported from `frontend/src/types/index.ts`.

### Auth (`types/auth.ts`)

```typescript
interface User {
  id: string
  email: string
  display_name: string
  is_verified: boolean
  created_at: string
}

interface AuthResponse {
  user: User
  access_token: string
  refresh_token: string
  token_type: string
}

interface RefreshResponse {
  access_token: string
  token_type: string
}

interface LoginRequest {
  email: string
  password: string
}

interface RegisterRequest {
  email: string
  password: string
  display_name: string
}
```

### Conversations (`types/conversation.ts`)

```typescript
interface ConversationCreate {
  title?: string | null
}

interface MessageCreate {
  content: string  // min 1, max 4000 chars
}

interface MessageResponse {
  id: string
  conversation_id: string
  role: string  // "user" | "assistant"
  content: string
  metadata_: Record<string, unknown> | null
  created_at: string
}

interface ConversationResponse {
  id: string
  user_id: string
  title: string
  message_count: number
  created_at: string
  updated_at: string | null
}

interface ConversationDetailResponse extends ConversationResponse {
  messages: MessageResponse[]
}

interface ConversationListResponse {
  items: ConversationResponse[]
  total: number
  offset: number
  limit: number
}

interface MessageListResponse {
  items: MessageResponse[]
  total: number
  offset: number
  limit: number
}
```

### Profile (`types/profile.ts`)

```typescript
type SkillLevel = 'beginner' | 'intermediate' | 'advanced' | 'professional'
type WeightUnit = 'kg' | 'lb'
type Role = 'fighter' | 'coach' | 'hobbyist'

interface ProfileCreate {
  skill_level?: SkillLevel | null
  martial_arts?: string[] | null
  goals?: string | null
  weight_class?: string | null
  training_frequency?: string | null
  injuries?: string[] | null
  role?: Role               // default: "fighter"
  primary_domain?: string | null
  game_style?: string | null
  strategic_leaks?: string[] | null
  language_code?: string    // default: "en"
  weight_unit?: WeightUnit  // default: "kg"
}

interface ProfileUpdate {
  // Same fields as ProfileCreate, all optional
  skill_level?: SkillLevel | null
  martial_arts?: string[] | null
  goals?: string | null
  weight_class?: string | null
  training_frequency?: string | null
  injuries?: string[] | null
  role?: Role
  primary_domain?: string | null
  game_style?: string | null
  strategic_leaks?: string[] | null
  language_code?: string
  weight_unit?: WeightUnit
}

interface ProfileResponse {
  id: string
  user_id: string
  skill_level: string | null
  martial_arts: string[] | null
  goals: string | null
  weight_class: string | null
  training_frequency: string | null
  injuries: string[] | null
  role: string
  primary_domain: string | null
  game_style: string | null
  strategic_leaks: string[] | null
  conversation_insights: Record<string, unknown> | null
  profile_completeness: number  // 0-100
  language_code: string
  weight_unit: string
  current_streak: number
  longest_streak: number
  last_active_date: string | null
  grace_days_remaining: number
  created_at: string
  updated_at: string | null
}
```

### Journal (`types/journal.ts`)

```typescript
type SessionType =
  | 'muay_thai' | 'bjj_gi' | 'bjj_nogi' | 'boxing'
  | 'mma' | 'wrestling' | 'conditioning' | 'strength' | 'other'

type SessionSource = 'manual' | 'voice' | 'ai'

interface SessionCreate {
  session_type: SessionType
  session_date?: string | null       // ISO date, defaults to today
  title?: string | null              // max 200
  notes?: string | null              // max 5000
  duration_minutes?: number | null   // 1-599
  rounds?: number | null             // 0-100
  round_duration_minutes?: number | null  // 0.1-99.9
  intensity_rpe?: number | null      // 1-10
  mood_before?: number | null        // 1-5
  mood_after?: number | null         // 1-5
  energy_level?: number | null       // 1-5
  techniques?: string[] | null
  training_partner?: string | null   // max 100
  gym_name?: string | null           // max 100
  source?: SessionSource             // default: "manual"
}

interface SessionUpdate {
  // Same fields as SessionCreate, all optional
}

interface SessionResponse {
  id: string
  user_id: string
  session_type: string
  session_date: string
  title: string | null
  notes: string | null
  duration_minutes: number | null
  rounds: number | null
  round_duration_minutes: number | null
  intensity_rpe: number | null
  mood_before: number | null
  mood_after: number | null
  energy_level: number | null
  techniques: string[] | null
  training_partner: string | null
  gym_name: string | null
  source: string
  exertion_load: number | null  // computed: duration_minutes * intensity_rpe
  created_at: string
  updated_at: string | null
}

interface SessionListResponse {
  items: SessionResponse[]
  total: number
  offset: number
  limit: number
}
```

### Recovery (`types/recovery.ts`)

```typescript
interface RecoveryLogCreate {
  sleep_quality?: number | null   // 1-5
  soreness?: number | null        // 1-5
  energy?: number | null          // 1-5
  notes?: string | null           // max 2000
  logged_for?: string | null      // ISO date, defaults to today
}

interface RecoveryLogResponse {
  id: string
  user_id: string
  sleep_quality: number | null
  soreness: number | null
  energy: number | null
  notes: string | null
  logged_for: string
  created_at: string
}

interface RecoveryLogListResponse {
  items: RecoveryLogResponse[]
  total: number
  offset: number
  limit: number
}
```

### Notes (`types/note.ts`)

```typescript
type NoteType = 'technique' | 'drill' | 'goal' | 'gear' | 'gym' | 'insight'
type NoteStatus = 'active' | 'archived'
type NoteSource = 'ai' | 'manual'

interface NoteCreate {
  type: NoteType
  title: string              // min 1, max 200
  summary?: string | null
  user_notes?: string | null
}

interface NoteUpdate {
  title?: string | null      // min 1, max 200
  summary?: string | null
  user_notes?: string | null
  status?: NoteStatus | null
  pinned?: boolean | null
}

interface NoteResponse {
  id: string
  user_id: string
  type: string
  title: string
  summary: string | null
  user_notes: string | null
  status: string             // "active" | "archived"
  pinned: boolean
  source: string             // "ai" | "manual"
  source_conversation_id: string | null
  created_at: string
  updated_at: string | null
}

interface NoteListResponse {
  items: NoteResponse[]
  total: number
  offset: number
  limit: number
}
```

### Stats (`types/stats.ts`)

```typescript
interface ACWRResponse {
  acute_load: number    // last 7 days
  chronic_load: number  // last 28 days
  acwr_ratio: number | null
  risk_zone: string     // "optimal" | "under-training" | "danger" | "insufficient_data"
}

interface DailyVolumePoint {
  date: string          // ISO date
  total_load: number
  total_duration: number
}
```

### Health (`types/health.ts`)

```typescript
interface ServiceHealth {
  status: string       // "connected" | "disconnected"
  latency_ms: number
}

interface HealthResponse {
  status: string       // "healthy" | "degraded" | "unhealthy"
  version: string
  database: ServiceHealth
  ai: ServiceHealth
}
```

---

## 3. Auth Architecture

### Token Strategy

- **Access token**: JWT, 30 min TTL, `type: "access"` claim
- **Refresh token**: JWT, 7 day TTL, `type: "refresh"` claim
- Algorithm: HS256
- Storage: `localStorage` keys `access_token` and `refresh_token`

### Request Flow

1. `apiClient` (Axios instance at `services/api-client.ts`) attaches `Authorization: Bearer <access_token>` to every request via a request interceptor
2. On 401 response, the response interceptor attempts a silent refresh:
   - Calls `POST /api/v1/auth/refresh` with the stored refresh token
   - On success: stores new access token, replays all queued requests
   - On failure: clears both tokens, redirects to `/login`
3. Concurrent 401s are handled with a queue pattern — only one refresh request fires, others wait

### AuthContext (`contexts/AuthContext.tsx`)

```typescript
interface AuthContextValue {
  user: User | null
  isLoading: boolean       // true during initial token validation
  isAuthenticated: boolean // derived: !!user
  login(email: string, password: string): Promise<void>
  register(email: string, password: string, displayName: string): Promise<void>
  logout(): void
}
```

- On mount, if `access_token` exists in localStorage, calls `GET /auth/me` to restore session
- `ProtectedRoute` component wraps all authenticated routes — shows a spinner during `isLoading`, redirects to `/login` if not authenticated
- Login/Register pages redirect to `/chat` (or back to the page the user came from) if already authenticated

### Auth Service (`services/auth.ts`)

Pre-built functions: `login()`, `register()`, `getMe()`, `logout()` — all use the shared `apiClient`.

---

## 4. Exception Mapping

The backend uses domain exceptions (not raw `HTTPException`) to keep business logic decoupled from HTTP. The exception handlers in `core/exception_handlers.py` map them to HTTP responses.

| Domain Exception | HTTP Status | Response Shape | When It Fires | UI Handling |
|-----------------|-------------|----------------|---------------|-------------|
| `EntityNotFoundError` | 404 | `{ detail: string }` | Resource doesn't exist or user can't access it | Show "not found" toast, redirect to list view |
| `AuthenticationError` | 401 | `{ detail: string }` | Bad credentials, expired/invalid token | Interceptor handles refresh; if refresh fails, redirect to login |
| `ConflictError` | 409 | `{ detail: string }` | Duplicate email on register, duplicate resource | Show inline form error (e.g. "Email already registered") |
| `ValidationError` | 400 | `{ detail: string }` | Business rule violation (not schema) | Show toast with the `detail` message |
| `QuotaExceededError` | 429 | `{ detail: string }` | Daily AI message limit reached (50/day) | Show "limit reached" banner in chat, disable send button |
| Pydantic validation | 422 | `{ detail: [{loc, msg, type}] }` | Schema validation failure | Parse `detail` array, map to form field errors |
| Rate limit (slowapi) | 429 | `{ error: string }` | Too many requests per minute | Show "slow down" toast, disable button briefly |

### Error Response Pattern

All domain errors return `{ detail: string }`. The frontend can extract the error message as:

```typescript
const message = error.response?.data?.detail || 'Something went wrong'
```

For 422 (Pydantic), the `detail` is an array of objects with `loc`, `msg`, and `type` fields.

---

## 5. Domain Entities

### The "Big 4" + Profile

```
User (1)
 ├── Profile (1:1)
 │   ├── skill_level, martial_arts, goals, injuries
 │   ├── role, game_style, strategic_leaks
 │   ├── streak tracking (current_streak, longest_streak, grace_days)
 │   └── profile_completeness (0-100)
 │
 ├── Conversations (1:N)
 │   ├── title, message_count, created_at, updated_at
 │   └── Messages (1:N)
 │       ├── role ("user" | "assistant")
 │       ├── content
 │       └── metadata_ (token counts, model info)
 │
 ├── Journal Sessions (1:N)
 │   ├── session_type, session_date, duration, RPE
 │   ├── rounds, techniques, mood, energy
 │   └── exertion_load (computed: duration * RPE)
 │
 ├── Recovery Logs (1:N, unique per date)
 │   ├── sleep_quality, soreness, energy (1-5 scales)
 │   └── logged_for (date, upsert semantics)
 │
 └── Notes (1:N)
     ├── type (technique|drill|goal|gear|gym|insight)
     ├── source ("ai" auto-extracted | "manual" user-created)
     ├── status (active|archived), pinned
     └── source_conversation_id (links AI notes back to chat)
```

### Cross-Domain Relationships

- **Chat → Notes**: AI note extraction runs as a background task after each assistant message. Notes link back to the source conversation via `source_conversation_id`.
- **Journal → Stats**: ACWR and volume trends are computed from journal session data (exertion_load, duration, session_date).
- **Profile → Chat**: The AI coach uses profile data (skill level, martial arts, goals, injuries) as context injection for personalized responses.
- **Journal + Recovery → Profile**: Session logging updates the streak counter on the profile.

---

## 6. Frontend Stack

| Library | Version | Purpose |
|---------|---------|---------|
| React | 19 | UI framework |
| Chakra UI | v2 | Component library (NOT v3 — different API) |
| React Router | v7 | Client-side routing |
| React Query (TanStack) | v5 | Server state management, caching, mutations |
| Axios | latest | HTTP client with interceptors |
| Vite | latest | Build tool, dev server with proxy |
| Framer Motion | latest | Animations (Chakra UI dependency) |

### Key Configuration

- **Vite proxy**: `frontend/vite.config.js` proxies `/api` → `http://localhost:8000`
- **API client**: `frontend/src/services/api-client.ts` — Axios instance with auth interceptors
- **Query client**: Instantiated in `App.tsx`, default config

### Project Structure

```
frontend/src/
├── App.tsx                    # Route definitions, providers
├── components/
│   ├── AppLayout.tsx          # Header nav + Outlet (done)
│   └── ProtectedRoute.tsx     # Auth guard (done)
├── contexts/
│   └── AuthContext.tsx         # Auth state management (done)
├── pages/
│   ├── LoginPage.tsx           # Functional (done)
│   ├── RegisterPage.tsx        # Functional (done)
│   ├── ChatPage.tsx            # PLACEHOLDER
│   ├── JournalPage.tsx         # PLACEHOLDER
│   ├── NotesPage.tsx           # PLACEHOLDER
│   ├── StatsPage.tsx           # PLACEHOLDER
│   ├── RecoveryPage.tsx        # PLACEHOLDER
│   └── ProfilePage.tsx         # PLACEHOLDER
├── services/
│   ├── api-client.ts           # Axios + interceptors (done)
│   └── auth.ts                 # Auth API calls (done)
└── types/
    ├── index.ts                # Re-exports all types
    ├── auth.ts                 # (done)
    ├── conversation.ts         # (done)
    ├── profile.ts              # (done)
    ├── journal.ts              # (done)
    ├── recovery.ts             # (done)
    ├── note.ts                 # (done)
    ├── stats.ts                # (done)
    └── health.ts               # (done)
```

---

## 7. Unfinished Business

### Placeholder Pages (6 pages need full implementation)

| Page | Route | Priority | API Endpoints Used |
|------|-------|----------|-------------------|
| **ChatPage** | `/chat` | P0 — core feature | Conversations CRUD, Messages, sends to AI |
| **JournalPage** | `/journal` | P1 — daily use | Sessions CRUD, date filtering |
| **RecoveryPage** | `/recovery` | P1 — daily use | Recovery logs upsert, date filtering |
| **NotesPage** | `/notes` | P2 — AI value-add | Notes CRUD, type/status/pinned filtering |
| **StatsPage** | `/stats` | P2 — engagement | ACWR, volume trends (charting library needed) |
| **ProfilePage** | `/profile` | P1 — onboarding | Profile create/get/update, completeness bar |

### Missing Frontend Infrastructure

- **API service modules**: Only `services/auth.ts` exists. Need `services/conversations.ts`, `services/journal.ts`, `services/recovery.ts`, `services/notes.ts`, `services/stats.ts`, `services/profile.ts`.
- **React Query hooks**: No hooks directory yet. Need `useConversations`, `useJournalSessions`, `useRecoveryLogs`, `useNotes`, `useProfile`, `useStats`.
- **Charting library**: Stats page needs a chart library (e.g. recharts, chart.js) for ACWR gauge and volume trend line chart.
- **Voice input**: Web Speech API integration for voice-to-text in chat and journal — not started.
- **Toast/error handling**: Login/Register pages handle errors inline. Need a consistent pattern for all CRUD operations.
- **Loading/empty states**: Skeleton loaders, empty state illustrations for lists with no data.
- **Pagination**: List endpoints all support `offset`/`limit` — need pagination or infinite scroll UI.

### Suggested Build Order

1. **ProfilePage** — needed for onboarding, profile feeds AI context
2. **ChatPage** — core feature, depends on profile existing
3. **JournalPage** — daily logging, feeds streak + stats
4. **RecoveryPage** — daily logging, complements journal
5. **NotesPage** — AI-generated notes appear after chat
6. **StatsPage** — requires journal data to be meaningful
