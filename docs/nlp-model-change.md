# 初心者向け：映画レビューのモデルを変更して試す

対象は手元の `competitions/word2vec-nlp-tutorial/` です。
個別コンペは Git 除外なので、新しく clone した環境にはこの実装がありません。
新コンペを自作する場合は [Python の実行順と入出力](competition-python-flow.md) を参照してください。
コマンドは Dev Container 内のリポジトリルートで実行します。

## 1. 変更する場所を知る

学習ファイル全体をコピーする必要はありません。モデルを選ぶ設定と、モデル自身の処理を分けています。

| ファイル | 役割 | モデル変更で編集するか |
| --- | --- | --- |
| `src/train.py` | 従来コマンドの入口 | 通常は編集しない |
| `src/experiment.py` | 共通実験入口の run 関数 | 通常は編集しない |
| `src/data.py` | データ読み込み・ID 検査・検証分割 | 入力形式を変えるとき |
| `src/pipeline.py` | 指標計算・予測の検査・提出ファイル作成 | 通常は編集しない |
| `src/features.py` | EmbeddingBag 用の単語処理・バッチ | その方式の前処理を変えるとき |
| `src/models/embedding_bag.py` | EmbeddingBag のモデル・前処理・学習・推論 | ニューラルモデルを変えるとき |
| `src/models/tfidf.py` | TF-IDF とロジスティック回帰 | CPU 方式の変更例 |
| `src/interfaces.py` | モデルに必要な関数の説明 | 仕様を読む |
| `configs/<実験名>.json` | 選択するモデルと学習設定 | まずここを編集する |

入力が異なるモデルでも、生のレビューを受け取る `fit()` と `predict()` にまとめます。
Transformer 用の tokenizer もそのモデル側に置くので、共通 pipeline を書き換える必要はありません。

## 2. データと依存関係を準備する

環境・Kaggle 認証・コンペの規約同意は [ルート README](../README.md) を参照します。

```bash
python -m pip install -r requirements-kaggle.txt
python -m pip install -r competitions/word2vec-nlp-tutorial/requirements.txt
python scripts/kaggle_cli.py competitions download -c word2vec-nlp-tutorial -p data/word2vec-nlp-tutorial
python -m competitions.word2vec-nlp-tutorial.src.prepare_data
```

すでに展開済みなら取得と展開は省略します。再展開は同名データを上書きします。
EmbeddingBag を手元で学習するには PyTorch が必要です。GPU コンテナには導入済みです。
TF-IDF を選ぶ場合はこのコンペの実装から PyTorch を読み込まないので、CPU 環境でも試せます。

| データ | 用途 |
| --- | --- |
| `labeledTrainData.tsv` | 正解付きレビュー。学習と検証に分割 |
| `testData.tsv` | 提出する予測を作るレビュー |
| `sampleSubmission.csv` | 提出列と ID の順序 |
| `unlabeledTrainData.tsv` | 現在の2方式では使用しない |

## 3. 自分の設定を作って、学習回数だけ変える

次のコピーは初回だけ行い、すでに変更した設定を上書きしないでください。

```bash
mkdir -p competitions/word2vec-nlp-tutorial/configs
cp competitions/word2vec-nlp-tutorial/config.json competitions/word2vec-nlp-tutorial/configs/my-model.json
```

`configs/my-model.json` の `epochs` を、動作確認の例として `2` にします。
JSON は二重引用符を使い、コメントや最後の余分なカンマを書きません。

```bash
python scripts/run_experiment.py word2vec-nlp-tutorial --config configs/my-model.json --name quick-check --device cpu
```

同じ seed と validation_size を使えば、モデルを変えても同じ検証 ID で比較できます。
主な設定は `learning_rate`（更新の大きさ）、`batch_size`（一度に読む件数）、
`embedding_dim` / `hidden_dim`（層の幅）、`dropout`（過学習を抑える設定）です。
これらは EmbeddingBag 側が読む設定です。TF-IDF には自動適用されません。

## 4. 方式そのものを設定で変える

`configs/my-model.json` の **model 項目**を次に変更します。他の設定は残します。

```json
"model": "tfidf_logistic"
```

