"""
Hermes Agent CLI トリガー。

使用例:
  python -m app.hermes.cli run-daily                     # 昨日分の日次フロー
  python -m app.hermes.cli run-daily --date 2026-05-28
  python -m app.hermes.cli collect --store 1 --date 2026-05-28
  python -m app.hermes.cli analyze --store 1 --date 2026-05-28
  python -m app.hermes.cli deliver --store 1 --date 2026-05-28
  python -m app.hermes.cli status --date 2026-05-28
"""
import argparse
import asyncio
import json
from datetime import date, timedelta

from app.hermes import tools
from app.hermes.orchestrator import run_daily_flow


def _parse_date(s: str | None) -> date:
    if s:
        return date.fromisoformat(s)
    return date.today() - timedelta(days=1)


async def _main(args) -> None:
    if args.command == "run-daily":
        result = await run_daily_flow(_parse_date(args.date), trigger="cli")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    rd = _parse_date(args.date)
    if args.command == "collect":
        res = await tools.tool_collect(args.store, rd)
    elif args.command == "analyze":
        res = await tools.tool_analyze(args.store, rd)
    elif args.command == "deliver":
        res = await tools.tool_deliver(args.store, rd)
    elif args.command == "status":
        res = await tools.tool_status(rd)
    elif args.command == "health":
        res = await tools.tool_health()
    else:
        raise SystemExit(f"unknown command: {args.command}")

    print(json.dumps(res.to_dict(), ensure_ascii=False, indent=2))


def main() -> None:
    p = argparse.ArgumentParser(prog="hermes", description="Hermes Agent CLI")
    sub = p.add_subparsers(dest="command", required=True)

    rd = sub.add_parser("run-daily", help="日次フローを実行")
    rd.add_argument("--date", help="対象日 YYYY-MM-DD（省略時は昨日）")

    for name in ("collect", "analyze", "deliver"):
        sp = sub.add_parser(name, help=f"{name} を単体実行")
        sp.add_argument("--store", type=int, required=True)
        sp.add_argument("--date", help="対象日 YYYY-MM-DD（省略時は昨日）")

    ss = sub.add_parser("status", help="運用状況サマリー")
    ss.add_argument("--date", help="対象日 YYYY-MM-DD（省略時は昨日）")

    sub.add_parser("health", help="ヘルスチェック")

    args = p.parse_args()
    asyncio.run(_main(args))


if __name__ == "__main__":
    main()
