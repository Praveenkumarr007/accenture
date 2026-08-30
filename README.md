# BusinessIntelligence.AI

> **KPI Intelligence → Evidence → Action**

An AI-powered KPI Intelligence-to-Action web application that detects material KPI movements, investigates drivers using deterministic/statistical methods, calculates confidence, provides traceable evidence, generates persona-specific explanations, recommends business actions, and abstains when evidence is insufficient.

---

## Core Philosophy

**THE LLM EXPLAINS THE TRUTH. THE DATA AND ANALYTICS DETERMINE THE TRUTH.**

## Problem Statement

Business leaders face a flood of KPI data but struggle to understand *why* metrics change, *what* evidence supports conclusions, and *what* actions to take. Most BI tools show dashboards but don't provide actionable intelligence.

---

## Solution Approach

The application follows a **"deterministic-first, LLM-second"** architecture:

1. **Ingest** sales, marketing, and inventory data (pre-seeded demo data or user-uploaded CSV/Excel).
2. **Compute** all KPI values with deterministic SQL-based engines (no LLM involved in calculation).
3. **Analyze**: detect anomalies (rolling z-score), assess materiality, decompose changes into drivers, check for contradictions.
4. **Validate** the analysis across multiple evidence sources and score an overall confidence.
5. **Abstain** when confidence is too low or critical data is missing — the system says "I don't know" instead of guessing.
6. **Recommend** business actions only when supporting evidence is strong enough.
7. **Explain** everything in natural language, persona-adjusted, and answer follow-up questions via the AI Assistant.

The key design rule: **the LLM never invents numbers and never calculates KPIs** — it only narrates what the deterministic engines already proved.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                    FRONTEND (React + Vite)            │
│  Overview │ KPI Detail │ Insights │ Drivers │        │
│  Recommendations │ Help │ AI Assistant │ Admin       │
├──────────────────────────────────────────────────────┤
│                    API LAYER (FastAPI)                │
│  Auth │ KPIs │ Insights │ Feedback │ Telemetry │      │
│  Upload (CSV/Excel/SQL) │ Assistant │ Scenarios      │
├──────────────────────────────────────────────────────┤
│               ANALYTICAL ENGINES (Deterministic)      │
│  KPI Engine │ Anomaly │ Materiality │ Driver          │
│  Confidence │ Evidence │ Recommendation               │
├──────────────────────────────────────────────────────┤
│               LLM LAYER (Optional, disabled in demo)  │
│  Narrative Generation │ Persona Narratives │ Chat     │
├──────────────────────────────────────────────────────┤
│               DATA LAYER                              │
│  SQLite (bi_intelligence.db) : Sales / Marketing /    │
│  Inventory tables + uploaded tables + mappings        │
└──────────────────────────────────────────────────────┘
```

### Project Structure

```
businessintelligence-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, all REST endpoints, SPA serving
│   │   ├── api/v1/                 # Versioned API routers (auth, kpis, insights, ...)
│   │   ├── core/                   # Config, database, security (JWT), KPI contracts
│   │   ├── engines/                # Deterministic engines
│   │   │   ├── kpi_engine.py       # KPI calculations + daily trends (SQL)
│   │   │   ├── anomaly_detector.py # Rolling z-score anomaly detection
│   │   │   ├── materiality.py      # Composite materiality scoring
│   │   │   ├── driver_analyzer.py  # Product/Region/Category contribution analysis
│   │   │   ├── confidence_engine.py# Confidence + abstention + contradictions
│   │   │   ├── evidence_engine.py  # Cross-source evidence collection
│   │   │   └── recommendation_engine.py # Actionable recommendations
│   │   ├── llm/                    # Optional OpenAI integration + deterministic fallbacks
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   ├── schemas/                # Pydantic request/response models
│   │   └── services/               # Orchestrator, data generator, upload, mapping
│   ├── requirements.txt
│   └── data/bi_intelligence.db     # SQLite database (auto-created on first run)
└── frontend/
    ├── public/                     # Static assets (logo, favicon)
    ├── src/
    │   ├── pages/                  # Overview, KPI Detail, Insights, Drivers, Help, ...
    │   ├── components/             # Layout (Sidebar/TopNav), charts, assistant
    │   ├── lib/                    # API client, utils (formatting)
    │   ├── hooks/                  # Auth (JWT) hooks
    │   └── types/                  # TypeScript types
    ├── index.html
    ├── package.json
    └── vite.config.ts              # Dev server + /api proxy → :8000
