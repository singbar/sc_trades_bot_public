#!/usr/bin/env python3
import sqlite3
import sys
from datetime import datetime

DB_PATH = "routes.db"

def show_routes(ship_filter: str = None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if ship_filter:
        cur.execute("""
            SELECT ship, origin, destination, commodity, buy_price, profit, timestamp
            FROM routes
            WHERE ship = ?
            """, (ship_filter,))
    else:
        cur.execute("""
            SELECT ship, origin, destination, commodity, buy_price, profit, timestamp
            FROM routes
            ORDER BY ship
        """)

    rows = cur.fetchall()
    conn.close()

    # Print header
    header = f"{'Ship':20s} | {'Origin':15s} | {'Destination':15s} | {'Commodity':15s} | {'Buy Price':>10s} | {'Profit':>10s} | {'Timestamp'}"
    sep = "-" * len(header)
    print(header)
    print(sep)

    for ship, origin, dest, comm, buy, profit, ts in rows:
        # Format timestamp if it's ISO; else print raw
        try:
            ts_fmt = datetime.fromisoformat(ts).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            ts_fmt = ts
        print(f"{ship:20s} | {origin:15s} | {dest:15s} | {comm:15s} | {buy:10,d} | {profit:10,d} | {ts_fmt}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        show_routes(sys.argv[1])
    else:
        show_routes()
