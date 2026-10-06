# 自分でコンペ・実験を進める

コマンドは Dev Container 内のターミナルで、リポジトリルートから実行します。

| やりたいこと | 手順 |
| --- | --- |
| VS Code の導入・WSL・認証設定から始める | [ルート README](../README.md) |
| 公開ベースラインの取得から提出まで、コマンドを順に追う | [competition-commands.md](competition-commands.md) |
| 既存コンペで自分のモデルや設定を試す | [experiments.md](experiments.md) |
| 手元の NLP コンペのモデルを初心者として変更する | [nlp-model-change.md](nlp-model-change.md) |
| 新しいコンペを追加して、実装・検証・提出する | [new-competition.md](new-competition.md) |
| コンペ名から Kaggle の公開ベースラインを取得して始める | [new-competition.md・手順4の A](new-competition.md#4-公開ベースラインを取り込むまたは自分で実装する) |
| 新コンペの Python の呼び出し順・入力・出力を理解する | [competition-python-flow.md](competition-python-flow.md) |
| モデルの定義と重みを分け、保管・再利用する | [models.md](models.md) |
| モデル・解法だけを差し替える共通構成を理解する | [components.md](components.md) |

コンペ固有のデータ形式・評価指標・実測結果は、各 `competitions/<slug>/README.md` と
`RESULTS.md` に記録します。トークン、配布データ、学習済みモデルはこの文書に貼りません。
