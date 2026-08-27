"""Data Upload Service - Handles CSV, Excel, and SQL file uploads."""
import os
import sqlite3
import csv
import io
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
import pandas as pd

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def _get_db_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _sanitize_table_name(name: str) -> str:
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    name = re.sub(r'_+', '_', name).strip('_').lower()
    if not name:
        name = "uploaded_table"
    if not name[0].isalpha():
        name = "t_" + name
    return name


def _infer_sqlite_type(series: pd.Series) -> str:
    if pd.api.types.is_integer_dtype(series):
        return "INTEGER"
    if pd.api.types.is_float_dtype(series):
        return "REAL"
    if pd.api.types.is_bool_dtype(series):
        return "INTEGER"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "TEXT"
    return "TEXT"


def detect_columns(df: pd.DataFrame) -> list[dict]:
    columns = []
    for col in df.columns:
        series = df[col].dropna()
        col_info = {
            "name": str(col),
            "sqlite_type": _infer_sqlite_type(df[col]),
            "pandas_dtype": str(df[col].dtype),
            "non_null_count": int(series.count()),
            "null_count": int(df[col].isna().sum()),
            "total_count": len(df),
            "unique_count": int(series.nunique()) if len(series) > 0 else 0,
            "sample_values": [str(v) for v in series.head(5).tolist()] if len(series) > 0 else [],
        }
        if pd.api.types.is_numeric_dtype(series) and len(series) > 0:
            col_info["min"] = float(series.min())
            col_info["max"] = float(series.max())
            col_info["mean"] = float(series.mean())
        columns.append(col_info)
    return columns


def preview_file(file_path: str, file_type: str, max_rows: int = 10) -> dict:
    try:
        if file_type == "csv":
            df = pd.read_csv(file_path, nrows=max_rows)
            full_df = pd.read_csv(file_path)
        elif file_type in ("xlsx", "xls"):
            df = pd.read_excel(file_path, nrows=max_rows)
            full_df = pd.read_excel(file_path)
        else:
            return {"error": f"Unsupported file type: {file_type}"}

        return {
            "filename": os.path.basename(file_path),
            "file_type": file_type,
            "total_rows": len(full_df),
            "total_columns": len(full_df.columns),
            "columns": detect_columns(full_df),
            "preview": df.head(max_rows).fillna("").to_dict(orient="records"),
            "row_count": len(full_df),
        }
    except Exception as e:
        return {"error": str(e)}


def upload_csv(file_content: bytes, filename: str, table_name: Optional[str] = None, db_path: Optional[str] = None) -> dict:
    if not db_path:
        db_path = str(DATA_DIR / "bi_intelligence.db")

    if not table_name:
        table_name = _sanitize_table_name(Path(filename).stem)

    try:
        df = pd.read_csv(io.BytesIO(file_content))
        if df.empty:
            return {"error": "File is empty or has no data rows"}

        df.columns = [_sanitize_table_name(c) for c in df.columns]

        conn = _get_db_connection(db_path)
        columns = detect_columns(df)

        create_sql = f"CREATE TABLE IF NOT EXISTS [{table_name}] (\n"
        col_defs = []
        for col_info in columns:
            col_defs.append(f"  [{col_info['name']}] {col_info['sqlite_type']}")
        col_defs.append("  id INTEGER PRIMARY KEY AUTOINCREMENT")
        create_sql += ",\n".join(col_defs) + "\n)"
        conn.execute(create_sql)

        placeholders = ", ".join(["?" for _ in df.columns])
        col_names = ", ".join([f"[{c}]" for c in df.columns])
        insert_sql = f"INSERT INTO [{table_name}] ({col_names}) VALUES ({placeholders})"

        rows = df.where(df.notna(), None).values.tolist()
        conn.executemany(insert_sql, rows)
        conn.commit()

        row_count = conn.execute(f"SELECT COUNT(*) FROM [{table_name}]").fetchone()[0]
        conn.close()

        return {
            "success": True,
            "table_name": table_name,
            "rows_inserted": len(rows),
            "total_rows_in_table": row_count,
            "columns": columns,
            "filename": filename,
        }
    except Exception as e:
        return {"error": str(e)}


def upload_excel(file_content: bytes, filename: str, table_name: Optional[str] = None, db_path: Optional[str] = None) -> dict:
    if not db_path:
        db_path = str(DATA_DIR / "bi_intelligence.db")

    if not table_name:
        table_name = _sanitize_table_name(Path(filename).stem)

    try:
        df = pd.read_excel(io.BytesIO(file_content))
        if df.empty:
            return {"error": "File is empty or has no data rows"}

        df.columns = [_sanitize_table_name(c) for c in df.columns]

        conn = _get_db_connection(db_path)
        columns = detect_columns(df)

        create_sql = f"CREATE TABLE IF NOT EXISTS [{table_name}] (\n"
        col_defs = []
        for col_info in columns:
            col_defs.append(f"  [{col_info['name']}] {col_info['sqlite_type']}")
        col_defs.append("  id INTEGER PRIMARY KEY AUTOINCREMENT")
        create_sql += ",\n".join(col_defs) + "\n)"
        conn.execute(create_sql)

        placeholders = ", ".join(["?" for _ in df.columns])
        col_names = ", ".join([f"[{c}]" for c in df.columns])
        insert_sql = f"INSERT INTO [{table_name}] ({col_names}) VALUES ({placeholders})"

        rows = df.where(df.notna(), None).values.tolist()
        conn.executemany(insert_sql, rows)
        conn.commit()

        row_count = conn.execute(f"SELECT COUNT(*) FROM [{table_name}]").fetchone()[0]
        conn.close()

        return {
            "success": True,
            "table_name": table_name,
            "rows_inserted": len(rows),
            "total_rows_in_table": row_count,
            "columns": columns,
            "filename": filename,
        }
    except Exception as e:
        return {"error": str(e)}


