import os
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

from activities.scraper_activity    import fetch_best_trade_route
from activities.ship_loader_activity import load_ships_from_file
from activities.db_activity         import upsert_route_to_db
from activities.uex_activity        import fetch_and_store_uex_data
from workflows.hauling_workflow      import HaulingWorkflow
from workflows.daily_update_workflow import DailyUpdateWorkflow
from workflows.uex_refresh_workflow import UexRefreshWorkflow
async def main():
    address = os.getenv("TEMPORAL_ADDRESS", "us-east-1.aws.api.temporal.io:7233")
    namespace = os.getenv("TEMPORAL_NAMESPACE", "quickstart-singbar00-e2d9a520.xfqa6")
    api_key = os.getenv("TEMPORAL_API_KEY")
    uex_key = os.getenv("UEX_KEY")

    print(f"addrress={address}")
    print(f"api_key={api_key}")

    client = await Client.connect(
        address,
        namespace=namespace,
        api_key=api_key,
        tls=True
    )

    worker = Worker(
        client,
        task_queue="hauling-task-queue",
        workflows=[DailyUpdateWorkflow, HaulingWorkflow,UexRefreshWorkflow],
        activities=[fetch_best_trade_route, upsert_route_to_db, load_ships_from_file,fetch_and_store_uex_data],
        max_concurrent_activities=5
    )
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
