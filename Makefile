# =========================================================
# Makefile for ML Quant Strategies (Dev Container compatible)
#
# This Makefile is "smart" and works on both:
# (A) Inside the Dev Container / CI (Linux)
# (B) On the Host OS (Windows/Mac)
#
# It detects where it's running and routes commands
# into the container if necessary.
# =========================================================

# --- Tool Definitions ---
DEVCONTAINER_CLI := npx devcontainer

# --- Environment Detection ---
ifeq ($(OS),Windows_NT)
	IS_HOST_OS := true
else
	IS_HOST_OS := false
	ifneq ($(shell test -f /.dockerenv && echo true), true)
		ifeq ($(CI), true)
			IS_IN_CONTAINER_OR_CI := true
		else
			IS_IN_CONTAINER_OR_CI := false
		endif
	else
		IS_IN_CONTAINER_OR_CI := true
	endif
endif

ifeq ($(IS_HOST_OS), true)
	IS_IN_CONTAINER_OR_CI := false
endif

# =========================================================
# SHARED TARGETS (All .PHONY declarations in one place)
# =========================================================
.PHONY: help sync fetch chart lint format fmt format-check \
		generate-experiments label split full-pipeline \
		kfold kfold-report up ssh exec

# =========================================================
# (A) CONTAINER / CI LOGIC
# =========================================================
ifeq ($(IS_IN_CONTAINER_OR_CI), true)

help:
	@echo "=== Inside Container ==="
	@echo ""
	@echo "Data Management:"
	@echo "  sync                  - Sync Python dependencies"
	@echo "  fetch                 - Fetch daily stock data"
	@echo "  chart ticker=TSLA     - Generate chart for ticker"
	@echo ""
	@echo "Experiment Pipeline:"
	@echo "  generate-experiments  - Generate config for all tickers"
	@echo "  label ticker=TSLA     - Label data for specific ticker"
	@echo "  split ticker=TSLA     - Split data for specific ticker"
	@echo "  full-pipeline         - Run complete pipeline (all tickers)"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint                  - Run linter (ruff check)"
	@echo "  format / fmt          - Format code (ruff format)"
	@echo "  format-check          - Check formatting (CI)"
	@echo ""
	@echo "Data Analysis (Deprecated):"
	@echo "  kfold                 - K-Fold data splitting"
	@echo "  kfold-report          - K-Fold split report"

sync:
	@echo "📦 Syncing Python dependencies..."
	uv sync --all-extras

fetch:
	@echo "📊 Fetching stock data..."
	uv run python src/get_data/fetcher.py

chart:
	@echo "📈 Generating chart for $(ticker)..."
	uv run python src/get_data/visualizer.py --ticker $(ticker)

lint:
	@echo "🔍 Running linter..."
	uv run ruff check src/

format fmt:
	@echo "✨ Formatting code..."
	uv run ruff format src/

format-check:
	@echo "✅ Checking code formatting..."
	uv run ruff format --check src/

generate-experiments:
	@echo "📝 Generating experiment configs for all tickers..."
	@mkdir -p data/experiments
	uv run python src/core/generate_ticker_yaml.py \
	  --config src/config_universe.yaml \
	  --template src/data_split_labeling.yaml \
	  --output-dir data/experiments/
	@echo "✅ Generated experiment configs in data/experiments/"

label:
	@if [ -z "$(ticker)" ]; then \
	  echo "❌ Usage: make label ticker=TSLA"; \
	  exit 1; \
	fi
	@echo "🏷️  Labeling data for $(ticker)..."
	uv run python src/core/labeling/triple_barrier_labeler.py \
	  --config data/experiments/$(ticker)_experiment.yaml

full-pipeline: generate-experiments
	@echo "🚀 Running full pipeline for all tickers..."
	@for config in data/experiments/*_experiment.json; do \
	  ticker=$$(basename $$config _experiment.json); \
	  echo ""; \
	  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	  echo "Processing: $$ticker"; \
	  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	  echo "Step 1/2: Labeling..."; \
	  uv run python src/core/labeling/triple_barrier_labeler.py --config $$config || exit 1; \
	  echo "Step 2/2: Splitting..."; \
	  uv run python src/core/data_splitter.py --config $$config || exit 1; \
	  echo "✅ $$ticker completed"; \
	done
	@echo ""
	@echo "🎉 Full pipeline completed for all tickers!"

kfold:
	@echo "⚠️  'make kfold' is deprecated."
	@echo "    Use 'make full-pipeline' for all tickers"
	@echo "    or 'make split ticker=TSLA' for specific ticker."
	@exit 1

kfold-report:
	@echo "⚠️  'make kfold-report' is deprecated."
	@echo "    Split results are in data/splits/{TICKER}/fold_*/stats.json"
	@exit 1

up:
	@echo "❌ 'make up' is only available from Host OS."
	@exit 1

ssh:
	@echo "❌ 'make ssh' is only available from Host OS."
	@exit 1

exec:
	@echo "❌ 'make exec' is only available from Host OS."
	@exit 1

# =========================================================
# (B) HOST OS LOGIC
# =========================================================
else

help:
	@echo "=== On Host OS ==="
	@echo ""
	@echo "Container Management:"
	@echo "  up                    - Build and start Dev Container"
	@echo "  ssh                   - Open shell in container"
	@echo "  exec CMD=...          - Execute command in container"
	@echo ""
	@echo "All other targets will relay into the container:"
	@echo "  make sync, fetch, chart, lint, format, full-pipeline, etc."

up:
	@echo "🐳 Building Dev Container and running 'make sync'..."
	$(DEVCONTAINER_CLI) up --workspace-folder .
	@echo "✅ Container is ready."

ssh:
	@echo "🔌 Opening shell in Dev Container..."
	$(DEVCONTAINER_CLI) exec --workspace-folder . /bin/bash

exec:
	@echo "⚙️  Executing command in Dev Container: $(CMD)"
	$(DEVCONTAINER_CLI) exec --workspace-folder . $(CMD)

# Relay all other targets into the container
sync fetch chart lint format fmt format-check \
generate-experiments label split full-pipeline \
kfold kfold-report:
	@$(DEVCONTAINER_CLI) exec --workspace-folder . make $@ $(ARGS)

endif