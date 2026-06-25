# 06. Frontend Dashboard (Phase 3 & 4)

## Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| Vite | 8.x | Build tool + dev server with HMR |
| React | 19 | UI framework |
| TypeScript | 6.x | Type safety |
| Tailwind CSS | v4 | Utility layer (via `@tailwindcss/vite`) |
| Chart.js + react-chartjs-2 | 4.x | Data visualization |
| Lucide React | latest | Icon system |
| Axios | 1.x | Typed HTTP client |
| React Router | v6 | Client-side routing |

---

## Design System

The entire UI uses a custom **automotive dark design system** defined in `src/index.css`.

### Philosophy
Inspired by Tesla, Rivian, and BMW ConnectedDrive:
- **Single accent color**: `#0ea5e9` electric blue — no rainbow gradients
- **Dark charcoal base**: `#0d0f14` background, not navy
- **Tabular numbers**: JetBrains Mono for all numeric data readouts
- **Flat, precise cards**: subtle `1px` borders, not heavy glassmorphism
- **Data-forward layout**: information density over decoration

### CSS Tokens

```css
--bg-base:       #0d0f14   /* Page background */
--bg-raised:     #13161d   /* Cards, sidebar */
--bg-overlay:    #1a1d26   /* Inputs, hover states */
--accent:        #0ea5e9   /* Electric blue — only accent */
--success:       #10b981   /* Green — good battery state */
--warning:       #f59e0b   /* Amber — medium wear */
--danger:        #ef4444   /* Red — high wear, errors */
--text-primary:  #f1f3f8
--text-secondary:#8b9dc3
--text-tertiary: #4a5060
```

---

## Layout

The app uses a **sidebar layout** — not a top navbar:

```
┌─────────────────────────────────────────┐
│  Sidebar (240px fixed)  │  Main content  │
│                         │                │
│  [Logo: ChargeMind]     │  Page header   │
│  [Vehicle Status Card]  │  Page body     │
│  > Dashboard            │  (scrollable)  │
│  > Optimizer            │                │
│  > Battery              │                │
│  > Analytics            │                │
│  ─────────────────────  │                │
│  Alerts · Settings      │                │
│  v2.0.0                 │                │
└─────────────────────────────────────────┘
```

---

## Pages

### Dashboard (`/`)
- **SoC gauge**: Circular SVG gauge showing current State of Charge
- **4 KPI tiles**: SoH%, avg savings, total sessions, avg wear
- **Battery Status card**: range estimate, capacity, charge rate, progress bar
- **Charging Conditions card**: temperature, weather, departure time countdown
- **System Overview**: 3-column LP→ML→DB flow description
- **Health tips** from the backend API

### Optimizer (`/optimizer`)
- **Vehicle Telemetry Status Banner**:
  - Automatically queries `/api/vehicle/status` on component mount.
  - Dynamically displays vehicle model, connection type (e.g. *Live · smartcar* or *Demo Mode*), battery range, and charge states.
  - Form parameters (SoC, battery capacity, SOH, max charge rate) are automatically auto-filled from the vehicle state.
  - Clicking **"Connect Live EV"** redirects the user to the Smartcar OAuth portal.
  - Clicking **"Disconnect"** clears active tokens and reverts to simulated mode.
- **Left panel (320px)**:
  - Vehicle parameters and environmental forms.
  - Collapsible **Electricity Prices** card with an active **Region Selector dropdown** (`US_CA`, `US_TX`, `UK`, `DE`, `IN`). Changing the region automatically updates the dynamic prices table and charts.
- **Right panel**: Results area
  - Mixed Chart.js schedule (bars) + dynamic spot prices (line).
  - Net cost comparison table showing savings percentages.
  - XGBoost wear ring and sub-score metrics.
  - Conversational explanations and optimization advice.

### Battery Health (`/battery`)
- **240° arc SoH gauge** with color-coded fill (green/amber/red)
- ML model status pill (XGBoost Active / Heuristic Mode)
- **4 stat tiles**: sessions, avg savings, avg wear, total energy
- **Wear Score History** line chart (dot color encodes rating)
- **Session Log** data table with sortable columns
- **Longevity Tips** card grid from backend API

### Analytics (`/analytics`)
- **4 KPI tiles**: total sessions, total $ saved, avg wear, avg savings
- **Wear Score Trend** — line chart per session
- **Cost Savings Trend** — line chart (%)
- **Charging Start Hours** — bar chart (when do users plug in?)
- **Target SoC Distribution** — doughnut chart

---

## Running

```bash
# 1. Backend must be running first
cd backend
python -m uvicorn main:app --reload --port 8000

# 2. Start dev server
cd frontend
npm run dev
# → http://localhost:5173

# 3. Production build
npm run build
# → frontend/dist/
```

## API Proxy

`vite.config.ts` proxies all `/api/*` and `/health` requests to `http://localhost:8000` during development, so no CORS issues.
