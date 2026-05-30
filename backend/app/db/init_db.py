"""
DB初期化スクリプト（開発・初回セットアップ用）。

    python -m app.db.init_db

全モデルのテーブルを作成する。本番環境では将来的に Alembic マイグレーションへ移行する。
"""
import asyncio
import logging

from app.db.base import engine, Base
import app.models  # noqa: F401  全モデルを Base.metadata に登録するため

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_models() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    tables = ", ".join(sorted(Base.metadata.tables.keys()))
    logger.info(f"テーブル作成完了: {tables}")


def main() -> None:
    asyncio.run(init_models())


if __name__ == "__main__":
    main()
