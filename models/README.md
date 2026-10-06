# モデルの保管庫

このフォルダには、再利用する事前学習済みモデルや、選んだ学習済みモデルを保管します。
Git で共有するのはこの README だけです。重み・設定・辞書・成績などの実物は Git 除外です。

```text
models/
  README.md
  pretrained/<モデル名>/<バージョン>/
    weights.safetensors
    config.json
    tokenizer.json
    model-card.json
  trained/<コンペ名>/<モデル名>/<バージョン>/
    best-model.pt
    config.json
    vocab.json
    model-card.json
```

中身のファイル名はモデルの保存形式に合わせます。上は配置例で、実物は各自のローカルに保存します。
`pretrained/` と `trained/` はローカルに作成済みです。
新しく clone した環境では `mkdir -p models/pretrained models/trained` で作成できます。

モデル定義の Python コードは `competitions/<slug>/src/models/`、コンペだけで使う
重み・関連ファイルは `competitions/<slug>/models/` に置きます。
実験中のチェックポイントは `runs/` に残し、再利用したいものだけここにコピーします。
詳しい配置・保存・読み込み方法は [モデルの管理手順](../docs/models.md) を参照してください。
