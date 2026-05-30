# P店データリサーチ株式会社 - 組織図・部署定義

> ツール群を職能別の部署に編成し、Hermes Agent による AI 社員工場として自動運用する。
> バックエンド実装、Herems フロー、リリース資材をここに閉じる。


## 1. 会社概要（AI社員編成ベース）

- 社名：P店データリサーチ株式会社
- 提供：パチンコ・スロットの公開データを自動収集・分析し、日次レポートを配信する SaaS
- 運用主体：Hermes Agent（オーケストレーター）
- 開発支援：Claude Code（1フェーズ限定、本番常駐しない）
- ユーザー：ホール営業・開発・販売戦略担当


## 2. 組織概要

```
[代表取締役/CEO] Hermes Agent（セッション本体 = オーケストレーター）
│
├── データ収集部       Minnrepo スクレイパー群
├── クライアントリサーチ部  ブラウザリサーチ機能
├── 分析部            分析エンジン
├── レポーティング部   CSV/Text/通知
├── API & 基盤部        FastAPI/認証/バッチ
└── 運用監視部         Hermes日次フロー/ログ/通知
```

- 原則：1ツール1役割。ツールに「ついでに～」を書かない。
- 入出力は構造化（JSON/YAML/Markdown/CSV）で固定。


## 3. 部署定義


### 3.1 データ収集部

責務: 許諾済み公開サイトのみからデータを収集する。

| ファイル | 役割 | 公開/非公開 |
| --- | --- | --- |
| scraper/minnrepo.py | 機種/台番ページのテーブル抽出 | 非公開 |
| scraper/minnrepo_browser.py | ブラウザ経由で店舗一覧を取得 | 非公開 |
| scraper/minnrepo_finder.py | 店舗名→レポートURL解決 | 非公開 |
| scraper/base.py | Playwright 共通ラッパ | 非公開 |
| scraper/throttle.py | レート制御・リトライ | 非公開 |
| scraper/sources.py | 取得元サイトの定義・ホワイトリスト | 非公開 |
| scraper/registry.py | サイト名→スクレイパーの対応表 | 非公開 |

成果物:
- 生データ: `output/raw/` 相当
- 収集ログ
- 失敗レポート（API or Slack 通知）


### 3.2 クライアントリサーチ部

責務: Web UI からエリア選択→店舗→その場リサーチの提供。

| ファイル | 役割 | 公開/非公開 |
| --- | --- | --- |
| api/routes/browse.py | ブラウザリサーチ API | 公開 |

操作フロー:
1. 都道府県を選択
2. 店舗一覧から target を選択
3. リサーチ実行 → 結果を返却


### 3.3 分析部

責務: 台データから店舗・機種サマリーを計算し、DayReport / MachineResult を生成する。

| ファイル | 役割 | 公開/非公開 |
| --- | --- | --- |
| analyzer/compute.py | 分析ロジック純粋関数 | 非公開 |
| analyzer/engine.py | DB からの実行ラッパ | 非公開 |

主要指標:
- 総差枚 = Σ差枚
- 平均差枚 = 有効台あたり
- 平均G数 = 有効台あたり
- 勝率 = プラス台数 / 有効台数
- プラス台割合
- 注目機種 = 総差枚最大機種

設計ルール:
- DB 非依存の Compute と DB 依存 Engine を分離
- 欠損値(None)は母数から除外（未取得を0にしない）


### 3.4 レポーティング部

責務: 分析結果をファイル化し、通知する。

| ファイル | 役割 | 公開/非公開 |
| --- | --- | --- |
| reporter/csv_reporter.py | CSV 生成 | 非公開 |
| reporter/text_reporter.py | テキスト/要約生成 | 非公開 |
| notifier/dispatcher.py | Chatwork/Slack 配信判定 | 非公開 |
| notifier/chatwork.py | Chatwork 配送 | 非公開 |
| notifier/admin.py | 管理通知 | 非公開 |

成果物: `output/reports/YYYY-MM-DD.csv` / `YYYY-MM-DD.md` 等


### 3.5 API & 基盤部

責務: 外部公開/操作系 API、DB/Redis 接続、セキュリティ、静的フロント配信。

| ファイル | 役割 | 公開/非公開 |
| --- | --- | --- |
| main.py | FastAPI アプリ全体 | 公開 |
| api/routes/stores.py | 店舗 API | 公開 |
| api/routes/analysis.py | 分析 API | 公開 |
| api/routes/batch.py | バッチ API | 非公開 |
| api/routes/hermes.py | Hermes 実行ログ API | 非公開 |
| core/config.py | 設定/環境変数 | 非公開 |
| core/security.py | APIキー/ヘッダ/レート制御 | 非公開 |
| db/base.py | DB セッション/マイグレ | 非公開 |

セキュリティ:
- 公開: `/api/v1/...` のうち認証不要
- 操作系: X-API-Key 要求


### 3.6 運用監視部

責務: 日次フローの Orchesration、リトライ、ログ、障害通知。

| ファイル | 役割 | 公開/非公開 |
| --- | --- | --- |
| hermes/orchestrator.py | run-daily の全体制御 | 非公開 |
| hermes/cli.py | CLI | 非公開 |
| hermes/tools.py | 各ツールの戻り値整形 | 非公開 |
| hermes/types.py | ToolResult 型 | 非公開 |
| batch/tasks.py | Celery タスク定義 | 非公開 |
| batch/jobs.py | 日次バックジョブ | 非公開 |

HermesRun 記録:
- GET `/api/v1/hermes/runs`
- GET `/api/v1/hermes/runs/{id}`

通知順:
- Slack Webhook → Chatwork（config 可）
