.PHONY: dev build prod clean test backup logs

dev:
	docker compose -f docker/docker-compose.yml -f docker/docker-compose.override.yml up --build

build:
	docker compose -f docker/docker-compose.yml build

prod:
	docker compose -f docker/docker-compose.yml up -d

clean:
	docker compose -f docker/docker-compose.yml down -v
	docker compose -f docker/docker-compose.yml build --no-cache

test:
	cd backend && python -m pytest tests/ -v

backup:
	cp data/zerowhisper.db data/zerowhisper.db.backup.$$(date +%Y%m%d_%H%M%S)

logs:
	docker compose -f docker/docker-compose.yml logs -f
