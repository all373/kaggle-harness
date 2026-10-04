# 新しい Kaggle competition を追加して提出する

VS Code・WSL・Dev Container・Kaggle 認証は [ルート README](../README.md) の手順で準備します。
ここからは **コンテナ内ターミナル、リポジトリルート** で作業します。
例では `titanic` を使います。自分のコンペでは URL の `/competitions/` に続く名前に置き換えます。
既存の NLP / ARC の再現には、それぞれのコンペ README を使ってください。

## 1. 参加条件と提出方式を確認する

コンペの Overview・Rules・Data・Evaluation を読み、ブラウザーで参加・規約同意を済ませます。
評価指標、提出ファイル名・形式、外部データの利用条件、締切を確認してください。
Code Competition では Notebook を再実行して採点するため、オフライン実行・制限時間・
採点時の入力の扱いも確認します。コンペごとの規約を優先します。

```bash
export COMPETITION="titanic"
export EXPERIMENT="my-model"
export KAGGLE_OWNER="your-kaggle-username"
```

`KAGGLE_OWNER` は Kaggle のプロフィール URL のユーザー名です。トークンは書きません。
この3変数は新しいターミナルで再設定します。実験名は英小文字・数字・ハイフンで決めます。

## 2. コンペ用フォルダを作る

```bash
python scripts/new_competition.py "$COMPETITION"
```

```text
competitions/titanic/
  README.md
  config.json
  configs/README.md
  requirements.txt
  src/__init__.py
  src/experiment.py
  notebooks/
```

既存フォルダは上書きしません。すでにある場合はそのフォルダで続きを進めます。
`src/experiment.py` は関数の雛形です。**モデルはまだ実装されていないため、この段階では学習・提出はできません。**
README にコンペ URL・指標・データ取得方法・検証方針を書いておきます。

## 3. データを取得して構造を確認する

```bash
python scripts/kaggle_cli.py competitions files -c "$COMPETITION"
python scripts/kaggle_cli.py competitions download -c "$COMPETITION" -p "data/$COMPETITION"
python -m zipfile -l "data/$COMPETITION/$COMPETITION.zip"
python -m zipfile -e "data/$COMPETITION/$COMPETITION.zip" "data/$COMPETITION"
```

ZIP 名は実際にダウンロードされたものに合わせます。ZIP 以外の形式や二重の ZIP は
配布形式に合わせて展開します。NLP の二重 ZIP は専用の `prepare_data.py` が対応します。
403 の場合は規約同意・参加条件を、401 の場合はローカル認証設定を確認します。

学習ラベル、テストデータ、提出例の列名・件数・ID・欠損値を確認します。
データは `data/<slug>/` に置き、Git には追加しません。
Kaggle Notebook では入力の基点が `/kaggle/input` に変わります。
実装では渡された `data_dir` の下からファイルを探し、Windows の絶対パスを埋め込まないでください。

## 4. 自分の設定と実装を作る

初回だけ設定をコピーします。

```bash
cp "competitions/$COMPETITION/config.json" "competitions/$COMPETITION/configs/$EXPERIMENT.json"
python -m pip install -r "competitions/$COMPETITION/requirements.txt"
```

必要なライブラリを `requirements.txt` に追記し、再現に必要なバージョンを記録します。
空の requirements は何もインストールしません。
`configs/my-model.json` に seed、分割比率、モデルのパラメーターなどを追加します。
設定には認証情報を書きません。選択した設定は Kaggle Notebook に埋め込まれます。

