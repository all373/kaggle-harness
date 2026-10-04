# 自分の実装を試す

既存のベースラインを残し、別ファイルと別設定で試せます。共通の実行入口は
`scripts/run_experiment.py`、Kaggle Notebook の生成は `scripts/prepare_experiment_notebook.py` です。
このページのコマンドはローカル実行・Notebook 生成までです。
外部実行と提出は [新しいコンペの手順](new-competition.md#6-kaggle-notebook-で実行する) を参照してください。

## 1. NLP の実装をコピーして変更する

データ取得と依存関係の導入は [NLP README](../competitions/word2vec-nlp-tutorial/README.md) を先に実施します。
CPU コンテナでローカル学習する場合は PyTorch の導入も必要です。

以下のコピーは初回だけ行います。すでに編集したファイルに再実行すると上書きされます。

```bash
mkdir -p competitions/word2vec-nlp-tutorial/configs
cp competitions/word2vec-nlp-tutorial/src/train.py competitions/word2vec-nlp-tutorial/src/my_model.py
cp competitions/word2vec-nlp-tutorial/config.json competitions/word2vec-nlp-tutorial/configs/my-model.json
```

`src/my_model.py` のモデル・前処理や `configs/my-model.json` の epoch・学習率を編集します。
元の `src/train.py` と `config.json` は比較用に残します。

```bash
# 元のベースラインを共通入口で実行
python scripts/run_experiment.py word2vec-nlp-tutorial --name baseline --device cpu

# 自分の実装・設定を実行
python scripts/run_experiment.py word2vec-nlp-tutorial --entry src/my_model.py --config configs/my-model.json --name my-model --device cpu
```

GPU コンテナで実行するときは `--device cuda` に変えます。
CPU / GPU 比較では同じ seed・検証分割・指標を使います。
デバイス指定は設定値として実装に渡すため、自分のコードでもその値を反映してください。
PyTorch なら `harness.device.resolve_device(config["device"])` を使えます。

## 2. 実験結果を見る

```text
runs/word2vec-nlp-tutorial/experiments/
  baseline/<実行日時と識別子>/
  my-model/<実行日時と識別子>/
    experiment.json
    metrics.json
    best-model.pt
    submission.csv
    ...
```

同じ `--name` で再実行しても出力先は新しく作られます。
`experiment.json` には選択したコード・設定・返された指標・処理時間・Python ソースの
SHA-256 を記録します。それ以外の成果物は各実装が保存します。
共通入口は config 内の `output_dir` よりも上の実験別保存先を優先します。
学習コードでは渡された `output_dir` に保存してください。

ソースはハッシュを記録し、全文のバックアップは作りません。
あとで同じ実装に戻せるよう、変更したコードと設定を Git にコミットしてください。
比較結果は `competitions/<slug>/RESULTS.md` に実行名・指標・条件と一緒に残します。
検証スコアと Kaggle public score は別々に記録します。

## 3. 実装の共通入口

`--entry` はコンペ内の `src/` 以下の Python ファイルです。
`--config` はコンペ内の JSON ファイルで、どちらもリポジトリルートからのパスではありません。
`--name` は英小文字・数字・ハイフンを使います。Python ファイル名にはアンダースコアを使えます。

実装には次の関数を用意します。

```python
from pathlib import Path

def run(config: dict, data_dir: Path, output_dir: Path) -> dict:
    # ここで読み込み・学習・検証・テスト予測を行う。
    # output_dir は新規パスなので、実装側で作成する。
    output_dir.mkdir(parents=True, exist_ok=False)
    # モデルや submission.csv / submission.json を output_dir に保存する。
    # 実測した指標を Python の float / int などの JSON 化できる値で返す。
    raise NotImplementedError("自分の学習・推論処理を実装してください")
```

この例は関数の形を示すもので、学習コードではありません。
NaN / Infinity の指標は実験記録として保存できません。
実装を `src/features.py` などに分ける場合は `from .features import ...` で相対 import できます。
さらにサブフォルダを作る場合はその中にも `__init__.py` を置いてください。
他コンペのコードを直接 import する代わりに、共通処理は `harness/` に置きます。

## 4. 自分のコードを Kaggle GPU に送る準備

```bash
export KAGGLE_OWNER="your-kaggle-username"
python scripts/prepare_experiment_notebook.py word2vec-nlp-tutorial --owner "$KAGGLE_OWNER" --entry src/my_model.py --config configs/my-model.json --name my-model --device cuda --submission-file submission.csv
```

このコマンドはローカルで `runs/word2vec-nlp-tutorial/notebooks/my-model/` に
Notebook と metadata を生成します。まだ GPU 実行も提出も行いません。
実行方法・依存関係・Notebook バージョンの扱いは [新しいコンペの手順](new-competition.md) を参照してください。
既存の `run_kaggle_training.py` は元の NLP ベースライン用なので、自分の `--entry` には共通生成スクリプトを使います。

## 5. ARC の別実装を試す

ARC にも `src/experiment.py` があり、既存 solver を共通入口から呼べます。
ローカルで公開評価を行う場合は、コピーした設定に `"validate": true` を加えます。

```bash
mkdir -p competitions/arc-prize-2026-arc-agi-2/configs
cp competitions/arc-prize-2026-arc-agi-2/config.json competitions/arc-prize-2026-arc-agi-2/configs/local-validation.json
# エディターで local-validation.json に "validate": true を追加してから実行
python scripts/run_experiment.py arc-prize-2026-arc-agi-2 --config configs/local-validation.json --name baseline-validation --device cpu
```

自作 solver は別ファイルに置き、上の `run(config, data_dir, output_dir)` 形式で呼び出します。
既存 solver の関数は引数が異なるため、`src/experiment.py` の adapter を参考にしてください。
現在の規則探索は CPU 用です。`--device cuda` を指定しても GPU モデルにはなりません。
Kaggle 実行では公開正解を参照しない設定（`validate` を省略するか `false`）を使い、
採点時に差し替えられる入力から予測します。
