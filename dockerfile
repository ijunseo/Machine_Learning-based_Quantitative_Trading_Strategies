# =========================================
# 開発用の軽量なCPUベースイメージ
# =========================================
FROM python:3.11-slim

# ====== 基本ツールとpipxの導入 ======
# - pipxはPython製CLIツールを独立した環境にインストールするためのツールです
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      git curl ca-certificates build-essential make pipx && \
    rm -rf /var/lib/apt/lists/*

# ====== uv のインストール（pipx を使用）======
# - この方法が権限の問題を回避し、最も安定しています
RUN pipx install uv

# pipxによってインストールされたコマンドをPATHに追加
ENV PATH="/root/.local/bin:${PATH}"

# ====== 作業ディレクトリ ======
WORKDIR /workspace