```

---

## Technology Stack & Versions

The project is fully built and verified with the exact versions below:

### Backend

| Component | Version |
|-----------|---------|
| Python | **3.13.7** |
| FastAPI | 0.109.0 |
| Uvicorn | 0.27.0 |
| SQLAlchemy | 2.0.25 |
| Pydantic | 2.5.3 |
| pandas | 2.2.0 |
| numpy | 1.26.3 |
| scipy | 1.12.0 |
| scikit-learn | 1.4.0 |
| python-jose (JWT) | 3.3.0 |
| passlib[bcrypt] | 1.7.4 |
| openai (optional) | 1.12.0 |
| httpx | 0.26.0 |

### Frontend

| Component | Version |
|-----------|---------|
| Node.js | **v24.18.0** |
| npm | 11.16.0 |
| React | 18.3.1 |
| TypeScript | 5.3.3 |
| Vite | 5.1.0 (builds to 5.4.21) |
| Tailwind CSS | 3.4.1 |
| Recharts | 2.12.0 |
| react-router-dom | 6.22.0 |
| lucide-react | 0.344.0 |

### Database & Tooling

| Component | Version |
|-----------|---------|
| SQLite | Bundled with Python |
| cloudflared (tunnel) | 2026.8.2 (optional, for phone/public access) |

---

## Key Features

1. **Adaptive Analysis Periods** — The current/prior comparison windows adapt to the actual data span (whole span → 14-day → 30-day → 90-day windows), so both 7-day uploads and longer histories analyze correctly.
2. **Honest "N/A" for change** — When there is no prior baseline (e.g. only 7 days of data), the app reports `N/A` instead of fabricating a percentage.
3. **5 KPI cards** — Revenue, Orders, Average Order Value, Conversion Rate, Marketing ROI — each with value, trend, and materiality priority.
4. **Materiality Engine** — Composite scoring (percentage change + business impact + statistical significance) with Critical / High / Medium / Low priorities.
5. **Anomaly Detection** — Rolling z-score with historical baseline comparison.
6. **Driver Analysis** — Multi-factor decomposition (product, region) ranked by contribution percentage.
7. **Confidence Engine** — Weighted scoring of data completeness, freshness, statistical strength, source corroboration, and contradictions.
8. **Abstention Logic** — System abstains when confidence is too low or critical sources are missing, explicitly stating "insufficient evidence".
9. **AI Assistant** — Intent-based chat answering "why", "drivers", "recommendations", "trend", "product/region breakdown", "confidence" and "summary" questions with distinct, data-driven answers per role.
10. **Role-Based Access (RBAC)** — CEO/Admin see everything; Sales sees Revenue/Orders/AOV; Marketing sees Conversion/ROI/Orders; Supply Chain sees Orders only. Forbidden access returns 403.
11. **Persona switching** — Same data, different narrative lens (CEO / Sales / Marketing) via the top-right persona selector.
12. **Data Upload** — Upload CSV/Excel/SQL files, preview, auto-detect column mapping (sales/marketing/inventory), and connect them to the dashboard.
13. **Demo Scenarios** — Simulate Major Decline, Low Confidence, Sparse History, Contradictory Evidence, and Access Restriction.
14. **Help & FAQ page** — In-app documentation of data, periods, roles, and features.
15. **Apple-style light theme** — SF Pro system font, frosted-glass top bar, near-black text on light gray (#f5f5f7), Apple blue (#0071e3) accent.

---

## Data Model

### 3 Data Sources
1. **Sales Database** — Hourly refresh, order-level transactions
2. **Marketing Database** — 4-hour refresh, campaign performance
3. **Inventory Database** — 30-minute refresh, stock levels

### 5 KPIs
1. **Revenue** — SUM(units_sold × unit_price)
2. **Orders** — COUNT(DISTINCT order_id)
3. **Average Order Value** — Revenue / Orders
4. **Conversion Rate** — (Conversions / Clicks) × 100
5. **Marketing ROI** — Revenue / Marketing Spend

## KPI Semantic Contract

Each KPI has a contract defining:
- Name, description, formula
- Data sources, dimensions
- Refresh frequency, threshold
- Owner, allowed roles
- Lineage, business meaning

## Role-Based Access

| Role | Accessible KPIs |
|------|----------------|
| CEO | All KPIs |
| Sales Manager | Revenue, Orders, AOV |
| Marketing Manager | Conversion Rate, Marketing ROI, Orders |
| Supply Chain Manager | Orders |
| Admin | All KPIs |

---

## Getting Started — Run from Your Own Device

### Prerequisites

Install these first:

1. **Python 3.13.x** → https://www.python.org/downloads/
   - During install, tick **"Add Python to PATH"**.
2. **Node.js 24.x** → https://nodejs.org/ (includes npm)
3. *(Optional)* **Git** → https://git-scm.com/downloads (only needed if you clone the repo)

Verify the installs open a terminal (Command Prompt / PowerShell) and run:

```bash
python --version   # Python 3.13.7
node --version     # v24.18.0
npm --version      # 11.16.0
```

### Step 1 — Get the code

```bash
git clone <your-repo-url>
cd businessintelligence-ai
```

(or copy/unzip the project folder to your machine.)

### Step 2 — Install the backend

```bash
cd backend
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> If `pip` is not recognized, use `python -m pip install -r requirements.txt`.

