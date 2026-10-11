FILE ?= data/pendaftar.csv

.PHONY: check demo impor bantu

check:
	python3 scripts/check.py

demo:
	python3 scripts/demo.py

# Coba importer pada file mana pun:  make impor FILE=data/contoh/beberapa.csv
impor:
	@python3 app/impor.py $(FILE)

bantu:
	@echo "make check                       -> nilai lab ini"
	@echo "make demo                        -> yang dilihat pengguna di tiap file contoh"
	@echo "make impor FILE=<file.csv>       -> jalankan importer sekali"
