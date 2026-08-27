from fastapi import APIRouter

router = APIRouter()


@router.get("")
def get_lineage(kpi_name: str = None):
    nodes = [
        {"type": "source", "name": "Sales Database", "id": "src_sales"},
        {"type": "source", "name": "Marketing Database", "id": "src_marketing"},
        {"type": "source", "name": "Inventory Database", "id": "src_inventory"},
        {"type": "table", "name": "sales.revenue", "id": "tbl_revenue"},
        {"type": "table", "name": "marketing.spend", "id": "tbl_spend"},
        {"type": "table", "name": "inventory.stock", "id": "tbl_stock"},
        {"type": "transformation", "name": "KPI Calculation", "id": "kpi_calc"},
        {"type": "transformation", "name": "Anomaly Detection", "id": "anomaly_detect"},
        {"type": "transformation", "name": "Driver Analysis", "id": "driver_analysis"},
        {"type": "output", "name": "Insight", "id": "insight"},
        {"type": "output", "name": "Recommendation", "id": "recommendation"},
    ]
    edges = [
        {"source": "src_sales", "target": "tbl_revenue"},
        {"source": "src_marketing", "target": "tbl_spend"},
        {"source": "src_inventory", "target": "tbl_stock"},
        {"source": "tbl_revenue", "target": "kpi_calc"},
        {"source": "tbl_spend", "target": "kpi_calc"},
        {"source": "tbl_stock", "target": "kpi_calc"},
        {"source": "kpi_calc", "target": "anomaly_detect"},
        {"source": "anomaly_detect", "target": "driver_analysis"},
        {"source": "driver_analysis", "target": "insight"},
        {"source": "driver_analysis", "target": "recommendation"},
    ]
    return {"nodes": nodes, "edges": edges}
