# __SLUG__

このディレクトリにコンペ固有のコード・設定・検証方法を置く。

- `config.json`: device と入出力パス（リポジトリルート基準）
- `requirements.txt`: コンペ固有の依存関係
- `src/`: 学習・前処理・検証コード
- `notebooks/`: 探索用 Notebook

リポジトリルートから依存関係をインストールする:

```bash
python -m pip install -r competitions/__SLUG__/requirements.txt
```

データは `data/__SLUG__/`、実験結果は `runs/__SLUG__/<run-id>/` に保存する。
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
