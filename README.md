# Machine_Learning-based_Quantitative_Trading_Strategies

# 機械学習を用いたクオンツ戦略（Machine Learning-based Quantitative Trading Strategies）

本リポジトリは、**機械学習を活用したクオンツ（数量的）投資戦略**の研究・実装を目的としています。

急速に変化する市場環境に適応し、データに基づいた投資判断の精度を高めるための

多様な仮説立案・検証・モデル改善のプロセスを通じて、経済的知見とAI応用力を磨くことを目指します。

## 🎯 目的（Goals）

### 🧑‍💻 Jun-Seo

機械学習を利用したクオンツ戦略を実践し、

急速な時代変化に合わせた戦略導入の過程で、

多様な仮説と検証を繰り返しながらモデルを改善。

その経験を通じて、**経済的な洞察を深める**とともに、

実際の株価やデータに影響を与える要素を理解・考察することを目的とする。

### 💡 Hyun-Jin

経済的な知識にとどまらず、

現在有望な技術である**機械学習の解像度を高める**ことで、

投資戦略への多様なアプローチを体験。

仮説を立て、検証を行うサイクルを通じて、

**AIおよびデータ分析の理解度を高める**ことを目指す。

## 🚀 実行方法 (How to Run)

本プロジェクトは Dev Container を使用し、全ての開発環境を隔離された Docker コンテナ内部で実行します。セットアップには2つの方法があります。

### (A) CLIベースの高速セットアップ (推奨)

ターミナル操作に慣れており、VS Code の GUI 操作なしで環境構築を自動化したい場合に推奨されます。

#### 1. 必須ツール (初回のみ)

ホストOS（お使いのPC）に以下がインストールされている必要があります:

1. **Git**
    
2. **Docker Desktop** (必ず起動した状態にしてください)
    
3. **Node.js / npm** (Dev Container CLI のインストールに必要)
    
4. **make** (Windows の場合は `choco install make` や `scoop install make` でインストール)
    
5. **Dev Container CLI**:
    
    ```
    npm install -g @devcontainers/cli
    ```
    

#### 2. 環境構築 (プロジェクト初回のみ)w

ホストOSのターミナル（PowerShell, iTermなど）から以下を実行します。

```
# 1. リポジトリをクローン
git clone https://github.com/ijunseo/Machine_Learning-based_Quantitative_Trading_Strategies
cd Machine_Learning-based_Quantitative_Trading_Strategies

# 2. Dev Container のビルドと起動 (make sync が自動実行されます)
make up
```

> **解説:** `make up` は、`.devcontainer/devcontainer.json` の設定を読み込み、Dockerイメージのビルド、コンテナの起動、さらに `postCreateCommand` (`make sync`) の自動実行まで、全ての初期設定を全自動で行います。

#### 3. コマンドの実行 (開発時)

ホストOSのターミナルから、コンテナ内部のコマンドを意識せず、直接 `make` コマンドを実行します。

**株価データの取得:**

```
make fetch
```

_(内部動作: Host OS -> `devcontainer exec ... make fetch` -> Container -> `uv run python ...`)_

**データの可視化:**

```
# 例：テスラ(TSLA)のチャートを生成
make chart ticker=TSLA
```

**Lint と Format の実行:**

```
make lint
make format
```

### (B) VS Code GUIベースの標準セットアップ (従来の方法)

VS Code の Dev Containers 拡張機能の GUI を使用して環境をセットアップする方法です。

#### 1. 必要なもの (Prerequisites)

1. **Docker Desktop**
    
2. **Visual Studio Code**
    
3. **Dev Containers (拡張機能)** (ID: `ms-vscode-remote.remote-containers`)
    

#### 2. 開発環境のセットアップ (初回のみ)

1. **リポジトリのクローン:** まず、このリポジトリをローカルPCにクローンします。
    
2. **VS Codeでフォルダを開く:** クローンしたプロジェクトフォルダを VS Code で開きます。
    
3. **コンテナで再度開く:**
    
    - フォルダを開くと、VS Code の右下に **"Reopen in Container"** というポップアップが表示されます。このボタンをクリックしてください。
        
    - VS Code が `.devcontainer` フォルダの設定を自動で読み込み、Dockerイメージのビルド、コンテナの実行、そしてPythonライブラリのインストール(`make sync`)までを**全自動で**行います。(初回は数分かかります)
        

#### 3. データ取得と可視化

セットアップが完了すると、VS Code は Docker コンテナ内部に直接接続された状態になります。**VS Code 内で開くターミナル** (`Ctrl + ``) で以下のコマンドを実行します。

**株価データの取得:**

```
# VS Code 内のターミナルで実行
make fetch
```

**データの可視化:**

```
# VS Code 内のターミナルで実行 (例：テスラ)
make chart ticker=TSLA
```