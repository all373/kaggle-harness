# 新しい Kaggle competition を追加して提出する

VS Code・WSL・Dev Container・Kaggle 認証は [ルート README](../README.md) の手順で準備します。
ここからは **コンテナ内ターミナル、リポジトリルート** で作業します。
例では `titanic` を使います。自分のコンペでは URL の `/competitions/` に続く名前に置き換えます。
既存の NLP / ARC の再現には、それぞれのコンペ README を使ってください。
実行する Python の役割と入出力は [Python の実行順と入出力](competition-python-flow.md) で説明しています。
公開ベースラインから始める場合の実行コマンドだけを追うには [コマンド集](competition-commands.md) を使ってください。

## 1. 参加条件と提出方式を確認する

コンペの Overview・Rules・Data・Evaluation を読み、ブラウザーで参加・規約同意を済ませます。
評価指標、提出ファイル名・形式、外部データの利用条件、締切を確認してください。
Code Competition では Notebook を再実行して採点するため、オフライン実行・制限時間・
採点時の入力の扱いも確認します。コンペごとの規約を優先します。

```bash
export COMPETITION="titanic"
export EXPERIMENT="baseline"
export KAGGLE_OWNER="your-kaggle-username"
```

`KAGGLE_OWNER` は Kaggle のプロフィール URL のユーザー名です。トークンは書きません。
この3変数は新しいターミナルで再設定します。実験名は英小文字・数字・ハイフンで決めます。
公開 Notebook の例では `baseline`、自作 Python の例では手順4の B で `my-model` に変更します。

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
  src/models/__init__.py
  models/README.md
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

## 4. 公開ベースラインを取り込む、または自分で実装する

初めてなら **A：Kaggle の公開 Notebook を取り込む** から始められます。
このルートでは `src/my_model.py` や `run()` の実装は不要です。
Python の共通入口を使って自作する場合は B を選びます。

### A：Kaggle Code のベースラインを使う

最初に設定した `$COMPETITION` から公開 Notebook を自動選択して取り込みます。
Notebook の URL を探したり、Python ファイルを自作したりする必要はありません。

```bash
python scripts/import_kaggle_baseline.py "$COMPETITION" --owner "$KAGGLE_OWNER" --name "$EXPERIMENT" --device cpu
```

