# このワークスペースで作業するエージェントへ

単一リポジトリで Kaggle のコンペ別コードを管理する。利用者は初心者も想定し、
CPU / GPU の開発環境と、Kaggle Notebook の実行・提出を再現できるようにする。
ユーザーの現在の依頼と会話中の指定を優先し、このファイルは作業の案内として使う。

## 作業を始めるとき

1. [.agent/README.md](.agent/README.md) で資料の場所を確認する。
2. [PROGRESS.md](PROGRESS.md) と `git status --short` で残っている作業を把握する。
3. 対象コンペの README / RESULTS.md と、変更するスクリプトを読む。
4. 実行方法は [.agent/WORKFLOWS.md](.agent/WORKFLOWS.md)、構成は
   [.agent/MAP.md](.agent/MAP.md) を参照する。

状態メモは記録時点の情報。現在の Git 状態・コード・取得済みの result.json を
確認し、メモを根拠に提出済み・未提出や最新スコアを決めつけない。

## 変更する場所

- コンペ固有の学習・推論は `competitions/<slug>/src/` に置く。
- モデル定義はコンペの `src/models/`、コンペで使う重みは同コンペの `models/`。
  直下の `models/pretrained/` / `models/trained/` は重みの保管庫で、README 以外は Git 除外。
  既存の `runs/` の成果物は保持し、利用者のモデルを勝手に移動・アップロードしない。
- 共通の処理は `harness/`、実行・取得の入口は `scripts/`。
- 自分の実装・新コンペの入口は `run_experiment.py` と `prepare_experiment_notebook.py`。
  `src/` 内の `run(config, data_dir, output_dir)` とコンペ内の JSON 設定を選択する。
  手順は `docs/experiments.md` と `docs/new-competition.md`。比較用のベースラインを保持する。
- NLP の `train.py` と ARC の `solver.py` は薄い互換入口。
  コンペの pipeline・data / validation・models に役割を分ける。
  Notebook は対象 src と harness 全体を同梱する。生成物だけを編集しない。
- モデル・解法の選択は `model` / `solver` 設定。詳細は `docs/components.md`。
- `run_kaggle_training.py` は現在 NLP コンペ向け。ARC には
  `run_arc_submission.py` を使う。コンペ slug を置き換えるだけで汎用化できるとは扱わない。
- 既存コンペのコード・ローカル成果物・ユーザーの未コミット変更を保持する。
- 共通 Notebook は対象コンペの `src/**/*.py` と `harness/**/*.py`、選択設定を同梱する。
  非 Python 資産や requirements は自動で同梱・インストールしない。

## 認証・データ・提出

- Kaggle の認証は `scripts/kaggle_cli.py` を通す。
- `config/kaggle.local.json` は秘密情報。内容を表示・検索結果に出力・コピー・
  コミットしたり、Notebook に埋め込んだりしない。共有するのは設定例だけ。
- `data/` と `runs/` は Git 除外のローカル成果物。コードや記録だけを共有する。
- `competitions/` は `_template/` だけ Git 管理する。それ以外は利用者の個人情報を
  含むローカル作業。強制追加したり、内容を共有ファイルへ転記したりしない。
- Notebook の push は実行を開始し、提出は別の外部操作。
  ユーザーが依頼した範囲と回数で実行し、認証設定があるだけで再提出しない。
  会話ですでに指定された実行・提出について確認を繰り返す必要はない。
- 通信エラーで提出結果が不明なら、提出一覧と記録を確認して重複を避ける。
- ARC は Notebook のバージョンを固定した Code Competition 提出。
  採点時に差し替えられる入力を読み取り、正解ファイルや問題 ID の参照表を使わない。
- 検証スコアと Kaggle public score は区別する。0点や採点待ちもそのまま報告する。

## 確認と記録

変更に関連するテストを実行する。文書だけの修正で学習・提出を再実行しない。
テスト一覧とコマンドは WORKFLOWS.md を参照し、最後に `git diff --check` を行う。

作業が進んだら PROGRESS.md を更新する。実測結果は対象コンペの RESULTS.md に
実行条件・提出 ID / version・状態とともに記録する。数字を実測のように推測しない。
初心者向けの手順が変わったらルート README とコンペ README も合わせる。
`.agent/` には安定した案内を置き、進捗や成績の詳細を重複して管理しない。
