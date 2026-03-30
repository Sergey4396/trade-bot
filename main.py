#!/usr/bin/env python3
import os
import asyncio
from datetime import datetime
from tinkoff.api import TinkoffAPI, init as init_api
from tinkoff.balance_strategy import run_balance_strategy, FIGI

TOKEN = os.environ.get('TINKOFF_TOKEN', 't.KNbRWnr_MoKUOuBfzvjyUTUYftgAdZhpZ4zBqfwkgYtd4wnOaYuHCJHAeRXounciZ3N4NSQGPtH-8v5Mw0f_fQ')

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
                print(f"=== {datetime.now().strftime('%H:%M:%S')} ===")
        except KeyboardInterrupt:
            print("\nОстановка...")
            break
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(10)


if __name__ == '__main__':
    asyncio.run(main())
