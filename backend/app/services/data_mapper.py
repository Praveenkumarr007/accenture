"""Auto-detect column mappings from uploaded data."""
import sqlite3
import re
import json
from typing import Optional
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"

COLUMN_PATTERNS = {
    "date": [
        # exact canonical names match first
        r"^\bdate\b$", r"^order_date$", r"^transaction_date$", r"^created_at$",
        r"^timestamp$", r"^datetime$",
        # token matches
        r"\bdate\b", r"date$", r"_date$",
    ],
    "revenue": [
        r"^\brevenue\b$", r"^total_revenue$", r"^net_revenue$", r"^gross_revenue$",
        r"^total_sales$", r"^sales_amount$", r"^amount$", r"^sales$", r"^revenue_attributed$",
        r"\brevenue\b", r"^net_revenue", r"^gross_",
    ],
    "units_sold": [
        r"^units_sold$", r"^quantity$", r"^qty$", r"^units$", r"^num_units$",
        r"^items_sold$", r"^sold$", r"^order_quantity$",
        r"units_sold", r"\bunits\b", r"_sold$", r"\bqty\b",
    ],
    "order_id": [
        r"^order_id$", r"^transaction_id$", r"^order_number$", r"^invoice$",
        r"^bill_id$", r"^order$",
        r"order_id", r"transaction_id", r"order_number", r"invoice",
    ],
    "product_name": [
        r"^product_name$", r"^product$", r"^item_name$", r"^sku$", r"^product_id$",
        r"^goods$", r"^merchandise$",
        r"\bproduct\b", r"\bitem\b", r"\bsku\b",
    ],
    "region": [
        r"^\bregion\b$", r"^area$", r"^zone$", r"^location$", r"^territory$", r"^market$",
        r"\bregion\b", r"\bstate\b", r"\bcity\b", r"\bcountry\b",
    ],
    "conversions": [
        r"^conversions$", r"^conversion$", r"^leads$", r"^qualified_leads$",
        r"^signups$", r"^purchases$", r"^orders$",
        r"\bconversions\b", r"\bleads\b",
    ],
    "clicks": [
        r"^clicks$", r"^click$", r"^hits$", r"^visits$", r"^sessions$", r"^page_views$",
        r"\bclicks\b", r"\bclicks", r"clicks$",
    ],
    "spend": [
        r"^spend$", r"^marketing_spend$", r"^ad_spend$", r"^cost$", r"^budget$",
        r"^advertising$", r"^expense$", r"^marketing_cost$", r"^ad_cost$",
        r"\bspend\b", r"spend$", r"\bcost\b", r"\bbudget\b", r"\badvertising\b",
    ],
    "stock_available": [
        r"^stock_available$", r"^closing_stock$", r"^on_hand$", r"^available$",
        r"^stock_qty$", r"^quantity_available$",
        r"\bstock\b", r"\binventory\b", r"^closing_stock", r"stock$",
    ],
    "stockout": [
        r"^stockout$", r"^out_of_stock$", r"^oos$", r"^shortage$", r"^depleted$",
        r"\bstockout\b", r"out_of_stock", r"\bshortage\b",
    ],
}

FIELD_TABLE_MAP = {
    "date": ["sales", "marketing", "inventory"],
    "revenue": ["sales"],
    "units_sold": ["sales"],
    "order_id": ["sales"],
    "product_name": ["sales", "inventory"],
    "region": ["sales"],
    "conversions": ["marketing"],
    "clicks": ["marketing"],
    "spend": ["marketing"],
    "stock_available": ["inventory"],
    "stockout": ["inventory"],
}

TABLE_MINIMUMS = {
    "sales": ["date", "revenue"],
    "marketing": ["date", "clicks"],
    "inventory": ["date", "product_name"],
}


def _match_column(col_name: str) -> list[tuple[str, float]]:
    """Return list of (field, confidence) for a column name.

    Exact canonical-name matches score 0.98. Specific known names (e.g.
    order_date, marketing_spend) score 0.95. Token/contains matches score
    between 0.6 and 0.85.
    """
    col = col_name.lower().strip()
    matches = []
    for field, patterns in COLUMN_PATTERNS.items():
        best = None
        for pattern in patterns:
            pattern_is_anchored = pattern.startswith("^") and pattern.endswith("$")
            if pattern_is_anchored:
                if re.search(pattern, col):
                    # exact/specific known name
                    stripped = pattern.strip("^$").replace("\\b", "")
                    if stripped == field:
                        best = max(best or 0, 0.98)
                    elif col == stripped:
                        best = max(best or 0, 0.95)
                    else:
                        best = max(best or 0, 0.88)
            else:
                if re.search(pattern, col):
                    best = max(best or 0, 0.75)
        if best:
            matches.append((field, best))
    return matches


