# __SLUG__

このディレクトリにコンペ固有のコード・設定・検証方法を置く。

- `config.json`: device と入力パス（リポジトリルート基準）などの基本設定
- `configs/`: 自分の実験ごとの JSON 設定
- `requirements.txt`: コンペ固有の依存関係
- `src/`: 学習・前処理・検証コード
- `src/experiment.py`: `run(config, data_dir, output_dir)` の雛形。処理は自分で実装する
- `notebooks/`: 探索用 Notebook

リポジトリルートから依存関係をインストールする:

```bash
python -m pip install -r competitions/__SLUG__/requirements.txt
```

`src/experiment.py` を実装したら、リポジトリルートから実行する:

```bash
python scripts/run_experiment.py __SLUG__ --name baseline --device cpu
```

別実装は `--entry src/my_model.py`、別設定は `--config configs/my-model.json` で選ぶ。
データは `data/__SLUG__/`、共通入口の実験結果は
`runs/__SLUG__/experiments/<実験名>/<実行日時と識別子>/` に保存する。
config の `output_dir` ではなく、関数に渡された出力先へ保存する。
どちらも Git 管理対象外。CPU と GPU の比較では同じ分割・seed・指標を使う。
PyTorch を使う場合は `harness.device.resolve_device(config["device"])` で
`auto` / `cpu` / `cuda` を選ぶ。GPU 必須の処理には `cuda` を明示する。

コンペ開始時に以下を記入する:

- コンペ URL と評価指標:
- データ取得方法:
- 検証分割と seed:
- リポジトリルートから実行する学習・検証コマンド:
- ベースラインのスコア:

共有する際は、再現に必要な依存バージョンと実行コマンドも更新する。

追加・データ取得・Notebook 実行・提出の全手順は
[新しいコンペの手順](../../docs/new-competition.md)、
実装の契約と既存ベースラインからの変更方法は
[自分の実装を試す](../../docs/experiments.md) を参照する。
