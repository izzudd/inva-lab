COMPOSE = docker compose
API     = http://localhost:58000

.PHONY: up down reset bench check logs psql shell

up:
	$(COMPOSE) up -d --build
	@printf "nunggu API siap"
	@until curl -sf $(API)/health >/dev/null 2>&1; do printf "."; sleep 1; done
	@echo " ok -> $(API)/api/posts?limit=50"

down:
	$(COMPOSE) down

# Buang volume, seed ulang dari nol. Pakai ini kalau kalian mengubah schema.
reset:
	$(COMPOSE) down -v
	$(COMPOSE) up -d --build
	@until curl -sf $(API)/health >/dev/null 2>&1; do sleep 1; done

bench:
	python3 scripts/bench.py

check:
	python3 scripts/check.py

logs:
	$(COMPOSE) logs -f api

psql:
	docker compose exec db psql -U inva -d inva

explain:
	@curl -s "$(API)/api/posts?limit=50" -o /dev/null -D - | grep -i x-db-query-count
