.PHONY: install deploy test load-test clean help

STAGE ?= dev
PYTHON = python3
PIP    = pip3

help:
	@echo ""
	@echo "╔══════════════════════════════════════╗"
	@echo "║     NexusPlay — Commandes Make       ║"
	@echo "╠══════════════════════════════════════╣"
	@echo "║  make install     Install deps       ║"
	@echo "║  make deploy      Deploy on AWS      ║"
	@echo "║  make test        Test API (dev)     ║"
	@echo "║  make test STAGE=prod                ║"
	@echo "║  make load-test   Run Locust         ║"
	@echo "║  make clean       Clean temp files   ║"
	@echo "╚══════════════════════════════════════╝"
	@echo ""

install:
	@echo "📦 Installing dependencies..."
	$(PIP) install boto3 requests locust flake8

deploy:
	@echo "🚀 Deploying NexusPlay to AWS..."
	$(PYTHON) scripts/deploy.py

test:
	@echo "🧪 Testing stage: $(STAGE)"
	$(PYTHON) scripts/test_api.py $(STAGE)

test-all:
	@echo "🧪 Testing all stages..."
	$(PYTHON) scripts/test_api.py dev
	$(PYTHON) scripts/test_api.py test
	$(PYTHON) scripts/test_api.py prod

load-test:
	@echo "🔥 Starting load test..."
	@if [ ! -f config.json ]; then echo "❌ Run make deploy first"; exit 1; fi
	@API_ID=$$(python3 -c "import json; print(json.load(open('config.json'))['api_id'])"); \
	locust -f scripts/load_test.py \
		--host=https://$$API_ID.execute-api.us-east-1.amazonaws.com \
		--users=50 --spawn-rate=5 --run-time=60s --headless \
		--html=monitoring/load_test_report.html
	@echo "📊 Report saved: monitoring/load_test_report.html"

lint:
	@echo "🔍 Linting..."
	flake8 services/ scripts/ --max-line-length=120 \
		--ignore=E501,W503,E302,E241,E221,F401

clean:
	@echo "🧹 Cleaning..."
	find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -f /tmp/nexusplay-*.zip
	@echo "✅ Clean done"
