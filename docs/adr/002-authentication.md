# ADR-002: Authentication System

## Status
Accepted

## Context
MMAi V2 needs user authentication for the AI coaching chat and related features. We need to choose between building custom auth with standard libraries or using an opinionated framework like FastAPI-Users.

## Decision

### Standard JWT + bcrypt (manual routes)
- **python-jose** for JWT encoding/decoding
- **bcrypt** (direct, not via passlib) for password hashing
- Manual FastAPI routes for register, login, refresh, verify-email

### Why not FastAPI-Users?
- Portfolio signal: building auth from scratch demonstrates understanding, not just library installation
- Control: fits our async SQLAlchemy 2.0 setup without adapting to external abstractions
- Scope: we only need register/login/verify — FastAPI-Users brings OAuth2 social login, RBAC, etc. that we don't need
- Teaching mode: inline code is self-documenting

### Why bcrypt directly instead of passlib?
- passlib has known compatibility issues with bcrypt >= 4.x on Python 3.12+
- passlib's `CryptContext` wraps bcrypt but adds no meaningful security benefit for our use case
- bcrypt 5.x works directly with `bcrypt.hashpw()` and `bcrypt.checkpw()` — simple and reliable
- Fewer dependencies, fewer deprecation warnings

### Token Strategy
- **Access token**: 30 min expiry, type="access"
- **Refresh token**: 7 days expiry, type="refresh"
- Both are JWTs with a `type` claim to prevent cross-use (using a refresh token as an access token is rejected)
- Tokens contain `sub` (user UUID), `type`, `iat`, `exp`

### User Model
Single `users` table with UUID PKs, email verification support (token + timestamp columns), and password reset stub columns for future use.

### Email Verification
- On registration, a `verification_token` is generated and logged to console
- Email transport is pluggable — console logging is the stub for now
- `POST /api/auth/verify-email` accepts the token and marks the user as verified

### Password Reset
- Columns exist in the model (`password_reset_token`, `password_reset_sent_at`)
- Endpoints return 501 Not Implemented — ready for future implementation

## Consequences
- All auth logic is visible and auditable in `app/services/auth.py` and `app/core/security.py`
- No external auth framework to upgrade or maintain
- Email sending must be implemented separately when needed
- Token refresh requires client-side logic to call `/api/auth/refresh` before access token expires
