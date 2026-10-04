# 作業の再開メモ

## 目的

WSL containers の Dev Container を使い、単一リポジトリで Kaggle の
コンペ別コードを管理する。CPU / NVIDIA GPU に対応し、GitHub で共有する。

## 現在の共有方針（2026-10-04 更新）

ユーザーの指定により、`competitions/` は `_template/` だけ Git 管理する。
その他のコンペは個人情報を含むため、ローカルに保持して Git の追跡から外す。
共通の環境・ツール・テンプレート・手順を共有し、個別コンペを強制追加しない。
以前のコミットはすでに origin/main に反映されていることを確認した。
追跡除外に続き、ユーザーの明示依頼で個別コンペを全 Git 履歴から削除した。

## 確認済み（2026-10-04）

- CPU / GPU の Dev Container、コンペのテンプレート、共通のデバイス選択を用意済み。
- `scripts/new_competition.py` でコンペのディレクトリを作成できる。
- データ・モデル・認証情報を `.gitignore` で除外済み。
- `origin` は `https://github.com/all373/kaggle-harness.git`。
- 環境構築時点の `main` / `origin/main` は `d7552f5`。
  最新の共有状態は `git log` / `git status -sb` で確認する。
- GPU コンテナで `python scripts/check_env.py --require-cuda` が成功。
  Python 3.11.10 / PyTorch 2.5.1+cu124 / NVIDIA GeForce RTX 3060 Ti。
- 両 Dev Container の拡張一覧に `openai.chatgpt` を追加。
  実際の rebuild 後のインストールは未確認。

## コンペ・Kaggle の確認済み状態

最初のコンペは `word2vec-nlp-tutorial`（Bag of Words Meets Bags of Popcorn）。
2026-10-04 にコンペ用フォルダを作成し、データ取得・二段階の ZIP 展開を完了。
学習 25,000 件、テスト 25,000 件、ラベルなし 49,999 件を確認。
再取得・展開手順と検証方針はコンペの README に記載。
GPU の EmbeddingBag + MLP の学習・検証・提出フローを実装済み。

Kaggle Notebook GPU 対応も追加済み。`scripts/prepare_kaggle_notebook.py` で
ユーザー別の非公開 GPU Notebook metadata を生成できる。
2026-10-04 に `koheiminami/word2vec-nlp-tutorial-gpu-check` の version 1 を
300 秒の上限でアップロード・実行し、COMPLETE を確認。
Kaggle の Tesla T4 ×2 で両 GPU の演算と全コンペファイルの読み込みが成功。
実行環境は Python 3.13.15 / PyTorch 2.11.0+cu128 / CUDA 12.8。
結果は `runs/word2vec-nlp-tutorial/kaggle-gpu-output/gpu-check.json`。
GPU 確認 Notebook は学習せず、別の `gpu-train` Notebook で学習する。

Kaggle 認証は `config/kaggle.example.json` を各自で
`config/kaggle.local.json` にコピーして設定する方式を追加済み。
ローカル設定は Git 管理から除外し、`scripts/kaggle_cli.py` で CLI に渡す。
2026-10-04 に Kaggle CLI 2.2.4 をインストールし、実際のトークンで
`python scripts/kaggle_cli.py competitions list` が成功（終了コード 0）。
認証情報は Git 除外対象のローカル設定に保存し、共有する設定例はプレースホルダー。

## GPU 学習とスコア（2026-10-04）

- 学習 Notebook: `koheiminami/word2vec-nlp-tutorial-gpu-train` version 1、COMPLETE。
- Tesla T4 上で10 epoch、検証が最良の5 epoch目のモデルを採用。
- 検証 ROC AUC: 0.94938688、accuracy: 0.8782。
- ユーザーの明示指示により Kaggle に1回提出。提出 ID 56815495、COMPLETE。
- Kaggle public score: 0.93598。
- `scripts/run_kaggle_training.py` で生成 → GPU 実行 → 成果物取得を実行。
  `--submit` で1回提出し、対応する提出のスコアを取得する。
- モデル・予測・設定・検証分割・スコアは `runs/` に保存して Git 除外。
- 再現条件と数値はコンペの `RESULTS.md`、コマンドはコンペの README。
- テスト2件成功。学習・検証の分離と提出 ID 順序、GPU 必須時の失敗を確認。

## ARC Prize 2026 - ARC-AGI-2（2026-10-04）

`competitions/arc-prize-2026-arc-agi-2/` にオフライン CPU 規則探索を追加。
公開評価120問題・172出力の pass@2 は0%。単純な規則群の精度には限界がある。
`scripts/run_arc_submission.py` で Notebook 生成・実行・特定バージョンの
Code Competition 提出・スコア取得を行う。
`koheiminami/arc-agi-2-symbolic-baseline` version 1 は COMPLETE。
240問題・259出力の JSON を検査済み。推論時間は約8.46秒。
ユーザーの依頼により1回提出し、提出 ID 56815910 が COMPLETE となった。
Kaggle public score は 0.00。初回のベースラインは非公開テストでも解けなかった。
ARC 用テスト5件が成功。認証情報・配布データ・成果物は Git 除外。
再実行手順と成績はコンペの README / RESULTS.md に記録。

