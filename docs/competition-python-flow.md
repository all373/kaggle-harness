# 新コンペを自作する人向け：Python の実行順と入出力

このリポジトリでは、環境や実験記録の処理は共通 Python が担当し、データの読み込み・
モデル・検証・予測は自分で書きます。この文書は **何を実行すると、次に何が呼ばれるか** を順に説明します。
環境構築は [ルート README](../README.md)、参加・提出の詳しい操作は
[新しいコンペの手順](new-competition.md) を参照してください。

この文書は自分の Python を実装するルートの説明です。公開 Notebook から始める場合は
`scripts/import_kaggle_baseline.py` がコンペ名から選択・取得し、Python の `run()` は使いません。
その場合は [新しいコンペの手順4・A](new-competition.md#4-公開ベースラインを取り込むまたは自分で実装する) を使います。

個別コンペは Git 除外です。テンプレートだけが共有されます。
コマンドは Dev Container 内のリポジトリルートで実行します。

## 0. 登場するファイルを区別する

`scripts/` はターミナルから実行する入口、`harness/` はそこから呼ばれる共通処理です。
`competitions/<slug>/src/` は自分が実装する処理です。

| ファイル | 作る人 | 主な仕事 |
| --- | --- | --- |
| `scripts/new_competition.py` | 用意済み | コンペ用フォルダを作る |
| `scripts/kaggle_cli.py` | 用意済み | 認証を設定して Kaggle CLI を呼ぶ |
| `scripts/run_experiment.py` | 用意済み | 実行する Python と設定を選ぶ |
| `harness/experiments.py` | 用意済み | run 関数の呼び出し・実験記録 |
| `src/experiment.py` | 自分 | 学習・検証・予測を組み立てる |
| `src/data.py` / `src/features.py` | 必要なら自分 | 読み込み・前処理を分けるための任意ファイル |
| `src/models/my_model.py` | 必要なら自分 | モデル定義を分けるための任意ファイル |
| `harness/device.py` | 用意済み | CPU / CUDA の選択を補助する |
| `scripts/prepare_experiment_notebook.py` | 用意済み | 自作 Python を Kaggle Notebook にまとめる |

任意ファイルは自動では呼ばれません。`experiment.py` から import し、関数を呼んだときに動きます。
手元の NLP / ARC は分割済みで、設定からモデル・解法を選べます。
具体的な関数の契約は [モデル・解法を差し替える構成](components.md) を参照してください。

## 1. コンペ用フォルダを作る

```bash
export COMPETITION="titanic"
python scripts/new_competition.py "$COMPETITION"
```

**入力**は URL のコンペ名 `titanic` とテンプレートです。
**出力**は `competitions/titanic/` にコピーされた設定・README・Python の雛形です。
既存フォルダは拒否します。データのダウンロード、モデルの実装、学習は行いません。
`src/experiment.py` は未実装なので、そのまま実行すると `NotImplementedError` になります。

## 2. 依存関係とデータを用意する

使用するライブラリをコンペの `requirements.txt` に記載してインストールします。

```bash
python -m pip install -r "competitions/$COMPETITION/requirements.txt"
python scripts/kaggle_cli.py competitions files -c "$COMPETITION"
python scripts/kaggle_cli.py competitions download -c "$COMPETITION" -p "data/$COMPETITION"
```

ここで `kaggle_cli.py` はローカル認証設定を読み、トークンを子プロセスの環境変数に渡します。
実際の通信はインストール済みの `kaggle` CLI が行います。
`files` の出力は配布ファイル一覧、`download` の出力は `data/<slug>/` の配布ファイルです。
学習コードはまだ呼ばれません。規約同意は先にブラウザーで済ませます。

展開は配布形式に合わせて実施します。新コンペに自動の展開 Python は用意されていません。
繰り返し使う前処理なら、自分で `src/prepare_data.py` を作成できます。
その入力は配布データ、出力は読み込みやすいデータです。
共通の実験入口はこのファイルを自動実行しないため、必要なら別途実行するか run 内で呼びます。

## 3. 学習設定を書く

```bash
cp "competitions/$COMPETITION/config.json" "competitions/$COMPETITION/configs/my-model.json"
```

コピーは初回だけにして、自分の seed・モデル設定を追加します。
JSON は処理そのものではなく、Python に渡す値の集まりです。
例えば `learning_rate` を追加しても、実装がその値を読むまでは効果がありません。

| 設定・引数 | 共通入口での扱い |
| --- | --- |
| `data_dir` | ローカル入力フォルダ。リポジトリルート基準 |
| `device` | `auto` / `cpu` / `cuda` の値を実装へ渡す |
| `--entry` | 呼び出す Python ファイル。コンペ内の `src/` 以下 |
| `--config` | 読む JSON ファイル。コンペ内の相対パス |
| `--name` | 結果を分ける実験名 |
| config 内の `output_dir` | 共通入口では実験別の出力先を優先する |
| それ以外の設定 | 自分の run 関数が使う |

## 4. 最初に run 関数の入出力を確認する

共通入口は、選択した Python の次の関数を呼びます。

```python
def run(config: dict, data_dir: Path, output_dir: Path) -> dict:
    ...
```

| 引数・戻り値 | 実際に渡されるもの | 自分のコードで行うこと |
| --- | --- | --- |
| `config` | 選択した JSON の内容のコピー | seed・モデル設定などを読む |
| `data_dir` | 入力フォルダの Path | 配下から必要なファイルを読む |
| `output_dir` | 実行専用の新しい Path | フォルダを作り、モデル・予測を保存 |
| 戻り値 | 指標などの dict | Python の float / int 等で実測値を返す |

`Path` はファイルやフォルダを表す Python の型です。
`output_dir / "submission.csv"` と書くと、その出力先のファイルを表せます。
戻り値はファイル名だけではなく dict にします。NaN / Infinity は保存できません。

まず接続だけ確認したい場合、雛形の `src/experiment.py` を次のコードに置き換えられます。
**これは入力ファイルを確認するだけで、学習・予測・提出はできません。**

```python
import json
from pathlib import Path

def run(config: dict, data_dir: Path, output_dir: Path) -> dict:
    if not data_dir.is_dir():
        raise FileNotFoundError(f"入力フォルダがありません: {data_dir}")
    files = sorted(str(p.relative_to(data_dir))
                   for p in data_dir.rglob("*") if p.is_file())
    output_dir.mkdir(parents=True, exist_ok=False)
    report = {"input_files": files, "input_file_count": len(files)}
    (output_dir / "input-check.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"input_file_count": len(files)}
```

```bash
python scripts/run_experiment.py "$COMPETITION" --config configs/my-model.json --name input-check --device cpu
```

出力先の `input-check.json` と `experiment.json` が作られれば、呼び出しと保存の接続を確認できています。
input_file_count は実際に数えたファイル数で、モデルの精度ではありません。

## 5. run の中身を実際の学習に置き換える

入力確認ができたら、同じ run 関数に次の順番で処理を実装します。

| 順番 | 処理・置くファイルの例 | 入力 → 出力 | 効果 |
| --- | --- | --- | --- |
| 1 | 読み込み：`data.py` | 学習・テストのファイル → 表や配列 | 正解と特徴を取り出す |
| 2 | 分割：`experiment.py` | 学習データと seed → 学習側・検証側 | 未使用データで性能を見る |
| 3 | 特徴量：`features.py` | 学習側 → 変換器、検証・テスト → 特徴量 | モデルが受け取れる形にする |
| 4 | モデル定義：`models/my_model.py` | 構造の設定 → 未学習モデル | 計算方法を決める |
| 5 | 学習：`experiment.py` 等 | 学習側の特徴・正解 → 学習済みモデル | 重みを更新する |
| 6 | 検証：`experiment.py` 等 | 検証側の特徴・正解 → 指標 | 変更前後の性能を比べる |
| 7 | 推論：`experiment.py` 等 | テスト特徴・学習済みモデル → 予測 | 正解のないデータを予測する |
| 8 | 保存：`experiment.py` 等 | 予測・提出例・モデル → 提出物と重み | 提出・再利用できる形にする |

これらの関数名・ファイル分割は自分で決めます。共通入口はその中身を自動で作りません。
`from .features import ...` のように相対 import して run から呼びます。
前処理を学習側で fit してから検証・テストへ適用し、分割や seed も保存します。
学習済み重みとモデル定義の違いは [モデルの管理手順](models.md) を確認してください。

PyTorch でデバイスを選ぶ場合は `harness.device.resolve_device(config["device"])` を使えます。
戻り値は文字列 `cpu` / `cuda` で、モデルと入力をそのデバイスへ移す処理は自分で実装します。
GPU を使わないライブラリでは `--device cuda` だけで GPU 化はできません。

## 6. ローカル実行中に共通 Python が行うこと

```text
ターミナル
  → scripts/run_experiment.py の main()
  → harness/experiments.py の load_config() と execute()
  → 選択した src/experiment.py の run()
  → 自分の前処理・モデル・学習・検証・予測・保存
  → run() が指標の dict を返す
  → execute() が experiment.json を保存
  → main() が指標を表示して終了
```

`execute()` は Python を import し、run を呼びます。
そのファイルの `if __name__ == "__main__":` の中は実行されません。
学習をファイル最上段に書くと import 時に始まってしまうため、実行処理は run にまとめます。

`execute()` が作る出力先は `runs/<slug>/experiments/<name>/<実行ID>/` です。
自分のコードはそこに提出物などを保存し、共通処理は `experiment.json` に設定・指標・
処理時間・Python のソースハッシュを追加します。
ソースの全文はバックアップしないため、自分のコードと設定は別途保管します。

## 7. Kaggle 用 Notebook を生成する

学習と提出形式が実装できたら、実装が保存する提出ファイル名に合わせて生成します。
次は `output_dir/submission.csv` がある場合です。入力確認だけのコードでは進めません。

```bash
export KAGGLE_OWNER="your-kaggle-username"
python scripts/prepare_experiment_notebook.py "$COMPETITION" --owner "$KAGGLE_OWNER" --config configs/my-model.json --name my-model --device cpu --submission-file submission.csv
```

**入力**は選択した Python、JSON 設定、Notebook 名・デバイス・提出ファイル名です。
**出力**は `runs/<slug>/notebooks/my-model/experiment.ipynb` と `kernel-metadata.json` です。
ローカルでファイルを作るだけで、学習・通信・提出は行いません。
GPU 学習なら `--device cuda`、別ファイルなら `--entry src/my_model.py` を指定します。

Notebook には対象の `src/` と `harness/` の Python、選択設定を埋め込みます。
モデルの重み・配布データ・認証情報・requirements は自動同梱しません。
追加依存や資産は Kaggle 入力として準備する必要があります。

## 8. Kaggle で同じ run 関数を呼ぶ

```bash
python scripts/kaggle_cli.py kernels push -p "runs/$COMPETITION/notebooks/my-model" --timeout 3600
python scripts/kaggle_cli.py kernels status "$KAGGLE_OWNER/$COMPETITION-my-model"
```

push により Notebook が実行され、次の順に処理します。

```text
生成 Notebook
  → 埋め込んだ Python を /kaggle/working/workspace に配置
  → harness/experiments.py の execute()
  → 自分の run(config, data_dir, output_dir)
  → /kaggle/working/experiments/my-model/<実行ID>/ に保存
  → submission.csv を /kaggle/working/submission.csv にもコピー
```

ローカルと同じ run を使いますが、`data_dir` は `/kaggle/input` になります。
入力ファイルは配下のコンペ用フォルダなどにあるので、直下にあるとは決めつけません。
採点時に入力が差し替えられるコンペでは、その入力から毎回推論します。
ローカルの絶対パスや問題 ID を固定した予測は使えません。

## 9. 結果を取得し、提出する

COMPLETE 後に実際の Notebook バージョンを確認し、出力ファイルを取得します。
`kernels output` は学習をやり直さず、保存された成果物をダウンロードします。
取得した指標と提出ファイルを検査してから submit を実行します。
submit は採点を依頼する処理で、自分の Python の学習関数をローカルで呼ぶ処理ではありません。
Code Competition では指定した Notebook バージョンを Kaggle が採点時に再実行します。

ファイル提出と Notebook 提出のコマンドは
[新しいコンペの手順・提出](new-competition.md#7-提出してスコアを確認する) を参照してください。
この順序で、データ取得 → 自分の run の実装 → ローカル検証 → Notebook 生成 →
Kaggle 実行 → 結果取得 → 提出 → スコア記録まで進めます。
