# StrataView Frontend

Next.js 16 / React 19 frontend for the NYC Housing Investment Simulator.

See the [main README](../README.md) for full project documentation.

## Development

```bash
npm install
npm run dev          # http://localhost:3000
npm run build        # production build
npm run lint         # ESLint
```

## Environment

Copy `.env.local` and set your API URL:

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Stack

- Next.js 16.2 (App Router, Turbopack)
- React 19
- TypeScript 5
- Tailwind CSS v4
- Recharts v3 (charts)
- TanStack Query v5 (server state)
- Zustand v5 (auth state)
- React Hook Form v7
