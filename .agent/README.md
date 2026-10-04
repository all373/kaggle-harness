# エージェント用の入口

会話がなくても、このワークスペースでの作業を再開するための案内。
認証情報・会話全文・データは置かない。このフォルダは Git で共有できる。

| 知りたいこと | 読む場所 |
| --- | --- |
| 作業上の方針 | [ルート AGENTS.md](../AGENTS.md) |
| 現在までの進捗・未完了事項 | [PROGRESS.md](../PROGRESS.md) |
| ファイルの役割・依存関係・モデルの限界 | [MAP.md](MAP.md) |
| 実行・テスト・再取得・提出のコマンド | [WORKFLOWS.md](WORKFLOWS.md) |
| 初心者向けの環境構築 | [ルート README](../README.md) |
| 自分の実装と新しいコンペの手順 | [docs/README.md](../docs/README.md) |
| NLP の再現手順 | [NLP README](../competitions/word2vec-nlp-tutorial/README.md) |
| NLP の実測結果 | [NLP RESULTS](../competitions/word2vec-nlp-tutorial/RESULTS.md) |
| ARC の再現手順 | [ARC README](../competitions/arc-prize-2026-arc-agi-2/README.md) |
| ARC の実測結果 | [ARC RESULTS](../competitions/arc-prize-2026-arc-agi-2/RESULTS.md) |

最初は AGENTS.md と PROGRESS.md を読み、対象の資料だけを追加で読む。
広い検索では `rg --files` を使い、`data/`・`runs/`・秘密設定の全文検索を避ける。
成果物を調べるときは必要な `metrics.json` / `result.json` を指定して読む。

2026-10-04 に既存の構成と実行結果をもとに作成。以後は実際のコードと記録に合わせて更新する。
