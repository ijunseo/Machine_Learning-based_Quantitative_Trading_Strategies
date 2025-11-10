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
# Use npx to reliably find the devcontainer CLI on Host OS
# (Solves Windows PATH issues)
DEVCONTAINER_CLI := npx devcontainer

# --- Environment Detection (Robust Cross-Platform) ---
# Check 1: Are we on Windows Host OS?
ifeq ($(OS),Windows_NT)
    IS_HOST_OS := true
else
    # We are on a Unix-like system (Linux, Mac, Container, CI)
    IS_HOST_OS := false
    
    # Check 2: Are we specifically INSIDE the container or in CI?
    # We use `test -f /.dockerenv` which is reliable inside containers.
    # We add CI check for GitHub Actions.
    ifneq ($(shell test -f /.dockerenv && echo true), true)
        ifeq ($(CI), true)
            # We are in CI
            IS_IN_CONTAINER_OR_CI := true
        else
            # We are on Mac/Linux Host OS, not in container
            IS_IN_CONTAINER_OR_CI := false
        endif
    else
        # We are inside the Dev Container
        IS_IN_CONTAINER_OR_CI := true
    endif
endif

# Final Logic:
# If OS is Windows, we are definitely HOST.
# If OS is Unix, use the detailed check.
ifeq ($(IS_HOST_OS), true)
    IS_IN_CONTAINER_OR_CI := false
endif

# --- Target Definitions ---

# (A) CONTAINER / CI LOGIC
# Executed if running INSIDE the Dev Container or in GitHub Actions CI
ifeq ($(IS_IN_CONTAINER_OR_CI), true)

.PHONY: help sync fetch chart lint format fmt format-check up ssh kfold kfold-report

help:
	@echo "--- Inside Container ---"
	@echo "Usage: make [target]"
	@echo "Targets:"
	@echo "  sync          - Sync Python dependencies (uv sync --all-extras)"
	@echo "  fetch         - Fetch daily stock data"
	@echo "  chart ticker= - Generate a chart (e.g., make chart ticker=TSLA)"
	@echo "  lint          - Run linter (ruff check)"
	@echo "  format        - Format code (ruff format)"
	@echo "  fmt           - Alias for format"
	@echo "  format-check  - (CI) Check formatting without changing files"
	@echo "  kfold         - Run K-Fold data splitting"
	@echo "  kfold-report  - Show K-Fold split report"

sync:
	@echo "Syncing Python dependencies inside container based on 'uv.lock' (including dev)..."
	uv sync --all-extras
	@echo "Sync complete."

fetch:
	uv run python src/get_data/fetcher.py

chart:
	@echo "Generating chart for $(ticker)..."
	uv run python src/get_data/visualizer.py --ticker $(ticker)

lint:
	@echo "Running Linter..."
	uv run ruff check .

format:
	@echo "Running Formatter..."
	uv run ruff format .

fmt: format

format-check:
	@echo "Running Formatter Check (CI)..."
	uv run ruff format --check .

# データ分割コマンド
.PHONY: kfold
kfold:
	@echo "🔀 Running K-Fold data splitting..."
	uv run python -m src.data_split.split

.PHONY: kfold-report
kfold-report:
	@echo "📊 Showing K-Fold split report..."
	uv run python -c "from src.data_split.split import DataSplitter; DataSplitter().report()"


up:
	@echo "Command 'make up' is only available from Host OS."

ssh:
	@echo "Command 'make ssh' is only available from Host OS."

# (B) HOST OS LOGIC (Windows/Mac/Linux)
# Executed if running on the HOST OS.
# Relays all commands into the container using the Dev Container CLI.
else

# Define all targets that need to be relayed.
# This is more robust than a generic catch-all (%).
.PHONY: help sync fetch chart lint format fmt format-check up ssh kfold kfold-report

