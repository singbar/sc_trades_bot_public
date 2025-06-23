from datetime import timedelta
from temporalio import workflow
from activities.uex_activity import fetch_and_store_uex_data

@workflow.defn
class UexRefreshWorkflow:
    """Runs fetch_and_store_uex_data every 10 minutes forever."""
    @workflow.run
    async def run(self) -> None:

        await workflow.execute_activity(
            fetch_and_store_uex_data,
            start_to_close_timeout=timedelta(seconds=60),
        )