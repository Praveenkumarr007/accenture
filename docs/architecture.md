# Architecture Document

## System Architecture

### Data Flow

```
Data Sources (Sales, Marketing, Inventory)
    ↓
Data Ingestion & Cleaning (SQLAlchemy ORM)
    ↓
KPI Calculation Engine (Deterministic)
    ↓
Materiality Engine (Threshold + Statistical)
    ↓
Anomaly Detection (Rolling Mean + Z-Score)
    ↓
Driver Analysis (Multi-factor Decomposition)
    ↓
Evidence Engine (Source + Metric + Value)
    ↓
Confidence Engine (Multi-factor Score)
    ↓
Recommendation Engine (Driver → Lever → Action)
    ↓
Insight Assembly (All components combined)
    ↓
LLM Narrative Generation (Guarded, Structured Input)
    ↓
API Response → Frontend Display
```

### KPI Pipeline

```
Raw Data → Daily KPI Values → Baseline Calculation →
Deviation Detection → Materiality Check → Analysis Trigger
```

### LLM Pipeline

```
Structured Context (KPI, Drivers, Evidence, Confidence)
    ↓
System Prompt (Guardrails, Persona)
    ↓
OpenAI API Call (JSON output)
    ↓
Pydantic Validation
    ↓
Fallback if LLM fails
```

### Evidence Pipeline

```
Driver Detected → Relevant Data Queried →
Metric Comparison → Evidence Item Created →
Source + Timestamp + Method Recorded
```

### Recommendation Pipeline

```
Driver → Category Mapping → Controllable Lever →
Action Template → Expected Impact → Owner Assignment →
Monitoring Plan → Priority Scoring
```

### Feedback Loop

```
Insight Displayed → User Feedback →
Feedback Stored → Driver Weight Adjustment →
Problematic Rules Flagged → Future Improvement
```

### Security Model

```
User → Login → JWT Token →
Request + Token → Middleware →
Role Check → Permission Validation →
Data Filtering → Response
```

## Separation of Concerns

### Deterministic Processing (Never LLM)
- Data ingestion and cleaning
- KPI calculations
- Statistical tests
- Contribution analysis
- Confidence calculation
- Materiality assessment
- Anomaly detection
- Access control
- Data lineage tracking
- Recommendation scoring

### LLM Processing (Guarded)
- Natural language explanation
- Persona-specific narrative
- Intent understanding
- Contextual summarization
- Recommendation wording
- Conversational Q&A
