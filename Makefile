.PHONY: dev down test seed migrate
dev:
	docker compose up --build
down:
	docker compose down
test:
	cd apps/api && .venv/bin/pytest --cov=app
	cd apps/web && npm test
migrate:
	cd apps/api && .venv/bin/alembic upgrade head
seed:
	cd apps/api && .venv/bin/python -m app.data.seed

