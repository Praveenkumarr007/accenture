# BusinessIntelligence.AI

> **KPI Intelligence → Evidence → Action**

An AI-powered KPI Intelligence-to-Action web application that detects material KPI movements, investigates drivers using deterministic/statistical methods, calculates confidence, provides traceable evidence, generates persona-specific explanations, recommends business actions, and abstains when evidence is insufficient.

## Core Philosophy

**THE LLM EXPLAINS THE TRUTH. THE DATA AND ANALYTICS DETERMINE THE TRUTH.**

## Problem Statement

Business leaders face a flood of KPI data but struggle to understand *why* metrics change, *what* evidence supports conclusions, and *what actions* to take. Most BI tools show dashboards but don't provide actionable intelligence.

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                    FRONTEND (React)                   │
│  Dashboard │ KPI Detail │ Insights │ AI Assistant     │
├──────────────────────────────────────────────────────┤
│                    API LAYER (FastAPI)                 │
│  Auth │ KPIs │ Insights │ Feedback │ Telemetry        │
├──────────────────────────────────────────────────────┤
│               ANALYTICAL ENGINES (Deterministic)      │
│  KPI Engine │ Anomaly │ Materiality │ Driver          │
│  Confidence │ Evidence │ Recommendation               │
├──────────────────────────────────────────────────────┤
│               LLM LAYER (Optional)                    │
│  Narrative Generation │ Persona Narratives │ Chat     │
├──────────────────────────────────────────────────────┤
│               DATA LAYER                              │
│  Sales DB │ Marketing DB │ Inventory DB               │
└──────────────────────────────────────────────────────┘
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, TypeScript, Tailwind CSS, Recharts |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy |
| Database | SQLite (demo) / PostgreSQL (production) |
| AI | OpenAI API (optional, for narratives only) |
| Auth | JWT + Role-Based Access Control |

## Data Model

### 3 Data Sources
1. **Sales Database** - Hourly refresh, order-level transactions
2. **Marketing Database** - 4-hour refresh, campaign performance
3. **Inventory Database** - 30-minute refresh, stock levels

### 5 KPIs
1. **Revenue** - SUM(units_sold × unit_price)
2. **Orders** - COUNT(DISTINCT order_id)
3. **Average Order Value** - Revenue / Orders
4. **Conversion Rate** - (Conversions / Clicks) × 100
5. **Marketing ROI** - Revenue / Marketing Spend

## Analytical Methods

### Materiality Engine
Composite scoring using percentage change, business impact, and statistical significance.

### Anomaly Detection
Rolling z-score with historical baseline comparison.

### Driver Analysis
Multi-factor decomposition ranking drivers by contribution percentage.

### Confidence Engine
Weighted scoring of data completeness, freshness, statistical strength, source corroboration, and contradiction detection.

### Abstention Logic
System abstains when confidence < 40% or critical data sources are missing.

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

## Demo Scenarios

1. **Major Revenue Decline** - Revenue ↓25.3% with multi-factor analysis
2. **Low Confidence** - Missing data triggers abstention
3. **Sparse History** - New product with insufficient data
4. **Contradictory Evidence** - Conflicting signals
5. **Access Restriction** - Role-based denial

## Installation

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m app.services.data_generator
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Environment Variables

```bash
DATABASE_URL=sqlite:///./data/bi_intelligence.db
SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-api-key  # Optional
DEMO_MODE=true
LLM_ENABLED=false
```

## Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend
cd frontend
npm run build
```

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

## License

MIT
