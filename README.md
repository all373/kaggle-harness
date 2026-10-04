# Kaggle Harness

コンペごとのコード・設定を単一リポジトリで管理するための開発用雛形。
CPU / NVIDIA GPU の Dev Container を切り替えて使う。
学習・検証・Kaggle 提出の実行処理は、各コンペの実装として追加する。

## Dev Container

WSL containers と VS Code Dev Containers を使う場合:

1. Windows 版 VS Code のユーザー設定で `Dev Containers: Docker Path` を `wslc` にする。必要なら `C:\Program Files\WSL\wslc.exe` を指定する。マシン固有のパスはリポジトリに書かない。
2. WSL の Linux ファイルシステムにリポジトリを置き、端末で `code .` を実行する。
3. `Dev Containers: Reopen in Container` で CPU または NVIDIA GPU を選ぶ。切り替える場合は `Dev Containers: Reopen Folder Locally` で戻ってから構成を選び直す。
4. 以下の環境検査を実行する。

```bash
# CPU: PyTorch がなくても成功する
python scripts/check_env.py

# GPU: CUDA と GPU 上の演算が使えることを必須にする
python scripts/check_env.py --require-cuda
```

GPU 構成は `--gpus all` を使用する。ホスト側で GPU をコンテナに渡せる設定が必要。
両構成とも Dockerfile からビルドする。GPU Dockerfile は PyTorch / CUDA ベースに Git を追加する。
設定変更後は `Dev Containers: Rebuild Container` を実行する。

CPU コンテナには PyTorch を追加していない。必要なライブラリはコンペの
`requirements.txt` に明示する。GPU コンテナの既存 PyTorch を変更する場合は
CUDA との互換性も確認する。両構成は共有の作業ディレクトリを使うため、
コンペ用の `.venv` を作る場合は `.venv-cpu` / `.venv-gpu` を分ける。

## ディレクトリ構成

```text
.devcontainer/
  cpu/                       # CPU 開発環境
  gpu/                       # NVIDIA GPU 開発環境
harness/                     # コンペ共通のユーティリティ
competitions/
  _template/                 # 新規コンペの雛形
  <slug>/
    README.md                # データ取得・検証方法・実行コマンド
    config.json              # device、seed、入出力パス
    requirements.txt         # コンペ固有の依存関係
    src/                     # 学習・前処理・検証コード
    notebooks/               # 探索用 Notebook
scripts/                     # コンペ作成・環境検査
data/<slug>/                 # ローカルデータ（Git 管理対象外）
runs/<slug>/<run-id>/         # スコア・ログ・モデル・提出物（Git 管理対象外）
```

## コンペを追加する

リポジトリルートで実行する。既存ディレクトリは上書きしない。

```bash
python scripts/new_competition.py titanic
python -m pip install -r competitions/titanic/requirements.txt
```

`competitions/titanic/README.md` に評価指標、データ取得方法、検証分割、
学習・検証コマンドを記入し、`src/` に処理を追加する。
`config.json` は設定の雛形であり、各コンペのコードから読み込む。
Notebook に出力やデータが残る場合は、共有前にクリアする。

PyTorch のコードでは、リポジトリルートからモジュールとして実行すると
共通ユーティリティを読み込める。例: `python -m competitions.titanic.src.train`
（`train.py` はコンペごとに実装する）。

```python
from harness.device import resolve_device

device = resolve_device("auto")  # CUDA が使えれば cuda、それ以外は cpu
# config.json の device を渡してもよい。cuda を明示すると未対応環境でエラーになる。
```

CPU/GPU の比較では検証分割、seed、評価指標を揃える。seed が同じでも
デバイスやライブラリによって結果が完全一致するとは限らない。
各実験の出力には設定、依存バージョン、スコアを記録する。

## GitHub で共有する

共有するものはコード、設定、依存関係、再現手順。
`.gitignore` はデータ、実験結果、モデル、認証情報、WSL の
`Zone.Identifier` ファイルを除外する。すでに追跡しているファイルには
`.gitignore` が効かないため、ステージした差分を確認する。
`.env.example` には実際の秘密情報を入れない。

Git がない起動済み GPU コンテナでは、設定変更後にリビルドするか
Git がある WSL 側で操作する。以下は、まだ Git リポジトリを作っていない場合の手順:

```bash
git init -b main
git add .
git status --short
git diff --cached --stat
git diff --cached
# データ・認証情報・Notebook の出力が含まれていないことを確認してからコミット
git commit -m "Set up competition workspace with CPU and GPU containers"
```

GitHub で空のリポジトリを作り、実際の URL を指定する:

```bash
git remote add origin https://github.com/<owner>/<repository>.git
git push -u origin main
```

既存リポジトリでは `git status`、`git branch --show-current`、`git remote -v`
で状態を確認し、初期化や remote の追加を重複して行わない。
認証は各自の GitHub 認証手段を使い、トークンを URL やファイルに埋め込まない。
共同作業では変更用ブランチから Pull Request を作り、コンペの再現手順も更新する。

## 次に追加するもの

- 最初のコンペの学習・ローカル検証コマンド
- 実験結果を記録・比較する処理
- 試行回数を制限した編集 → 検証 → 記録ループ
- Kaggle Notebook の実行と提出
