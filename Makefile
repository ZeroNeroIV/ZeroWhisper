COMPOSE_PROJECT_NAME ?= zerowhisper
COMPOSE_CMD = docker compose -p $(COMPOSE_PROJECT_NAME) -f docker/docker-compose.yml

.PHONY: dev build prod clean test backup logs

dev:
	$(COMPOSE_CMD) -f docker/docker-compose.override.yml up --build

build:
	$(COMPOSE_CMD) build

prod:
	$(COMPOSE_CMD) down --remove-orphans 2>/dev/null; $(COMPOSE_CMD) up -d

clean:
	$(COMPOSE_CMD) down -v --remove-orphans
	$(COMPOSE_CMD) build --no-cache

test:
	cd backend && python -m pytest tests/ -v

backup:
	cp data/zerowhisper.db data/zerowhisper.db.backup.$$(date +%Y%m%d_%H%M%S)

logs:
	$(COMPOSE_CMD) logs -f
