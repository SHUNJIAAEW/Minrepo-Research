# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-01

### Added
- みんレポからの台データ自動収集（Playwright）
- 店舗別/機種別/台番別分析（総差枚・平均差枚・勝率等）
- Web UI（都道府県→店舗一覧→リサーチ）
- Hermes Agent による日次自動運用
- Chatwork/Slack へのレポート自動配信
- 実行履歴の記録・監視 API

### Infrastructure
- Docker Compose（PostgreSQL, Redis, API, Worker, Beat）
- FastAPI REST API
- Celery バッチ実行
- フロントエンド SPA（index.html）

### Release Docs
- CLAUDE.md
- README.md
- deploy_notes.md
- .env.template (in docs/リリース資材/)
