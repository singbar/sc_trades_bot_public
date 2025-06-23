import os
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
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    api_key = os.getenv("TEMPORAL_API_KEY","YOUR_TEMPORAL_KEY")

    client = await Client.connect(
        address,
        namespace=namespace,
        api_key=api_key,
        tls=True
    )

    print("\nSelect option:")
    print("1. Trigger Daily Update Workflow (once)")
    print("2. Start Daily Update Workflow (recurring)")


    choice = input("> ")

    if choice == "1":
        handle = await client.start_workflow(
            DailyUpdateWorkflow,
            id=f"daily-update-once-{uuid.uuid4()}",
            task_queue="hauling-task-queue"
        )
        print(f"Started Daily Update Workflow once: {handle.id}")

    elif choice == "2":
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

    else:
        print("Invalid selection.")


if __name__ == "__main__":
    asyncio.run(main())
