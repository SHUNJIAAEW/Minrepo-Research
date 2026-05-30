# 配備手順書 - P店データリサーチ

## 前提条件

- Docker / Docker Compose がインストールされていること
- ポート 8000, 5432, 6379 が空いていること
- Git がインストールされていること

## 手順

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd "P店データリサーチ"
```

### 2. 環境変数の設定

```bash
cp backend/.env.example backend/.env
# backend/.env を編集して、必要な値を設定
```

### 3. Docker Compose で起動

```bash
docker compose -f infra/docker-compose.yml up -d
```

### 4. 動作確認

```bash
# API ヘルスチェック
curl http://localhost:8000/health

# ブラウザで起動
open http://localhost:8000
```

### 5. Celery の起動（バッチ運用）

```bash
docker compose -f infra/docker-compose.yml up -d worker beat
```

## トラブルシューティング

- ポート競合: docker-compose.yml の ports を変更してください
- DB接続エラー: DATABASE_URL を確認してください
- ログ確認: `docker compose logs`

## 本番運用

- Hermes日次フロー: 毎日03:00 JST に自動起動
- 実行履歴: `/api/v1/hermes/runs` で確認
- 失敗通知: Slack → Chatwork の順で配信
