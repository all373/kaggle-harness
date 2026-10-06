# 公開ベースラインから提出まで：コマンド集

Dev Container 接続・Kaggle 認証設定・コンペ参加済みで使います。
準備は [README](../README.md)、詳しい説明は [新しいコンペの手順](new-competition.md)。
各ブロックを順番に実行し、エラーが出たらその場で止めて修正してください。
例は Titanic の CSV 提出です。別コンペでは提出例の名前・形式を合わせます。

**すでに push 済みなら「1 → 5 → 6 → 7 → 8」へ進みます。**

## 1. 変数を設定する（新しいターミナルでも実行）

```bash
cd /workspaces/kaggle-harness

export COMPETITION="titanic"
export EXPERIMENT="baseline"                    # 取得時の --name と同じ名前
export KAGGLE_OWNER="koheiminami"      # 自分のプロフィール URL のユーザー名
export DEVICE="cpu"                            # GPU を使うコードなら cuda
export SAMPLE_SUBMISSION="gender_submission.csv"  # Titanic の提出例

export BASELINE_DIR="competitions/$COMPETITION/notebooks/baselines/$EXPERIMENT"
export NOTEBOOK_DIR="runs/$COMPETITION/notebooks/$EXPERIMENT"

python scripts/check_env.py
test -f config/kaggle.local.json
```

## 2. コンペフォルダとデータを用意する

```bash
# 既存のコンペフォルダはそのまま使う
if [ ! -d "competitions/$COMPETITION" ]; then
    python scripts/new_competition.py "$COMPETITION"
fi

# ローカルデータは提出ファイルの確認に使う
# Kaggle 上の学習は Notebook に設定されたコンペ入力を使う
python scripts/kaggle_cli.py competitions files -c "$COMPETITION"
python scripts/kaggle_cli.py competitions download -c "$COMPETITION" -p "data/$COMPETITION"
python -m zipfile -l "data/$COMPETITION/$COMPETITION.zip"
python -m zipfile -e "data/$COMPETITION/$COMPETITION.zip" "data/$COMPETITION"

ls "data/$COMPETITION"
```

## 3. ベースラインを取得・確認・反映する

```bash
# 取得済みなら再取得せず、自分の編集を保持する
if [ ! -d "$BASELINE_DIR" ]; then
    python scripts/import_kaggle_baseline.py "$COMPETITION" --owner "$KAGGLE_OWNER" --name "$EXPERIMENT" --device "$DEVICE"
fi

ls "competitions/$COMPETITION/notebooks/baselines"
test -f "$BASELINE_DIR/baseline.ipynb"
test -f "$BASELINE_DIR/kernel-metadata.json"

# VS Code で入力・依存関係・提出ファイル名・ライセンスを確認し、変更したら保存する
# Titanic の Random Forest は CPU 学習。cuda 指定だけでは GPU 学習には変わらない
code "$BASELINE_DIR/baseline.ipynb"
code "$BASELINE_DIR/kernel-metadata.json"
```

```bash
# 編集・保存が終わってから実行する
mkdir -p "$NOTEBOOK_DIR"
cp "$BASELINE_DIR/baseline.ipynb" "$NOTEBOOK_DIR/baseline.ipynb"
cp "$BASELINE_DIR/kernel-metadata.json" "$NOTEBOOK_DIR/kernel-metadata.json"

# アップロード先と実行設定を確認する（認証情報は読み込まない）
python - <<'PY'
import json
import os
from pathlib import Path
metadata = json.loads((Path(os.environ['NOTEBOOK_DIR']) / 'kernel-metadata.json').read_text())
for key in ('id', 'code_file', 'is_private', 'enable_gpu', 'enable_internet', 'competition_sources'):
    print(f'{key}: {metadata.get(key)}')
PY

# 表示された id のユーザー名が自分のものか確認してから次へ
```

## 4. Kaggle に push して実行する（実行ごとに新しいバージョン）

```bash
# すでに push 成功済みなら、このブロックを飛ばして 5 へ
python scripts/kaggle_cli.py kernels push -p "$NOTEBOOK_DIR" --timeout 3600

# 成功メッセージのバージョン番号を控える
```

## 5. 実行状態を確認する（COMPLETE になるまで）

