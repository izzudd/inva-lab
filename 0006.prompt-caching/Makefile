.PHONY: check demo bench what-changes run help

check:
	python3 scripts/check.py

demo:
	python3 scripts/demo.py

# python3 scripts/bench.py            -> first ticket, turn by turn
# python3 scripts/bench.py T-1043     -> one ticket
bench:
	python3 scripts/bench.py $(ID)

# python3 scripts/what_changes.py            -> first ticket, turns 1 and 2
# python3 scripts/what_changes.py T-1043 3    -> a ticket and a turn
what-changes:
	python3 scripts/what_changes.py $(ID) $(TURN)

run:
	python3 agent/loop.py

help:
	@echo "make demo     -> what the bill looks like now, per ticket"
	@echo "make bench    -> the same loop turn by turn (ID=T-1043 for one ticket)"
	@echo "make what-changes  -> two consecutive requests, block by block"
	@echo "make check    -> this lab's target"
	@echo "make run      -> run the loop once"
