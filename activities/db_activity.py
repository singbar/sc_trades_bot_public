import os
import sqlite3
from temporalio import activity

# Always use EFS path inside ECS/Fargate
def get_db_path():
    return os.getenv("DB_PATH", "/mnt/routes/routes.db")

@activity.defn
async def upsert_route_to_db(ship, route):
    """
    Insert or update the best trade route.
    Expects payload as [ship, route_dict]
    """
    db_path = get_db_path()
    print(f"[EFS DEBUG] Opening database at: {db_path}")

    # Ensure parent directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Create table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS routes (
                ship TEXT PRIMARY KEY,
                origin TEXT,
                destination TEXT,
                commodity TEXT,
                buy_price INTEGER,
                profit INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Perform upsert
        cur.execute("""
            INSERT INTO routes (ship, origin, destination, commodity, buy_price, profit)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(ship) DO UPDATE SET
                origin      = excluded.origin,
                destination = excluded.destination,
                commodity   = excluded.commodity,
                buy_price   = excluded.buy_price,
                profit      = excluded.profit,
                timestamp   = CURRENT_TIMESTAMP
        """, (
            ship,
            route["origin"],
            route["destination"],
            route["commodity"],
            route["buy_price"],
            route["profit"],
        ))

        conn.commit()
        print(f"[EFS DEBUG] Successfully upserted route for ship: {ship}")

    except Exception as e:
        print(f"[EFS ERROR] Failed to upsert route for ship {ship}: {e}")
        raise  # This will fail the activity and allow Temporal retries

    finally:
        if 'conn' in locals():
            conn.close()
