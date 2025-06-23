from datetime import timedelta
from dataclasses import dataclass
from typing import Optional
from temporalio import workflow
from activities.scraper_activity    import fetch_best_trade_route
from activities.db_activity         import upsert_route_to_db
from activities.ship_loader_activity import load_ships_from_file
from temporalio.common import RetryPolicy
import json
import asyncio

default_retry = RetryPolicy(
    initial_interval=timedelta(seconds=2),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=2),
    maximum_attempts=5,
)

@dataclass
class HaulingMissionState:
    origin: str
    destination: str
    profit_per_scu: float
    cargo_loaded: float
    cargo_capacity: float
    ship_type: str
    investment: int
    aborted: bool = False

@workflow.defn
class DailyUpdateWorkflow:

    @workflow.run
    async def run(self,input_data):
        ships = await workflow.execute_activity(
            load_ships_from_file,
            start_to_close_timeout=timedelta(seconds=10)
        )

        tasks = []
        for ship_entry in ships:
            ship = ship_entry['name']
            investment = 5_000_000

            async def process_single_ship(ship=ship, investment=investment):
                route = await workflow.execute_activity(
                    fetch_best_trade_route,
                    args=(ship, investment),
                    retry_policy=default_retry,
                    start_to_close_timeout=timedelta(seconds=90)
                )

                await workflow.execute_activity(
                    upsert_route_to_db,
                    args=(ship, route),
                    start_to_close_timeout=timedelta(seconds=30)
                )

            tasks.append(process_single_ship())

        await asyncio.gather(*tasks)

        workflow.logger.info("Daily update complete")