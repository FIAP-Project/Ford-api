.PHONY: help up down logs build sync test fmt lint clean

help:
	@echo "Ford API — common commands"
	@echo "  make up       - docker compose up --build"
	@echo "  make down     - docker compose down"
	@echo "  make logs     - tail logs from all services"
	@echo "  make build    - rebuild images"
	@echo "  make sync     - uv sync (workspace)"
	@echo "  make test     - run pytest across services"
	@echo "  make fmt      - format with ruff"
	@echo "  make lint     - lint with ruff"
	@echo "  make clean    - remove containers + volumes"

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

build:
	docker compose build

sync:
	uv sync

test:
	uv run pytest packages services -q

fmt:
	uv run ruff format packages services

lint:
	uv run ruff check packages services

clean:
	docker compose down -v
