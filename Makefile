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

.PHONY: help sync fetch chart lint format fmt format-check up ssh

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
.PHONY: help sync fetch chart lint format fmt format-check up ssh

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
sync fetch chart lint format fmt format-check:
	@echo "--> [HOST] Relaying target '$@' with args '$(ARGS)' into Dev Container..."
	$(DEVCONTAINER_CLI) exec --workspace-folder . make $@ $(ARGS)

endif