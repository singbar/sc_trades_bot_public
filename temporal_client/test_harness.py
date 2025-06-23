import os
import workflows
from workflows.hauling_workflow import HaulingWorkflow
from workflows.daily_update_workflow import DailyUpdateWorkflow
from workflows.uex_refresh_workflow import UexRefreshWorkflow
from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleIntervalSpec,
    ScheduleSpec,
    ScheduleState,
)
import asyncio
import uuid
from datetime import timedelta

async def main():
    address = os.getenv("TEMPORAL_ADDRESS", "us-east-1.aws.api.temporal.io:7233")
    namespace = os.getenv("TEMPORAL_NAMESPACE", "quickstart-singbar00-e2d9a520.xfqa6")
    api_key = os.getenv("TEMPORAL_API_KEY","eyJhbGciOiJFUzI1NiIsICJraWQiOiJXdnR3YUEifQ.eyJhY2NvdW50X2lkIjoieGZxYTYiLCAiYXVkIjpbInRlbXBvcmFsLmlvIl0sICJleHAiOjE3NTI2MDY4NTAsICJpc3MiOiJ0ZW1wb3JhbC5pbyIsICJqdGkiOiJKclVwQjc5YTVJSGt3MVAzSFpNQzNNWkJMWXBtZGpkZiIsICJrZXlfaWQiOiJKclVwQjc5YTVJSGt3MVAzSFpNQzNNWkJMWXBtZGpkZiIsICJzdWIiOiIyMzQwZTdiMzUxM2Q0MmJlODE5MmI1N2ZhNTAzZDI4NyJ9.vwSJ0y7mNNwqXki6JneVgCBLR773TgzyPk6Grfc6DLfQoQ55DyOnLRY0N5Upml7AqtZZYvhtND5UlZj06MMTvw")

    client = await Client.connect(
        address,
        namespace=namespace,
        api_key=api_key,
        tls=True
    )

    print("\nSelect option:")
    print("1. Start Hauling Workflow")
    print("2. Load Cargo")
    print("3. Abort Mission")
    print("4. Get Mission Status")
    print("5. Trigger Daily Update Workflow (once)")
    print("6. Start Daily Update Workflow (cron)")
    print("7. Start UEX update process (once)")

    choice = input("> ")

    if choice == "1":
        ship = input("Ship type: ")
        investment = int(input("Initial investment: "))
        cargo_capacity = int(input("Cargo capacity: "))

        handle = await client.start_workflow(
            HaulingWorkflow,
            args=(cargo_capacity, ship, investment),
            id=f"hauling-workflow-{uuid.uuid4()}",
            task_queue="hauling-task-queue"
        )
        print(f"Started Hauling Workflow: {handle.id}")

    elif choice == "2":
        wid = input("Workflow ID to load cargo: ")
        handle = client.get_workflow_handle(wid)
        amount = float(input("Enter cargo amount: "))
        await handle.signal("load_cargo", amount)
        print("Cargo loaded.")

    elif choice == "3":
        wid = input("Workflow ID to abort: ")
        handle = client.get_workflow_handle(wid)
        await handle.signal("abort_mission")
        print("Mission aborted.")

    elif choice == "4":
        wid = input("Workflow ID to query: ")
        handle = client.get_workflow_handle(wid)
        state = await handle.query("get_mission_status")
        print("Current state:", state)

    elif choice == "5":
        handle = await client.start_workflow(
            DailyUpdateWorkflow,
            id=f"daily-update-once-{uuid.uuid4()}",
            task_queue="hauling-task-queue"
        )
        print(f"Started Daily Update Workflow once: {handle.id}")

    elif choice == "6":
        handle = await client.create_schedule(
            "routes-update-scheduled",
            Schedule(
                action=ScheduleActionStartWorkflow(
                    DailyUpdateWorkflow.run,
                    "my schedule arg",
                    id=f"Scheduled-12h-update-{uuid.uuid4()}",
                    task_queue="hauling-task-queue"

                ),
                spec=ScheduleSpec(
                    intervals=[ScheduleIntervalSpec(every=timedelta(hours=12))]
                )
            )
        )

    elif choice == "7":
        handle = await client.start_workflow(
            UexRefreshWorkflow,
            id=f"uex-refresh-once-{uuid.uuid4()}",
            task_queue="hauling-task-queue"
        )
        print(f"Started UEX Update Workflow once: {handle.id}")


    else:
        print("Invalid selection.")


if __name__ == "__main__":
    asyncio.run(main())
