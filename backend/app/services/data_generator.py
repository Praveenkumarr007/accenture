"""
Synthetic data generator for ShopSmart e-commerce company.

Generates 90+ days of realistic data across 3 sources:
1. Sales Database (hourly grain)
2. Marketing Database (4-hour grain)
3. Inventory Database (30-min grain)

Creates deliberate patterns:
- Weekly seasonality (weekday/weekend differences)
- Product-level trends
- Regional variations
- Marketing campaigns with varying performance
- Stockout events (especially laptops)
- Price changes
- Anomalies for detection

Key scenario: Laptop inventory becomes critically low,
causing cascading effects on sales and revenue.
"""
import random
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
import math

random.seed(42)

PRODUCTS = [
    {"id": 1, "name": "Laptop", "base_price": 65000, "base_daily_units": 25},
    {"id": 2, "name": "Smartphone", "base_price": 35000, "base_daily_units": 45},
    {"id": 3, "name": "Headphones", "base_price": 3500, "base_daily_units": 80},
    {"id": 4, "name": "Smartwatch", "base_price": 12000, "base_daily_units": 30},
    {"id": 5, "name": "Tablet", "base_price": 28000, "base_daily_units": 20},
]

REGIONS = ["North", "South", "East", "West"]

CAMPAIGNS = [
    {"id": "C001", "name": "Summer Sale", "channel": "Google Ads", "base_spend": 150000, "start_day": 0, "end_day": 30},
    {"id": "C002", "name": "Festive Promotion", "channel": "Facebook", "base_spend": 200000, "start_day": 45, "end_day": 75},
    {"id": "C003", "name": "Brand Awareness", "channel": "Instagram", "base_spend": 100000, "start_day": 0, "end_day": 90},
    {"id": "C004", "name": "Retargeting", "channel": "Google Ads", "base_spend": 80000, "start_day": 20, "end_day": 80},
    {"id": "C005", "name": "Affiliate Push", "channel": "Affiliate", "base_spend": 60000, "start_day": 10, "end_day": 60},
]

WAREHOUSES = ["North_WH", "South_WH", "East_WH", "West_WH"]


def day_of_week_factor(day_offset: int, base_date: datetime) -> float:
    dow = (base_date + timedelta(days=day_offset)).weekday()
    factors = [1.15, 1.0, 1.05, 1.0, 0.95, 0.7, 0.65]
    return factors[dow]


def trend_factor(day_offset: int) -> float:
    """Slight upward trend then decline in last 3 weeks for laptops"""
    return 1.0 + 0.002 * day_offset


def laptop_stock_curve(day_offset: int) -> float:
    """Laptops start losing stock around day 60, critical by day 75"""
    if day_offset < 55:
        return 1.0
    elif day_offset < 65:
        return max(0.2, 1.0 - 0.08 * (day_offset - 55))
    elif day_offset < 80:
        return max(0.02, 0.2 - 0.012 * (day_offset - 65))
    else:
        return max(0.02, 0.02 + 0.005 * (day_offset - 80))


