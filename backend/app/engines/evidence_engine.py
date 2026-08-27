"""
Evidence Engine

Every insight must have traceable evidence.
Collects, validates, and presents evidence from all data sources.
"""


class EvidenceEngine:
    def collect_evidence(self, kpi_name, current_data, previous_data, drivers, data_sources_info):
        evidence = []
        if "sales" in data_sources_info:
            evidence.append(self._sales_evidence(current_data, previous_data))
        if "marketing" in data_sources_info:
            evidence.append(self._marketing_evidence(current_data, previous_data))
        if "inventory" in data_sources_info:
            evidence.append(self._inventory_evidence(current_data, previous_data))
        evidence.append(self._driver_evidence(drivers))
        return [e for e in evidence if e is not None]

    def _sales_evidence(self, current, previous):
        curr = current.get("sales", {})
        prev = previous.get("sales", {})
        rev_change = curr.get("revenue", 0) - prev.get("revenue", 0)
        rev_pct = (rev_change / prev["revenue"] * 100) if prev.get("revenue", 0) > 0 else 0
        return {"source": "Sales Database", "metric": "Revenue", "metric_value": round(curr.get("revenue", 0), 2),
                "previous_value": round(prev.get("revenue", 0), 2), "change_percent": round(rev_pct, 2),
                "analytical_method": "Direct aggregation from sales records", "timestamp": current.get("timestamp"),
                "data_lineage": {"source_system": "Sales Database", "table": "sales", "operation": "SUM(revenue)"}}

    def _marketing_evidence(self, current, previous):
        curr = current.get("marketing", {})
        prev = previous.get("marketing", {})
        spend_change = curr.get("spend", 0) - prev.get("spend", 0)
        spend_pct = (spend_change / prev["spend"] * 100) if prev.get("spend", 0) > 0 else 0
        return {"source": "Marketing Database", "metric": "Marketing Spend & Traffic",
                "metric_value": round(curr.get("spend", 0), 2), "previous_value": round(prev.get("spend", 0), 2),
                "change_percent": round(spend_pct, 2), "analytical_method": "Aggregation from marketing data",
                "timestamp": current.get("timestamp"),
                "data_lineage": {"source_system": "Marketing Database", "table": "marketing", "operation": "SUM(spend)"}}

    def _inventory_evidence(self, current, previous):
        curr = current.get("inventory", {})
        prev = previous.get("inventory", {})
        stock_change = curr.get("avg_stock", 0) - prev.get("avg_stock", 0)
        stock_pct = (stock_change / prev["avg_stock"] * 100) if prev.get("avg_stock", 0) > 0 else 0
        return {"source": "Inventory Database", "metric": "Stock Availability",
                "metric_value": round(curr.get("avg_stock", 0), 0), "previous_value": round(prev.get("avg_stock", 0), 0),
                "change_percent": round(stock_pct, 2), "analytical_method": "Average stock level calculation",
                "timestamp": current.get("timestamp"),
                "data_lineage": {"source_system": "Inventory Database", "table": "inventory", "operation": "AVG(stock_available)"}}

    def _driver_evidence(self, drivers):
        return {"source": "Analytical Engine", "metric": "Driver Analysis", "metric_value": len(drivers),
                "analytical_method": "Multi-factor decomposition with contribution ranking",
                "data_lineage": {"source_system": "Cross-source", "operation": "Driver contribution"}}
