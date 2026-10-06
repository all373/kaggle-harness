# モデルの定義・使用・保管

モデルのコードと重みを分け、実験結果を残したまま再利用できる構成です。

| 場所 | 用途 | Git 管理 |
| --- | --- | --- |
| `competitions/<slug>/src/models/` | モデルのクラス・構築関数などの Python コード | 個別コンペは除外 |
| `competitions/<slug>/models/` | そのコンペで使う重み・設定・辞書 | 個別コンペは除外 |
| `runs/<slug>/experiments/…/` | 各学習実行のチェックポイント・検証・予測 | 除外 |
| `models/pretrained/<name>/<version>/` | コンペ横断で使う事前学習モデル | 除外 |
| `models/trained/<slug>/<name>/<version>/` | 選んで保管する自分の学習済みモデル | 除外 |

Git で共有するのはテンプレートと案内です。保管庫内では `models/README.md` のみ共有します。
重みが JSON や独自の拡張子でも、README 以外の保管庫の中身は Git 除外になります。

## モデルを定義する

新しいコンペを作成すると `src/models/__init__.py` と `models/README.md` も作成されます。
例えばモデルを `src/models/my_model.py` に実装し、`src/experiment.py` から次のように呼びます。

```python
from .models.my_model import MyModel
```

`MyModel` は自分で定義するクラスです。既存コンペは、必要なときに
`src/models/` と `models/` を追加してください。既存のモデル定義や保存先は自動で移動しません。

## 重みを保管する

学習中はこれまでどおり `run(config, data_dir, output_dir)` に渡された `output_dir` に
チェックポイントを保存します。検証して採用したモデルだけ別の保存先にコピーします。
以下はリポジトリルートで実行する例です。

```bash
export COMPETITION="your-competition"
export MODEL_NAME="my-model"
export MODEL_VERSION="v1"
# 実際に学習した実験フォルダに置き換える
export MODEL_RUN="runs/$COMPETITION/experiments/$MODEL_NAME/実際の実行ID"

# コンペで利用するモデルを置く
mkdir -p "competitions/$COMPETITION/models/$MODEL_NAME"
cp -r "$MODEL_RUN" "competitions/$COMPETITION/models/$MODEL_NAME/$MODEL_VERSION"

# 長期保管したいモデルを保管庫へコピーする
mkdir -p "models/trained/$COMPETITION/$MODEL_NAME"
cp -r "competitions/$COMPETITION/models/$MODEL_NAME/$MODEL_VERSION" "models/trained/$COMPETITION/$MODEL_NAME/$MODEL_VERSION"
```

コピー先のバージョンは新しい名前を選び、すでに存在する場合は実行しないでください。
この例は実験フォルダ全体をコピーするので、指標や設定も一緒に残ります。
サイズを抑えたい場合は、重みと推論に必要な設定・前処理の資産だけを選んでコピーします。
PyTorch の重みだけを保存したモデルは、対応するモデル定義のコードも別途必要です。
モデル定義はコンペ側でバックアップしておきます。

事前学習モデルは `models/pretrained/<name>/<version>/` に、配布元の形式を保って配置します。
取得元・バージョン・ライセンス・使用したコンペの設定・学習コードのバックアップ先を
各モデルの `model-card.json` や README に残すと、後から何か判別できます。
これらの個人の記録も Git 除外です。モデルの自動ダウンロード・登録・同期は行いません。

## コンペで読み込む

実験設定には、使用するファイルのパスを自分で追加します。

```json
{
  "model_path": "models/trained/your-competition/my-model/v1/best-model.pt"
}
```

上は設定項目の例です。共通実行入口はこの項目を自動で読み込みません。
実装側で `Path(config["model_path"])` を読み、使用するライブラリの方法でロードしてください。
ローカルではリポジトリルートから実行するので、この相対パスを利用できます。
CPU / GPU を切り替える場合は重みの読み込み先とモデルの実行デバイスを揃えます。

コンペ用コピーを使うなら、パスを `competitions/<slug>/models/<name>/<version>/…` にします。
同じ重みを各コンペへコピーせず、直下の `models/` を直接参照することもできます。

## Kaggle Notebook で使う

`prepare_experiment_notebook.py` は `src/` 以下の Python コードを同梱するため、
`src/models/` のモデル定義も同梱されます。
**重みを入れた2種類の `models/` フォルダは、自動ではアップロードされません。**

規約に従って重みと必要な設定・辞書を Kaggle Dataset / Model の入力に用意し、
metadata の `dataset_sources` / `model_sources` を設定します。
Kaggle 用の実験設定では `model_path` を、その入力の `/kaggle/input/…` のパスに変更します。
オフラインで必要なファイルが揃っていることを確認してから実行してください。
詳しい Notebook の実行方法は [新しいコンペの手順](new-competition.md#6-kaggle-notebook-で実行する) を参照してください。
