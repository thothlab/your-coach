.PHONY: install dev test lint fmt build db-up db-down clean

PY := backend/.venv/bin/python
PIP := backend/.venv/bin/pip

install:
	cd backend && python3 -m venv .venv && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -e ".[dev]"
	cd mini-app && npm install

db-up:
	docker compose up -d db
	@echo "Waiting for Postgres..."
	@for i in 1 2 3 4 5 6 7 8 9 10; do docker compose exec -T db pg_isready -U trainbeat >/dev/null 2>&1 && exit 0; sleep 1; done; \
		echo "Postgres did not become ready" >&2; exit 1

db-down:
	docker compose down

dev: db-up
	@echo "Starting backend on :8000 and Mini-App on :5173 (Ctrl-C to stop both)"
	@trap 'kill %1 %2 2>/dev/null' EXIT; \
		(cd backend && $(PY) -m trainbeat) & \
		(cd mini-app && npm run dev) & \
		wait

test:
	cd backend && .venv/bin/pytest -q
	cd mini-app && npm run test

lint:
	cd backend && .venv/bin/ruff check src tests
	cd mini-app && npm run lint

fmt:
	cd backend && .venv/bin/ruff format src tests
	cd mini-app && npm run format

build:
	cd mini-app && npm run build && npm run check-size

clean:
	rm -rf backend/.venv backend/.pytest_cache backend/.ruff_cache backend/src/trainbeat.egg-info
	rm -rf mini-app/node_modules mini-app/dist mini-app/.vite
