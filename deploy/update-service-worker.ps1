aws ecs register-task-definition --cli-input-json file://deploy/worker-task-def.json
aws ecs update-service --cluster sc-trades-cluster --service sc-trades-worker-service --task-definition sc-trades-worker
