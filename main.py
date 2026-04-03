#!/usr/bin/env python3
import os
import asyncio
from datetime import datetime, timezone, timedelta
from tinkoff.api import TinkoffAPI, init as init_api
from tinkoff.balance_strategy import run_balance_strategy, FIGI

TOKEN = os.environ.get('TINKOFF_TOKEN', 't.KNbRWnr_MoKUOuBfzvjyUTUYftgAdZhpZ4zBqfwkgYtd4wnOaYuHCJHAeRXounciZ3N4NSQGPtH-8v5Mw0f_fQ')

MOSCOW_TZ = timezone(timedelta(hours=3))

init_api(TOKEN)
api = TinkoffAPI()


async def main():
    print("Tinkoff Trading Bot - Лесенка")
    print(f"FIGI: {FIGI}")
    
    await api.get_account_id()
    print(f"Account ID: {api.account_id}")
    
    while True:
        try:
            await run_balance_strategy(api)
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