Titanic では取得を確認した [Titanic Tutorial](https://www.kaggle.com/code/alexisbcook/titanic-tutorial)
を選びます。他のコンペでは Code の人気順20件から、タイトルに baseline / starter / tutorial / submission /
benchmark を含む候補を最大5件取得し、対象コンペの入力と `submission` の記述があるものを選びます。
これは候補の絞り込みです。実行成功や検証スコアの計算、提出形式の正しさまでは保証しません。
開いて評価方法・必要な入力・ライブラリ・ライセンスを確認してください。

自動選択できない場合や別の Notebook を使いたい場合は、コンペ画面の **Code** で
予測・提出ファイルまで作る Python Notebook を選び、`--kernel` を追加します。

```bash
python scripts/import_kaggle_baseline.py "$COMPETITION" --kernel "https://www.kaggle.com/code/作者/Notebook名" --owner "$KAGGLE_OWNER" --name "$EXPERIMENT" --device cpu
```

`作者/Notebook名` や `作者/Notebook名/バージョン番号` も指定できます。
バージョンを省略すると取得時の最新版です。GPU が必要なコードでは `--device cuda` を指定します。

このコマンドはダウンロードとローカル準備だけで、コードの実行・提出は行いません。

```text
competitions/<slug>/notebooks/
  imports/<実験名>/<取得ID>/     # 元の Notebook と metadata
  baselines/<実験名>/
    baseline.ipynb             # 自分で編集するコピー。保存出力を消去済み
    kernel-metadata.json       # 自分の ID、非公開、CPU / GPU の設定
    origin.json                # 取得元・日時・元コードのハッシュ
runs/<slug>/notebooks/<実験名>/  # アップロード用の Notebook と metadata
```

取得元の Notebook ID / 数値 ID は自分のアップロード設定に引き継ぎません。
元の Dataset / Model / Notebook 入力は引き継ぎ、コンペ入力を選択したコンペに設定します。
このコンペで使える入力か、Notebook のパスと一致するかを確認します。
同じ実験名のコピーがあると上書きを拒否するので、別名を選ぶか既存コピーを使います。
取得物はコンペ内と runs 内に保存され、Git 除外です。元の作者の表記は残します。
コード中の通常の文字列で書かれた `/kaggle/input/<slug>/...` と
`/kaggle/input/competitions/<slug>/...` は、実際に存在する入力を探す処理に変更します。
元の Notebook は imports 内に保持します。f-string や独自のパス組み立ては手動で確認してください。

`competitions/<slug>/notebooks/baselines/<実験名>/baseline.ipynb` を開き、
入力パス・学習処理・提出ファイルの名前を確認します。ここでは `submission.csv` が
`/kaggle/working` に出力される Notebook を想定します。
自分の変更はこの Notebook に加えてから **手順6の A** へ進みます。
このルートの指標と成果物は元の Notebook の実装に従い、共通入口の `experiment.json` は作りません。

### B：自分の Python を実装する

自作実験の名前を設定し、初回だけ設定をコピーします。

```bash
export EXPERIMENT="my-model"
cp "competitions/$COMPETITION/config.json" "competitions/$COMPETITION/configs/$EXPERIMENT.json"
python -m pip install -r "competitions/$COMPETITION/requirements.txt"
```

必要なライブラリを `requirements.txt` に追記し、再現に必要なバージョンを記録します。
空の requirements は何もインストールしません。
`configs/my-model.json` に seed、分割比率、モデルのパラメーターなどを追加します。
設定には認証情報を書きません。選択した設定は Kaggle Notebook に埋め込まれます。

モデル定義は `src/models/`、このコンペで使う重みは `models/` に置けます。
コンペ横断の保管庫はリポジトリ直下の `models/` です。
配置と読み込み方法は [モデルの管理手順](models.md) を参照してください。

`src/experiment.py` を編集するか、自分の `src/my_model.py` を作ります。
必須の入口は `run(config, data_dir, output_dir)` です。
関数の形・実験ファイルの分け方は [自分の実装を試す](experiments.md#3-実装の共通入口) を参照してください。
手元の NLP にはモデルを設定で差し替えられる実装があります。
ただし、新コンペの雛形に学習モデルが自動で入るわけではありません。

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

手順4の A を選んだ場合は手順6へ進みます。
B では、雛形の `src/experiment.py` を実装してから実行します。
別途 `src/my_model.py` を作った場合だけ `--entry` をそのファイルに変更してください。

```bash
python scripts/run_experiment.py "$COMPETITION" --entry src/experiment.py --config "configs/$EXPERIMENT.json" --name "$EXPERIMENT" --device cpu
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

### A：取り込んだ Notebook を使う

`import_kaggle_baseline.py` がアップロード用ファイルを用意済みなので、
`prepare_experiment_notebook.py` は使いません。
`EXPERIMENT` は取得時の `--name` と同じ値にしてください。取得済みの名前は次で確認できます。

```bash
ls "competitions/$COMPETITION/notebooks/baselines"
```

取得済みの Titanic のコピーが `baseline` なら `export EXPERIMENT="baseline"` に設定します。
`cannot stat .../my-model/...` が出た場合も、表示されたフォルダ名に合わせてから再実行してください。
編集したコピーをアップロード用フォルダへ反映します。

```bash
cp "competitions/$COMPETITION/notebooks/baselines/$EXPERIMENT/baseline.ipynb" "runs/$COMPETITION/notebooks/$EXPERIMENT/baseline.ipynb"
cp "competitions/$COMPETITION/notebooks/baselines/$EXPERIMENT/kernel-metadata.json" "runs/$COMPETITION/notebooks/$EXPERIMENT/kernel-metadata.json"
```

metadata は非公開・インターネット無効で準備します。
元の Notebook がダウンロードや pip install を必要とする場合は、オフラインで動くように
入力を準備するか、規約が許す場合に metadata の `enable_internet` を変更します。
GPU の必要性や出力ファイル名も元のコードに合わせます。
準備したら、以下の共通の push / status コマンドへ進みます。

### B：自作 Python から Notebook を生成する

実装が `output_dir/submission.csv` を生成する場合の例です。
`src/experiment.py` の `run()` を実装済みであることが前提です。

```bash
python scripts/prepare_experiment_notebook.py "$COMPETITION" --owner "$KAGGLE_OWNER" --entry src/experiment.py --config "configs/$EXPERIMENT.json" --name "$EXPERIMENT" --device cpu --submission-file submission.csv
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

### 共通：アップロード・実行・取得

A または B の準備ができたらアップロードして実行します。

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
これは B の生成機能です。A では元の Notebook 自身が提出ファイルをこの場所に保存します。
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

## 8. 個人の記録と共通機能の共有

`competitions/<slug>/RESULTS.md` を作り、次を記録します。

このコンペフォルダは個人のローカル作業として Git 除外です。
GitHub で共有するコンペフォルダは `_template/` だけです。
実装・設定・実測結果のバックアップは別途自分で管理してください。
このリポジトリへ `git add -f` で追加しないでください。

- 実験名、実行コマンド、コードの commit / ハッシュ、設定、依存関係
- 検証分割・seed・検証スコア
- Notebook ID・バージョン・提出 ID・採点状態・Kaggle public score
- 改善した点と、次に試すこと

```bash
git status --short
git diff --check
# 共通機能や手順を変更した場合だけ、そのファイルを選択する例
git add docs/new-competition.md
git diff --cached --stat
git commit -m "Update shared competition workflow documentation"
git push
```

ステージした内容を確認してからコミットします。個別コンペ・認証情報・データ・成果物は Git 除外です。
共通コードやテンプレートを変更した場合は、そのファイルを選んで追加してください。
他の人は共通環境とテンプレートを取得し、自分の認証・データ・実装を用意します。

CLI 引数はこの環境に導入済みの `--help` で確認しています。
別環境で挙動が変わる場合は `python scripts/kaggle_cli.py <サブコマンド> --help` と
[公式 CLI ドキュメント](https://github.com/Kaggle/kaggle-cli/blob/main/docs/README.md)、
[公式 Notebook metadata](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels_metadata.md) を確認してください。
