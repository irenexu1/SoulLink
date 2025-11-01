dev:
	docker compose up -d --build
down:
	docker compose down -v
seed:
	node apps/desktop/src/index.ts
