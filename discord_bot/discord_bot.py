import os
import json
import sqlite3
import logging
import discord
from discord import app_commands

# -------- Configuration --------
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN environment variable not set")

# SQLite database paths (routes and UEX data)
ROUTES_DB_PATH = os.getenv("DB_PATH", "/mnt/routes/routes.db")
UEX_DB_PATH    = os.getenv("UEX_DB_PATH", "/mnt/data/trade_data.db")

# Load ship names for autocompletion and validation
CURRENT_DIR = os.path.dirname(__file__)
SHIPS_FILE  = os.path.join(CURRENT_DIR, "ships.json")
with open(SHIPS_FILE, "r", encoding="utf-8") as f:
    ships_data = json.load(f)
SHIP_NAMES = [ship["name"] for ship in ships_data]

# -------- Logging --------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sc-trades-bot")

# -------- Discord Client & Command Tree --------
intents = discord.Intents.default()
client  = discord.Client(intents=intents)
tree    = app_commands.CommandTree(client)

# -------- Event Handlers --------
@client.event
async def on_ready():
    # Syncing globally; for dev you can pass guild=discord.Object(id=GUILD_ID)
    await tree.sync()
    logger.info(f"Logged in as {client.user} (ID: {client.user.id})")
    logger.info("Slash commands synced.")

# -------- Helper Functions --------
async def query_routes(ship: str, limit: int = 5):
    conn = sqlite3.connect(ROUTES_DB_PATH)
    cur  = conn.cursor()
    cur.execute(
        """
        SELECT origin, destination, commodity, buy_price, profit, timestamp
        FROM routes
        WHERE ship = ?
        ORDER BY profit DESC
        LIMIT ?
        """, (ship, limit)
    )
    rows = cur.fetchall()
    conn.close()
    return rows

async def query_commodity(commodity: str):
    code = commodity.upper().replace(" ", "_")
    conn = sqlite3.connect(UEX_DB_PATH)
    cur  = conn.cursor()
    cur.execute(
        "SELECT location, buy_price FROM trades WHERE commodity_code = ? ORDER BY buy_price DESC LIMIT 1",
        (code,)
    )
    best_buy = cur.fetchone() or ("—", 0)
    cur.execute(
        "SELECT location, sell_price FROM trades WHERE commodity_code = ? ORDER BY sell_price ASC LIMIT 1",
        (code,)
    )
    best_sell = cur.fetchone() or ("—", 0)
    conn.close()
    return code, best_buy, best_sell

# -------- Autocomplete for /routes --------
async def ship_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> list[app_commands.Choice[str]]:
    # filter by substring, max 25
    suggestions = [
        app_commands.Choice(name=name, value=name)
        for name in SHIP_NAMES
        if current.lower() in name.lower()
    ][:25]
    return suggestions

# -------- Slash Commands --------
@tree.command(
    name="routes",
    description="Get top trade routes for a specific ship"
)
@app_commands.describe(
    ship="Name of the ship (e.g. Caterpillar)",
    limit="Number of top routes to return"
)
@app_commands.autocomplete(ship=ship_autocomplete)
async def routes(
    interaction: discord.Interaction,
    ship: str,
    limit: int = 5
):
    # Validate
    if ship not in SHIP_NAMES:
        await interaction.response.send_message(
            f"🚫 Ship '{ship}' not recognized. Please choose from the list.",
            ephemeral=True
        )
        return

    await interaction.response.defer()
    try:
        rows = await query_routes(ship, limit)
    except Exception:
        logger.exception("Failed to query routes DB")
        return await interaction.followup.send(
            "⚠️ Could not retrieve routes. Please try again later.",
            ephemeral=True
        )

    if not rows:
        return await interaction.followup.send(
            f"No route data found for **{ship}**.",
            ephemeral=True
        )

    embed = discord.Embed(
        title=f"Top {limit} trade routes for {ship}",
        color=discord.Color.green()
    )
    for idx, (origin, destination, commodity, buy_price, profit, timestamp) in enumerate(rows, 1):
        embed.add_field(
            name=f"{idx}. {origin} ➔ {destination}",
            value=(
                f"Commodity: **{commodity}**\n"
                f"Buy Price: ¤{buy_price:,} UEC\n"
                f"Profit: ¤{profit:,} UEC\n"
                f"Last updated: {timestamp}"
            ),
            inline=False
        )
    await interaction.followup.send(embed=embed)

@tree.command(
    name="commodity",
    description="Get best buy/sell locations for a commodity (UEX data)"
)
@app_commands.describe(
    commodity="Commodity code or name (e.g. QUANTUM_FUEL)"
)
async def commodity(
    interaction: discord.Interaction,
    commodity: str
):
    await interaction.response.defer()
    try:
        code, (buy_loc, buy_price), (sell_loc, sell_price) = await query_commodity(commodity)
    except Exception:
        logger.exception("Failed to query commodity DB")
        return await interaction.followup.send(
            "⚠️ Could not retrieve commodity pricing. Please try again later.",
            ephemeral=True
        )

    embed = discord.Embed(
        title=f"UEX Prices for {code}",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="🔼 Best place to sell",
        value=f"**{buy_loc}** at ¤{buy_price:,} UEC",
        inline=False
    )
    embed.add_field(
        name="🔽 Best place to buy",
        value=f"**{sell_loc}** at ¤{sell_price:,} UEC",
        inline=False
    )
    await interaction.followup.send(embed=embed)

# -------- Run Bot --------
if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