def detect_mapping(table_name: str, columns: list[str], db_path: Optional[str] = None) -> dict:
    if not db_path:
        db_path = str(DATA_DIR / "bi_intelligence.db")

    field_scores = {"sales": 0, "marketing": 0, "inventory": 0}
    field_mappings = {}
    unmapped_columns = []

    for col in columns:
        matches = _match_column(col)
        if matches:
            best_field, best_conf = max(matches, key=lambda x: x[1])
            # keep the strongest mapping per target field
            if best_field not in field_mappings or field_mappings[best_field]["confidence"] < best_conf:
                field_mappings[best_field] = {
                    "uploaded_column": col,
                    "target_field": best_field,
                    "confidence": best_conf,
                }
            for tname in FIELD_TABLE_MAP.get(best_field, []):
                field_scores[tname] += best_conf
        else:
            unmapped_columns.append(col)

    if not field_mappings:
        return {
            "table_name": table_name,
            "detected_type": "unknown",
            "confidence": 0,
            "field_mappings": {},
            "missing_fields": [],
            "unmapped_columns": unmapped_columns,
            "all_columns": columns,
        }

    best_table = max(field_scores, key=field_scores.get)
    best_score = field_scores[best_table]

    total_possible = sum(1.0 for f in TABLE_MINIMUMS.get(best_table, []) if f in field_mappings)
    total_needed = len(TABLE_MINIMUMS.get(best_table, []))
    min_match = total_possible / total_needed if total_needed > 0 else 0
    col_match_ratio = len(field_mappings) / len(columns) if columns else 0
    confidence = round(min(0.95, (best_score / max(len(field_mappings), 1)) * 0.5 + min_match * 0.3 + col_match_ratio * 0.2), 2)

    all_needed_fields = set()
    for f in FIELD_TABLE_MAP:
        if best_table in FIELD_TABLE_MAP[f]:
            all_needed_fields.add(f)
    missing = [f for f in all_needed_fields if f not in field_mappings]

    return {
        "table_name": table_name,
        "detected_type": best_table,
        "confidence": confidence,
        "field_mappings": field_mappings,
        "missing_fields": missing,
        "unmapped_columns": unmapped_columns,
        "all_columns": columns,
    }


def save_mapping(table_name: str, mapped_type: str, column_mapping: dict, db_path: Optional[str] = None) -> dict:
    if not db_path:
        db_path = str(DATA_DIR / "bi_intelligence.db")

    try:
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS data_config (
                id INTEGER PRIMARY KEY,
                table_name TEXT UNIQUE NOT NULL,
                mapped_type TEXT NOT NULL,
                column_mapping TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)
        conn.execute("UPDATE data_config SET is_active = 0 WHERE mapped_type = ?", (mapped_type,))
        conn.execute(
            "INSERT OR REPLACE INTO data_config (table_name, mapped_type, column_mapping, is_active) VALUES (?, ?, ?, 1)",
            (table_name, mapped_type, json.dumps(column_mapping)),
        )
        conn.commit()
        conn.close()
        return {"success": True, "table_name": table_name, "mapped_type": mapped_type}
    except Exception as e:
        return {"error": str(e)}


def get_active_mappings(db_path: Optional[str] = None) -> list[dict]:
    if not db_path:
        db_path = str(DATA_DIR / "bi_intelligence.db")

    try:
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS data_config (
                id INTEGER PRIMARY KEY,
                table_name TEXT UNIQUE NOT NULL,
                mapped_type TEXT NOT NULL,
                column_mapping TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)
        rows = conn.execute("SELECT table_name, mapped_type, column_mapping, is_active FROM data_config WHERE is_active = 1").fetchall()
        conn.close()
        return [{"table_name": r[0], "mapped_type": r[1], "column_mapping": json.loads(r[2]), "is_active": bool(r[3])} for r in rows]
    except Exception as e:
        return [{"error": str(e)}]


def get_mapping_for_type(mapped_type: str, db_path: Optional[str] = None) -> Optional[dict]:
    if not db_path:
        db_path = str(DATA_DIR / "bi_intelligence.db")

    try:
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS data_config (
                id INTEGER PRIMARY KEY,
                table_name TEXT UNIQUE NOT NULL,
                mapped_type TEXT NOT NULL,
                column_mapping TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)
        row = conn.execute("SELECT table_name, mapped_type, column_mapping FROM data_config WHERE mapped_type = ? AND is_active = 1", (mapped_type,)).fetchone()
        conn.close()
        if row:
            return {"table_name": row[0], "mapped_type": row[1], "column_mapping": json.loads(row[2])}
        return None
    except Exception:
        return None


def deactivate_mapping(table_name: str, db_path: Optional[str] = None) -> dict:
    if not db_path:
        db_path = str(DATA_DIR / "bi_intelligence.db")
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("UPDATE data_config SET is_active = 0 WHERE table_name = ?", (table_name,))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}