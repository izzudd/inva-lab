COMPOSE = docker compose
API     = http://localhost:58102
GATEWAY = http://localhost:58103
DAY     = 2026-10-09

.PHONY: up down reset check demo settlement jobs entries psql logs

up:
	$(COMPOSE) up -d --build
	@printf "nunggu API siap"
	@until curl -sf $(API)/health >/dev/null 2>&1; do printf "."; sleep 1; done
	@echo " ok -> POST $(API)/jobs/reconcile (gateway: $(GATEWAY))"

down:
	$(COMPOSE) down

# Buang volume, seed ulang dari nol. Pakai ini kalau kamu mengubah skema.
reset:
	$(COMPOSE) down -v
	$(COMPOSE) up -d --build
	@until curl -sf $(API)/health >/dev/null 2>&1; do sleep 1; done
	@echo "database baru, siap dipakai"

check:
	python3 scripts/check.py

# Cerita lengkapnya: webhook malam itu, job rekonsiliasi paginya, lalu
# webhook yang telat nyusul.
demo:
	python3 scripts/demo.py $(DAY)

settlement:
	@curl -s "$(GATEWAY)/settlements/$(DAY)" | python3 -m json.tool

jobs:
	@curl -s $(API)/api/jobs | python3 -m json.tool

entries:
	@curl -s $(API)/api/accounts/1/entries | python3 -m json.tool

psql:
	docker compose exec db psql -U inva -d inva

logs:
	$(COMPOSE) logs -f api