上は JSON の1項目の抜粋です。ファイル全体をこの1行に置き換えないでください。

```bash
python scripts/run_experiment.py word2vec-nlp-tutorial --config configs/my-model.json --name tfidf --device cpu
```

これで TF-IDF + ロジスティック回帰に変わります。データ分割・検証・提出の Python は同じです。
この方式の任意設定は `tfidf_max_features`、`logistic_c`、`logistic_max_iter` です。
元の方式に戻す場合は `"model": "embedding_bag_mlp"` にします。
TF-IDF は CPU 用なので `--device cuda` は使いません。スコアの向上は保証されません。

## 5. 層の構造だけを変える場合は、モデルクラスだけ書く

EmbeddingBag の入力処理と学習方法をそのまま使い、層だけを変える場合は、
`src/models/my_network.py` を作って次のクラスを置きます。
新しいファイルを作るだけで、学習ループのコピーは不要です。

```python
from torch import nn
from .embedding_bag import SentimentModel

class MyNetwork(SentimentModel):
    def __init__(self, config):
        super().__init__(config["num_embeddings"], config)
        self.classifier = nn.Sequential(
            nn.Linear(config["embedding_dim"], config["hidden_dim"]),
            nn.ReLU(),
            nn.Dropout(config["dropout"]),
            nn.Linear(config["hidden_dim"], config["hidden_dim"]),
            nn.ReLU(),
            nn.Linear(config["hidden_dim"], 1),
        )
```

元のクラスを継承し、中間層を1つ増やす例です。
config の `num_embeddings` は学習側で作った語彙の実際のサイズで、学習処理が渡します。
この数を自分で固定しないでください。
設定の model を `embedding_bag_mlp` に戻し、network を追加します。

```json
"model": "embedding_bag_mlp",
"network": "models.my_network:MyNetwork"
```

上は設定の2項目の抜粋です。他の項目は残します。
元の `forward(self, tokens, offsets)` を引き継ぎ、出力はレビューごとの実数1個です。
学習時に logits 用の損失、推論時に sigmoid を使うため、このモデルに sigmoid を追加しません。
以前の重みは形が合わない可能性があるので、新しく学習します。

```bash
python scripts/run_experiment.py word2vec-nlp-tutorial --config configs/my-model.json --name deeper-mlp --device cpu
```

GPU コンテナなら `--device cuda` にします。利用できない場合は失敗します。
この変更で読み込み・前処理・学習ループ・評価・提出処理を編集する必要はありません。
元の構造に戻す場合は network 項目を削除します。

## 6. Transformer など新しい方式を書く場合

`src/models/my_transformer.py` に、設定を受け取るクラスと次の2関数を実装します。
既存の `src/interfaces.py` と2種類のモデルが参考になります。

| 関数 | 入力 | 出力・保存 |
| --- | --- | --- |
| `__init__(config)` | モデルの設定 | tokenizer・モデルの準備など |
| `fit(texts, labels, validation_texts, validation_labels, output_dir)` | 生レビュー・学習正解・検証レビューと正解 | 学習し、重み等を保存。学習情報の dict を返す |
| `predict(texts)` | 生レビューのリスト | 入力順で0〜1の肯定確率を1件につき1個返す |

設定は `"model": "models.my_transformer:MyTransformerEstimator"` のように指定します。
独自の tokenizer、バッチ化、学習ループ、重みの読み込みはそのクラスにまとめます。
共通 pipeline が学習・検証分割、ROC AUC 計算、提出 ID の整列、CSV 保存を担当します。
Transformer 自体の実装・依存関係・事前学習重みはまだ用意されていません。
保管済みモデルを使う方法は [モデルの管理手順](models.md) を参照してください。

## 7. 実験結果を比較する

```text
runs/word2vec-nlp-tutorial/experiments/
  quick-check/<実行ID>/
  tfidf/<実行ID>/
  deeper-mlp/<実行ID>/
```

