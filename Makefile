# =========================================================
# スマートMakefile（ホスト/コンテナ自動判別）
# - Host OS (Windows/Mac) と Dev Container 内部の両方で使用可能
# =========================================================

# デフォルトターゲット（`make` だけで help を表示）
.DEFAULT_GOAL := help

# uv コマンド (PATH経由で実行)
UV := uv

# --- コンテナ内部で実行されているか確認 ---
# devcontainerが自動的に設定する環境変数
# これがtrueなら、コンテナ内部と判断
IS_IN_CONTAINER := $(shell echo $${REMOTE_CONTAINERS:-false})

# 'make chart ticker=TSLA' のような引数を正しく渡すための処理
# $@ (ターゲット名 'chart') を除外し、'ticker=TSLA' のみを取得
ARGS = $(filter-out $@,$(MAKECMDGOALS))

.PHONY: help up ssh sync fetch chart lint format fmt

# 'ifeq' でホストOSかコンテナ内部かを分岐
ifeq ($(IS_IN_CONTAINER), true)

# ===============================================
# (A) コンテナ内部での実行時 (IS_IN_CONTAINER=true)
# (uv run コマンドを直接実行)
# ===============================================
help:
	@echo "Targets (Running INSIDE Container):"
	@echo "  sync          - 依存関係を同期"
	@echo "  fetch         - 日次データを取得"
	@echo "  chart ticker=... - チャートを生成"
	@echo "  lint          - Lint 実行"
	@echo "  format / fmt  - コード整形"

sync:
	@echo "コンテナ内でPythonの依存関係を'uv.lock'に基づいて同期します..."
	$(UV) sync
	@echo "✅ 同期が完了しました。"

fetch:
	@echo "コンテナ内で日次の株価データを取得します..."
	$(UV) run python src/get_data/fetcher.py

chart:
	@echo "コンテナ内で $(ticker) のチャートを生成します..."
	$(UV) run python src/get_data/visualizer.py --ticker $(ticker)

lint:
	$(UV) run ruff check .

format:
	$(UV) run ruff format .

fmt: format
	@echo "Running format via fmt alias..."

else

# ===============================================
# (B) ホストOSでの実行時 (IS_IN_CONTAINER=false)
# (devcontainer exec 経由でコンテナに中継)
# ===============================================
help:
	@echo "Targets (Running on HOST OS):"
	@echo "  up            - [推奨] Dev Container をビルドして起動 (make sync 自動実行)"
	@echo "  fetch         - (中継) 日次データを取得"
	@echo "  chart ticker=... - (中継) チャートを生成"
	@echo "  lint          - (中継) Lint 実行"
	@echo "  format / fmt  - (中継) コード整形"
	@echo "  sync          - (中継) 依存関係を同期"
	@echo "  ssh           - (Utility) 実行中のコンテナにシェルで接続"

# ホストOS専用ターゲット
up:
	@echo "Dev Container をビルドし、'make sync' を実行します..."
	@devcontainer up --workspace-folder .
	@echo "✅ コンテナの準備が完了しました。"

ssh:
	@echo "実行中の 'app' サービスに接続します..."
	@docker-compose exec app /bin/bash

# 'help', 'up', 'ssh' 以外のすべてのターゲットをキャッチ
# これが 'make fetch', 'make chart ticker=TSLA' などを処理する
%:
	@echo "--> [HOST] Relaying target '$@' with args '$(ARGS)' into Dev Container..."
	@devcontainer exec --workspace-folder . make $@ $(ARGS)

endif