# Architecture Document

## System Architecture

### Overview
BusinessIntelligence.AI follows a layered architecture with clear separation between deterministic analytics and LLM-powered narrative generation.

### Data Flow

```
Raw Data Sources
    ↓
Data Ingestion (SQL queries)
    ↓
KPI Calculation Engine (Deterministic)
    ↓
Anomaly Detection (Statistical)
    ↓
Materiality Assessment (Rule-based)
    ↓
Driver Analysis (Multi-factor decomposition)
    ↓
Evidence Collection (Cross-source)
    ↓
Confidence Calculation (Weighted scoring)
    ↓
Contradiction Detection (Logic-based)
    ↓
Abstention Check (Threshold-based)
    ↓
Recommendation Generation (Rule-based)
    ↓
LLM Narrative Generation (When enabled)
    ↓
UI Presentation (React)
```

### KPI Pipeline

```
1. KPI Semantic Contract defines formula and thresholds
2. Raw data is aggregated per contract formula
3. Current period vs previous period comparison
4. Materiality check determines if investigation needed
5. If material: run full analysis pipeline
6. If not material: skip (don't alert on insignificant changes)
```

### Driver Analysis Pipeline

```
1. Decompose KPI change by dimension:
   - Product contribution
   - Region contribution
   - Marketing factors
   - Inventory factors
   - Seasonality estimate
2. Calculate raw contribution of each factor
3. Normalize to percentage of total change
4. Rank by absolute contribution
5. Assign primary driver status
6. Attach supporting evidence per driver
```

### Evidence Pipeline

```
1. For each data source:
   - Calculate current period metrics
   - Calculate previous period metrics
   - Compute change percentage
   - Record analytical method
   - Build data lineage chain
2. Cross-validate between sources
3. Flag contradictions
```

### Confidence Pipeline

```
Inputs:
- Data source completeness
- Data freshness
- Statistical z-score
- Corroborating sources count
- Historical coverage
- Contradiction presence

Weights:
- Data completeness: 25%
- Statistical strength: 20%
- Data freshness: 15%
- Source corroboration: 15%
- Historical coverage: 15%
- Contradiction penalty: 10%

Output:
- Confidence score (0-100%)
- Level: high (≥80), medium (≥50), low (<50)
- Abstention recommendation if < 40%
```

### Feedback Loop

```
Insight → User Feedback → Evaluation → Rule Update → Improved Insights
```

### Security Model

```
1. JWT token authentication
2. Role-based access control (RBAC)
3. Backend authorization (not just frontend hiding)
4. KPI contracts define allowed roles
5. API middleware validates token and role
```

### LLM Pipeline

```
1. Deterministic analysis produces structured evidence object
2. Evidence object sent to LLM as context
3. LLM generates persona-specific narrative
4. Pydantic validates LLM response structure
5. If LLM fails, deterministic results still shown
6. LLM never accesses raw data
7. LLM never calculates KPI values
```

### Telemetry Pipeline

```
Every API request:
1. Record start time
2. Execute operation
3. Record end time
4. Calculate latency
5. Log to telemetry table
6. Track LLM usage (tokens, cost)
```

## Database Schema

### Core Tables
- `users` - User accounts with roles
- `roles` - Role definitions with permissions
- `data_sources` - Connected data sources metadata
- `kpi_definitions` - KPI semantic contracts
- `kpi_values` - Calculated KPI values
- `anomalies` - Detected anomalies
- `insights` - Generated insights
- `drivers` - Driver analysis results
- `evidence` - Evidence items per insight
- `recommendations` - Action recommendations
- `feedback` - User feedback
- `llm_logs` - LLM usage tracking
- `telemetry` - System telemetry
- `lineage` - Data lineage records

## API Design

### RESTful Endpoints
- `POST /api/auth/login` - Authentication
- `GET /api/kpis` - List KPIs
- `GET /api/kpis/{id}` - KPI detail with full analysis
- `GET /api/kpis/{id}/trend` - Historical trend
- `GET /api/kpis/{id}/drivers` - Driver analysis
- `GET /api/insights` - All insights
- `GET /api/recommendations` - All recommendations
- `GET /api/data-sources` - Data source status
- `GET /api/lineage` - Data lineage
- `POST /api/feedback` - Submit feedback
- `GET /api/feedback/dashboard` - Feedback metrics
- `POST /api/assistant` - AI chat
- `GET /api/telemetry` - System metrics
- `POST /api/demo/scenario` - Switch demo scenario
- `GET /api/admin/*` - Admin endpoints