def upload_sql(file_content: bytes, filename: str, db_path: Optional[str] = None) -> dict:
    if not db_path:
        db_path = str(DATA_DIR / "bi_intelligence.db")

    try:
        sql_text = file_content.decode("utf-8-sig")
        sql_text = sql_text.strip()
        if not sql_text:
            return {"error": "SQL file is empty"}

        conn = _get_db_connection(db_path)
        cursor = conn.cursor()

        statements = []
        current = []
        in_string = False
        string_char = None

        for char in sql_text:
            if in_string:
                current.append(char)
                if char == string_char:
                    in_string = False
            else:
                if char in ("'", '"'):
                    in_string = True
                    string_char = char
                    current.append(char)
                elif char == ";":
                    stmt = "".join(current).strip()
                    if stmt:
                        statements.append(stmt)
                    current = []
                else:
                    current.append(char)

        last_stmt = "".join(current).strip()
        if last_stmt:
            statements.append(last_stmt)

        results = []
        tables_created = []
        total_rows_affected = 0

        for stmt in statements:
            upper = stmt.upper().strip()
            try:
                cursor.execute(stmt)
                if upper.startswith("CREATE"):
                    match = re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`"\[]?(\w+)', stmt, re.IGNORECASE)
                    if match:
                        tables_created.append(match.group(1))

                if cursor.rowcount > 0:
                    total_rows_affected += cursor.rowcount

                try:
                    rows = cursor.fetchall()
                    if rows:
                        results.append({
                            "statement": stmt[:200],
                            "rows_returned": len(rows),
                            "sample": [list(r) for r in rows[:5]],
                        })
                except Exception:
                    pass

            except Exception as e:
                results.append({
                    "statement": stmt[:200],
                    "error": str(e),
                })

        conn.commit()
        conn.close()

        return {
            "success": True,
            "filename": filename,
            "statements_executed": len(statements),
            "tables_created": tables_created,
            "total_rows_affected": total_rows_affected,
            "results": results,
        }
    except Exception as e:
        return {"error": str(e)}


def list_uploaded_tables(db_path: Optional[str] = None) -> list[dict]:
    if not db_path:
        db_path = str(DATA_DIR / "bi_intelligence.db")

    system_tables = {
        "roles", "users", "data_sources", "kpi_definitions", "kpi_values",
        "anomalies", "insights", "drivers", "evidence", "recommendations",
        "feedback", "llm_logs", "telemetry", "lineage",
    }

    try:
        conn = _get_db_connection(db_path)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()

        result = []
        for (tname,) in tables:
            if tname in system_tables or tname.startswith("sqlite_"):
                continue
            row_count = conn.execute(f"SELECT COUNT(*) FROM [{tname}]").fetchone()[0]
            cols = conn.execute(f"PRAGMA table_info([{tname}])").fetchall()
            result.append({
                "table_name": tname,
                "row_count": row_count,
                "column_count": len(cols),
                "columns": [{"name": c[1], "type": c[2]} for c in cols],
                "is_uploaded": True,
            })
        conn.close()
        return result
    except Exception as e:
        return [{"error": str(e)}]


def delete_uploaded_table(table_name: str, db_path: Optional[str] = None) -> dict:
    if not db_path:
        db_path = str(DATA_DIR / "bi_intelligence.db")

    system_tables = {
        "roles", "users", "data_sources", "kpi_definitions", "kpi_values",
        "anomalies", "insights", "drivers", "evidence", "recommendations",
        "feedback", "llm_logs", "telemetry", "lineage",
    }

    if table_name in system_tables:
        return {"error": "Cannot delete system table"}

    try:
        conn = _get_db_connection(db_path)
        conn.execute(f"DROP TABLE IF EXISTS [{table_name}]")
        conn.commit()
        conn.close()
        return {"success": True, "message": f"Table '{table_name}' deleted"}
    except Exception as e:
        return {"error": str(e)}


def query_table(table_name: str, limit: int = 50, offset: int = 0, db_path: Optional[str] = None) -> dict:
    if not db_path:
        db_path = str(DATA_DIR / "bi_intelligence.db")

    try:
        conn = _get_db_connection(db_path)
        total = conn.execute(f"SELECT COUNT(*) FROM [{table_name}]").fetchone()[0]
        cursor = conn.execute(f"SELECT * FROM [{table_name}] LIMIT ? OFFSET ?", (limit, offset))
        cols = [d[0] for d in cursor.description]
        rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
        conn.close()
        return {
            "table_name": table_name,
            "total_rows": total,
            "limit": limit,
            "offset": offset,
            "columns": cols,
            "rows": rows,
        }
    except Exception as e:
        return {"error": str(e)}
