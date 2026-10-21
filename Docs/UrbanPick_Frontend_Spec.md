# UrbanPick Frontend: Build Specification

You are building the complete web frontend for **UrbanPick**, a multimodal AI shopping assistant that recommends products from every category. Read this whole file before writing any code. A reference image of the approved design ("Midnight Market") is at `frontend/docs/design/midnight-market.png`; match its look, layout, spacing and tone closely. A second image, `frontend/docs/design/login.png`, shows the login style.

Work in phases (section 11). Finish one phase, run the checks, report, then continue.

---

## 1. What UrbanPick is (and is not)

- A shopping **recommendation** site. Users search by text, by image, or both. The backend finds matching products, explains them, and compares them.
- Products come from **every category**: clothing, shoes, watches, electronics, home, beauty, sports and more. Never design for one product type.
- **No payments, no checkout.** UrbanPick never takes money. Each product has store links (Amazon, Flipkart, etc.). The "buy" action opens the store's product page in a new tab.
- It tracks what the logged-in user searches, views and saves, so it can recommend better and show their interests.
- It shows **price history** per product and tells the user whether it looks like a good time to buy or whether to wait.
- Products in the database are populated later by an n8n automation. Do not build any scraping or n8n integration now.

## 2. Backend contract

Backend: FastAPI at `VITE_API_BASE_URL` (default `http://localhost:8001`). Before coding, **read `backend/main.py`, `backend/schemas.py` and `backend/config.py`** and use the exact field names found there. Put all field mapping in one file (`src/api/mappers.ts`) so a later backend change touches one place.

Real endpoints available today:

| Method | Path | Notes |
|---|---|---|
| POST | `/api/v1/search` | `multipart/form-data`: `text_prompt?`, `image_file?`, `max_price?`, `category?`, `top_k?`. At least one of text or image is required. Returns `query`, `recommended_products[]`, `ai_analysis` (string), `comparison_table[]` (list of objects), `total_results`, `search_type` (`text`, `image` or `multimodal`). |
| GET | `/api/v1/products/{id}` | One product's metadata. |
| GET | `/api/v1/health` | Status. Use it for a small "assistant offline" banner. |

Product data includes (verify exact names in `schemas.py`): id, title, brand, category, price, original price, discount percentage, rating, image URL, specs, store availability (JSON string or list of stores with links), price history (JSON string or list of date and price pairs). Search results also carry a similarity score.

Rules:
- Do NOT call `/ingest` or `DELETE /products/{id}` from the frontend, and never put `INGEST_API_KEY` in frontend code.
- Search can take several seconds (embedding plus an LLM). Use a 60 second timeout, an abort on navigation, and a good loading state. Handle HTTP 429 ("You're searching very fast. Please wait a moment."), 422, 400, 5xx and network failure with friendly messages.
- Verify the backend CORS config allows `http://localhost:5173`. If not, make the smallest change to allow it, and tell me. Do not change anything else in `backend/` without asking.

### Things the backend does NOT have yet (build against a service layer, mock for now)

1. Browse or list products (home sections, category pages). **Workaround:** use `POST /search` with `text_prompt` = the category or section name and the `category` filter. Hide this behind `catalogService.listByCategory()` so a real list endpoint can replace it later.
2. Auth (sign up, log in), user profile.
3. Cart, saved items, purchase history.
4. User activity tracking and personalized recommendations.
5. A price-insight endpoint (the verdict is computed in the frontend for now, see section 7).

For 2, 3 and 4 build **service interfaces with a localStorage adapter** (`AuthService`, `CartService`, `SavedService`, `HistoryService`, `ActivityService`). Switch adapters with `VITE_USE_MOCK_USER_API=true`. Mock auth is not secure; add a visible code comment saying so. Never store plain passwords: for the mock, store a salted SHA-256 hash via `crypto.subtle`.

## 3. Tech stack

- Vite + React 18 + TypeScript (strict)
- Tailwind CSS with design tokens as CSS variables
- React Router v6, TanStack Query, Zustand (with `persist`)
- Recharts for charts
- react-hook-form + zod for forms
- lucide-react icons (thin stroke, 1.5 px, no filled icons) and `@fontsource` for fonts
- Framer Motion only for the splash screen and light page transitions
- Vitest + React Testing Library for a few core tests
- ESLint + Prettier

Project location: `frontend/` at the repo root, next to `backend/`.

```
frontend/src/
  api/          client.ts, search.ts, products.ts, health.ts, mappers.ts, types.ts
  services/     auth, cart, saved, history, activity, catalog (interfaces + local adapters)
  store/        zustand stores (auth, cart, ui)
  lib/          priceInsight.ts, format.ts, interests.ts, url.ts
  components/   layout/, ui/, product/, search/, charts/, home/
  pages/        Splash, Home, Search, Category, Product, Login, Signup, Cart, Orders, Insights, Settings, NotFound
  styles/       tokens.css, globals.css
```