### Step 3 — Install the frontend

```bash
cd ../frontend
npm install
```

> This installs React, Vite, Tailwind, Recharts, etc. Run inside the `frontend` folder.

### Step 4 — Build the frontend (so the backend can serve it)

The backend serves the built frontend from `frontend/dist`, so build it first:

```bash
npm run build
```

The build output goes to `frontend/dist/`.

### Step 5 — Start the backend server

```bash
cd ../backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

On startup the app:
- Creates the SQLite database (`backend/data/bi_intelligence.db`) automatically, if missing
- Seeds the demo data (5 users, 5 roles, 3 data sources, sample sales/marketing/inventory records)
- Serves both the API (`/api/...`) and the built frontend at `http://localhost:8000/`

### Step 6 — Open the app in your browser

Go to: **http://localhost:8000**

Log in with a demo account:

| Role | Username | Password |
|------|----------|----------|
| CEO | `ceo` | `demo123` |
| Sales Manager | `sales_mgr` | `demo123` |
| Marketing Manager | `marketing_mgr` | `demo123` |
| Supply Chain Manager | `supply_mgr` | `demo123` |
| Admin | `admin` | `admin123` |

---

## Options for Development

### Run the backend with auto-reload (while coding)

```bash
cd backend
python -m uvicorn app.main:app --reload
```

### Run the frontend dev server with hot reload

```bash
cd frontend
npm run dev
```

This starts Vite at **http://localhost:5173** and proxies `/api` calls to the backend at `http://localhost:8000` (configured in `vite.config.ts`). Use this while developing the UI; use the built version (Step 4–5) for a single-server deployment.

---

## Accessing from Another Device / Phone

### Option A — Same WiFi (LAN)

1. Keep the backend running on `0.0.0.0` (Step 5 does this).
2. Find this computer's local IP:
   - Windows: `ipconfig` → look for the **IPv4 Address** (e.g. `192.168.x.x` or `172.16.x.x`).
3. On the phone/browser, open `http://<that-ip>:8000`.
4. **Troubleshooting:** if it doesn't load, Windows Firewall may be blocking port 8000. Allow it:
   ```powershell
   New-NetFirewallRule -DisplayName "BI.AI 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
   ```
   Also, some routers enable *client isolation* which blocks device-to-device traffic — if so, use Option B.

### Option B — Cloudflare Quick Tunnel (public, works anywhere)

