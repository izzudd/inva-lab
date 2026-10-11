COMPOSE = docker compose
API     = http://localhost:58100
ACCOUNT = 1

.PHONY: up down reset check replay entries probe psql logs

up:
	$(COMPOSE) up -d --build
	@printf "nunggu API siap"
	@until curl -sf $(API)/health >/dev/null 2>&1; do printf "."; sleep 1; done
	@echo " ok -> POST $(API)/webhooks/payments"

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

# Putar ulang satu event, seperti yang dilakukan gateway.
replay:
	python3 scripts/replay.py

entries:
	@curl -s $(API)/api/accounts/$(ACCOUNT) | python3 -m json.tool
	@curl -s $(API)/api/accounts/$(ACCOUNT)/entries | python3 -m json.tool

psql:
	docker compose exec db psql -U inva -d inva

# Bukti untuk klaim di SOLUSI.md: apa yang dilakukan ON CONFLICT DO NOTHING
# waktu barisnya masih dipegang transaksi lain.
probe:
	docker compose cp scripts/probe_on_conflict.py api:/tmp/probe.py
	docker compose exec -T api python3 /tmp/probe.py

logs:
	$(COMPOSE) logs -f api
