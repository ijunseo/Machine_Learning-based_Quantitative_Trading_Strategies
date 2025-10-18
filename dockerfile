# =========================================
# 開発用の軽量なCPUベースイメージ
# - GPUが必要になった場合は、コメントアウトされたPyTorchイメージに切り替えてください
# =========================================
FROM python:3.11-slim

# pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

# ====== 基本ツールの導入（makeを追加）======
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      git curl ca-certificates build-essential make && \
    rm -rf /var/lib/apt/lists/*

# ====== uv のインストール（公式スクリプト）======
# - PATH への追加も自動で行われる
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# ====== 作業ディレクトリ ======
WORKDIR /workspace

# （最適化）pyproject.toml と uv.lock を先にコピーするとレイヤキャッシュが効く
# - 初回は存在しない可能性があるため、存在時のみコピーする運用にしてもOK
#   ここではシンプルにリポジトリ全体をマウントする前提でスキップ

# デフォルトのエントリポイントは docker-compose 側で指定

