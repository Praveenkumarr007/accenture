import sqlite3, os
db = os.path.abspath('data/bi_intelligence.db')
conn = sqlite3.connect(db)
for t in ['sales','marketing','inventory']:
    dcol = 'order_date' if t == 'sales' else 'date'
    row = conn.execute(f"SELECT MIN([{dcol}]), MAX([{dcol}]) FROM [{t}]").fetchone()
    n = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
    sample = conn.execute(f"SELECT DISTINCT [{dcol}] FROM [{t}] LIMIT 5").fetchall()
    print(f"{t}: {n} rows | min={row[0]} max={row[1]} | distinct sample={[s[0] for s in sample]}")
conn.close()