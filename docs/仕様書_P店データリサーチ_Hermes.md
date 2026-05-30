





仕様書
System Specification Document


パチンコ・スロット データ収集・分析プラットフォーム
運用エージェント Hermes









目次

1. 本書の位置づけ
本書は要件定義書(RD-2026-001)で定めた要件を実現するための技術仕様を記述する。システム全体構成、Hermes運用層の設計、データ収集、分析、API、データベース、セキュリティ、配備、運用を対象とする。
2. システム全体構成
2.1 構成概要
フロントエンド（SPA）、バックエンド（FastAPI）、運用層（Hermes + Celery）、データストア（PostgreSQL/Redis）から成る。Hermes は本番運用のオーケストレーターとして、収集・分析・配信を制御する。
2.2 技術スタック
3. Hermes 運用層 設計
Hermes は「定時に起きて、全店舗の収集→分析→配信を回し、ログを残し、失敗を通知する」本番運用エージェント。トリガー／ツール／監視の3層で構成する。
3.1 レイヤ構成
3.2 日次実行フロー
仕様書の10ステップに対応する。
3.3 ツール仕様
各ツールは ToolResult{ok, tool, detail, data, error} を返し、例外を握りつぶさず構造化して報告する。CLI/REST/Celery/将来のLLMエージェントが同一インターフェースを共有する。
3.4 トリガー仕様
3.5 監視・障害通知
実行ごとに HermesRun（status/steps/metrics/error_summary）を記録。
GET /api/v1/hermes/runs, /runs/{id} で参照。
失敗・部分失敗時に notify_admin() が Slack Webhook → Chatwork の順でアラート送信。
4. データ収集 設計
4.1 スクレイパー構成
BaseScraper: Playwright制御、robots.txt判定、ホスト単位レート制御、同時実行数制御、リトライを共通化。
MinnrepoScraper: みんレポの全台一覧(?kishu=all)をヘッダ名(機種/台番/差枚/G数)でテーブル検出して解析。
MinnrepoBrowser: 都道府県カテゴリページから店舗カード(ichiran_post)を解析。
MinnrepoFinder: 店舗名検索から最新レポートURLを解決。
registry: サイト名→スクレイパーの対応表でプラグイン的に拡張。
4.2 コンプライアンス制御
5. 分析 設計
compute.analyze_units(): DB非依存の純粋関数。台データから店舗・機種サマリーを算出。
欠損値(None)の差枚・G数は平均・勝率の母数から除外（未取得台を0扱いして歪めない）。
engine.run_analysis(): DB上の台データを分析し MachineResult/DailyReport を生成（再分析時は delete-then-insert）。
主要指標: 総差枚=Σ差枚、平均差枚=総差枚/有効台数、勝率=プラス台数/有効台数、プラス台割合、注目機種=総差枚最大の機種。
6. API 仕様
6.1 公開（認証不要）
6.2 操作系（APIキー必須: X-API-Key）
7. データベース設計
8. セキュリティ設計
9. 配備・運用
9.1 コンテナ構成
9.2 主要環境変数
9.3 運用手順(例)
起動: docker compose up -d（api/worker/beat/db/redis）
手動実行: python -m app.hermes.cli run-daily --date YYYY-MM-DD
監視: GET /api/v1/hermes/runs で実行状況・失敗を確認
障害対応: error_summaryを確認し、該当店舗のtoolを個別再実行
10. 将来拡張
HermesのLLMエージェント化: TOOL_CATALOGをfunction-calling/MCPツールに変換し自律オーケストレーション。
高度分析(配分・並び・塊・末尾・島、高設定推定、異常検知)の追加。
ステップ単位リトライ、実行履歴ダッシュボード、複数媒体対応。