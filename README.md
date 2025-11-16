# Machine Learning-based Quantitative Trading Strategies

機械学習を活用したクオンツ（数量的）投資戦略の研究・実装プロジェクト

## 🎯 プロジェクトの目的

### 🧑‍💻 Jun-Seo
機械学習を利用したクオンツ戦略を実践し、急速な時代変化に合わせた戦略導入の過程で、多様な仮説と検証を繰り返しながらモデルを改善。その経験を通じて、**経済的な洞察を深める**とともに、実際の株価やデータに影響を与える要素を理解・考察することを目的とする。

### 💡 Hyun-Jin
経済的な知識にとどまらず、現在有望な技術である**機械学習の解像度を高める**ことで、投資戦略への多様なアプローチを体験。仮説を立て、検証を行うサイクルを通じて、**AIおよびデータ分析の理解度を高める**ことを目指す。

---

## 🚀 クイックスタート

### 必須環境

1. **Git**

2. **Docker Desktop** (必ず起動した状態にしてください)

3. **Node.js / npm** (Dev Container CLI のインストールに必要)

4. **make** (Windows の場合は `choco install make` や `scoop install make` でインストール)

5. **Dev Container CLI**:

    ```bash
    npm install -g @devcontainers/cli
    ```

---

### 環境構築 (プロジェクト初回のみ)

ホストOSのターミナル（PowerShell, iTermなど）から以下を実行します。

```bash
# 1. リポジトリをクローン
git clone https://github.com/ijunseo/Machine_Learning-based_Quantitative_Trading_Strategies
cd Machine_Learning-based_Quantitative_Trading_Strategies

# 2. Dev Container のビルドと起動 (make sync が自動実行されます)
make up
```

> **解説:** `make up` は、`.devcontainer/devcontainer.json` の設定を読み込み、Dockerイメージのビルド、コンテナの起動、さらに `postCreateCommand` (`make sync`) の自動実行まで、全ての初期設定を全自動で行います。

---

### コマンドの実行 (開発時)

ホストOSのターミナルから、コンテナ内部のコマンドを意識せず、直接 `make` コマンドを実行します。

**Windows PowerShellの場合:**
```powershell
# 日本語の文字化けを防ぐため、最初に実行してください
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

---

## 📊 データパイプライン

### 1. 株価データの取得

```bash
# 全ティッカーの株価データを取得 (Yahoo Finance)
make fetch

# Windowsの場合、必要に応じてデータディレクトリを作成
mkdir data\processed -Force
```

**データ保存先:** `data/raw/{ticker}.parquet`

**対象ティッカー** (`src/config_universe.yaml`で設定):
- AAPL, TSLA, NVDA, MSFT, META, GOOGL, GOOG, AMZN, AMD, LUNR, RKLB, NOW, PLTR

---

### 2. フルパイプライン実行 (推奨)

以下のステップを自動実行します:
1. 実験設定ファイル生成
2. Triple-Barrierラベリング
3. **CPCV (Combinatorial Purged Cross-Validation)** 分割

```bash
make full-pipeline
```

**実行内容:**
- **設定生成:** 各ティッカーの実験設定JSON作成 (`data/experiments/`)
- **ラベリング:** 株価データにラベル付与 (`data/processed/{ticker}_features_labeled.csv`)
- **データ分割:** CPCV方式で訓練/テストセット作成 (`data/splits/{ticker}/`)

**CPCV設定 (デフォルト):**
- ブロック数: 10
- テストブロック数: 2
- Purge Window: 5サンプル
- Embargo Window: 3サンプル
- **生成Folds:** C(10,2) = **45 folds/ticker**

**⚠️ 注意:** `make chart` を実行する前に、必ず `make full-pipeline` を実行してください。

---

### 3. データの可視化 (CPCV分割 + ラベリング結果)

```bash
# 特定ティッカーのインタラクティブチャート生成
make chart ticker=AAPL
```

**出力先:** `data/charts/{ticker}_cpcv_chart.html`

**可視化内容:**
- 📊 **ローソク足チャート**: 株価の推移
- 🟩 **Fold別Train期間**: 薄い色付き背景 (各foldで異なる色)
- 🟥 **Fold別Test期間**: 濃い色付き背景 + 枠線
- 🟢 **Long (Label=1)**: 緑の▲マーカー (上昇予測)
- 🔴 **Short (Label=-1)**: 赤の▼マーカー (下降予測)
- ⚪ **Neutral (Label=0)**: 灰色の●マーカー (横ばい予測)
- 📈 **20日移動平均線**: オレンジの点線

**使い方:**
1. HTMLファイルをブラウザで開く
2. ズーム/パンでインタラクティブに操作
3. 各マーカーにマウスオーバーで詳細表示

**チャート例 (AAPL):**
- 総サンプル: 1477
- Long: 97 | Short: 106 | Neutral: 92 | 保有中: 1182
- **Folds: 45** (CPCV C(10,2) 組み合わせ)

---

### 4. 個別ステップ実行

#### 4.1 実験設定の生成

```bash
make generate-experiments
```

各ティッカーの設定ファイル (`data/experiments/{ticker}_experiment.json`) を**JSON形式**で生成します。

**なぜJSON？**
- `data/` 全体を `.gitignore` で管理可能
- `src/` 内のYAML設定テンプレートは引き続きバージョン管理

#### 4.2 Triple-Barrierラベリング

```bash
# 特定ティッカー
make label ticker=AAPL