1. Install `cloudflared` from https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
2. With the backend running on port 8000, in a terminal:
   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```
3. cloudflared prints a public URL like `https://random-words-xxxx.trycloudflare.com` — open that on any phone/browser.
4. **Important:** the URL is temporary and changes every time the tunnel restarts. Fetch the current URL from the tunnel's log output.

---

## Demo Scenarios

1. **Major Revenue Decline** - Revenue ↓25.3% with multi-factor analysis
2. **Low Confidence** - Missing data triggers abstention
3. **Sparse History** - New product with insufficient data
4. **Contradictory Evidence** - Conflicting signals
5. **Access Restriction** - Role-based denial

Select these from the **"Select Scenario"** dropdown in the top bar.

---

## Environment Variables

Create a `.env` file in the `backend` folder (optional; defaults shown):

```bash
DATABASE_URL=sqlite:///./data/bi_intelligence.db
SECRET_KEY=dev-secret-key-change-in-production
OPENAI_API_KEY=your-api-key        # Optional (LLM features stay disabled without it)
OPENAI_MODEL=gpt-4
DEMO_MODE=true
LLM_ENABLED=false                   # Keep false to use deterministic narratives
ACCESS_TOKEN_EXPIRE_MINUTES=480
CORS_ORIGINS=["*"]
```

**LLM mode:** without an OpenAI key the app runs 100% on deterministic engines and returns perfectly usable analyses. Set `LLM_ENABLED=true` and add an `OPENAI_API_KEY` to enable optional natural-language narrative enrichment.

---

## Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend type-check + production build
cd frontend
npm run build
```

---

## API Overview (key endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login, returns JWT + user |
| GET | `/api/kpis?persona=CEO` | KPI cards (role-filtered) |
| GET | `/api/kpis/{kpi_id}` | Full analysis: drivers, evidence, confidence, recommendations |
| GET | `/api/kpis/{kpi_id}/trend` | Daily trend points |
| GET | `/api/kpis/{kpi_id}/drivers` | Driver decomposition |
| GET | `/api/insights` | All insights (role-filtered, by materiality) |
| GET | `/api/recommendations` | Recommended actions |
| POST | `/api/assistant` | AI Assistant (intent-based Q&A) |
| POST | `/api/upload/file` | Upload CSV/Excel/SQL |
| GET | `/api/upload/tables` | List uploaded tables |
| POST | `/api/upload/apply-mapping` | Map columns to sales/marketing/inventory |
| GET | `/api/data-sources` | Data source health |
| GET | `/api/telemetry` | System/LLM stats (Admin) |
| GET | `/api/admin/users` | User list (Admin/CEO only) |

---

## LLM Architecture

### Deterministic (Non-LLM)
- Data ingestion and cleaning
- KPI calculations
- Anomaly detection
- Statistical tests
- Contribution analysis
- Confidence calculation
- Access control
- Data lineage
- Materiality assessment
- Recommendation scoring

### LLM (When Enabled)
- Intent understanding
- Natural-language explanation
- Persona-specific narratives
- Contextual summarization
- Recommendation wording
- Conversational Q&A

### Guardrails
- LLM never invents numbers
- LLM never calculates KPI values
- LLM only uses provided evidence
- LLM explicitly states uncertainty
- All responses validated with Pydantic

## Cost Optimization
- Cache repeated explanations
- Only call LLM when necessary
- Use deterministic logic first
- Track estimated cost per insight

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `pip` not found | Use `python -m pip install -r requirements.txt` |
| `npm` not found | Reinstall Node.js and reopen the terminal |
| Port 8000 already in use | Change port: `python -m uvicorn app.main:app --port 8001`, open `http://localhost:8001` |
| Assistant returns errors | Ensure the backend is running (LLM is optional; deterministic mode works keyless) |
| Phone can't open LAN link | Add firewall rule (above) or use the Cloudflare tunnel |
| KPI shows "N/A" | Your dataset has no prior period — expected behavior, not an error |
| White screen / blank | Re-run `npm run build` after frontend changes |

---

## License

MIT