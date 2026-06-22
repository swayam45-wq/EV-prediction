# 06. Frontend Dashboard (Phase 3)

## Tech Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| Framework | React 19 + TypeScript | Type-safe, industry standard |
| Build tool | Vite 8 | Instant HMR, fast builds |
| Styling | Tailwind CSS v4 | Utility-first, zero runtime overhead |
| Charts | Chart.js + react-chartjs-2 | Flexible, performant |
| Icons | Lucide React | Consistent, lightweight |
| HTTP | Axios | Typed API client with timeout |
| Routing | React Router v6 | SPA navigation |

## Pages

### 🏠 Home (`/`)
- Animated SVG battery gauge showing current SoC
- Live stats pulled from `GET /api/battery-health`
- Feature cards explaining LP optimizer, ML model, cost savings
- Battery health tips from backend

### ⚡ Optimizer (`/optimizer`)
- Full input form: SoC, target, capacity, charge rate, SoH, departure time, temperature, weather
- Live SoC progress bar that updates as you type
- Collapsible 24-hour electricity price viewer
- **POST /api/recommend** → mixed Bar+Line chart (energy per slot + price overlay)
- Cost comparison table (normal vs. optimized cost, savings)
- XGBoost wear score ring with sub-score breakdown bars
- AI explanation bullets and battery health advice

### 🔋 Battery Health (`/battery`)
- 270° SoH arc gauge (green/yellow/red based on health)
- Session count, avg savings, avg wear, total energy stats
- Wear trend Line chart across recent sessions
- Sessions table with rating badges
- Longevity tips grid from backend

### 📊 Analytics (`/analytics`)
- KPI row: sessions, total saved, avg wear, avg savings
- Wear score trend (Line chart)
- Savings trend (Line chart)
- Charging start hour distribution (Bar chart)
- Target SoC distribution (Doughnut chart)

## Running the Frontend

```bash
# Make sure backend is running first
cd backend
uvicorn main:app --reload --port 8000

# In a second terminal
cd frontend
npm run dev
# Opens on http://localhost:5173
```

The Vite dev server proxies all `/api/*` requests to `http://localhost:8000`.

## Project Structure

```
frontend/
├── src/
│   ├── api.ts            # Typed Axios client for all endpoints
│   ├── types.ts          # TypeScript interfaces matching Pydantic schemas
│   ├── App.tsx           # Root component with routes
│   ├── main.tsx          # App entry point + BrowserRouter
│   ├── index.css         # Global design system (tokens, glassmorphism, animations)
│   ├── components/
│   │   └── Navbar.tsx    # Sticky glassmorphism nav with active links
│   └── pages/
│       ├── Home.tsx
│       ├── Optimizer.tsx
│       ├── BatteryHealth.tsx
│       └── Analytics.tsx
├── vite.config.ts        # Vite config with Tailwind plugin + API proxy
├── index.html            # SEO-ready HTML shell
└── package.json
```

## Design System

The dark design system is defined in `index.css` using CSS custom properties:

- `--clr-bg`: Deep navy `#0a0f1e`
- `--clr-primary`: Blue `#3b82f6`
- `--clr-accent`: Green `#06d6a0`
- `.glass-card`: Glassmorphism card with hover glow
- `.gradient-text`: Blue → green gradient text
- `.btn-primary` / `.btn-secondary`: Styled buttons with hover lift
- `.badge-green/yellow/red/blue`: Status badge variants
- Animations: `fadeInUp`, `pulse-glow`, `spin-slow`