| 成果物 | 見る内容 |
| --- | --- |
| `metrics.json` | 検証 ROC AUC・accuracy・採用 epoch（方式によっては null） |
| `history.json` | EmbeddingBag の epoch ごとの学習・検証結果 |
| `split.json` | 学習と検証の ID。方式を変えても同じか確認 |
| `best-model.pt` / `best-model.joblib` | 各方式が保存した重み・学習済み変換器 |
| `vocab.json` | EmbeddingBag の語彙。TF-IDF は学習済み変換器に保持 |
| `validation_predictions.csv` | 検証データの正解と予測確率 |
| `submission.csv` | テストデータの提出用予測 |
| `experiment.json` | 使用した設定・指標・Python のハッシュ |

ROC AUC は大きいほど良い指標です。loss が下がるだけで改善とは判断しません。
同じ検証分割で比較し、最良 epoch の選択にもその検証データを使うことを考慮します。
実装が返す確率の件数・範囲・欠損は共通 pipeline が検査します。
個別コンペは Git 除外なので、コードと設定は自分でバックアップしてください。

## 8. Kaggle GPU で自分のモデルを動かす

手元の学習を省略して Kaggle GPU を使う場合も、自分の Python と設定を選びます。

```bash
export KAGGLE_OWNER="your-kaggle-username"
python scripts/prepare_experiment_notebook.py word2vec-nlp-tutorial --owner "$KAGGLE_OWNER" --entry src/experiment.py --config configs/my-model.json --name deeper-mlp --device cuda --submission-file submission.csv
```

これは EmbeddingBag 系の設定で GPU を使う例です。TF-IDF の設定なら `--device cpu` に変えます。これは生成だけです。`src/models/` の Python も同梱しますが、保管済みの重みは同梱しません。
依存関係が Kaggle 環境に揃っているか確認してから実行します。

```bash
python scripts/kaggle_cli.py kernels push -p runs/word2vec-nlp-tutorial/notebooks/deeper-mlp --timeout 3600
python scripts/kaggle_cli.py kernels status "$KAGGLE_OWNER/word2vec-nlp-tutorial-deeper-mlp"
```

COMPLETE になったら Notebook ページで実際のバージョン番号を確認します。
次の `1` は実際の番号に置き換えます。

```bash
export NOTEBOOK_VERSION="1"
python scripts/kaggle_cli.py kernels output "$KAGGLE_OWNER/word2vec-nlp-tutorial-deeper-mlp/$NOTEBOOK_VERSION" -p "runs/word2vec-nlp-tutorial/downloads/deeper-mlp-v$NOTEBOOK_VERSION"
```

既存の `run_kaggle_training.py` も分割後の全モジュールを同梱します。別設定・別実験名を選ぶ場合は上の共通生成コマンドを使います。

## 9. 提出は結果を確認してから行う

取得した指標と `submission.csv` の ID・列名・件数・予測値を確認します。
この実装は提出例の順序で `id,sentiment` を出力し、sentiment は0〜1の確率です。
`submission-binary.csv` は比較用の0/1予測で、ここでは確率の `submission.csv` を使います。

```bash
python scripts/kaggle_cli.py competitions submit word2vec-nlp-tutorial -f "runs/word2vec-nlp-tutorial/downloads/deeper-mlp-v$NOTEBOOK_VERSION/submission.csv" -m "deeper-mlp v$NOTEBOOK_VERSION"
python scripts/kaggle_cli.py competitions submissions word2vec-nlp-tutorial
```

`submit` は毎回新しい提出になります。状態が不明ならまず提出一覧を確認します。
検証スコアと Kaggle public score は別々にコンペ内の `RESULTS.md` に記録します。
個別コンペのコード・重み・成績は Git 除外のまま管理してください。

## 困ったとき

| エラーや疑問 | 確認すること |
| --- | --- |
| `No module named torch` | ローカル学習環境に PyTorch があるか |
| `Missing labeledTrainData.tsv` | データ取得・二段階の ZIP 展開が済んでいるか |
| CUDA required | GPU コンテナまたは Kaggle GPU を使っているか |
| 行列のサイズが合わない | Linear の入力・出力と embedding_dim / hidden_dim が一致するか |
| メモリ不足 | batch_size やモデル容量を減らして再確認 |
| 設定を変えても効かない | `--config` が編集したファイルか、コードがその設定項目を読むか |
| Notebook に変更が反映されない | 正しい `--entry` で再生成し、新しい version を実行したか |
