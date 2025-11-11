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
- **Docker Desktop** (起動済み)
- **Git**
- **make** (Windows: `choco install make` または `scoop install make`)

### セットアップ

```bash
# 1. リポジトリをクローン
git clone https://github.com/ijunseo/Machine_Learning-based_Quantitative_Trading_Strategies
cd Machine_Learning-based_Quantitative_Trading_Strategies

# 2. Dev Containerで開く (VS Code推奨)
# VS Codeで開き、"Reopen in Container"をクリック
```

---

## 📊 データパイプライン

### 1. 株価データの取得

```bash
# 全ティッカーの株価データを取得 (Yahoo Finance)
make fetch
```

**データ保存先:** `data/raw/{ticker}.parquet`

**対象ティッカー** (`src/config_universe.yaml`で設定):
- AAPL, TSLA, NVDA, MSFT, META, GOOGL, GOOG, AMZN, AMD, LUNR, RKLB, NOW, PLTR

---

### 2. データの可視化

```bash
# 特定ティッカーのチャート生成
make chart ticker=TSLA

# 全ティッカーのチャート一括生成
make chart-all
```

**出力先:** `data/charts/{ticker}_chart.png`

---

### 3. フルパイプライン実行 (推奨)

以下のステップを自動実行します:
1. 実験設定ファイル生成
2. Triple-Barrierラベリング
3. Rolling Horizon分割

```bash
make full-pipeline
```

**実行内容:**
- **設定生成:** 各ティッカーの実験設定YAML作成 (`data/experiments/`)
- **ラベリング:** 株価データにラベル付与 (`data/processed/{ticker}_features_labeled.csv`)
- **データ分割:** 訓練/テストセット作成 (`data/splits/{ticker}/`)

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
make label ticker=TSLA

# 全ティッカー
make label-all
```

**ラベリングロジック:**
- **Upper Barrier (+3%):** 利益確定 → Label = 1 (Long)
- **Lower Barrier (-2%):** 損切り → Label = -1 (Short)
- **Time Barrier (5日):** 時間切れ → Label = 0 (Neutral)

**出力:** `data/processed/{ticker}_features_labeled.csv`

#### 4.3 Rolling Horizon分割

```bash
# 特定ティッカー
make split ticker=TSLA

# 全ティッカー
make split-all
```

**分割設定:**
- 訓練データ: 200サンプル/Fold
- テストデータ: 5サンプル/Fold
- 分割方式: 最新データから遡って固定ウィンドウ

**出力:** `data/splits/{ticker}/fold_{N}_train.csv`, `fold_{N}_test.csv`

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
  method: "rolling_horizon"
  batch_unit: 200        # 訓練データサイズ (変更可能)
  horizon: 5             # テストデータサイズ (変更可能)
  latest_first: true     # 最新データから遡る

labeling:
  enabled: true
  method: "triple_barrier"
  upper_return: 0.03     # 利益確定 +3% (変更可能)
  lower_return: -0.02    # 損切り -2% (変更可能)
  max_holding_days: 5    # 最大保有日数 (変更可能)
  reference_column: "Close"
  input_data: "data/raw/{ticker}.parquet"
  output_data: "data/processed/{ticker}_features_labeled.csv"
```

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
│   │   ├── labeling/                  # ラベリング機能
│   │   │   ├── __init__.py
│   │   │   └── triple_barrier_labeler.py
│   │   ├── utils/                     # ユーティリティ
│   │   │   ├── __init__.py
│   │   │   └── io.py                  # I/O処理
│   │   ├── data_splitter.py           # データ分割
│   │   └── generate_ticker_yaml.py    # 実験設定生成
│   ├── get_data/
│   │   ├── __init__.py
│   │   ├── fetcher.py                 # 株価取得
│   │   └── visualizer.py              # チャート生成
│   ├── models/                        # モデルパッケージ（将来用）
│   │   ├── __init__.py
│   │   └── base.py                    # BaseModelインターフェース
│   ├── config_universe.yaml           # ティッカーリスト
│   └── data_split_labeling.yaml       # パイプライン設定
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
#    例: upper_return: 0.05 (利益確定を5%に変更)
vim src/data_split_labeling.yaml

# 2. 実験設定を再生成
make generate-experiments

# 3. 特定ティッカーで検証
make label ticker=TSLA
make split ticker=TSLA

# 4. 全ティッカーで実行
make full-pipeline
```

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