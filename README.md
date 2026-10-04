# Kaggle Harness：環境構築から最初の提出まで

Kaggle を初めて使う人向けに、VS Code のインストール、開発環境の準備、GPU 学習、提出、スコア確認までを順番に説明します。Windows 11 + WSL 2 + WSL containers を使う手順です。公式情報の確認日は **2026-10-04** です。

このリポジトリは、複数のコンペのコードをコンペ別のフォルダで管理します。最初の実例は、映画レビューの肯定・否定を予測する [Bag of Words Meets Bags of Popcorn](https://www.kaggle.com/competitions/word2vec-nlp-tutorial/overview) です。

**基本ルートは、手元の CPU コンテナでコードを編集し、Kaggle Notebook の GPU で学習する方法です。手元の NVIDIA GPU は不要です。** 手元の GPU でも学習したい人向けの手順は後半にあります。

## 全体の流れと必要なもの

開発エージェント向けの作業案内は [AGENTS.md](AGENTS.md) と
[.agent/README.md](.agent/README.md)、現在の進捗は [PROGRESS.md](PROGRESS.md) にあります。
初めて環境を構築する人は、この README を順に進めてください。

1. Windows に VS Code を入れる。
2. WSL / Ubuntu と WSL containers を準備する。
3. VS Code に WSL・Dev Containers 拡張を入れる。
4. このリポジトリを取得し、CPU Dev Container を開く。
5. Kaggle アカウントを作り、自分の API トークンを設定する。
6. コンペに参加し、データと GPU の利用条件を確認する。
7. Kaggle GPU で学習し、検証スコアを確認する。
8. 作成した CSV を1回提出し、Kaggle のスコアを確認する。

必要なものは Windows PC、インターネット接続、ソフトをインストールできる権限、Kaggle アカウントです。コンテナイメージやデータを取得するため、ディスクの空き容量も確保してください。GitHub アカウントは、自分のリポジトリへ変更を共有する段階で使います。

### コマンドを実行する場所

| この文書の表記 | 開き方・用途 |
| --- | --- |
| **PowerShell** | Windows のスタートメニューで検索して開く。WSL のインストール・確認に使用 |
| **Ubuntu** | スタートメニューの Ubuntu、または Windows Terminal の Ubuntu タブ。リポジトリ取得に使用 |
| **コンテナ内ターミナル** | Dev Container 接続後、VS Code の「ターミナル → 新しいターミナル」。Python / Kaggle コマンドに使用 |
| **ブラウザ** | VS Code のダウンロード、Kaggle の登録・規約同意・結果確認に使用 |

コマンドはコードブロックの中身をコピーしてください。`#` から始まる行は説明です。`your-kaggle-username` などの例は自分の値に置き換えます。

## 1. VS Code をインストールする

**操作場所：Windows のブラウザ**

1. [VS Code の公式ダウンロード](https://code.visualstudio.com/download)を開く。
2. Windows 用インストーラーをダウンロードして実行する。
3. インストール画面に「PATH への追加」があれば有効にする。
4. インストールが終わったら VS Code を起動する。

VS Code は Windows 側にインストールします。WSL / Ubuntu の中に別途インストールする必要はありません。[公式の WSL 開発手順](https://code.visualstudio.com/docs/remote/wsl)

## 2. WSL 本体（3.0.1 以降）と Ubuntu を準備する

**操作場所：管理者として開いた PowerShell**

スタートメニューで PowerShell を検索し、右クリックして「管理者として実行」を選びます。WSL がまだ入っていない場合は次を実行します。

```powershell
wsl --install -d Ubuntu
```

案内に従って Windows を再起動します。Ubuntu を初めて開いたら、Linux 用ユーザー名とパスワードを作成してください。パスワード入力中は文字が表示されませんが、入力は受け付けています。

**操作場所：PowerShell**

```powershell
wsl --update
wsl --version
wsl --list --verbose
```

2026-10-04 に確認した公式の最新安定版は **WSL 3.0.1** です。この README では、WSL containers が正式提供された **3.0.1 以降の安定版**を使います。`wsl --version` の WSL バージョンを確認してください。[公式の WSL 3.0.1 リリース](https://github.com/microsoft/WSL/releases/tag/3.0.1)

バージョン番号には次の2種類があります。

| 確認コマンド | 確認する値 | 意味 |
| --- | --- | --- |
| `wsl --version` | WSL バージョン `3.0.1` など | インストールした WSL 本体のリリース番号 |
| `wsl --list --verbose` | Ubuntu の `VERSION` が `2` | Ubuntu を WSL 2 の方式で動かしていること |

**WSL 本体が 3.0.1 でも、Ubuntu の `VERSION` は `2` のままで正常です。** `wsl --set-version Ubuntu 3` は使いません。

`wsl --list --verbose` で Ubuntu の `VERSION` が `1` の場合は、実際のディストリビューション名を指定して変換します。

```powershell
wsl --set-version Ubuntu 2
```

`Ubuntu` という名前が一覧にない場合は、一覧に表示された名前に置き換えてください。[公式の WSL インストール手順](https://learn.microsoft.com/en-us/windows/wsl/install)

## 3. WSL containers を確認する

**操作場所：PowerShell**

WSL containers は、このリポジトリの開発用コンテナを動かすために使います。**初めて構築する場合は、手順2のとおり WSL 本体 3.0.1 以降の安定版を使用してください。** 3.0.1 の公式リリースで WSL containers の正式提供が案内されています。

Microsoft Learn の最低要件は `2.9.3 以上`ですが、これは以前のプレビュー版も含む下限です。この README の推奨バージョンとは分けて考えてください。[公式の最低要件](https://learn.microsoft.com/en-us/windows/wsl/wsl-container)、[正式提供のリリース](https://github.com/microsoft/WSL/releases/tag/3.0.1)

```powershell
wslc version
wslc run --rm hello-world
```

バージョンが表示され、`hello-world` のメッセージが出れば準備完了です。`--rm` は確認用コンテナを終了後に削除する指定です。

`wslc` が見つからない場合は `wsl --update` を実行し、PowerShell を開き直してください。改善しない場合は、上の公式手順で WSL のインストール状態を確認します。このルートでは Docker Desktop の追加インストールは不要です。

すでに Docker Desktop を使っている場合は、その WSL 2 連携と Dev Containers を使うこともできます。その場合は次の手順の Docker Path を `wslc` に変更せず、Docker の設定を使ってください。[VS Code のコンテナ開発手順](https://code.visualstudio.com/docs/devcontainers/containers)

## 4. VS Code の拡張とコンテナ設定を準備する

**操作場所：Windows の VS Code**

左の拡張アイコン、または `Ctrl+Shift+X` を開き、Microsoft 提供の次の拡張をインストールします。

| 拡張 | 拡張 ID | 用途 |
| --- | --- | --- |
| WSL | `ms-vscode-remote.remote-wsl` | Ubuntu の作業フォルダを開く |
| Dev Containers | `ms-vscode-remote.remote-containers` | 開発用コンテナを開く |

WSL containers を使う場合は、`Ctrl+,` で設定を開き、**ユーザー設定**で `Dev Containers: Docker Path` を検索して `wslc` に変更します。見つからない場合は設定の検索欄に `@id:dev.containers.dockerPath` と入力してください。マシン固有の設定なので、リポジトリ内には書きません。

設定 JSON を編集する場合は、既存の設定に次の項目を追加します。ファイル全体を置き換えないでください。

```json
"dev.containers.dockerPath": "wslc"
```

`wslc` の実行ファイルが見つからない場合は、PowerShell の `Get-Command wslc` で場所を調べ、設定画面にその実際のパスを指定します。例：`C:\Program Files\WSL\wslc.exe`。

WSL containers 対応の新しい Dev Containers 拡張を使用してください。[Microsoft の正式提供・VS Code 連携の案内](https://blogs.windows.com/windowsdeveloper/2026/09/29/wsl-containers-now-generally-available/)

## 5. リポジトリを取得する

**操作場所：Ubuntu のターミナル**

スタートメニューから Ubuntu を開きます。Git をインストールして、Linux 側のホームフォルダに作業場所を作ります。

```bash
sudo apt update
sudo apt install -y git ca-certificates
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/all373/kaggle-harness.git
cd kaggle-harness
code .
```

`sudo` のパスワードは手順2で作った Linux 用のものです。`code .` は現在のフォルダを VS Code で開くコマンドです。

リポジトリは `~/projects/` のような WSL の Linux ファイルシステムに置きます。Linux のツールで作業する際、Windows の `C:` 配下よりファイルアクセスが速くなります。[Microsoft の配置に関する説明](https://learn.microsoft.com/en-gb/windows/wsl/tutorials/wsl-containers)

取得済みなら clone を繰り返さず、そのフォルダで `code .` を実行してください。取得先が非公開の場合は GitHub のアクセス権が必要です。共有用のコードが GitHub に反映されていない場合は、管理者に最新のコードの共有を依頼してください。

**確認：** VS Code の左下に WSL / Ubuntu の接続表示があり、ファイル一覧に `README.md`、`scripts/`、`.devcontainer/` が見えること。

## 6. CPU Dev Container を開く

**操作場所：WSL に接続した VS Code**

1. `Ctrl+Shift+P` でコマンドパレットを開く。
2. `Dev Containers: Reopen in Container` を実行する。
3. **Kaggle Harness (CPU)** を選ぶ。
4. 初回はイメージ取得・ビルド・拡張のインストールが終わるまで待つ。
5. 左下の表示が Dev Container になったら「ターミナル → 新しいターミナル」を開く。

**操作場所：ここからのコマンドはコンテナ内ターミナル**

```bash
pwd
python --version
git --version
python scripts/check_env.py
```

`pwd` が通常 `/workspaces/kaggle-harness` になり、Python と Git のバージョンが表示されれば準備完了です。以降は **README.md があるリポジトリルート**でコマンドを実行してください。

CPU 構成では `PyTorch: not installed` と表示されても正常です。Kaggle 側で学習する基本ルートでは、ローカルに PyTorch を入れる必要はありません。

Python・Pylance・Codex 拡張は両コンテナ構成でインストールする設定です。Codex は任意の補助ツールで、利用しなくてもこの手順を進められます。

## 7. Kaggle アカウントと GPU の利用条件を確認する

**操作場所：ブラウザ**

1. [Kaggle](https://www.kaggle.com/) でアカウントを作成し、ログインする。
2. プロフィール URL のユーザー名を確認する。`https://www.kaggle.com/ユーザー名` の部分です。表示名やメールアドレスではありません。
3. Kaggle の Code ページから新しい Notebook を開き、設定の Accelerator で GPU を選べることを確認する。画面に表示される GPU の利用枠も確認する。この確認用 Notebook で学習コードを手入力する必要はない。
4. GPU を選べずアカウント確認を求められる場合は、その案内に従って電話番号などの確認を完了する。

GPU の提供条件や利用枠はアカウント・時期によって変わります。固定の時間数を前提にせず、Kaggle 画面で現在の状態を確認してください。[Kaggle Notebook の公式説明](https://www.kaggle.com/docs/notebooks)

**操作場所：コンテナ内ターミナル**

以降のコマンドで使う、自分のユーザー名を設定します。引用符の中を自分の値に置き換えてください。

```bash
export KAGGLE_OWNER="your-kaggle-username"
```

この変数は現在のターミナル内だけで有効です。新しいターミナルを開いたら再度設定します。他の人のユーザー名を指定すると、その人の Notebook を作成・更新しようとして失敗します。

## 8. Kaggle API トークンをローカルに設定する

**操作場所：ブラウザ**

[Kaggle の API 設定](https://www.kaggle.com/settings/api)を開き、**API Tokens (Recommended) → Generate New Token** でトークンを発行します。この構成は API トークンに対応しています。Legacy API Key やログイン用パスワードは使いません。[Kaggle CLI の公式認証手順](https://github.com/Kaggle/kaggle-cli/blob/main/docs/README.md#authentication)

**操作場所：コンテナ内ターミナル**

```bash
python -m pip install -r requirements-kaggle.txt
cp -n config/kaggle.example.json config/kaggle.local.json
chmod 600 config/kaggle.local.json
```

`cp -n` は設定例をコピーし、既存のローカル設定がある場合は上書きしません。

VS Code のファイル一覧で **`config/kaggle.local.json`** を開き、次のように発行したトークンを記入して `Ctrl+S` で保存します。`kaggle.example.json` は共有用なので編集しません。

```json
{
  "api_token": "ここに自分のAPIトークンを記入"
}
```

**確認：** 次を実行します。

```bash
git check-ignore config/kaggle.local.json
python scripts/kaggle_cli.py competitions list
```

1つ目で `config/kaggle.local.json` が表示され、2つ目でコンペ一覧が取得できれば設定できています。

このリポジトリのコマンドはローカル設定を読み込み、Kaggle CLI に `KAGGLE_API_TOKEN` として渡します。直接 `kaggle` を実行する代わりに `python scripts/kaggle_cli.py` を使ってください。

トークンは各自のものを使います。GitHub、チャット、Notebook に貼らないでください。共有するのは設定例だけで、実際の `*.local.json` は Git 除外対象です。CLI は API トークン対応の 1.8.0 以上を指定しています。

## 9. 最初のコンペに参加する

**操作場所：ブラウザ**

[Bag of Words Meets Bags of Popcorn](https://www.kaggle.com/competitions/word2vec-nlp-tutorial/overview)を開き、参加ボタンや規約同意の案内が表示された場合は内容を確認して参加します。規約への同意は、リポジトリの利用者ごとに必要です。

このコンペ用のコードはすでに `competitions/word2vec-nlp-tutorial/` にあります。新しく同じフォルダを作る必要はありません。

| 用語 | このコンペでの意味 |
| --- | --- |
| 学習データ | 正解ラベル付きの映画レビュー25,000件 |
| 検証データ | 学習データから分けた5,000件。モデルの性能を手元で測る |
| テストデータ | 正解ラベル非公開の25,000件。提出用の予測対象 |
| ROC AUC | 予測順位を評価する指標。高いほどよい |
| submission.csv | テストデータの予測を Kaggle に渡すファイル |

評価指標と提出形式は[コンペ公式説明](https://www.kaggle.com/c/word2vec-nlp-tutorial)で確認できます。

## 10. データにアクセスできることを確認する

**操作場所：コンテナ内ターミナル**

```bash
python scripts/kaggle_cli.py competitions files -c word2vec-nlp-tutorial
```

`labeledTrainData.tsv.zip`、`testData.tsv.zip`、`unlabeledTrainData.tsv.zip`、`sampleSubmission.csv` が表示されれば確認完了です。

ローカルでもデータを見たい場合は、次で取得・展開できます。Kaggle GPU 学習だけを行う場合、このダウンロードは省略できます。Notebook にはコンペデータが直接接続されます。

```bash
python scripts/kaggle_cli.py competitions download -c word2vec-nlp-tutorial -p data/word2vec-nlp-tutorial
python -m competitions.word2vec-nlp-tutorial.src.prepare_data
```

ファイルは `data/word2vec-nlp-tutorial/` に保存されます。ZIP の中にさらに ZIP があるため、展開処理は二段階です。再実行すると展開済みファイルを配布 ZIP の内容で置き換えます。

## 11. Kaggle GPU で学習し、検証スコアを確認する

**操作場所：コンテナ内ターミナル**

手順7の `KAGGLE_OWNER` が自分のユーザー名になっていることを確認し、実行します。

```bash
python scripts/run_kaggle_training.py word2vec-nlp-tutorial --owner "$KAGGLE_OWNER"
```

この1コマンドが順に行うことは次のとおりです。

1. `src/train.py` と `config.json` から学習 Notebook を生成する。
2. 自分の Kaggle アカウントに **非公開** Notebook をアップロードする。
3. コンペデータを接続し、Kaggle の T4 GPU で10 epoch 学習する。
4. 検証 ROC AUC が最良のモデルで検証スコアとテスト予測を作る。
5. モデル・スコア・予測 CSV をローカルの `runs/` に取得する。

ローカルのトークンやデータは Notebook にコピーされません。アップロードされるのはコードと Notebook の設定です。Notebook はインターネット無効で動きます。GPU は T4 ×2 を指定しますが、小さな分類モデルの学習には GPU 0 を使用します。[公式の Notebook 設定項目](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels_metadata.md)

デフォルトの Notebook 実行上限は1,800秒です。GPU 利用枠を消費し、起動待ち・実行・取得中はターミナルに状態が表示されます。

**確認：** `KernelWorkerStatus.COMPLETE`、`validation_roc_auc`、最後に `Result: runs/.../result.json` が表示されれば成功です。この段階ではコンペへ提出していません。

自分の Notebook は `https://www.kaggle.com/code/自分のユーザー名/word2vec-nlp-tutorial-gpu-train` に作成されます。ブラウザで開くとコード・学習ログ・出力を確認できます。

### 検証スコアを読む

学習用25,000件を seed 42 で層化分割し、20,000件を学習、5,000件を検証に使います。語彙は学習側だけで作ります。モデルは単語埋め込みの平均と小さなニューラルネットワークを使う PyTorch 分類器です。

10 epoch のうち最良の検証スコアを選ぶため、検証スコアにはモデル選択の影響があります。Kaggle のスコアとは区別してください。全25,000件での再学習は行わず、最良の検証モデルから提出用予測を作ります。

## 12. Kaggle に1回提出し、スコアを確認する

**操作場所：コンテナ内ターミナル**

手順11の学習が完了したら、次を実行します。

```bash
python scripts/run_kaggle_training.py word2vec-nlp-tutorial --owner "$KAGGLE_OWNER" --resume --submit
```

`--resume` は、すでに実行した Notebook の最新の完了結果を取得する指定です。**再学習はしません。** `--submit` はその結果の `submission.csv` を **このコマンドにつき1回、新たに提出する**指定です。

列名・行数・ID の一意性・予測確率を確認してから提出し、今回の提出メッセージに対応するスコアを取得します。

**確認：** `Successfully submitted` に続いて `Kaggle public score: ...` が表示されれば提出と採点が完了です。ブラウザではコンペの提出一覧からも確認できます。

```bash
python scripts/kaggle_cli.py competitions submissions word2vec-nlp-tutorial
```

採点が遅い場合は結果が pending のまま終了することがあります。再提出せず、上の提出一覧で確認してください。提出処理は自動で再試行しません。通信が切れた場合も、先に提出済みかを確認します。

### 2回目以降、学習から提出までまとめて実行する場合

設定を変更して学習と提出をまとめて行いたい場合は次を使います。

```bash
python scripts/run_kaggle_training.py word2vec-nlp-tutorial --owner "$KAGGLE_OWNER" --submit
```

このコマンドは **新しい Notebook バージョンを作り、再学習し、新たに1回提出します。** 結果を確認するだけなら繰り返し実行しないでください。Kaggle の GPU 枠と提出回数の制限は画面で確認します。

## 13. 結果の保存場所を確認する

ローカルの結果は `runs/word2vec-nlp-tutorial/kaggle-results/<取得日時>/` に保存します。最後に表示される `result.json` を VS Code で開くと、検証スコア・成果物の場所・取得できた Kaggle スコアを確認できます。フォルダ名の日時は UTC です。

| ファイル | 内容 |
| --- | --- |
| result.json | 全体の結果、取得先、提出状態、Kaggle スコア |
| metrics.json | 検証 ROC AUC・accuracy、最良 epoch、実行環境 |
| history.json | epoch ごとの loss と検証スコア |
| best-model.pt | 保存したモデルの重み |
| config.json / split.json / vocab.json | 実行設定・分割 ID・学習語彙 |
| validation_predictions.csv | 検証データの正解と予測確率 |
| submission.csv | Kaggle に提出する予測確率 |
| submission-binary.csv | 0 / 1 に変換した予測。自動提出では使用しない |

2026-10-04 の確認実行では、検証 ROC AUC **0.94939**、Kaggle public score **0.93598** でした。環境やモデル変更で値は変わります。[実測結果と再現条件](competitions/word2vec-nlp-tutorial/RESULTS.md)

## 14. コードを変更して次の実験をする

学習設定は `competitions/word2vec-nlp-tutorial/config.json`、モデルと前処理は `competitions/word2vec-nlp-tutorial/src/train.py` を編集します。

最初は epoch 数・学習率などを1つずつ変え、検証スコアを比較してください。ブラウザで Notebook を変更した場合はリポジトリ側にも反映します。通常はリポジトリを編集して Notebook を再生成する方が変更を管理しやすくなります。

```bash
# 学習は行わず、アップロード用 Notebook と設定だけを生成
python scripts/prepare_kaggle_notebook.py word2vec-nlp-tutorial --owner "$KAGGLE_OWNER" --notebook gpu-train
```

生成物は `runs/word2vec-nlp-tutorial/kaggle-gpu-train/` に置かれます。`run_kaggle_training.py` はこの生成処理も含んでいます。

## 15. 自分の GitHub にコードを共有する

**操作場所：ブラウザ、続いてコンテナ内ターミナル**

1. [GitHub](https://github.com/) でアカウントを作成する。
2. [このリポジトリ](https://github.com/all373/kaggle-harness)を開き、`Fork` で自分のアカウントにコピーする。
3. 自分の Fork の URL を確認し、ローカルの `origin` を変更する。

```bash
# 自分の GitHub ユーザー名に置き換える
export GITHUB_OWNER="your-github-username"
git remote -v
git remote set-url origin "https://github.com/$GITHUB_OWNER/kaggle-harness.git"
git switch -c my-first-experiment

# コミットの作者情報を、このリポジトリに設定
git config user.name "自分の名前"
git config user.email "自分のGitHub用メールアドレス"
```

Kaggle と GitHub のユーザー名は別のものです。clone 済みなので `git init` は不要です。

```bash
git check-ignore config/kaggle.local.json
git status --short
git add README.md competitions/word2vec-nlp-tutorial
git diff --cached --stat
git diff --cached
```

差分にコード・設定・手順だけが含まれることを確認します。Notebook にレビュー本文・出力・認証情報を残さないでください。`.gitignore` は、すでに追跡しているファイルを除外するものではありません。

```bash
git commit -m "Update sentiment baseline"
git push -u origin my-first-experiment
```

変更がなければ commit は不要です。push の認証は VS Code / GitHub の案内に従います。Kaggle のトークンは GitHub 認証には使えません。GitHub のパスワードやトークンを remote URL に埋め込まないでください。

共同作業では変更用ブランチから Pull Request を作ります。共有対象はコード・設定例・依存関係・再現手順で、データ・モデル・ローカル認証情報は共有しません。

## 補足A：手元の NVIDIA GPU / CPU でも学習する

### 手元の NVIDIA GPU を使う

Windows 側に、WSL の GPU 利用に対応した NVIDIA ドライバーをインストールします。具体的な条件は [Microsoft の WSL GPU 手順](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gpu-compute)を確認してください。

**PowerShell** で、GPU をコンテナへ渡せることを確認します。

```powershell
wslc run --rm --gpus all pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime python -c "import torch; print(torch.cuda.is_available())"
```

`True` が出れば、VS Code の `Dev Containers: Reopen Folder Locally` で戻ってから `Reopen in Container` を実行し、**Kaggle Harness (NVIDIA GPU)** を選びます。この構成は `--gpus all` を指定し、PyTorch / CUDA のベースイメージを使用します。[Microsoft の GPU コンテナ実行例](https://devblogs.microsoft.com/commandline/wsl-container-is-now-available-for-public-preview/)

**コンテナ内ターミナル**で次を実行します。手順10でローカルデータを取得・展開しておいてください。

```bash
python scripts/check_env.py --require-cuda
python -m pip install -r competitions/word2vec-nlp-tutorial/requirements.txt
python -m competitions.word2vec-nlp-tutorial.src.train --device cuda
```

### 手元の CPU で学習する

CPU コンテナには PyTorch が入っていないので追加します。[PyTorch の公式インストール案内](https://pytorch.org/get-started/locally/)で自分の環境に合うコマンドも確認できます。

```bash
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r competitions/word2vec-nlp-tutorial/requirements.txt
python -m competitions.word2vec-nlp-tutorial.src.train --device cpu
```

ローカル学習の結果は `runs/word2vec-nlp-tutorial/<実行日時>/` に保存します。CPU / GPU で比較する際は検証分割・seed・指標を揃えます。同じ seed でも環境が違うと結果が完全一致するとは限りません。

## 補足B：別のコンペを追加する

**コンテナ内ターミナル、リポジトリルートで実行**

```bash
python scripts/new_competition.py titanic
```

`competitions/titanic/` に設定・README・コード用フォルダを作ります。既存フォルダは上書きしません。

**テンプレート作成だけでは学習・提出は動きません。** 新しいコンペでは、自分でデータの読み込み・モデル・検証・提出形式を実装してください。上の GPU 学習コマンドは `word2vec-nlp-tutorial` 用です。

自分の実装は `src/`、設定のバリエーションは `configs/` に置き、共通入口から選択して実行できます。
`run(config, data_dir, output_dir)` を実装すると、ローカル実行と Kaggle Notebook 生成の両方で使えます。

```bash
# src/my_model.py を実装し、configs/my-model.json を作成してから実行
python scripts/run_experiment.py titanic --entry src/my_model.py --config configs/my-model.json --name my-model --device cpu
```

結果は `runs/titanic/experiments/my-model/<実行日時と識別子>/` に分けて保存します。
既存結果を残しながら試せます。詳しくは [自分の実装を試す](docs/experiments.md) と
[新しいコンペの追加から提出まで](docs/new-competition.md) を参照してください。

コンペの README に、URL・評価指標・規約・データ取得方法・検証分割・実行コマンドを記録します。依存関係はコンペの `requirements.txt` に追加します。

### ARC Prize 2026 - ARC-AGI-2 の提出

ARC 用の CPU 規則探索と Code Competition 提出フローも実装済みです。
各問題に2候補のグリッドを出し、`submission.json` を生成する Notebook を提出します。
こちらは CSV をアップロードする NLP コンペとは別のコマンドを使います。

```bash
python scripts/run_arc_submission.py --owner "$KAGGLE_OWNER" --submit
```

このコマンドは非公開 Notebook を生成・実行し、実行済みバージョンを1回提出して
スコアを取得します。軽量なベースラインで、初回の公開評価は0%でした。
詳しくは [ARC の手順](competitions/arc-prize-2026-arc-agi-2/README.md)を参照してください。

## 補足C：ディレクトリ構成

```text
.devcontainer/
  cpu/                         # 手元の CPU 開発環境
  gpu/                         # 手元の NVIDIA GPU 開発環境
config/
  kaggle.example.json          # 共有する設定例
  kaggle.local.json            # 各自のトークン（Git 除外）
harness/                       # コンペ共通のユーティリティ
docs/                          # 自分の実装・新しいコンペの手順
competitions/
  _template/                   # 新しいコンペ用テンプレート
  word2vec-nlp-tutorial/
    README.md                  # コンペ固有の手順
    RESULTS.md                 # 実測結果
    config.json                # 学習設定
    configs/                   # 自分の実験ごとの設定（任意に作成）
    requirements.txt           # 依存関係
    src/                       # 学習・前処理コード
    notebooks/                 # GPU 確認・学習 Notebook
scripts/                       # 認証・Notebook 生成・実行・結果取得
tests/                         # 学習フローの確認
data/<コンペ名>/                # ローカルデータ（Git 除外）
runs/<コンペ名>/                # モデル・スコア・提出物（Git 除外）
PROGRESS.md                    # 会話がなくても作業を再開するためのメモ
```

## 困ったとき

| 症状 | 確認・対処 |
| --- | --- |
| `code: command not found` | Windows に VS Code を入れ、Ubuntu のターミナルを開き直す。WSL 拡張も確認 |
| `wslc` が見つからない | PowerShell で `wsl --version` と `wsl --update`。手順3の公式案内を確認 |
| WSL のインストール・起動が失敗する | Windows の更新と PC の仮想化設定を確認。[Microsoft のトラブルシューティング](https://learn.microsoft.com/en-us/windows/wsl/troubleshooting)を参照 |
| コンテナが起動しない | VS Code の Dev Containers のログを開く。Docker Path と `wslc run --rm hello-world` を確認 |
| `README.md` やスクリプトが見つからない | `pwd` で作業場所を確認し、リポジトリルートに移動 |
| Kaggle CLI がない | コンテナ内で `python -m pip install -r requirements-kaggle.txt` |
| ローカル認証設定がない・JSON が不正 | `config/kaggle.local.json` に `api_token` を記入し保存。引用符・カンマを確認 |
| API が 401 / Unauthorized | トークンの誤記・失効・未保存を確認。必要なら新しい API トークンをローカルに設定 |
| データ取得・提出が 403 / Forbidden | 正しいアカウントでログインし、コンペへの参加・規約同意を確認 |
| Notebook を作成できない | `KAGGLE_OWNER` がトークンのアカウントのユーザー名と一致しているか確認 |
| GPU を選べない | Kaggle のアカウント確認と現在の GPU 利用枠を確認 |
| Notebook が ERROR | ブラウザの Notebook のログを開く。GPU・入力データ・依存関係を確認 |
| ターミナルが切れた・待ち時間を超えた | 下の status で状態を確認し、`--resume` で結果を再取得 |
| 提出したがスコアがまだない | submissions で採点状態を確認。`--submit` を繰り返さない |

```bash
python scripts/kaggle_cli.py kernels status "$KAGGLE_OWNER/word2vec-nlp-tutorial-gpu-train"
python scripts/run_kaggle_training.py word2vec-nlp-tutorial --owner "$KAGGLE_OWNER" --resume
python scripts/kaggle_cli.py competitions submissions word2vec-nlp-tutorial
```

### rebuild 後の再開

Dockerfile / Dev Container の設定を変えたら `Dev Containers: Rebuild Container` を実行します。rebuild や CPU / GPU の切り替え後は、必要な pip インストールを実行し直してください。コンテナ内だけに追加したライブラリは保持されるとは限りません。

同じ作業フォルダを開く限り、コード・`config/kaggle.local.json`・`data/`・`runs/` はそこに残ります。作業フォルダ自体を削除すると失われるので、Git 除外の成果物は必要に応じて別途バックアップします。

Codex 拡張の再インストールは、以前の会話の保持を保証しません。拡張が表示されない場合はコンテナ側へのインストール状態を確認し、必要なら再ログインしてください。作業の状態は [PROGRESS.md](PROGRESS.md) と各コンペの README / RESULTS に残して再開できます。
