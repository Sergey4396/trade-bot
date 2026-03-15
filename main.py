#!/usr/bin/env python3
import os
import asyncio
import ssl
import aiohttp
import aiohttp.web
from datetime import datetime
from balance_strategy import run_balance_strategy

TOKEN = os.environ.get('TINKOFF_TOKEN', 'YOUR_TOKEN_HERE')
HTTP_PORT = int(os.environ.get('HTTP_PORT', '8080'))
HTTP_PASSWORD = os.environ.get('HTTP_PASSWORD', 'secret123')

BASE_URL = 'https://invest-public-api.tbank.ru'
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
FIGI_NRH6 = 'FUTNGM032600'


class TinkoffAPI:
    FIGI_NRH6 = FIGI_NRH6
    
    def __init__(self):
        self.account_id = None
    
    async def _request(self, method, url, data=None):
        headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(url, json=data or {}, headers=headers) as resp:
                return await resp.json()
    
    async def get_account_id(self):
        data = await self._request('GetAccounts', f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.UsersService/GetAccounts')
        accounts = data.get('accounts', [])
        if accounts:
            self.account_id = accounts[0]['id']
        return self.account_id
    
    async def get_orders(self, figi=None):
        if not self.account_id:
            await self.get_account_id()
        data = await self._request('GetOrders', f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.OrdersService/GetOrders', {'accountId': self.account_id})
        orders = data.get('orders', [])
        if figi:
            orders = [o for o in orders if o.get('figi') == figi]
        return orders
    
    async def cancel_order(self, order_id):
        if not self.account_id:
            await self.get_account_id()
        return await self._request('CancelOrder', f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.OrdersService/CancelOrder', {'accountId': self.account_id, 'orderId': order_id})
    
    async def post_order(self, figi, quantity, direction, price=None):
        if not self.account_id:
            await self.get_account_id()
        order_data = {'figi': figi, 'quantity': str(quantity), 'direction': direction, 'accountId': self.account_id, 'orderType': 'ORDER_TYPE_LIMIT'}
        if price:
            price_str = f"{price:.3f}" if figi.startswith('FUT') else f"{price:.2f}"
            parts = price_str.split('.')
            order_data['price'] = {'units': int(parts[0]), 'nano': int(parts[1].ljust(9, '0')[:9])}
        return await self._request('PostOrder', f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.OrdersService/PostOrder', order_data)
    
    async def get_futures_price(self, figi):
        data = await self._request('GetOrderBook', f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.MarketDataService/GetOrderBook', {'figi': figi, 'depth': 1})
        bids, asks = data.get('bids', []), data.get('asks', [])
        if bids and asks:
            return (self._parse_price(bids[0].get('price', {})) + self._parse_price(asks[0].get('price', {}))) / 2
        return None
    
    def _parse_price(self, price_dict):
        units, nano = price_dict.get('units', 0), price_dict.get('nano', 0)
        return float(f"{units}.{str(nano // 1000000).zfill(3)}")
    
    async def get_position(self, figi):
        if not self.account_id:
            await self.get_account_id()
        data = await self._request('GetPositions', f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.OperationsService/GetPositions', {'accountId': self.account_id})
        for pos in data.get('futures', []):
            if pos.get('figi') == figi:
                return int(pos.get('balance', 0)) + int(pos.get('blocked', 0))
        return 0
    
    async def status_text(self):
        orders = await self.get_orders(FIGI_NRH6)
        pos = await self.get_position(FIGI_NRH6)
        return f'Orders: {len(orders)}, NRH6 position: {pos}'


api = TinkoffAPI()


async def handle_cancel_all(request):
    if request.query.get('password', '') != HTTP_PASSWORD:
        return aiohttp.web.Response(text='Unauthorized', status=401)
    orders = await api.get_orders(FIGI_NRH6)
    for order in orders:
        await api.cancel_order(order.get('orderId', ''))
    return aiohttp.web.Response(text=f'Cancelled {len(orders)} orders', status=200)


async def handle_status(request):
    return aiohttp.web.Response(text=await api.status_text(), status=200)


async def handle_health(request):
    return aiohttp.web.Response(text='OK', status=200)


async def main():
    print("Tinkoff Trading Bot")
    app = aiohttp.web.Application()
    app.router.add_get('/health', handle_health).add_get('/cancel-all', handle_cancel_all).add_get('/status', handle_status)
    runner = await aiohttp.web.AppRunner(app).setup()
    await aiohttp.web.TCPSite(runner, '0.0.0.0', HTTP_PORT).start()
    print(f"HTTP server started on port {HTTP_PORT}")
    
    await api.get_account_id()
    print(f"Account ID: {api.account_id}")
    
    while True:
        try:
            await run_balance_strategy(api)
            for _ in range(60):
                await asyncio.sleep(10)
                print(f"=== {datetime.now().strftime('%H:%M:%S')} ===")
                print(f"NRH6: заявок={len(await api.get_orders(FIGI_NRH6))}, позиция={await api.get_position(FIGI_NRH6)}")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(10)


if __name__ == '__main__':
    asyncio.run(main())
