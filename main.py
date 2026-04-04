#!/usr/bin/env python3
import asyncio
from datetime import datetime, timezone, timedelta
from tinkoff.balance_strategy import run_all_strategies
from tinkoff.config import TOKENS, INSTRUMENTS

MOSCOW_TZ = timezone(timedelta(hours=3))


async def main():
    print("Tinkoff Trading Bot - Лесенка")
    print(f"Аккаунтов: {len(TOKENS)}")
    print(f"Инструментов: {len(INSTRUMENTS)}")
    for inst in INSTRUMENTS:
        print(f"  - {inst['ticker']} ({inst['figi']}) @ {inst['account']}")
    
    while True:
        try:
            await run_all_strategies()
            for _ in range(60):
                await asyncio.sleep(10)
                now_utc = datetime.now(timezone.utc)
                now_moscow = now_utc.astimezone(MOSCOW_TZ)
                print(f"=== {now_moscow.strftime('%H:%M:%S')} мск ===")
        except KeyboardInterrupt:
            print("\nОстановка...")
            break
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(10)


if __name__ == '__main__':
    asyncio.run(main())
