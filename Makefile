.PHONY: up down logs backend-test frontend-test test

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

backend-test:
	docker compose run --rm backend pytest

frontend-test:
	docker compose run --rm frontend npm run test:run

test: backend-test frontend-test