## 4. Design system: "Midnight Market"

Mood: simple, calm, a little luxurious. Dark header and footer around a light shop floor, one champagne accent. Restraint is the whole point.

Colors (CSS variables):

| Token | Hex | Use |
|---|---|---|
| `--ink-900` | `#101114` | dark header, hero, banners, footer |
| `--ink-800` | `#1A1B20` | dark surfaces, search bar on dark |
| `--ink-700` | `#23252B` | dark rows and chips |
| `--ink-600` | `#2A2C33` | dark borders |
| `--ink-500` | `#3A3C44` | dark outlines |
| `--champagne` | `#C9B58A` | accent: primary buttons on dark, links on dark |
| `--champagne-deep` | `#8A7545` | accent on light backgrounds (icons, link hover) |
| `--paper` | `#F6F4F0` | page background |
| `--tile` | `#ECE8E0` | product image tiles, placeholders |
| `--card` | `#FFFFFF` | cards on paper |
| `--text` | `#17171A` | text on light |
| `--text-muted` | `#66625B` | secondary text on light |
| `--line` | `#E3DFD6` | borders on light |
| `--on-dark` | `#F2EEE6` | text on dark |
| `--on-dark-muted` | `#A9A59C` | secondary text on dark |

Add semantic colors for the price verdict that still feel premium: good `#3F7D5B`, fair `#8A7545`, wait `#A5523F` (text on light) with soft tinted backgrounds. Never use color alone: always pair with an icon and a label.

Typography: **Bodoni Moda** (400, 500) for headings and the wordmark; **Manrope** (300 to 600) for UI and body. Headings 34 to 64 px on desktop, scaling down on mobile. Body 15 to 16 px. Uppercase eyebrows 12 px with 0.2 to 0.26em tracking. Wordmark "URBANPICK" in Bodoni with 0.26 to 0.3em letter spacing.

Shape and feel: radius 16 to 28 on cards and banners, full pill on search bars, buttons and chips. 1 px borders instead of shadows (at most one very soft shadow on floating menus). **No gradients, glows, neon, glassmorphism, emoji or autoplay carousels.** Motion 150 to 250 ms, ease-out, nothing bouncy. Respect `prefers-reduced-motion`.

Components to build once and reuse: Button (primary champagne on dark, primary ink on light, outline, ghost), Chip, Input, SearchBar (text + image button + submit), ProductCard, PriceBlock, Badge, SectionHeader, Banner, Skeleton, EmptyState, ErrorState, Modal, Drawer, Toast, Tabs, Table.

Touch targets are at least 44 px. Visible focus rings (champagne on dark, ink on light). Text contrast at least 4.5:1.

## 5. Screens

### 5.1 Splash (first load of each session)
Full-screen `--ink-900`. The wordmark "URBANPICK" fades and rises in (letters stagger slightly), a thin champagne line draws under it, then the tagline "Every category, one smart search." fades in. About 2.2 seconds total, then the whole screen fades out into Home. Show it once per session (`sessionStorage`). Any click or key skips it. With reduced motion, use a plain 0.4 s fade.

### 5.2 Global layout
- **Announcement bar** (champagne, 40 px): short message from a config constant, e.g. "Compare prices across stores before you buy."
- **Header** (dark): wordmark left, category menu centered, right: search button, account menu (Sign in / Sign up when logged out; Insights, Cart, Orders, Settings, Log out when logged in), cart icon with count.
- **All categories mega menu:** opens from a "Categories" trigger and lists every category (Clothing, Shoes, Watches, Electronics, Home, Beauty, Sports, plus any others in the catalog) as a clean grid with a thin icon each. Keyboard accessible.
- **Mobile (390 px):** hamburger opens a drawer with categories and account links; the search bar sits full width below the header.
- **Footer** (dark): wordmark, Shop, Help, Company columns, and a short note: "UrbanPick doesn't sell products. We compare and link to the stores."

### 5.3 Home (follow the Midnight Market image)
1. Dark hero: eyebrow, large headline ("The whole market, one smart search."), the main **SearchBar** (text input, camera/image button, Search button) and category chips below.
2. Six to eight category cards overlapping the hero's bottom edge.
3. Dark "shopping assistant" banner with a short explanation and a real example result card.
4. A featured collection block (one large tile with caption plus a 2x2 product grid). Choose the collection from the catalog (e.g., the category with the best deals).
5. "Trending now" grid of 8 products with an add-to-cart round button.
6. **For you** row (logged-in only): recommended items from the user's interests.
7. Trust row. Do not invent claims; use only: "Compare store prices", "Price history", "Direct links to stores", "Smart recommendations".
8. Footer.

