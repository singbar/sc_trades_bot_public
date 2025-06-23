aws ecs register-task-definition --cli-input-json file://deployment/discord-task-def.json
aws ecs update-service --cluster sc-trades-cluster --service sc-trades-discord-service --task-definition sc-trades-discord
