# モデル・解法を差し替える構成

読み込み・検証・提出形式はコンペの pipeline に、方式固有の前処理・学習・推論は
1つのクラスにまとめています。共通入口は引き続き `run(config, data_dir, output_dir)` です。

```text
run_experiment.py / Kaggle Notebook
  → run(config, data_dir, output_dir)
  → コンペの pipeline（読み込み・評価・提出）
  → 設定で選ぶクラス（方式固有の前処理・学習・推論）
```

## 共通化した処理

| ファイル | 役割 |
| --- | --- |
| `harness/artifacts.py` | CSV / TSV / ZIP 読み込み、JSON / CSV 保存、入力検索、ソース指紋 |
| `harness/components.py` | `module:class` の設定からクラスを作り、必要な関数を検査 |
| `harness/notebooks.py` | コンペ内の複数 Python と harness を Notebook に同梱・復元 |
| `harness/experiments.py` | 実験別の保存先・設定・指標・ソースハッシュの記録 |

NLP の ROC AUC や ARC のグリッド検査など、問題ごとの評価は各 pipeline に残します。
個別コンペのコードは Git 除外のままです。

## NLP：生レビューを境界にする

設定の `model` で方式を選びます。

| 設定値 | 選ばれる実装 |
| --- | --- |
| `embedding_bag_mlp` | `src/models/embedding_bag.py` の `EmbeddingBagEstimator` |
| `tfidf_logistic` | `src/models/tfidf.py` の `TfidfEstimator`（CPU） |
| `models.my_model:MyEstimator` | 自分のモジュール・クラス |

クラスはコンストラクターで config を受け取り、次の2関数を持ちます。

- `fit(texts, labels, validation_texts, validation_labels, output_dir)`：生レビューから学習し、方式固有の成果物を保存して学習情報の dict を返す。
- `predict(texts)`：レビューの順序を保ち、肯定確率を1件につき1個返す。

語彙・tokenizer の fit は学習側だけで行い、検証側は評価・モデル選択に使います。
TF-IDF や Transformer に変えても、共通の分割・評価・ID 整列・CSV 保存はそのまま使えます。
Transformer 自体の実装・追加依存・重みは別途用意します。
EmbeddingBag の層だけを変える場合は `network` に `models.my_network:MyNetwork` を指定し、
設定を受け取る PyTorch のクラスだけを追加できます。前処理・学習ループもそのまま使えます。
変更例は [初心者向け NLP ガイド](nlp-model-change.md) を参照してください。

## ARC：1問題を境界にする

設定の `solver` で `symbolic` または `models.my_solver:MySolver` を選びます。
クラスは config を受け取り、`solve(task)` を実装します。
task はその問題の例題と test 入力です。解法はファイルや正解ファイルを読みません。
戻り値は `(予測リスト, 適合した規則数)` です。規則探索をしない方式は規則数を0にできます。
予測は test と同じ順序・件数で、各要素に `attempt_1` と `attempt_2` を持ちます。

以下は入力をそのまま返す、クラスの形を理解するための例です。性能向上の解法ではありません。
`src/models/my_solver.py` に置けます。

```python
class MySolver:
    def __init__(self, config):
        self.device = "cpu"

    def solve(self, task):
        predictions = [
            {"attempt_1": row["input"], "attempt_2": row["input"]}
            for row in task["test"]
        ]
        return predictions, 0
```

元の設定を `configs/my-solver.json` にコピーし、`"solver": "models.my_solver:MySolver"` を加えます。

```bash
python scripts/run_experiment.py arc-prize-2026-arc-agi-2 --config configs/my-solver.json --name my-solver --device cpu
```

pipeline が全問題の予測を集め、ID・件数・グリッドの形と色を検査して `submission.json` を保存します。
公開評価には `validate: true`、Kaggle 採点には false または省略の設定を使います。
`solver.py` は従来 CLI の入口、規則は `src/models/symbolic.py`、
検査と公開評価は `src/validation.py`、実行順の管理は `src/pipeline.py` です。

## 新コンペでもクラスを選択する

自分のコンペの src パッケージ内で、次の関数を作れます。

```python
from harness.components import create_component

def build_model(config):
    return create_component(
        __package__, config["model"], config, ("fit", "predict")
    )
```

`config["model"]` に `models.my_model:MyModel` を入れ、対応するクラスを用意します。
fit / predict の引数と意味は自分のコンペで決めます。この例だけでは学習は始まりません。
別コンペのファイルを import する代わりに、汎用処理だけを harness に置いてください。
