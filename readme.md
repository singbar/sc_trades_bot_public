# Star Citizen Discord Bot for Trade Routes

A Temporal-based workflow system for generating hauling routes using SC Trade Tools.

## Setup

1. Install Temporal dev server:

docker run --rm -it -p 7233:7233 temporalio/auto-start-dev


2. Setup virtualenv:

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install


3. Start the worker:

python worker.py

4. Use `test_harness.py` to start and test workflows.

5. Use `discord_bot.py` after inserting your Discord bot token.

