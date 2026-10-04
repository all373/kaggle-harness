# ワークスペースの見取り図

## 開発環境と保存場所

| 場所 | 役割 |
| --- | --- |
| `.devcontainer/cpu/` | Python 3.11 の CPU 開発環境。PyTorch は初期状態で入っていない |
| `.devcontainer/gpu/` | PyTorch 2.5.1 / CUDA 12.4 ベースの NVIDIA GPU 開発環境 |
| `config/kaggle.example.json` | 共有する API トークン設定の例 |
| `config/kaggle.local.json` | 各自の認証情報。Git 除外、内容を表示しない |
| `requirements-kaggle.txt` | 共通 CLI の依存指定 |
| `data/<slug>/` | 配布データ。Git 除外 |
| `runs/<slug>/` | 生成 metadata・モデル・予測・ログ・スコア。Git 除外 |
| `competitions/_template/` | コンペの雛形。`src/experiment.py` の関数契約を用意し、学習処理は未実装 |
| `harness/device.py` | `auto` / `cpu` / `cuda` のデバイス選択ユーティリティ |
| `harness/experiments.py` | 選択した実装の実行、実験別保存先、設定・指標・ソースハッシュの記録 |
| `docs/` | 自分の実装と新コンペ追加・提出の利用者向け手順 |

ホストは Windows + WSL + WSL containers を想定。WSL 本体のリリース番号と
Ubuntu の WSL 2 動作方式は別。具体的な導入条件はルート README の公式リンクを確認する。
Kaggle は独自の Python / ライブラリ環境で実行し、ローカル Dockerfile は適用されない。
コンテナを rebuild すると手動で追加した依存関係は再インストールが必要になる場合がある。

## スクリプトの役割

| スクリプト | 役割・副作用 |
| --- | --- |
| `scripts/check_env.py` | ローカル環境と任意の CUDA 演算確認 |
| `scripts/new_competition.py` | テンプレートを新規 slug にコピー。既存フォルダは拒否 |
| `scripts/kaggle_cli.py` | ローカルトークンを子プロセスの環境変数で CLI に渡す |
| `scripts/kaggle_helpers.py` | 専用実行スクリプトで共有する CLI 呼び出し。ARC から NLP への依存を除去 |
| `scripts/run_experiment.py` | `--entry` / `--config` / `--name` で自分の実装をローカル実行 |
| `scripts/prepare_experiment_notebook.py` | 同じ実装・相対 import の補助ファイルを非公開 CPU / GPU Notebook に同梱。ローカル生成のみ |
| `scripts/build_training_notebook.py` | NLP のソースと config を学習 Notebook に埋め込む |
| `scripts/prepare_kaggle_notebook.py` | NLP の GPU 確認 / 学習 Notebook と非公開 metadata を生成 |
| `scripts/run_kaggle_training.py` | NLP Notebook の実行・取得、任意の CSV 提出と採点確認 |
| `scripts/prepare_arc_notebook.py` | ARC ソースを Notebook に埋め込み、非公開 CPU metadata を生成 |
| `scripts/run_arc_submission.py` | ARC Notebook の実行・取得、任意の特定 version 提出と採点確認 |

## NLP：word2vec-nlp-tutorial

ソース: `competitions/word2vec-nlp-tutorial/src/train.py`。
設定: 同コンペの `config.json`。データ展開: `src/prepare_data.py`。

PyTorch EmbeddingBag + MLP。事前学習 Word2Vec は使用しない。
層化 80/20、seed 42、語彙は学習側だけで fit。検証 ROC AUC 最良の epoch を
保存し、そのモデルでテスト予測を生成する。全件での再学習はしない。
最良 epoch 選択にも同じ検証データを使うため、独立した最終評価とは区別する。

```text
src/train.py + config.json
  → build_training_notebook.py
  → notebooks/gpu-train.ipynb
  → runs/<slug>/kaggle-gpu-train/（アップロード用）
  → Kaggle 非公開 T4 Notebook
  → runs/<slug>/kaggle-results/<取得日時>/
  → 任意の submission.csv 提出
```

`--resume` は既存 Notebook の最新結果を取得し、version を固定しない。
`--resume --submit` も新しい提出を1回行う。
取得した結果の `artifacts` が学習成果物の場所を指す。

## ARC：arc-prize-2026-arc-agi-2

ソース: `competitions/arc-prize-2026-arc-agi-2/src/solver.py`。
NumPy の CPU 規則探索。幾何変換・色変換を各問題の例題に fit し、2候補を返す。
合う規則が不足したときは単純な fallback を使う。
現状は公開評価・Kaggle とも正解率0の提出基盤用ベースライン。
精度を上げるには、規則群やモデル自体を拡張する必要がある。

```text
src/solver.py
  → prepare_arc_notebook.py
  → notebooks/symbolic-baseline.ipynb
  → runs/<slug>/kaggle-symbolic-baseline/
  → Kaggle 非公開 CPU Notebook
  → /kaggle/working/submission.json
  → 任意の Notebook version を固定した Code Competition 提出
```

専用 solver / packager は ARC の `config.json` を読み込まない。
共通入口の `src/experiment.py` adapter は config の `validate`（既定 false）を読む。
規則を変えるなら solver を編集するか別実装を選ぶ。Kaggle Notebook は `validate=False` で動かす。
公開正解を読むのはローカルの `--validate` による評価だけ。
採点時の test challenges は Kaggle が差し替えるため、配布データの ID / 件数を
コードに固定してはいけない。`--resume-version` は指定 version の成果物を取得する。

## 自分の実装・設定

共通入口は `run(config, data_dir, output_dir) -> dict` を呼ぶ。
ローカル結果は `runs/<slug>/experiments/<name>/<日時と識別子>/experiment.json` に記録し、
既存結果は上書きしない。選択設定とソースハッシュを保存するが、ソース全文はバックアップしない。
個別コンペの実装は Git 除外で、利用者が別途バックアップする。
config 内の `output_dir` より渡された保存先を優先する。
NLP / ARC は `src/experiment.py` から既存ベースラインを呼ぶ adapter を用意済み。

共通 Notebook は対象 `src/` と `harness/` の Python ソースだけを同梱する。
依存関係・辞書・モデルなどは別途 Kaggle の入力とオフライン処理を準備する。
`--submission-file` は実装が出力したファイルを `/kaggle/working/<filename>` にコピーする。
Code Competition ではこの固定ファイル名と Notebook version を指定する。
