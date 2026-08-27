"""KPI Semantic Contracts - Source of truth for KPI definitions

Each KPI contract defines:
- name, description, formula
- data sources, dimensions
- refresh frequency, threshold
- owner, allowed roles
- lineage, business meaning

The LLM MUST NOT calculate KPI values.
All quantitative logic is governed by these contracts.
"""

KPI_CONTRACTS = {
    "revenue": {
        "name": "Revenue",
        "description": "Total recognized sales value from all product lines across regions",
        "formula": "SUM(units_sold * unit_price)",
        "data_source": "sales",
        "refresh_frequency": "hourly",
        "threshold_percent": 10.0,
        "owner": "Sales Director",
        "allowed_roles": ["CEO", "Sales Manager", "Admin"],
        "dimensions": ["product", "region", "date"],
        "business_meaning": "Primary top-line indicator of business health. Revenue decline signals potential issues in demand, supply, pricing, or market conditions.",
        "lineage": {
            "source_system": "Sales Database",
            "table": "sales",
            "column": "revenue",
            "transformations": ["SUM by date", "joined with product catalog"]
        },
        "critical_threshold": 20.0,
        "unit": "currency",
        "aggregation": "sum",
    },
    "orders": {
        "name": "Orders",
        "description": "Total distinct customer orders placed",
        "formula": "COUNT(DISTINCT order_id)",
        "data_source": "sales",
        "refresh_frequency": "hourly",
        "threshold_percent": 10.0,
        "owner": "Sales Director",
        "allowed_roles": ["CEO", "Sales Manager", "Admin"],
        "dimensions": ["product", "region", "date"],
        "business_meaning": "Volume indicator reflecting customer demand and purchase activity.",
        "lineage": {
            "source_system": "Sales Database",
            "table": "sales",
            "column": "order_id",
            "transformations": ["COUNT DISTINCT by date"]
        },
        "critical_threshold": 20.0,
        "unit": "count",
        "aggregation": "count_distinct",
    },
    "aov": {
        "name": "Average Order Value",
        "description": "Average revenue per order",
        "formula": "Revenue / Orders",
        "data_source": "sales",
        "refresh_frequency": "hourly",
        "threshold_percent": 8.0,
        "owner": "Sales Director",
        "allowed_roles": ["CEO", "Sales Manager", "Admin"],
        "dimensions": ["product", "region", "date"],
        "business_meaning": "Indicates basket size and pricing effectiveness. Changes may signal product mix shifts or pricing issues.",
        "lineage": {
            "source_system": "Sales Database",
            "table": "sales",
            "column": "revenue / order_count",
            "transformations": ["Revenue calculation", "Order count", "Division"]
        },
        "critical_threshold": 15.0,
        "unit": "currency",
        "aggregation": "derived",
    },
    "conversion_rate": {
        "name": "Conversion Rate",
        "description": "Percentage of clicks that result in conversions",
        "formula": "(Conversions / Clicks) * 100",
        "data_source": "marketing",
        "refresh_frequency": "4_hours",
        "threshold_percent": 5.0,
        "owner": "Marketing Manager",
        "allowed_roles": ["CEO", "Marketing Manager", "Admin"],
        "dimensions": ["channel", "campaign", "date"],
        "business_meaning": "Measures marketing effectiveness and website/landing page performance.",
        "lineage": {
            "source_system": "Marketing Database",
            "table": "marketing",
            "column": "conversions / clicks",
            "transformations": ["SUM conversions", "SUM clicks", "Division * 100"]
        },
        "critical_threshold": 15.0,
        "unit": "percent",
        "aggregation": "derived",
    },
    "marketing_roi": {
        "name": "Marketing ROI",
        "description": "Revenue generated per unit of marketing spend",
        "formula": "Revenue / Marketing Spend",
        "data_source": "marketing",
        "refresh_frequency": "4_hours",
        "threshold_percent": 10.0,
        "owner": "Marketing Manager",
        "allowed_roles": ["CEO", "Marketing Manager", "Admin"],
        "dimensions": ["channel", "campaign", "date"],
        "business_meaning": "Measures efficiency of marketing expenditure. Declining ROI suggests diminishing returns or channel saturation.",
        "lineage": {
            "source_system": "Cross-source",
            "tables": ["sales", "marketing"],
            "column": "revenue / spend",
            "transformations": ["Revenue from sales", "Spend from marketing", "Division"]
        },
        "critical_threshold": 20.0,
        "unit": "ratio",
        "aggregation": "derived",
    },
}

# Role-to-KPI access mapping
ROLE_KPI_ACCESS = {
    "CEO": ["revenue", "orders", "aov", "conversion_rate", "marketing_roi"],
    "Sales Manager": ["revenue", "orders", "aov"],
    "Marketing Manager": ["conversion_rate", "marketing_roi", "orders"],
    "Supply Chain Manager": ["orders"],
    "Admin": ["revenue", "orders", "aov", "conversion_rate", "marketing_roi"],
    "viewer": [],
}

# Persona-specific focus areas
PERSONA_FOCUS = {
    "CEO": {
        "narrative_style": "executive",
        "focus_areas": ["revenue", "business_impact", "major_drivers", "financial_impact"],
        "detail_level": "high_level",
        "preferred_metrics": ["revenue", "orders", "marketing_roi"],
    },
    "Marketing Manager": {
        "narrative_style": "operational",
        "focus_areas": ["campaign_performance", "traffic", "conversions", "spend_efficiency"],
        "detail_level": "detailed",
        "preferred_metrics": ["conversion_rate", "marketing_roi", "orders"],
    },
    "Sales Manager": {
        "narrative_style": "operational",
        "focus_areas": ["sales_volume", "product_mix", "regional_performance", "pipeline"],
        "detail_level": "detailed",
        "preferred_metrics": ["revenue", "orders", "aov"],
    },
}


def get_kpi_contract(kpi_name: str) -> dict | None:
    return KPI_CONTRACTS.get(kpi_name.lower())


def get_all_kpi_contracts() -> dict:
    return KPI_CONTRACTS


def check_kpi_access(kpi_name: str, role: str) -> bool:
    allowed = ROLE_KPI_ACCESS.get(role, [])
    return kpi_name.lower() in [k.lower() for k in allowed]
