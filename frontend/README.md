# UrbanPick Frontend

> The whole market, one smart search. — An AI-powered multimodal shopping discovery app.

## Quick start

```bash
cd frontend
cp .env.example .env
npm install
npm run dev        # http://localhost:5173
```

## Scripts

| Command | Description |
|---|---|
| `npm run dev` | Dev server at `http://localhost:5173` |
| `npm run build` | Type-check + production bundle in `dist/` |
| `npm run preview` | Preview the production bundle locally |
| `npm run lint` | Run oxlint |

## Environment variables

Copy `.env.example` to `.env` and fill in:

| Variable | Default | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8001` | FastAPI backend URL |
| `VITE_USE_MOCK_USER_API` | `true` | Use localStorage mocks for auth/cart/saved |

## Folder map

```
frontend/src/
  api/          API client, per-endpoint functions, field mappers, TypeScript types
  services/     Service interfaces + localStorage adapters (auth, cart, saved, history, activity, catalog)
  store/         Zustand stores (auth, cart, ui)
  lib/           priceInsight.ts, format.ts, interests.ts, url.ts
  components/
    layout/      AnnouncementBar, Header, Footer, MobileDrawer, Layout
    ui/           Button, Chip, Input, SectionHeader, Skeleton
    product/     ProductCard
    search/      SearchBar
    charts/      (Phase 3)
    home/        (Phase 5)
  pages/         Splash, Home, Login, Signup, NotFound
                 (Phase 2+) Search, Category, Product, Cart, Orders, Insights, Settings
  styles/        tokens.css, globals.css
```

## How to swap mock services for real APIs

1. Set `VITE_USE_MOCK_USER_API=false` in `.env`.
2. In each `services/<name>/index.ts`, export the `real` adapter instead of the `local` adapter.
3. The real adapter calls the backend auth/user endpoints with JWT stored in an httpOnly cookie.

> ⚠️  The mock auth is NOT secure. It stores a SHA-256 hash of the password in localStorage. It is fine for development only. Never deploy mock mode to production.

## Design system

Design tokens are in `src/styles/tokens.css` as CSS custom properties. All components use these variables — do not hard-code colors.

Theme: **Midnight Market** — dark ink header/footer, champagne (`#C9B58A`) accent, cream paper (`#F6F4F0`) page background. Fonts: **Bodoni Moda** (headings, wordmark) + **Manrope** (UI, body).

## Build phases

| Phase | Status | What's built |
|---|---|---|
| 1 – Foundation | ✅ Done | Scaffold, tokens, fonts, layout, Splash, static Home, Login, Signup, NotFound |
| 2 – Search & products | ⏳ Next | API client, SearchBar image upload, Search page, Category page, Product detail |
| 3 – Price intelligence | ⏳ | priceInsight.ts, Recharts line chart, verdict card |
| 4 – Accounts & lists | ⏳ | Mock auth, protected routes, Cart, Saved, Orders, Settings |
| 5 – Personalization | ⏳ | Activity tracking, Insights, For-you row, a11y pass, full test suite |
