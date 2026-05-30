# P店データリサーチ

パチンコ・スロット店舗の公開データ（みんレポ）を収集・分析し、日次レポートを自動配信するプラットフォーム。
本番運用は **Hermes Agent**（`app/hermes/`）が担う。

## 構成

```
backend/
├── app/
│   ├── api/routes/   browse(エリア店舗検索) / stores / analysis / batch / hermes
│   ├── scraper/      みんレポ収集・robots/レート制御・SSRF対策
│   ├── analyzer/     分析（DB非依存の純粋計算 + DB保存）
│   ├── reporter/     CSV / テキストレポート生成
│   ├── notifier/     Chatwork配信 / 管理者アラート
│   ├── hermes/       運用エージェント（orchestrator / tools / cli）
│   ├── batch/        Celery タスク・ジョブ
│   ├── models/       DBモデル
│   └── db/           接続・初期化
├── frontend/         エリア選択UI(SPA)
└── HERMES.md         Hermes連携ガイド
docs/                 要件定義書 / 仕様書(.docx)
infra/                docker-compose
```

## セットアップ

### 1. 依存インストール
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. 環境変数
```bash
cp .env.example .env   # ADMIN_API_KEY 等を設定
```

### 3. DB初期化
```bash
# PostgreSQL を起動（infra/docker-compose.yml の db サービス等）
python -m app.db.init_db
```

### 4. 起動
```bash
uvicorn app.main:app --port 8000
# → http://localhost:8000/  でエリア選択UI
```

## 使い方

### Web UI（エリアから店舗を選んでリサーチ）
`http://localhost:8000/` を開き、都道府県を選択 → 店舗カードをクリック → その場で収集・分析。

### Hermes（運用）
```bash
# 日次フロー（収集→分析→配信）を手動実行
python -m app.hermes.cli run-daily --date 2026-05-28

# 個別ツール
python -m app.hermes.cli collect --store 1 --date 2026-05-28
python -m app.hermes.cli status  --date 2026-05-28
```

REST / Celery / 監視の詳細は [backend/HERMES.md](backend/HERMES.md) を参照。

## Docker
```bash
cd infra
docker compose up -d   # api / worker / beat / db / redis
```

## 既知の制約 / 次フェーズ
本ツールはMVPとして稼働可能。本番スケール時に対応予定の事項（Codexレビュー由来）:

- **収集の対象日検証**: 現状はタグURLから最新レポートを取得するため、過去日バックフィルは未対応（同日運用が前提）。
- **Hermes多重起動の排他**: 同一日の同時起動防止（advisory lock）は未実装。単一スケジューラ運用を前提。
- **分散レート制限**: robots/レート制御はプロセス内。複数ワーカー運用時はRedisベースへ移行が必要。
- **配信の冪等性強化**: 配信outbox / 再送制御は未実装。
- **責務集約**: collect/analyze/deliver の application service への一本化（現状 jobs.py と hermes/tools.py が併存）。
- **Alembicマイグレーション**: 現状は `init_db.py`（create_all）。本番はAlembic化推奨。
```
