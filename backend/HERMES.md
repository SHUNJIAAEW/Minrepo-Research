# Hermes Agent 連携ガイド

Hermes Agent ＝ 本システムの **本番運用オーケストレーター**。
「定時に起きて、全店舗の収集→分析→配信を回し、ログを残し、失敗を通知する」役割を担う。

## アーキテクチャ

```
            ┌─────────────── トリガー ───────────────┐
   Celery Beat (cron)     REST API           CLI         外部エージェント/SaaS
   毎日03:00自動起動    POST /hermes/run-daily  python -m app.hermes.cli   (APIキーで叩く)
            └───────────────┬──────────────────────────┘
                            ▼
              orchestrator.run_daily_flow()      ← 日次フロー本体
                            │  ステップ管理 / 失敗継続 / HermesRun記録 / 失敗通知
                            ▼
        ┌──── ツール層 app/hermes/tools.py（操作の正本）────┐
        collect    analyze    deliver    status    health
        └───────────────┬───────────────────────────────┘
                        ▼
             既存ジョブ (collect_store / run_analysis / dispatch)
```

ポイント:
- **ツール層が「エージェントが呼べる操作」の正本**。CLI / REST / Celery / 将来のLLMエージェントはすべてこの層を共有する。
- Celery Beat は「定時にHermesを起こす」だけ。収集・分析・配信・リトライ・通知・ログはすべて orchestrator が担う。

## 1. トリガー（起動方法）

### A. スケジュール（本番デフォルト）
`app/batch/tasks.py` の Beat が毎日03:00(JST)に `run_daily_flow(昨日)` を実行。
```bash
celery -A app.batch.tasks.celery_app worker -l info
celery -A app.batch.tasks.celery_app beat -l info
```

### B. REST（外部エージェント / 運用ダッシュボードから）
```bash
# 日次フロー起動（即時202 → バックグラウンド実行）
curl -X POST http://localhost:8000/api/v1/hermes/run-daily \
  -H "X-API-Key: $ADMIN_API_KEY" -H "Content-Type: application/json" \
  -d '{"record_date":"2026-05-28","background":true}'
```

### C. CLI（手動 / 別スケジューラ / 障害復旧）
```bash
python -m app.hermes.cli run-daily --date 2026-05-28
python -m app.hermes.cli collect --store 1 --date 2026-05-28
python -m app.hermes.cli status  --date 2026-05-28
```

## 2. ツール（段階実行・エージェント連携）

LLMエージェントや外部基盤には、以下を「関数(tool)」として渡す。実体は `app/hermes/tools.py`。

| tool | 引数 | 役割 |
|------|------|------|
| `health` | — | DB接続・稼働店舗数 |
| `collect` | store_id, record_date | データ収集（冪等） |
| `analyze` | store_id, record_date | 分析・レポート生成 |
| `deliver` | store_id, record_date | レポート配信 |
| `status` | record_date | 運用状況サマリー |

すべて `ToolResult{ok, tool, detail, data, error}` を返すので、エージェントは結果を見て次手を判断できる。
REST でも同じツールを個別に叩ける（`POST /hermes/tools/collect` 等）。

### LLMエージェント / MCP に載せる場合
`TOOL_CATALOG`（tools.py）を function-calling のスキーマに変換するか、
各ツールをMCPサーバーの tool としてラップすれば、Claude等のエージェントが
「collect→analyze→deliver を自律的にオーケストレーションする Hermes」になる。

## 3. 監視

```bash
# 直近の実行履歴
curl http://localhost:8000/api/v1/hermes/runs -H "X-API-Key: $ADMIN_API_KEY"
# 個別実行の詳細（ステップ・メトリクス・エラーサマリー）
curl http://localhost:8000/api/v1/hermes/runs/1 -H "X-API-Key: $ADMIN_API_KEY"
```

- 各実行は `hermes_runs` テーブルに記録（status / steps / metrics / error_summary）。
- 失敗・部分失敗時は `notify_admin()` が Slack Webhook → Chatwork の順でアラート送信。
  - `.env`: `SLACK_WEBHOOK_URL` または `CHATWORK_API_TOKEN` + `CHATWORK_ROOM_ID`

## 次の拡張余地
- ステップ単位リトライ（現状は店舗単位で継続、収集失敗は当該店舗のみスキップ）
- `HermesRun` をフロントのダッシュボードに表示
- MCPサーバー化してClaude/GPTから直接オーケストレーション
