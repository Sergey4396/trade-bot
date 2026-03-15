#!/usr/bin/env python3
import os
import asyncio
import ssl
import aiohttp
import aiohttp.web
from datetime import datetime
from balance_strategy import run_balance_strategy

TOKEN = os.environ.get('TINKOFF_TOKEN', 'YOUR_TOKEN_HERE')
ACCOUNT_ID = None
HTTP_PORT = int(os.environ.get('HTTP_PORT', '8080'))
HTTP_PASSWORD = os.environ.get('HTTP_PASSWORD', 'secret123')

BASE_URL = 'https://invest-public-api.tbank.ru'

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

FIGI_NRH6 = 'FUTNGM032600'


class TinkoffAPI:
    """Обёртка над Tinkoff API"""
    FIGI_NRH6 = FIGI_NRH6
    
    def __init__(self):
        self.account_id = None
    
    async def get_account_id(self):
        url = f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.UsersService/GetAccounts'
        headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(url, json={}, headers=headers) as resp:
                data = await resp.json()
                accounts = data.get('accounts', [])
                if accounts:
                    self.account_id = accounts[0]['id']
                    return self.account_id
        return None
    
    async def get_positions(self):
        if not self.account_id:
            await self.get_account_id()
        
        url = f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.OperationsService/GetPositions'
        headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(url, json={'accountId': self.account_id}, headers=headers) as resp:
                data = await resp.json()
                return data.get('futures', [])
    
    async def get_orders(self):
        if not self.account_id:
            await self.get_account_id()
        
        url = f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.OrdersService/GetOrders'
        headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(url, json={'accountId': self.account_id}, headers=headers) as resp:
                data = await resp.json()
                return data.get('orders', [])
    
    async def cancel_order(self, order_id):
        if not self.account_id:
            await self.get_account_id()
        
        url = f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.OrdersService/CancelOrder'
        headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(url, json={'accountId': self.account_id, 'orderId': order_id}, headers=headers) as resp:
                return await resp.json()
    
    async def post_order(self, figi, quantity, direction, price=None, order_type='ORDER_TYPE_LIMIT'):
        if not self.account_id:
            await self.get_account_id()
        
        url = f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.OrdersService/PostOrder'
        headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
        
        order_data = {
            'figi': figi,
            'quantity': str(quantity),
            'direction': direction,
            'accountId': self.account_id,
            'orderType': order_type
        }
        
        if price is not None:
            if figi.startswith('FUT'):
                price_str = f"{price:.3f}"
            else:
                price_str = f"{price:.2f}"
            parts = price_str.split('.')
            units = int(parts[0])
            nano = int(parts[1].ljust(9, '0')[:9])
            order_data['price'] = {'units': units, 'nano': nano}
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(url, json=order_data, headers=headers) as resp:
                return await resp.json()
    
    async def get_futures_price_by_figi(self, figi):
        url = f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.MarketDataService/GetOrderBook'
        headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(url, json={'figi': figi, 'depth': 1}, headers=headers) as resp:
                data = await resp.json()
                bids = data.get('bids', [])
                asks = data.get('asks', [])
                if bids and asks:
                    bid_price = self._format_price(bids[0].get('price', {}))
                    ask_price = self._format_price(asks[0].get('price', {}))
                    return (bid_price + ask_price) / 2
                return None
    
    def _format_price(self, price_dict):
        if isinstance(price_dict, str):
            return float(price_dict)
        units = price_dict.get('units', 0)
        nano = price_dict.get('nano', 0)
        first_three = nano // 1000000
        return float(f"{units}.{str(first_three).zfill(3)}")


api = TinkoffAPI()


async def handle_cancel_all(request):
    password = request.query.get('password', '')
    if password != HTTP_PASSWORD:
        return aiohttp.web.Response(text='Unauthorized', status=401)
    
    try:
        orders = await api.get_orders()
        nrh6_orders = [o for o in orders if o.get('figi') == FIGI_NRH6]
        
        cancelled = 0
        for order in nrh6_orders:
            order_id = order.get('orderId')
            if order_id:
                await api.cancel_order(order_id)
                cancelled += 1
        
        return aiohttp.web.Response(text=f'Cancelled {cancelled} orders', status=200)
    except Exception as e:
        return aiohttp.web.Response(text=f'Error: {e}', status=500)


async def handle_status(request):
    try:
        orders = await api.get_orders()
        positions = await api.get_positions()
        
        nrh6_qty = 0
        for pos in positions:
            if pos.get('figi') == FIGI_NRH6:
                nrh6_qty = int(pos.get('balance', 0)) + int(pos.get('blocked', 0))
        
        nrh6_orders = [o for o in orders if o.get('figi') == FIGI_NRH6]
        
        return aiohttp.web.Response(
            text=f'Orders: {len(nrh6_orders)}, NRH6 position: {nrh6_qty}',
            status=200
        )
    except Exception as e:
        return aiohttp.web.Response(text=f'Error: {e}', status=500)


async def handle_health(request):
    return aiohttp.web.Response(text='OK', status=200)


async def start_http_server():
    app = aiohttp.web.Application()
    app.router.add_get('/health', handle_health)
    app.router.add_get('/cancel-all', handle_cancel_all)
    app.router.add_get('/status', handle_status)
    
    runner = await aiohttp.web.AppRunner(app).setup()
    site = aiohttp.web.TCPSite(runner, '0.0.0.0', HTTP_PORT)
    await site.start()
    print(f"HTTP server started on port {HTTP_PORT}")


async def print_status():
    """Печатаем текущий статус"""
    positions = await api.get_positions()
    nrh6_qty = 0
    for pos in positions:
        if pos.get('figi') == FIGI_NRH6:
            nrh6_qty = int(pos.get('balance', 0)) + int(pos.get('blocked', 0))
    
    orders = await api.get_orders()
    nrh6_orders = [o for o in orders if o.get('figi') == FIGI_NRH6]
    
    print(f"=== {datetime.now().strftime('%H:%M:%S')} ===")
    print(f"NRH6: позиция={nrh6_qty}, заявок={len(nrh6_orders)}")


async def main():
    print("Tinkoff Trading Bot")
    
    await start_http_server()
    await asyncio.sleep(1)
    
    await api.get_account_id()
    print(f"Account ID: {api.account_id}")
    
    await print_status()
    
    while True:
        try:
            await run_balance_strategy(api)
            
            for _ in range(60):
                await asyncio.sleep(10)
                await print_status()
                
        except KeyboardInterrupt:
            print("\nStopping...")
            break
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(10)


if __name__ == '__main__':
    asyncio.run(main())
