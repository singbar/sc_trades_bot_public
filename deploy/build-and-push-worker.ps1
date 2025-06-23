docker build -t sc-trades-worker:latest -f worker/Dockerfile .
docker tag sc-trades-worker:latest 260119304722.dkr.ecr.us-east-1.amazonaws.com/sc-trades-worker:latest
docker push 260119304722.dkr.ecr.us-east-1.amazonaws.com/sc-trades-worker:latest
