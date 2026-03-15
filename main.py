#!/usr/bin/env python3
import os
import asyncio
import aiohttp
import aiohttp.web
from datetime import datetime
from tinkoff.api import TinkoffAPI, init as init_api
from tinkoff.handlers import init as init_handlers, handle_health, handle_cancel_all, handle_status
from tinkoff.balance_strategy import run_balance_strategy, FIGI

TOKEN = os.environ.get('TINKOFF_TOKEN', 'YOUR_TOKEN_HERE')
HTTP_PORT = int(os.environ.get('HTTP_PORT', '8080'))
HTTP_PASSWORD = os.environ.get('HTTP_PASSWORD', 'secret123')

init_api(TOKEN)
init_handlers(HTTP_PASSWORD)
api = TinkoffAPI()


async def main():
    print("Tinkoff Trading Bot")
    app = aiohttp.web.Application()
    app.router.add_get('/health', handle_health)
    app.router.add_get('/cancel-all', lambda r: handle_cancel_all(r, api))
    app.router.add_get('/status', lambda r: handle_status(r, api))
    runner = await aiohttp.web.AppRunner(app).setup()
    await aiohttp.web.TCPSite(runner, '0.0.0.0', HTTP_PORT).start()
    print(f"HTTP server started on port {HTTP_PORT}")
    
    await api.get_account_id()
    print(f"Account ID: {api.account_id}")
    figi = FIGI
    
    while True:
        try:
            await run_balance_strategy(api)
            for _ in range(60):
                await asyncio.sleep(10)
                print(f"=== {datetime.now().strftime('%H:%M:%S')} ===")
                print(f"заявок={len(await api.get_orders(figi))}, позиция={await api.get_position(figi)}")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(10)


if __name__ == '__main__':
    asyncio.run(main())
