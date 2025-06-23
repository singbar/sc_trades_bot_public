#This worklflow is an early version of the workflow used for local testing. Please use daily_update_workflow instead. 

from datetime import timedelta
from dataclasses import dataclass
from typing import Optional
from temporalio import workflow
from activities.scraper_activity    import fetch_best_trade_route
from temporalio.common import RetryPolicy

default_retry = RetryPolicy(
    initial_interval=timedelta(seconds=2),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=1),
    maximum_attempts=4,
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
class HaulingWorkflow:
    def __init__(self):
        self.state: Optional[HaulingMissionState] = None

    @workflow.run
    async def run(self, cargo_capacity: float, ship: str, investment: int):
        route = await workflow.execute_activity(
            fetch_best_trade_route,
            args=(ship, investment),
            start_to_close_timeout=timedelta(minutes=10),
            schedule_to_start_timeout=timedelta(minutes=15)
        )

        self.state = HaulingMissionState(
            origin=route["origin"],
            destination=route["destination"],
            profit_per_scu=route["profit"],
            cargo_loaded=0,
            cargo_capacity=cargo_capacity,
            ship_type=ship,
            investment=investment
        )

        workflow.logger.info(f"Starting haul: {self.state}")

        while not self.state.aborted:
            await workflow.sleep(10)
            workflow.logger.info(f"Hauling in progress... {self.state.cargo_loaded} SCU loaded")

    @workflow.signal
    async def load_cargo(self, amount: float):
        self.state.cargo_loaded += amount
        self.state.cargo_loaded = min(self.state.cargo_loaded, self.state.cargo_capacity)

    @workflow.signal
    async def abort_mission(self):
        self.state.aborted = True

    @workflow.query
    def get_mission_status(self) -> HaulingMissionState:
        return self.state

