docker build -t sc-trades-discord:latest -f discord_bot/Dockerfile .
docker tag sc-trades-discord:latest 260119304722.dkr.ecr.us-east-1.amazonaws.com/sc-trades-discord:latest
docker push 260119304722.dkr.ecr.us-east-1.amazonaws.com/sc-trades-discord:latest