`src/experiment.py` を編集するか、自分の `src/my_model.py` を作ります。
必須の入口は `run(config, data_dir, output_dir)` です。
関数の形・実験ファイルの分け方は [自分の実装を試す](experiments.md#3-実装の共通入口) を参照してください。
既存 NLP にはそのままコピーして変更できる学習コードがあります。

実装する処理は次の順序です。

1. `data_dir` 以下から学習・テスト・提出例を読む。ローカルと Kaggle の両方で動くようにする。
2. 学習データを学習用と検証用に分け、seed と分割方法を保存する。
3. 前処理や特徴量変換を学習側で fit してから、検証側へ適用する。
4. モデルを学習し、コンペの指標で検証スコアを計算する。
5. テストデータを予測し、提出例と同じ ID・列・順序・形式で保存する。
6. モデルや予測を渡された `output_dir` に保存し、実測した指標を dict で返す。

分類の層化分割、時系列の時間順分割、同一人物などのグループ分割は問題に合わせて選びます。
テストの正解や検証側で fit した特徴量を学習に混ぜないようにします。
提出物は CSV に限りません。ARC なら `submission.json` のグリッド形式を実装します。

## 5. ローカルで学習・検証する

`src/my_model.py` を作成した場合のコマンドです。雛形を直接編集した場合は
`--entry src/experiment.py` にします。

```bash
python scripts/run_experiment.py "$COMPETITION" --entry src/my_model.py --config "configs/$EXPERIMENT.json" --name "$EXPERIMENT" --device cpu
```

ローカル NVIDIA GPU で学習する場合は GPU Dev Container を使い、`--device cuda` に変えます。
`auto` は実装に自動選択を任せる指定です。共通入口だけではモデルを GPU に移しません。
入力を別の場所に置いた場合は `--data-dir /実際のデータパス` を付けます。

結果は `runs/<slug>/experiments/<name>/<実行日時と識別子>/` に保存されます。
`experiment.json` で設定・指標・コードのハッシュを確認し、モデルの成果物も確認します。
同じ名前で再実行しても前の結果は残ります。
GPU を Kaggle 側だけで使う場合、ローカルの本学習を省略して次へ進めますが、
入力読み込みや提出形式は小さいデータでも確認してください。

## 6. Kaggle Notebook で実行する

実装が `output_dir/submission.csv` を生成する場合の例です。

```bash
python scripts/prepare_experiment_notebook.py "$COMPETITION" --owner "$KAGGLE_OWNER" --entry src/my_model.py --config "configs/$EXPERIMENT.json" --name "$EXPERIMENT" --device cpu --submission-file submission.csv
```

GPU 学習なら `--device cuda` に変えます。生成段階では API を呼びません。
`runs/<slug>/notebooks/<name>/` に `experiment.ipynb` と `kernel-metadata.json` ができます。
Notebook ID は `<owner>/<slug>-<name>` です。
同じコンペ・実験名での再生成はアップロード用の2ファイルを更新します。
違う Notebook として比較したい場合は実験名を変えます。

生成 Notebook は非公開・インターネット無効で、コンペデータを入力に追加します。
対象コンペの `src/` 以下と `harness/` の Python ファイル、選択した JSON 設定を同梱します。
相対 import した補助モジュールも含まれます。ローカルトークン・配布データ・モデルは同梱しません。
Python ソースと選択設定の中にも秘密情報を書かないでください。

**依存ライブラリの自動インストールと、Python 以外の資産の同梱は行いません。**
ローカルの requirements や Dockerfile は Kaggle に適用されません。
足りないライブラリ、事前学習モデル、辞書などは規約に従って Kaggle Dataset / Model の
入力として用意し、metadata の `dataset_sources` / `model_sources` や読み込み処理を調整します。
オフラインで追加ライブラリを入れる場合は wheel と依存 wheel を入力に用意して
Notebook にインストール処理を追加します。再生成で手編集が消えるため、必要な変更は
生成スクリプト側にも反映して再現可能にしてください。

ローカル依存関係が揃っている場合は、生成 Notebook を Jupyter で開き、
入出力パスをローカル用に調整して読み込みや import を確認できます。
Kaggle GPU の利用条件・残り枠は本人のアカウント画面で確認します。

準備できたらアップロードして実行します。

```bash
python scripts/kaggle_cli.py kernels push -p "runs/$COMPETITION/notebooks/$EXPERIMENT" --timeout 3600
python scripts/kaggle_cli.py kernels status "$KAGGLE_OWNER/$COMPETITION-$EXPERIMENT"
```

`push` は新しい Notebook バージョンを作り、学習・推論を開始します。
`status` が COMPLETE になるまで確認します。ERROR なら Notebook のログを読んで修正します。
RUNNING / QUEUED の間に再 push すると別の実行が増えるため、状態確認で待ちます。
timeout はモデルとコンペの上限に合わせて調整します。

完了した Notebook のページでバージョン番号を確認し、その番号を指定して取得します。
以下の `1` は例です。実際の番号に置き換えます。

```bash
export NOTEBOOK_VERSION="1"
python scripts/kaggle_cli.py kernels output "$KAGGLE_OWNER/$COMPETITION-$EXPERIMENT/$NOTEBOOK_VERSION" -p "runs/$COMPETITION/downloads/$EXPERIMENT-v$NOTEBOOK_VERSION"
```

`--submission-file submission.csv` は生成されたファイルを `/kaggle/working/submission.csv` にもコピーします。
取得先にある `submission.csv` と実験フォルダ内の指標を確認します。
ファイルが作られていない場合、Notebook は失敗します。名前は実装と揃えてください。

## 7. 提出してスコアを確認する

提出前に、提出例と列名・行数・ID・予測値の範囲を比較し、欠損や重複がないことを確認します。
Notebook が完了しただけではコンペに提出されません。

### CSV などのファイルをアップロードするコンペ

```bash
python scripts/kaggle_cli.py competitions submit "$COMPETITION" -f "runs/$COMPETITION/downloads/$EXPERIMENT-v$NOTEBOOK_VERSION/submission.csv" -m "$EXPERIMENT notebook-v$NOTEBOOK_VERSION"
python scripts/kaggle_cli.py competitions submissions "$COMPETITION"
```

ローカルで学習した提出物なら `-f` を該当する実験フォルダのファイルに変更します。
`submit` を実行するたびに新しい提出になります。通信が途切れた場合も、
まず提出一覧でメッセージ・ID・状態を確認してから再試行します。

### ARC などの Code Competition

こちらは Notebook の指定バージョンを提出します。
上の生成コマンドを `--submission-file submission.json` に変更し、実装で
`output_dir/submission.json` を生成してから push・完了確認・バージョン確認を行います。
ARC の場合は `COMPETITION` を `arc-prize-2026-arc-agi-2` にし、
公開正解を読む `validate` は `false` にした設定を選びます。

```bash
python scripts/kaggle_cli.py competitions submit "$COMPETITION" -k "$KAGGLE_OWNER/$COMPETITION-$EXPERIMENT" -v "$NOTEBOOK_VERSION" -f submission.json -m "$EXPERIMENT notebook-v$NOTEBOOK_VERSION"
python scripts/kaggle_cli.py competitions submissions "$COMPETITION"
```

`-f` は採点時に Notebook が出力するファイル名です。
毎回変わる日時付きの実験パスではなく、`--submission-file` がコピーした固定の出力を使います。
採点時に入力が差し替えられても同じコードで推論できる必要があります。
ローカル JSON をアップロードする方式には置き換えません。
既存 ARC ベースラインをそのまま提出する場合は [ARC README](../competitions/arc-prize-2026-arc-agi-2/README.md) の専用コマンドも使えます。

採点待ちなら提出一覧を再確認し、COMPLETE とスコアを確認します。
検証スコアと public score の違いを確認し、次の改善は検証スコアも使って判断します。

## 8. 記録して GitHub で共有する

`competitions/<slug>/RESULTS.md` を作り、次を記録します。

- 実験名、実行コマンド、コードの commit / ハッシュ、設定、依存関係
- 検証分割・seed・検証スコア
- Notebook ID・バージョン・提出 ID・採点状態・Kaggle public score
- 改善した点と、次に試すこと

```bash
git status --short
git diff --check
git add "competitions/$COMPETITION"
git diff --cached --stat
git commit -m "Add competition implementation and experiment notes"
git push
```

ステージした内容を確認してからコミットします。認証情報・データ・成果物は Git 除外です。
共通コードや手順も変更した場合は、そのファイルも選んで追加してください。
他の人は同じコードを取得し、自分の認証とデータを設定して再現します。

CLI 引数はこの環境に導入済みの `--help` で確認しています。
別環境で挙動が変わる場合は `python scripts/kaggle_cli.py <サブコマンド> --help` と
[公式 CLI ドキュメント](https://github.com/Kaggle/kaggle-cli/blob/main/docs/README.md)、
[公式 Notebook metadata](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels_metadata.md) を確認してください。
