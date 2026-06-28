.PHONY: install dev dev-backend dev-frontend test lint clean

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

dev:
	@echo "Starting Nexus..."
	@(cd backend && uvicorn app.main:app --reload --port 8000 & \
	  cd frontend && npm run dev & \
	  wait)

test:
	cd backend && pytest tests/ -v

lint:
	cd backend && ruff check app/
	cd frontend && npm run lint

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
