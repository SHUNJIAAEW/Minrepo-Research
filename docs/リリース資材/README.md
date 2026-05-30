# P店データリサーチ リリース資材一式

このフォルダは、クライアントへの導入に必要なドキュメント・テンプレートを
1箇所に束ねた配布物です。

- `README.md`
- `CHANGELOG.md`
- `deploy_notes.md`
- `.env.template`

配布時はこのREADMEを先に提示し、導入先の環境に合わせて
`deploy_notes.md` と `.env.template` を渡してください。


## 1. はじめに

本書では、P店データリサーチ株式会社が提供する
「パチンコ・スロット データ収集・分析プラットフォーム」
について、リリースに必要な情報を整理しています。

- 自動収集元: みんレポ
- 分析: 店舗別/機種別/台番別の 総差枚/平均差枚/平均G数/勝率
- レポート配信: Chatwork/Slack
- Web UI: 都道府県→店舗一覧→リサーチ


## 2. 対象ドキュメント一覧

| ファイル | 用途 | 共有先 |
| --- | --- | --- |
| `README.md` | リリース概要・導入手順・運用フロー | クライアント/運用担当 |
| `CHANGELOG.md` | リリースノート | クライアント |
| `deploy_notes.md` | 配備手順書 | インフラ担当 |
| `.env.template` | 環境変数テンプレート | インフラ担当 |


## 3. 導入の前提

- OS: Linux / macOS
- Docker / Docker Compose が動作する環境
- 取得対象: みんレポ
- 告示: 取得対象はホワイトリスト固定


## 4. クイックスタート

```bash
git clone <repository-url>
cd "P店データリサーチ"
cp docs/.env.template backend/.env
# backend/.env を編集してから起動
docker compose -f infra/docker-compose.yml up -d
open http://localhost:8000
```

## 5. 関連ドキュメント

- [requirements_definition](その他/requirements_definition.md)
- [organization_definition](その他/organization_definition.md)
