# Milestone 8 — Chat Interface Hardening (State Preservation & Retry)

> PRD for hardening the existing chat UI mutation flow. The chat interface is fully built; this milestone addresses error handling, state preservation, and retry UX.

---

## Problem

When `useSendMessage` fails (Grok API timeout, 500, or 429 quota), the `onError` callback rolls back the optimistic message from the React Query cache. The user's typed message vanishes — destroying user data with no recovery path.

## Goal

Replace the destructive rollback with a **State Preservation + Retry** pattern. Failed messages stay visible, are visually marked as errored, and expose a one-tap Retry button.

---

## Architecture

### 1. Frontend-Only Type Extension

The backend `MessageResponse` Pydantic schema is **not modified**. We extend it on the frontend with UI-only state:

```typescript
// frontend/src/types/conversation.ts

type MessageStatus = 'confirmed' | 'pending' | 'error';

type ChatMessage = MessageResponse & {
  status: MessageStatus;
  errorReason?: string;
};
```

- `confirmed` — message exists on the server (default for all API-fetched messages)
- `pending` — optimistic message, waiting for server response
- `error` — mutation failed, message preserved locally with retry affordance

The `status` and `errorReason` fields **never touch the wire**. They exist only in the React Query cache and component props.

### 2. React Query Cache Strategy

The React Query cache for messages stores `ChatMessage[]` everywhere.

#### Hydration (API → Cache)

When `useMessages` fetches from the API, map each `MessageResponse` to `ChatMessage`:

```typescript
// In useMessages select/transform
const hydrate = (msg: MessageResponse): ChatMessage => ({
  ...msg,
  status: 'confirmed',
});
```

#### `onMutate` (Optimistic Insert)

```
IF retryId is present:
  → Find the errored message by retryId in the cache
  → Replace it in-place with status: 'pending' (same position, no flicker)
ELSE:
  → Append a new ChatMessage with:
    - id: `optimistic-${Date.now()}`
    - status: 'pending'
    - role: 'user'
    - content: the user's input
    - created_at: new Date().toISOString()
```

#### `onSuccess` (Server Confirmation)

The backend returns `MessageResponse[]` (2 items: user message + assistant response).

```
→ Find the optimistic/pending message in the cache
→ Replace it with the real user message (status: 'confirmed')
→ Append the assistant message (status: 'confirmed')
→ Invalidate conversations list query (message_count changed)
```

#### `onError` (Failure Preservation)

```
→ Find the optimistic/pending message by its id in the cache
→ Patch it to status: 'error'
→ Set errorReason from the axios error:
    - 429 → "Daily message limit reached"
    - 500 → "Server error — try again"
    - Network/timeout → "Connection lost — check your network"
→ Fire a Chakra toast with the same errorReason text
→ Do NOT remove the message from the cache
```

### 3. Unified Retry via `retryId`

The mutation signature changes from `{ conversationId, content }` to:

```typescript
interface SendMessageVariables {
  conversationId: string;
  content: string;
  retryId?: string;  // id of the errored ChatMessage to replace
}
```

When "Retry" is clicked on a failed `MessageBubble`:
1. Call the same `sendMessage` mutation with `{ conversationId, content: erroredMessage.content, retryId: erroredMessage.id }`
2. `onMutate` detects `retryId`, replaces the errored entry in-place → `status: 'pending'`
3. `onSuccess` / `onError` proceed identically to the normal flow

**Single code path. No flicker. No divergent retry logic.**

---

## UI Changes

### `MessageBubble.tsx` — Conditional Rendering by Status

| Status | Visual Treatment |
|--------|-----------------|
| `confirmed` | Normal rendering (no change from current) |
| `pending` | Normal rendering + typing indicator below (no change from current) |
| `error` | Greyed out text (`opacity: 0.6`), red `AlertCircle` icon, "Retry" button below the bubble |

Error state layout:

```
┌─────────────────────────────┐
│ [message content, greyed]   │
│                ⚠ Send failed │
│                [↻ Retry]     │
└─────────────────────────────┘
```

- The `AlertCircle` icon uses `color="red.400"`
- "Retry" is a `Button` with `variant="ghost"`, `size="xs"`, `color="brand.primary"`
- `MessageBubble` receives an `onRetry?: (message: ChatMessage) => void` prop — only passed for error-state messages

### Toast Notifications

Fire via Chakra `useToast` from the `onError` callback:

| HTTP Status | Toast Title | Toast Description | Toast Status |
|-------------|------------|-------------------|--------------|
| 429 | Quota Exceeded | Daily message limit reached. Resets at midnight. | `warning` |
| 500 | Server Error | Something went wrong. Tap Retry on your message. | `error` |
| Timeout/Network | Connection Lost | Check your network and tap Retry. | `error` |

Duration: 5000ms. Position: `top`. `isClosable: true`.

---

## Files Modified

| File | Change |
|------|--------|
| `frontend/src/types/conversation.ts` | Add `MessageStatus` type, `ChatMessage` type, `SendMessageVariables` interface |
| `frontend/src/hooks/use-conversations.ts` | Rewrite `useSendMessage` (`onMutate`/`onSuccess`/`onError`), add hydration in `useMessages` |
| `frontend/src/components/chat/MessageBubble.tsx` | Conditional error/pending/confirmed rendering, Retry button, `onRetry` prop |
| `frontend/src/components/chat/MessageList.tsx` | Accept and pass `onRetry` handler, type messages as `ChatMessage[]` |
| `frontend/src/pages/ChatPage.tsx` | Wire retry handler from mutation to MessageList |

## Files NOT Modified

| File | Reason |
|------|--------|
| Backend schemas/routes/services | `status` is frontend-only; no backend changes needed |
| `ChatInput.tsx` | Input component is complete (including voice) |
| `TypingIndicator.tsx` | Existing component, no changes needed |
| `CitationDrawer.tsx` | Unrelated to error handling |

---

## Acceptance Criteria

1. **State Preservation**: When `useSendMessage` fails, the user's message remains visible in the chat with error styling
2. **Error Differentiation**: Toast messages distinguish between 429 (quota), 500 (server), and network errors
3. **Retry Works**: Clicking "Retry" on a failed message re-sends it without visual flicker (in-place replacement)
4. **Retry Success**: A successful retry replaces the errored message with the confirmed user message + appends the assistant response
5. **Retry Failure**: A failed retry keeps the message in error state with a fresh toast
6. **Hydration Safety**: Messages fetched from the API always hydrate to `status: 'confirmed'` — no phantom error states after page refresh
7. **No Backend Changes**: The `MessageResponse` Pydantic schema and all API contracts remain untouched
8. **Existing Behavior Preserved**: Happy-path send (no errors) works identically to current behavior
