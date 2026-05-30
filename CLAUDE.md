# /claude 運用ドキュメント

## プロジェクト概要

P店データリサーチは、みんレポの公開データからパチンコ・スロット店舗の
日次データを自動収集・分析し、レポート配信するプラットフォームです。

- フロントエンド: index.html ベース SPA
- バックエンド: FastAPI + Celery
- 運用: Hermes Agent
- DB: PostgreSQL / Redis

## ディレクトリ構造

```
P店データリサーチ/
├── backend/
│   ├── app/
│   │   ├── api/        - RESTルート
│   │   ├── scraper/    - データ収集（Playwright）
│   │   ├── analyzer/   - 分析ロジック
│   │   ├── hermes/     - 運用オーケストレーター
│   │   ├── notifier/   - Chatwork/Slack配信
│   │   ├── reporter/   - CSV/Text生成
│   │   └── models/     - DBモデル
│   └── frontend/       - index.html ベースSPA
├── infra/
│   └── docker-compose.yml
└── docs/
    ├── リリース資材/
    └── 組織図_P店データリサーチ.md
```

## リリース資材

- `docs/リリース資材/README.md` - プロダクト概要・導入手順
- `docs/リリース資材/CHANGELOG.md` - バージョン履歴
- `docs/リリース資材/deploy_notes.md` - 配備手順書
- `docs/リリース資材/.env.template` - 環境変数テンプレート

## 開発コマンド

```bash
cd backend
python -m uvicorn app.main:app --reload
```

## 注意事項

- 取得対象: みんレポ（ホワイトリスト固定）
- CAPTCHA突破・匿名化回避は禁止
- 本番運用は Hermes Agent が担当（Celery Beat で毎日03:00起動）
