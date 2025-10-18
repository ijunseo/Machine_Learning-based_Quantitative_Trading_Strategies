# =========================================================
# 開発用 Makefile（uv を前提）
# - Dev Container内のターミナルから直接実行することを想定
# =========================================================

# 既定ターゲット（`make` だけで help を表示）
.DEFAULT_GOAL := help

# uv コマンド
UV := uv

# OS差異を吸収した削除コマンド
RM_RF := rm -rf

.PHONY: help
help:
	@echo "Targets:"
	@echo "  sync     - 依存関係を同期（uv.lock を生成/更新）"
	@echo "  fetch    - 日次データを取得（config.yaml に従う）"
	@echo "  run      - 取得済みデータの先頭表示で動作確認"
	@echo "  lint     - Lint 実行（ruff 等を導入している場合）"
	@echo "  format   - コード整形（ruff 等を導入している場合）"
	@echo "  clean    - 生成物を削除（キャッシュ・データ等）"
	@echo "  uv ...   - 任意のuvコマンドを実行 (例: make uv run python scripts/test.py)"

.PHONY: sync
sync:
	# 依存関係の同期
	$(UV) sync

.PHONY: fetch
fetch:
	# 日次の株価データを取得して Parquet で保存
	$(UV) run python scripts/fetch_daily.py

.PHONY: run
run:
	# 取得済みデータの先頭を表示して動作確認
	$(UV) run python -m app.main

.PHONY: lint
lint:
	# コード規約チェック
	$(UV) run ruff check .

.PHONY: format
format:
	# 自動整形
	$(UV) run ruff format .

# `uv` コマンドを直接実行するための汎用ターゲット
# `make uv` の後に続くすべての引数を `uv` コマンドの引数として渡す
uv:
	@$(UV) $(filter-out $@,$(MAKECMDGOALS))

.PHONY: clean
clean:
	# Pythonキャッシュや一時ファイルを削除
	$(RM_RF) .pytest_cache .ruff_cache **/__pycache__
	# 取得データを消したくない場合は以下をコメントアウト
	# $(RM_RF) data/*

