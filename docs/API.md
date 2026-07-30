# API overview

All sensitive routes are designed for session authentication, server-side RBAC checks, Zod validation, normalized Prisma access and JSON error envelopes. Current route groups:

- `GET/POST /api/students` — searchable student CRUD foundation.
- `GET/POST /api/lessons` — schedules lessons and rejects student/instructor/vehicle overlaps.
- `POST /api/payments` — records a payment transaction and updates invoice status atomically.
- `POST /api/gps` — records authorized GPS points for active sessions with audit logging.

Extend each route with middleware-level permission checks before deploying publicly.