# 全ティッカー
make label-all
```

**ラベリングロジック:**
- **Upper Barrier (+3%):** 利益確定 → Label = 1 (Long)
- **Lower Barrier (-2%):** 損切り → Label = -1 (Short)
- **Time Barrier (5日):** 時間切れ → Label = 0 (Neutral)

**出力:** `data/processed/{ticker}_features_labeled.csv`

**重要:** t日目の特徴量を使ってt+1～t+5日の価格変動を予測（未来データリークなし）

#### 4.3 CPCV分割

```bash
# 特定ティッカー
make split ticker=AAPL

# 全ティッカー
make split-all
```

**CPCV (Combinatorial Purged Cross-Validation) とは:**
- 時系列データを **N個のブロック** に分割
- **K個のテストブロック** をすべての組み合わせ (C(N,K)) で選択
- **Purging:** テスト期間前後のデータを訓練から除外（ラベル計算期間の重複防止）
- **Embargo:** テスト直後のデータを訓練から除外（look-ahead bias防止）

**デフォルト設定:**
- N=10ブロック, K=2テストブロック → **45 folds** (C(10,2))
- Purge Window: 5サンプル
- Embargo Window: 3サンプル

**出力:** `data/splits/{ticker}/fold_{0-44}_train.csv`, `fold_{0-44}_test.csv`

**従来のRolling Horizonとの違い:**
- ❌ **Rolling Horizon:** 固定サイズの移動ウィンドウ（時系列順序のみ考慮）
- ✅ **CPCV:** すべてのブロック組み合わせ + Purge/Embargo（より厳格なリーク防止）

---

## ⚙️ 設定のカスタマイズ

### ティッカーリストの変更

`src/config_universe.yaml`:

```yaml
tickers:
  - TSLA
  - NVDA
  - AAPL
  # 追加・削除可能

data_dir: "data"  # データディレクトリのベースパス
```

### ラベリング・分割設定の変更

`src/data_split_labeling.yaml`:

```yaml
split:
  method: "cpcv"                # CPCV方式（推奨）
  n_blocks: 10                  # ブロック数
  n_test_blocks: 2              # テストブロック数 → C(10,2)=45 folds
  purge_window: 5               # Purge期間（サンプル数）
  embargo_window: 3             # Embargo期間（サンプル数）

labeling:
  enabled: true
  method: "triple_barrier"
  upper_return: 0.03            # 利益確定 +3% (変更可能)
  lower_return: -0.02           # 損切り -2% (変更可能)
  max_holding_days: 5           # 最大保有日数 (変更可能)
  reference_column: "Close"
  input_data: "data/raw/{ticker}.parquet"
  output_data: "data/processed/{ticker}_features_labeled.csv"
```

**注意:** `method: "rolling_horizon"` も選択可能ですが、CPCVを推奨します。

**設定変更後は必ず実行:**

```bash
make generate-experiments
```

---

## 🛠️ 開発コマンド

### コード品質管理

```bash
# Lint (Ruff)
make lint