```bash
# 実際に push した metadata から ID を読む。ユーザー名の打ち間違いを避ける
export NOTEBOOK_ID="$(python - <<'PY'
import json
import os
from pathlib import Path
print(json.loads((Path(os.environ['NOTEBOOK_DIR']) / 'kernel-metadata.json').read_text())['id'])
PY
)"

printf 'Notebook: https://www.kaggle.com/code/%s\n' "$NOTEBOOK_ID"
python scripts/kaggle_cli.py kernels status "$NOTEBOOK_ID"

# RUNNING / QUEUED なら、時間を置いて上の status コマンドだけを繰り返す
# ERROR なら Notebook のページでログを確認する
# COMPLETE になってから 6 へ進む。待機中に再 push しない
```

```bash
# ERROR のログを取得する場合だけ実行する（成功時は 6 へ）
# 番号は失敗したバージョンに合わせる
export FAILED_VERSION="1"
python scripts/kaggle_cli.py kernels output "$NOTEBOOK_ID/$FAILED_VERSION" -p "runs/$COMPETITION/errors/$EXPERIMENT-v$FAILED_VERSION"

# .log ファイルを VS Code で開いて原因を確認する
ls "runs/$COMPETITION/errors/$EXPERIMENT-v$FAILED_VERSION"
# FileNotFoundError ならログ中の実際の /kaggle/input の配置とコードを比較する
# 修正・保存後に 3 のコピー → 4 の push → 5 の状態確認を行う
# 再実行時は新しいバージョン番号で 6 へ進む
```

## 6. 完了したバージョンの結果を取得する

```bash
export NOTEBOOK_VERSION="1"  # push の成功メッセージ／Notebook ページの番号に合わせる
export DOWNLOAD_DIR="runs/$COMPETITION/downloads/$EXPERIMENT-v$NOTEBOOK_VERSION"

python scripts/kaggle_cli.py kernels output "$NOTEBOOK_ID/$NOTEBOOK_VERSION" -p "$DOWNLOAD_DIR"
ls "$DOWNLOAD_DIR"
test -f "$DOWNLOAD_DIR/submission.csv"
```

## 7. 提出ファイルを確認する

```bash
python - <<'PY'
import csv
import os
from pathlib import Path

def read(path):
    with path.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return reader.fieldnames, rows

columns, sample = read(Path('data') / os.environ['COMPETITION'] / os.environ['SAMPLE_SUBMISSION'])
actual_columns, predictions = read(Path(os.environ['DOWNLOAD_DIR']) / 'submission.csv')
assert columns and len(columns) > 1, '提出例の列を確認してください'
assert actual_columns == columns, '列名または列順が異なります'
assert len(predictions) == len(sample) > 0, '行数が異なるか空です'
id_column = columns[0]
assert [row[id_column] for row in predictions] == [row[id_column] for row in sample], 'ID または行順が異なります'
assert len({row[id_column] for row in predictions}) == len(predictions), 'ID が重複しています'
assert all(set(row) == set(columns) and all(row[c] not in (None, '') for c in columns) for row in predictions), '欠損または余分な値があります'
if os.environ['COMPETITION'] == 'titanic':
    assert all(row['Survived'] in ('0', '1') for row in predictions), 'Survived は 0 / 1 にしてください'
print(f'提出形式 OK: {len(predictions)} 行 / {columns}')
PY

# 別コンペでは評価指標に応じて予測値の範囲なども確認する
# Titanic Tutorial には検証スコアの計算は含まれない
```

## 8. 1回提出してスコアを確認する

```bash
# 既存の提出を確認する
python scripts/kaggle_cli.py competitions submissions "$COMPETITION"

# 7 の確認が成功してから1回だけ実行する。これは新しい提出になる
python scripts/kaggle_cli.py competitions submit "$COMPETITION" -f "$DOWNLOAD_DIR/submission.csv" -m "$EXPERIMENT notebook-v$NOTEBOOK_VERSION"

# COMPLETE と publicScore を確認する。採点待ちなら、この一覧確認だけを繰り返す
python scripts/kaggle_cli.py competitions submissions "$COMPETITION"

# 通信エラー時も一覧で提出の有無を確認する。submit をそのまま繰り返さない
```

Code Competition のバージョン指定提出は [新しいコンペの手順7](new-competition.md#7-提出してスコアを確認する)。
自作 Python からの学習・Notebook 生成は [同手順4の B](new-competition.md#b自分の-python-を実装する)。