## 次の作業候補

1. 同じ検証分割で CPU の TF-IDF ベースラインや別モデルと比較する。
2. 実験結果を横並びで比較する処理を追加する。
3. 次のモデル・実験の変更も、機能ごとにコミットして GitHub で共有する。

## 自分の実装・新コンペ向けの整理（2026-10-04）

- 従来の Notebook 生成は NLP / ARC の特定ファイル向けだったため、汎用の実験入口を追加。
- `run_experiment.py` で `--entry` / `--config` / `--name` を指定できる。
  `run(config, data_dir, output_dir)` が共通契約。既存の学習・推論本体は保持する。
- 結果は `runs/<slug>/experiments/<name>/<日時と識別子>/` に分離し、
  `experiment.json` に指標・設定・Python ソースハッシュ・処理時間を記録する。
- `prepare_experiment_notebook.py` で同じ自作実装を CPU / GPU Notebook に生成できる。
  対象 src と harness の Python ソースを同梱し、相対 import に対応。
  `--submission-file` で採点用の固定出力ファイルを作れる。
  requirements・非 Python 資産は自動同梱せず、別途オフライン入力を準備する。
- テンプレートに関数の雛形と configs の案内を追加。新コンペのモデルは利用者が実装する。
- NLP / ARC に共通入口の adapter を追加。CLI 呼び出しを kaggle_helpers.py に分離し、
  ARC スクリプトから NLP スクリプトへの依存を除去。
- `docs/` に既存実装の変更方法、新コンペの追加・データ取得・検証・Notebook 実行・
  通常提出 / Code Competition 提出・記録 / GitHub 共有の手順を追加。
- テスト12件が成功。自作モジュールと補助ファイルの実行、設定切替、成果物の分離、
  ローカル秘密設定の非同梱、固定出力、既存 NLP / ARC の動作を確認。
  この整理では Kaggle への新規実行・提出は行っていない。
- 共通入口から既存 ARC をローカル実行し、240問題・259出力の生成と提出形式の検査が成功。
  結果は `runs/arc-prize-2026-arc-agi-2/experiments/adapter-check/20261004T064012568934Z-d5dd39cc/`。
  公開評価は実行していないため、新しい精度スコアではない。
- 新旧5個の CLI で `--help` が成功。関連 Markdown 12ファイルの相対リンク・
  コードブロックと `git diff --check` を確認。

## 会話が見つからない場合

エージェント向けの入口としてルート `AGENTS.md` と `.agent/README.md` を追加済み。
構成は `.agent/MAP.md`、実行・テスト・再開方法は `.agent/WORKFLOWS.md`。
秘密情報や会話全文は含めず、進捗の詳細は引き続きこのファイルに記録する。

このファイルと README、`git status`、`git log` を起点に再開する。
このメモは過去の会話そのものを復元したものではなく、残っているファイルと
現在の環境から確認できた状態を記録している。作業が進んだら更新する。

## GitHub 共有の整理（2026-10-04）

ユーザーの依頼により、既存のワークスペース変更を次の機能単位でコミットした。
共有先は `origin` の `main`（`all373/kaggle-harness`）。

| 機能 | コミット |
| --- | --- |
| CPU / GPU Dev Container の Codex 拡張 | `65a9b26` |
| Git 除外の Kaggle 認証設定・共通 CLI | `4e22f4a` |
| NLP の GPU 学習・検証・提出 | `4e2ef69` |
| ARC の solver・Notebook バージョン指定提出 | `29374d5` |
| 自作コード・設定の切替と実験別保存・Notebook 生成 | `8174ac5` |
| 環境構築・自作実験・新コンペの手順書 | `b7efdce` |
| エージェント向け案内・再開メモ | この記録を含むコミット |

共有前にテスト12件・差分の空白検査・Notebook に保存出力がないことを確認。
認証情報・配布データ・実験成果物は Git 除外のまま保持する。

`git push origin main` は GitHub の `Invalid username or token` で失敗。
このコンテナには有効な GitHub CLI / 環境変数 / SSH 認証も見つからなかった。
リモート main は `d7552f5` のままで、ローカル main が7コミット先行している。
GitHub の Git 認証を更新したあと、`git push origin main` で共有を完了できる。
Kaggle の認証とは別なので、Kaggle トークンを GitHub 認証に使わない。

## 個別コンペの履歴削除（2026-10-04）

ユーザーの依頼により git-filter-repo で全履歴から `competitions/_template/` 以外を削除。
書き換え後の全10コミットで対象ファイルがないことと、現在の共有ファイルが同一であることを検査した。
個別コンペ20ファイルはローカルに保持し、Git 除外を継続する。
GitHub main は変更前の先端を指定した force-with-lease で更新する。
別の clone がある場合は旧履歴を merge / push せず、取得し直して個人ファイルだけを戻す。
GitHub のキャッシュや他人の clone は履歴更新だけで消去を保証できない。
