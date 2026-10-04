# 実行と確認の手引き

コマンドはコンテナ内のリポジトリルートで実行する。
認証情報は既存のローカル設定を使い、この文書やコマンド引数に書かない。
`KAGGLE_OWNER` は本人のユーザー名を設定する。新しいターミナルでは再設定が必要。

## ローカル状態の確認

```bash
git status --short
git branch -vv
git remote -v
git log -5 --oneline
git check-ignore config/kaggle.local.json
python scripts/check_env.py
```

GPU を検査する必要がある場合のみ `python scripts/check_env.py --require-cuda`。
設定内容を `cat` して認証確認をしない。

## 関連するテスト

```bash
# NLP の学習・検証・成果物
python -m unittest discover -s tests -p test_sentiment_training.py -v

# ARC の規則探索・提出形式
python -m unittest discover -s tests -p test_arc_solver.py -v

# 自作 entry・設定・相対 import・成果物分離・Notebook 同梱
python -m unittest discover -s tests -p test_experiments.py -v

# 共通変更で両方に影響する場合
python -m unittest discover -s tests -v

git diff --check
```

NLP のテストは PyTorch / NumPy / scikit-learn、ARC のテストは NumPy が必要。
インストール方法はルート README とコンペの requirements.txt を参照する。
CPU 開発環境で Kaggle に送るだけなら、ローカルに PyTorch を入れる必要はない。

## 自分の実装の実行・Notebook 生成

利用者向けの詳細は [docs/experiments.md](../docs/experiments.md) と
[docs/new-competition.md](../docs/new-competition.md)。ベースラインを保持し、
`src/my_model.py` と `configs/my-model.json` を作成してから実行する。

```bash
python scripts/run_experiment.py word2vec-nlp-tutorial --entry src/my_model.py --config configs/my-model.json --name my-model --device cpu
python scripts/prepare_experiment_notebook.py word2vec-nlp-tutorial --owner "$KAGGLE_OWNER" --entry src/my_model.py --config configs/my-model.json --name my-model --device cuda --submission-file submission.csv
```

共通 packager はローカル生成だけ。push は外部実行、submit は新しい提出になる。
既存専用スクリプトは引き続き元のベースライン用に使う。

## Kaggle の状態確認（読み取り）

```bash
export KAGGLE_OWNER="your-kaggle-username"
python scripts/kaggle_cli.py kernels status "$KAGGLE_OWNER/word2vec-nlp-tutorial-gpu-train"
python scripts/kaggle_cli.py competitions submissions word2vec-nlp-tutorial
python scripts/kaggle_cli.py competitions submissions arc-prize-2026-arc-agi-2
```

## NLP の生成・実行・取得

```bash
# ローカルで Notebook と metadata を生成するだけ
python scripts/prepare_kaggle_notebook.py word2vec-nlp-tutorial --owner "$KAGGLE_OWNER" --notebook gpu-train

# 外部実行：新しい Notebook version を作り、GPU 学習して成果物を取得
python scripts/run_kaggle_training.py word2vec-nlp-tutorial --owner "$KAGGLE_OWNER"

# 既存 Notebook の最新の実行結果を取得。再学習・提出はしない
python scripts/run_kaggle_training.py word2vec-nlp-tutorial --owner "$KAGGLE_OWNER" --resume
```

提出を依頼された場合は上の run コマンドに `--submit` を付ける。
学習済み結果を提出する場合は `--resume --submit`。
いずれも新たに1回提出するので、既存の提出記録を確認する。

## ARC のローカル評価・生成・実行・取得

```bash
python -m competitions.arc-prize-2026-arc-agi-2.src.solver --data-dir data/arc-prize-2026-arc-agi-2 --output-dir runs/arc-prize-2026-arc-agi-2/local-baseline --validate
python scripts/prepare_arc_notebook.py --owner "$KAGGLE_OWNER"

# 外部実行：新しい Notebook version を実行し、成果物を取得
python scripts/run_arc_submission.py --owner "$KAGGLE_OWNER"

# 1 を対象の version 番号に置き換えて取得する
python scripts/run_arc_submission.py --owner "$KAGGLE_OWNER" --resume-version 1
```

ローカル評価の出力先は再実行で上書きする。以前の実験を残すなら別の出力先を指定する。
ARC 提出を依頼された場合は run コマンドに `--submit` を付ける。
Code Competition のため、Notebook version と出力ファイル名を指定して提出する。
ローカル JSON のアップロード方式へ置き換えない。

## 中断・失敗からの再開

1. `git status` と PROGRESS.md、対象の result.json を確認する。
2. Notebook の状態を確認する。起動待ち・採点待ちだけで新しい実行を作らない。
3. 実行が完了していれば resume で結果を取得する。
4. 提出の状態が不明なら submissions と提出メッセージ / ID を照合する。
5. スコアが確定したらコンペ RESULTS.md と PROGRESS.md を更新する。

実行 / 提出スクリプトは待ち時間を超えると未確定のまま終了する場合がある。
`PENDING` を成功や0点に読み替えず、実際の `COMPLETE` とスコアを記録する。
API の提出回数・GPU 枠は現在のアカウントで確認し、過去の残数を再利用しない。

## 更新する記録

| 変更したもの | 更新する資料 |
| --- | --- |
| 作業の進捗・未完了事項 | PROGRESS.md |
| 実測スコア・採点状態・実行条件 | コンペ RESULTS.md |
| 手順・依存関係・コマンド | コンペ README、必要ならルート README |
| 新しいコンペ・スクリプト・構造 | .agent/MAP.md、必要なら WORKFLOWS.md |
| 共有する作業方針 | AGENTS.md |