**Featured / ad slots:** build a `<FeaturedBanner>` and `<FeaturedProduct>` component, labelled "Featured". Fill them only from products in our own catalog (for example, the highest discounts). No external ad networks, no tracking scripts.

### 5.4 Search
Triggered from the hero or header. The SearchBar supports:
- Text, image, or both. Image: file picker, drag and drop, paste from clipboard, and `capture` on mobile. Validate type (jpg, jpeg, png, webp, gif, bmp) and size client-side (read the max from the backend config or default to 5 MB). Show a thumbnail with a remove button.
- Filters: category (chips) and max price (slider or input).

Results page `/search`:
- Heading showing the query and `search_type`.
- **AI analysis card:** render `ai_analysis` as plain text (never HTML). Title it "Why these picks".
- **Comparison table:** render `comparison_table` dynamically from whatever keys it has. Sticky first column, horizontal scroll on mobile, price and rating columns right-aligned.
- Product grid with sort (Best match, Price low to high, Price high to low) and a match percentage if the backend returns a similarity score.
- Loading: skeleton cards plus the line "Finding the best matches..." Empty: helpful suggestions. Error: retry button.

### 5.5 Category page `/category/:slug`
Header with the category name, filters (price), grid, and "Load more" (raise `top_k` up to 60). Uses `catalogService.listByCategory()`.

### 5.6 Product detail `/product/:id`
- Left: large image with a graceful fallback tile. Right: brand, title, rating, current price, original price and discount, **"Buy from" store list**, add to cart, save.
- **Store links:** one row per store with name, its price if known, and a "Buy on {Store}" button. The best price gets a "Lowest price" badge. Links open with `target="_blank" rel="noopener noreferrer sponsored"`. Only allow `http` and `https` URLs; otherwise hide the link. If there are none, show "Store link coming soon". Clicking a store link records an activity event and a history entry (section 8).
- **Price intelligence** section (section 7): line chart, stats, verdict.
- Specs as a clean two-column table.
- "Similar products" row (search using the title).

### 5.7 Auth
- `/login` and `/signup`, in the style of `docs/design/login.png`: dark page, centered dark card, champagne primary button.
- Fields: sign up has name, email, password, confirm password; login has email and password. Show/hide password, inline zod errors, disabled submit while loading, clear failure messages.
- Protected pages (`/cart`, `/orders`, `/insights`, `/settings`) redirect to `/login?next=...`. Guests can browse and search. When a guest taps add to cart or save, open a small modal that offers Sign in or Create account, then return them to what they were doing.

### 5.8 Cart `/cart` (with a "Saved" tab)
List of items: image, title, price, remove. Each row has "Buy on {Store}" buttons. Show an **estimated total** labelled "Estimate based on listed prices". Clear note: "You complete your purchase on the store's website. UrbanPick doesn't take payment." No checkout button. Saved tab holds heart-saved items.

### 5.9 Orders `/orders` (purchase history)
We cannot know if someone really bought something. So:
- When the user clicks a store link, create an entry: product, store, date, status "Went to {Store}".
- The entry offers "I bought this" (status Purchased) and "Not bought" (remove).
- Filters by status. Empty state explains how entries appear.