def generate_sales_data(base_date: datetime, days: int = 95) -> list[dict]:
    rows = []
    order_counter = 100000
    for day_offset in range(days):
        date = base_date + timedelta(days=day_offset)
        dow_factor = day_of_week_factor(day_offset, base_date)

        for product in PRODUCTS:
            if product["name"] == "Laptop":
                stock_factor = laptop_stock_curve(day_offset)
            else:
                stock_factor = 1.0

            for region in REGIONS:
                region_factor = {"North": 1.1, "South": 1.0, "East": 0.9, "West": 1.05}[region]
                base_units = product["base_daily_units"]
                expected = base_units * dow_factor * region_factor * stock_factor * trend_factor(day_offset)
                noise = random.gauss(0, expected * 0.12)
                units = max(0, int(expected + noise))
                if units == 0:
                    continue

                price_variation = random.uniform(0.95, 1.02)
                unit_price = product["base_price"] * price_variation
                revenue = units * unit_price

                num_orders = max(1, units // random.randint(1, 3))
                for _ in range(num_orders):
                    order_counter += 1
                    hour = random.randint(8, 22)
                    order_date = date.replace(hour=hour, minute=random.randint(0, 59))
                    rows.append({
                        "date": order_date.isoformat(),
                        "order_id": f"ORD-{order_counter}",
                        "product_id": product["id"],
                        "product_name": product["name"],
                        "region": region,
                        "units_sold": max(1, units // num_orders),
                        "unit_price": round(unit_price, 2),
                        "revenue": round(revenue / num_orders, 2),
                    })
    return rows


def generate_marketing_data(base_date: datetime, days: int = 95) -> list[dict]:
    rows = []
    for day_offset in range(days):
        date = base_date + timedelta(days=day_offset)
        dow_factor = day_of_week_factor(day_offset, base_date)

        for campaign in CAMPAIGNS:
            if day_offset < campaign["start_day"] or day_offset > campaign["end_day"]:
                continue

            spend_multiplier = 1.0
            if day_offset > 70:
                spend_multiplier = max(0.3, 1.0 - 0.03 * (day_offset - 70))

            spend = campaign["base_spend"] * spend_multiplier * random.uniform(0.85, 1.15) / 30
            impressions = spend * random.uniform(12, 18)
            ctr = random.uniform(0.02, 0.05)
            clicks = impressions * ctr

            conversion_rate = random.uniform(0.03, 0.08)
            if day_offset > 70:
                conversion_rate *= 0.85

            conversions = clicks * conversion_rate

            for hour_slot in range(0, 24, 4):
                slot_factor = random.uniform(0.8, 1.2)
                slot_date = date.replace(hour=hour_slot)
                rows.append({
                    "date": slot_date.isoformat(),
                    "campaign_id": campaign["id"],
                    "campaign_name": campaign["name"],
                    "channel": campaign["channel"],
                    "spend": round(spend / 6 * slot_factor, 2),
                    "impressions": round(impressions / 6 * slot_factor),
                    "clicks": round(clicks / 6 * slot_factor),
                    "conversions": round(conversions / 6 * slot_factor),
                })
    return rows


def generate_inventory_data(base_date: datetime, days: int = 95) -> list[dict]:
    rows = []
    stock_levels = {p["id"]: p["base_daily_units"] * 25 for p in PRODUCTS}

    for day_offset in range(days):
        date = base_date + timedelta(days=day_offset)

        for product in PRODUCTS:
            pid = product["id"]
            if pid == 1:
                base_stock = laptop_stock_curve(day_offset) * product["base_daily_units"] * 25
            else:
                base_stock = stock_levels.get(pid, product["base_daily_units"] * 20)

            for wh in WAREHOUSES:
                wh_factor = random.uniform(0.8, 1.2)
                available = max(0, int(base_stock * wh_factor / len(WAREHOUSES)))
                stockout = available < product["base_daily_units"] * 0.1
                replenish_time = random.randint(1, 7)
                if pid == 1 and day_offset > 60:
                    replenish_time = random.randint(14, 21)

                for hour_slot in range(0, 24, 2):
                    slot_date = date.replace(hour=hour_slot)
                    jitter = random.randint(-5, 5)
                    rows.append({
                        "date": slot_date.isoformat(),
                        "product_id": pid,
                        "product_name": product["name"],
                        "warehouse": wh,
                        "stock_available": max(0, available + jitter),
                        "stockout": stockout,
                        "replenishment_time": replenish_time,
                    })
    return rows


def create_database(db_path: str):
    base_date = datetime(2025, 5, 25, tzinfo=timezone.utc)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            order_id TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            region TEXT NOT NULL,
            units_sold INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            revenue REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS marketing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            campaign_id TEXT NOT NULL,
            campaign_name TEXT NOT NULL,
            channel TEXT NOT NULL,
            spend REAL NOT NULL,
            impressions INTEGER NOT NULL,
            clicks INTEGER NOT NULL,
            conversions INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            warehouse TEXT NOT NULL,
            stock_available INTEGER NOT NULL,
            stockout INTEGER NOT NULL,
            replenishment_time INTEGER NOT NULL
        );
    """)

    print("Generating sales data...")
    sales = generate_sales_data(base_date)
    cur.executemany(
        "INSERT INTO sales (date, order_id, product_id, product_name, region, units_sold, unit_price, revenue) "
        "VALUES (:date, :order_id, :product_id, :product_name, :region, :units_sold, :unit_price, :revenue)",
        sales,
    )
    print(f"  Inserted {len(sales)} sales records")

    print("Generating marketing data...")
    marketing = generate_marketing_data(base_date)
    cur.executemany(
        "INSERT INTO marketing (date, campaign_id, campaign_name, channel, spend, impressions, clicks, conversions) "
        "VALUES (:date, :campaign_id, :campaign_name, :channel, :spend, :impressions, :clicks, :conversions)",
        marketing,
    )
    print(f"  Inserted {len(marketing)} marketing records")

    print("Generating inventory data...")
    inventory = generate_inventory_data(base_date)
    cur.executemany(
        "INSERT INTO inventory (date, product_id, product_name, warehouse, stock_available, stockout, replenishment_time) "
        "VALUES (:date, :product_id, :product_name, :warehouse, :stock_available, :stockout, :replenishment_time)",
        inventory,
    )
    print(f"  Inserted {len(inventory)} inventory records")

    conn.commit()
    conn.close()
    print(f"Database created at {db_path}")


if __name__ == "__main__":
    db_path = str(Path(__file__).parent.parent.parent / "data" / "bi_intelligence.db")
    create_database(db_path)
