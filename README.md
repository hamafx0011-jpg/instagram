# Driving School Management System

Production-oriented Next.js + TypeScript + Prisma/PostgreSQL driving office management SaaS with Kurdish Sorani default locale, Arabic/English support, RTL/LTR layouts, RBAC, dashboards, portals, scheduling, GPS, accounting, reports, documents, notifications and audit-log architecture.

## Demo accounts
All development accounts use password `DemoPass123!`:
- `superadmin@demo.test`
- `officeadmin@demo.test`
- `reception@demo.test`
- `instructor@demo.test`
- `accountant@demo.test`
- `student@demo.test`

## Run locally
```bash
cp .env.example .env
npm install
npx prisma generate
npx prisma migrate dev --name init
npm run prisma:seed
npm run dev
```

## Production notes
Set `DATABASE_URL`, `NEXTAUTH_SECRET`, storage, email/SMS and map provider environment variables. Precise GPS is stored server-side and must only be exposed through permission-checked APIs.