# Format (Ruff)
make format

# Format Check (CI用)
make format-check
```

### 依存関係管理

```bash
# Python依存関係の同期
make sync
```

### コンテナ管理 (Host OSから)

```bash
# Dev Containerのビルドと起動
make up

# コンテナ内でシェルを開く
make ssh

# コンテナ内でコマンド実行
make exec CMD="python --version"
```

---

## 📁 プロジェクト構造

```
Machine_Learning-based_Quantitative_Trading_Strategies/
├── data/
│   ├── raw/                           # 株価データ (Parquet)
│   ├── processed/                     # ラベル付きデータ (CSV)
│   ├── splits/                        # 訓練/テストセット
│   ├── charts/                        # 可視化チャート
│   └── experiments/                   # ティッカー別実験設定 (JSON)
├── src/
│   ├── core/
│   │   ├── __init__.py                # パッケージ初期化
│   │   ├── backtesting/               # バックテスト機能
│   │   │   ├── __init__.py
│   │   │   └── cpcv_splitter.py       # CPCV分割ロジック
│   │   ├── labeling/                  # ラベリング機能
│   │   │   ├── __init__.py
│   │   │   └── triple_barrier_labeler.py
│   │   ├── utils/                     # ユーティリティ
│   │   │   ├── __init__.py
│   │   │   └── io.py                  # I/O処理
│   │   ├── data_splitter.py           # データ分割（CPCVエントリーポイント）
│   │   └── generate_ticker_yaml.py    # 実験設定生成
│   ├── get_data/
│   │   ├── __init__.py
│   │   ├── fetcher.py                 # 株価取得
│   │   └── visualizer.py              # チャート生成
│   ├── models/                        # モデルパッケージ（将来用）
│   │   ├── __init__.py
│   │   └── base.py                    # BaseModelインターフェース
│   ├── config_universe.yaml           # ティッカーリスト
│   └── data_split_labeling.yaml       # パイプライン設定（CPCV含む）
├── Makefile                           # タスク自動化
├── pyproject.toml                     # Python依存関係
└── README.md
```

**重要なポイント:**
- `data/experiments/` には**JSON形式**の実験設定ファイルが生成される
- `src/` 内の設定ファイルは**YAML形式**でバージョン管理
- `data/` ディレクトリは `.gitignore` で除外

---

## 🔄 ワークフロー例

### 新規ティッカーの追加

```bash
# 1. src/config_universe.yaml にティッカー追加
vim src/config_universe.yaml

# 2. データ取得
make fetch

# 3. フルパイプライン実行
make full-pipeline

# 4. チャート確認
make chart ticker=NEW_TICKER
```

### パラメータ実験

```bash
# 1. src/data_split_labeling.yaml でパラメータ変更
#    例: n_blocks: 15, n_test_blocks: 3 → C(15,3)=455 folds
#    例: upper_return: 0.05 (利益確定を5%に変更)
vim src/data_split_labeling.yaml

# 2. 実験設定を再生成
make generate-experiments

# 3. 特定ティッカーで検証
make label ticker=AAPL
make split ticker=AAPL

# 4. 全ティッカーで実行
make full-pipeline
```

**CPCV パラメータ調整のヒント:**
- `n_blocks` を増やす → より細かい時系列分割
- `n_test_blocks` を増やす → より多くのfolds（計算時間増加）
- `purge_window`, `embargo_window` を増やす → より保守的なリーク防止

### コードの品質チェック

```bash
# フォーマット適用
make format

# リント実行
make lint

# フォーマットチェック（CI環境）
make format-check
```

---

## 📚 技術スタック

- **言語:** Python 3.11
- **依存管理:** uv
- **データ処理:** pandas, numpy
- **機械学習:** scikit-learn (予定)
- **可視化:** matplotlib, seaborn
- **開発環境:** Docker + Dev Container

---

## 📝 ライセンス

MIT License

---

## 👥 開発者

- **Jun-Seo:** 経済的洞察とクオンツ戦略
- **Hyun-Jin:** AI/MLアプローチと実装