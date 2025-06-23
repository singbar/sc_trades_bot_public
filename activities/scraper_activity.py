import asyncio
import json
import sqlite3
import re
from datetime import timedelta
from temporalio import activity
from playwright.async_api import async_playwright
from urllib.parse import quote

@activity.defn
async def fetch_best_trade_route(ship, investment) -> dict:
    encoded_ship =quote(ship, safe='')
    url = f"https://sc-trade.tools/trade-routes?q=%7B%22ship%22:%22{ship}%22,%22investment%22:{investment},%22profitType%22:%22pure%22,%22allowWaitTimes%22:false%7D"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(url, wait_until='networkidle', timeout=60000)
        await page.wait_for_timeout(3000)

        full_html = await page.content()
        with open("page_dump.html", "w", encoding="utf-8") as f:
            f.write(full_html)
        print("Page HTML dumped for inspection.")

        route_selector = "div.card"
        await page.wait_for_selector(route_selector, timeout=60000)
        route_cards = await page.query_selector_all(route_selector)

        if not route_cards:
            await browser.close()
            raise activity.ApplicationError("No routes found. Site layout may have changed.")

        first_card = route_cards[0]

        # ✅ Extract both transaction panels: buy and sell
        transaction_panels = await first_card.query_selector_all("div.transaction")

        # ✅ Extract origin
        origin_elem = await transaction_panels[0].query_selector("h4.card-title a")
        origin = (await origin_elem.inner_text()).strip()

        # ✅ Extract destination
        destination_elem = await transaction_panels[1].query_selector("h4.card-title a")
        destination = (await destination_elem.inner_text()).strip()

        # ✅ Use your regex parsing for prices & commodities
        full_text = await first_card.inner_text()
        parsed = parse_route_card_text(full_text)

        await browser.close()

        result = {
            "origin": origin,
            "destination": destination,
            "commodity": parsed["commodity"],
            "buy_price": parsed["buy_price"],
            "profit": parsed["profit"]
        }

        return result

def parse_route_card_text(text: str) -> dict:
    buy_match = re.search(r"Buy \d+ SCU of (.*?) for ¤([\d,]+)", text)
    commodity = buy_match.group(1) if buy_match else "UNKNOWN"
    buy_price = int(buy_match.group(2).replace(",", "")) if buy_match else 0
    sell_match = re.search(r"Sell for ¤([\d,]+)", text)
    sell_price = int(sell_match.group(1).replace(",", "")) if sell_match else 0

    return {
        "commodity": commodity,
        "buy_price": buy_price,
        "sell_price": sell_price,
        "profit": sell_price - buy_price
    }