# Default target
help:
	@echo "--- On Host OS ---"
	@echo "Usage: make [target]"
	@echo "This will relay commands into the running Dev Container."
	@echo "Targets:"
	@echo "  up            - (First time) Build and start the Dev Container"
	@echo "  sync          - Sync Python dependencies (inside container)"
	@echo "  fetch         - Fetch daily stock data (inside container)"
	@echo "  chart ticker= - Generate a chart (e.g., make chart ticker=TSLA)"
	@echo "  lint          - Run linter (inside container)"
	@echo "  format / fmt  - Format code (inside container)"
	@echo "  ssh           - Get a shell inside the running container"
	@echo "  kfold         - Run K-Fold data splitting (inside container)"
	@echo "  kfold-report  - Show K-Fold split report (inside container)"

# --- Host-specific Commands ---
up:
	@echo "Building Dev Container and running 'make sync'..."
	$(DEVCONTAINER_CLI) up --workspace-folder .
	@echo "Container is ready."

ssh:
	@echo "Opening shell in Dev Container..."
	$(DEVCONTAINER_CLI) exec --workspace-folder . /bin/bash

# --- Relayed Commands ---
# All other targets are relayed into the container.
sync fetch chart lint format fmt format-check kfold kfold-report:
	@echo "--> [HOST] Relaying target '$@' with args '$(ARGS)' into Dev Container..."
	$(DEVCONTAINER_CLI) exec --workspace-folder . make $@ $(ARGS)

endif

# ========================================
# 実験設定の自動生成
# ========================================
.PHONY: generate-experiments
generate-experiments:
	@echo "📝 Generating experiment configs for all tickers..."
	@mkdir -p data/experiments
	uv run python src/core/generate_ticker_yaml.py \
	  --config src/config_universe.yaml \
	  --template src/data_split_labeling.yaml \
	  --output-dir data/experiments/
	@echo "✅ Generated experiment configs in data/experiments/"

# ========================================
# 特定ティッカーのラベル付け
# ========================================
.PHONY: label
label:
	@if [ -z "$(ticker)" ]; then \
	  echo "❌ Usage: make label ticker=TSLA"; \
	  exit 1; \
	fi
	@echo "🏷️  Labeling data for $(ticker)..."
	uv run python src/core/triple_barrier_labeler.py \
	  --config data/experiments/$(ticker)_experiment.yaml

# ========================================
# 特定ティッカーのデータ分割
# ========================================
.PHONY: split
split:
	@if [ -z "$(ticker)" ]; then \
	  echo "❌ Usage: make split ticker=TSLA"; \
	  exit 1; \
	fi
	@echo "🔀 Splitting data for $(ticker)..."
	uv run python src/core/data_splitter.py \
	  --config data/experiments/$(ticker)_experiment.yaml

# ========================================
# フルパイプライン（全ティッカー）
# ========================================
.PHONY: full-pipeline
full-pipeline: generate-experiments
	@echo "🚀 Running full pipeline for all tickers..."
	@for config in data/experiments/*_experiment.yaml; do \
	  ticker=$$(basename $$config _experiment.yaml); \
	  echo ""; \
	  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	  echo "Processing: $$ticker"; \
	  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	  echo "Step 1/2: Labeling..."; \
	  uv run python src/core/triple_barrier_labeler.py --config $$config || exit 1; \
	  echo "Step 2/2: Splitting..."; \
	  uv run python src/core/data_splitter.py --config $$config || exit 1; \
	  echo "✅ $$ticker completed"; \
	done
	@echo ""
	@echo "🎉 Full pipeline completed for all tickers!"

# ========================================
# Lint と Format
# ========================================
.PHONY: lint
lint:
	uv run ruff check src/

.PHONY: format
format:
	uv run ruff format src/

# ========================================
# 既存のkfoldターゲット（廃止予定）
# ========================================
.PHONY: kfold
kfold:
	@echo "⚠️  Warning: 'make kfold' is deprecated."
	@echo "    Please use 'make full-pipeline' for all tickers"
	@echo "    or 'make split ticker=TSLA' for specific ticker."
	@exit 1

.PHONY: kfold-report
kfold-report:
	@echo "⚠️  Warning: 'make kfold-report' is deprecated."
	@echo "    Split results are now in data/splits/{TICKER}/fold_*/stats.json"
	@exit 1

# ========================================
# Dev Container (ホストOS用)
# ========================================
.PHONY: up
up:
	devcontainer up --workspace-folder .

.PHONY: exec
exec:
	devcontainer exec --workspace-folder . $(CMD)