### 5.10 Insights `/insights` ("Your interests")
Built from the activity log: top categories (small bar chart), recent searches, recently viewed, typical budget range, and "Recommended for you" (run searches using the user's top interests). Honest copy: "Based on what you search and view on UrbanPick." Show a "Pause personalization" switch.

### 5.11 Settings `/settings`
Sections: Profile (name, email), Shopping preferences (favorite categories, budget range), Personalization (on/off, **Clear my activity**), Account (change password in mock mode, log out, delete account). Save with a toast.

### 5.12 Other
404 page, global error boundary, "assistant offline" banner when `/health` fails, page titles per route.

## 6. Data handling
- Prices in INR with `Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })`.
- Parse `price_history` and `store_availability` safely (they may be JSON strings). On bad data, show the empty version of that section, never crash.
- Images: lazy-load, fixed aspect boxes (no layout shift), `onError` fallback to the tinted tile with the category icon.
- Cache with TanStack Query (searches 5 min, products 10 min).

## 7. Price intelligence (deterministic, no LLM)
Implement in `lib/priceInsight.ts` with unit tests. Input: price history `[{date, price}]` and the current price.

- Need at least 5 data points. Otherwise show "Not enough price history yet" (no verdict).
- Compute min, max, average and the current price's percentile in the history.
- Verdict, first match wins:
  1. **Great time to buy:** current is within 3% of the lowest recorded, or in the lowest 15%.
  2. **Good price:** at least 5% below the average.
  3. **Consider waiting:** at least 5% above the average, or in the top 25%.
  4. **Fair price:** otherwise.
- Show the evidence in plain words: "Lowest recorded: ₹X on {date}. Average: ₹Y. Today: ₹Z ({n}% below/above average)."
- Chart (Recharts line chart): champagne-deep line on paper, dashed average line, a highlighted dot for today's price, tooltip with date and price, range tabs 1M / 3M / 6M / All. Provide a visually-hidden text summary and a "View as table" toggle for accessibility.
- Small disclaimer: "Based on recorded prices. Not a guarantee of future prices."
- Keep this logic behind one function so it can later be replaced by a backend endpoint.

## 8. Personalization and activity tracking
Track locally (per user) through `ActivityService`: `search` (text, category), `view_product`, `add_to_cart`, `save`, `store_click`, `view_category`. Store `{type, productId?, category?, brand?, query?, price?, ts}`; cap at 500 events.

`lib/interests.ts` derives: top categories and brands (recency-weighted), typical price band (median plus or minus spread), and recent queries. These feed Insights and the "For you" row.

Privacy: a one-time dismissible notice ("UrbanPick remembers your searches and views to improve recommendations. You can pause or clear this in Settings."), a working pause switch, and Clear activity. No third-party analytics.

## 9. Quality bars
- **Accessibility:** semantic HTML, real buttons and links, labels on every input, `aria-label` on icon-only buttons, focus trapped in modals and drawers, skip-to-content link, charts with text alternatives.
- **Responsive:** design at 390, 768, 1280 and 1440 px. Nothing overflows horizontally except intentional table scroll.
- **Performance:** route-level code splitting, lazy images, fonts via `@fontsource` (latin only), no layout shift. Target Lighthouse performance 90 or higher on Home.
- **Security:** no `dangerouslySetInnerHTML`; render AI text as text; validate external URLs (`http`/`https` only); no secrets in the bundle; no calls to admin endpoints.
- **Honesty in the UI:** do not show invented ratings, review counts, stock numbers, "X people bought this", fake urgency or fake discounts. Show only data from the API, or a clearly labelled empty state.

## 10. Files to add
- `frontend/.env.example`: `VITE_API_BASE_URL=http://localhost:8001` and `VITE_USE_MOCK_USER_API=true`
- `frontend/README.md`: setup, scripts, env vars, folder map, how to swap mock services for a real API
- `docs/BACKEND_GAPS.md`: the endpoints the frontend needs next (section 12)

## 11. Phases (stop and report after each)

**Phase 1: Foundation.** Scaffold, tokens, fonts, Tailwind, router, base UI components, layout (announcement bar, header, mega menu, drawer, footer), Splash, and a static Home matching the design image. Check: `npm run build` passes, Home matches the image at 1440 and 390 px.

**Phase 2: Search and products.** API client, SearchBar with image upload, Search results page (AI analysis, comparison table, grid), Category page, Product detail with store links, skeletons and all error states. Check: works against the real backend on port 8001 with text, image and combined search.

**Phase 3: Price intelligence.** `priceInsight.ts` with tests, price chart, verdict card, price history on the product page. Check: unit tests pass, handles missing or malformed history.

**Phase 4: Accounts and shopping lists.** Mock services, Login, Signup, protected routes, guest modal, Cart, Saved, Orders, Settings. Check: full flow works after a page refresh.

**Phase 5: Personalization and polish.** Activity tracking, Insights page, For-you row, featured slots, privacy notice, accessibility and responsive pass, README and BACKEND_GAPS. Check: `npm run build`, `npm run lint` and `npm test` all pass.

## 12. Backend gaps to document in `docs/BACKEND_GAPS.md`
1. `GET /api/v1/products?category=&q=&min_price=&max_price=&sort=&limit=&offset=` (browse and category pages)
2. `GET /api/v1/categories`
3. `GET /api/v1/products/{id}/price-insight` (server-side verdict, same output shape as the frontend one)
4. Auth: `POST /auth/signup`, `POST /auth/login`, `GET /auth/me`, `POST /auth/logout` (JWT in an httpOnly cookie)
5. User data: `/me/cart`, `/me/saved`, `/me/history`, `/me/activity`, `/me/preferences`
6. `GET /me/recommendations`
7. Redirect/click tracking: `POST /links/click` (log the store click, then return the store URL)

## Rules for you, the agent
- Ask before changing anything outside `frontend/`, except the CORS fix mentioned above.
- Do not add features that are not in this spec (no payments, no reviews, no chat history UI, no social login).
- Keep files small and typed. No `any`. Reuse components instead of copying styles.
- If the design image and this text disagree, the image wins for looks and this text wins for behavior.
- At the end of each phase: list the files you created, how to run it, what you tested, and anything unfinished.
