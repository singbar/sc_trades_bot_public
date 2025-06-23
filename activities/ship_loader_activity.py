import asyncio
import json
import sqlite3
import re
import os
from datetime import timedelta
from temporalio import activity
from playwright.async_api import async_playwright
from urllib.parse import quote


@activity.defn
async def load_ships_from_file() -> list:
    # Get directory where this file (the activity code) lives
    current_dir = os.path.dirname(__file__)

    # Build full path to ships.json relative to current file
    file_path = os.path.join(current_dir, '../discord_bot/ships.json')

    # Normalize path (works on Windows + Linux)
    file_path = os.path.abspath(file_path)


    with open(file_path, "r") as f:
        ships = json.load(f)
    return ships