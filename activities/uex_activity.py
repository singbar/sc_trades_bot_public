import aiohttp
import os
import sqlite3
import datetime
from temporalio import activity


#Set Database Path
def get_db_path():
    return os.getenv("DB_PATH", "/mnt/routes/routes.db")
def get_api_key():
    return os.getenv("UEX_KEY")
#Activity to pull UEX data and update the database.
@activity.defn
async def fetch_and_store_uex_data() -> None:
    """Fetch all tradeports from UEX and upsert into SQLite."""
    BEARER_TOKEN = get_api_key()
    UEX_API_URL = "https://api.uexcorp.space/2.0/commodities_prices_all"   

    headers = {
        "Authorization": f"{BEARER_TOKEN}"
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(UEX_API_URL) as response:
            if response.status != 200:
                print(f"Error: {response.status}")
                return
            data = await response.json()  # or .text() if it's not JSON
            print(data)

    # Upsert into SQLite
    db_path = get_db_path()
    print(f"[EFS DEBUG] Opening database at: {db_path}")

    # Ensure parent directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
      CREATE TABLE IF NOT EXISTS trades (
        commodity      TEXT,
        location       TEXT,
        buy_price      REAL,
        sell_price     REAL,
        time           TEXT,
        PRIMARY KEY(commodity, location)
      )
    """)
    # Overwrite all old records in one go
    cur.execute("DELETE FROM trades")
    for port in data:
        commodity = port["commodity_name"]
        loc  = port["terminal_name"]
        buy  = port["buy_price"] or 0
        sell = port["sell_price"] or 0
        time = datetime.datetime.now().isoformat()
        cur.execute(
            "INSERT INTO trades (commodity, location, buy_price, sell_price, time) VALUES (?,?,?,?,?)",
            (commodity, loc, buy, sell, time),
        )
    conn.commit()
    conn.close()
