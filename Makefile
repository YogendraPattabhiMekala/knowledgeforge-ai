up:
	docker compose up --build -d
down:
	docker compose down
seed:
	docker compose exec api python -m app.seed
migrate:
	docker compose run --rm migrate
logs:
	docker compose logs -f api worker
test-api:
	cd apps/api && python -m pytest -q
test-web:
	cd apps/web && npm run typecheck && npm test
test-e2e:
	cd apps/web && npm run test:e2e
contracts:
	cd apps/api && python ../../scripts/export_openapi.py
demo:
	bash ./scripts/demo.sh
release:
	python scripts/release.py
