# =========================================================
# 開発用 Makefile（uv を前提）
# - Dev Container内のターミナルから直接実行することを想定
# =========================================================

# 既定ターゲット（`make` だけで help を表示）
.DEFAULT_GOAL := help

# uv コマンド (PATH経由で実行)
UV := uv

.PHONY: help
help:
	@echo "Targets:"
	@echo "  sync          - 依存関係を同期（uv.lock を生成/更新）"
	@echo "  fetch         - 日次データを取得（config.yaml に従う）"
	@echo "  chart ticker=... - 指定したティッカーのチャートを生成 (例: make chart ticker=TSLA)"
	@echo "  lint          - Lint 実行"
	@echo "  format        - コード整形"

.PHONY: sync
sync:
	# 依存関係の同期
	@echo "Pythonの依存関係を'uv.lock'に基づいて同期します..."
	$(UV) sync
	@echo "✅ 同期が完了しました。"

.PHONY: fetch
fetch:
	# 日次の株価データを取得
	$(UV) run python src/get_data/fetcher.py

.PHONY: chart
chart:
	# 指定したティッカーのインタラクティブなチャートを生成し、HTMLで保存
	@echo "$(ticker) のチャートを生成します..."
	$(UV) run python src/get_data/visualizer.py --ticker $(ticker)

.PHONY: lint
lint:
	# コード規約チェック
	$(UV) run ruff check .

.PHONY: format
format:
	# 自動整形
	$(UV) run ruff format .
