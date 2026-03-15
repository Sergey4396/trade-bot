#!/usr/bin/env python3
import os
import asyncio
import ssl
import aiohttp
import aiohttp.web
from datetime import datetime

TOKEN = os.environ.get('TINKOFF_TOKEN', 'YOUR_TOKEN_HERE')
ACCOUNT_ID = None
HTTP_PORT = int(os.environ.get('HTTP_PORT', '8080'))
HTTP_PASSWORD = os.environ.get('HTTP_PASSWORD', 'secret123')

BASE_URL = 'https://invest-public-api.tbank.ru'

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

FIGI_NRH6 = 'FUTNGM032600'

last_balance_time = None
balance_running = False


def format_price(price_dict):
    """Format price from units/nano"""
    if isinstance(price_dict, str):
        return price_dict
    units = price_dict.get('units', 0)
    nano = price_dict.get('nano', 0)
    first_three = nano // 1000000
    return f"{units}.{str(first_three).zfill(3)}"


async def get_account_id():
    global ACCOUNT_ID
    url = f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.UsersService/GetAccounts'
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.post(url, json={}, headers=headers) as resp:
            data = await resp.json()
            accounts = data.get('accounts', [])
            if accounts:
                ACCOUNT_ID = accounts[0]['id']
                return ACCOUNT_ID
    return None


async def get_positions():
    global ACCOUNT_ID
    if not ACCOUNT_ID:
        await get_account_id()
    
    url = f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.OperationsService/GetPositions'
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.post(url, json={'accountId': ACCOUNT_ID}, headers=headers) as resp:
            data = await resp.json()
            return data.get('futures', [])


async def get_orders():
    global ACCOUNT_ID
    if not ACCOUNT_ID:
        await get_account_id()
    
    url = f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.OrdersService/GetOrders'
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.post(url, json={'accountId': ACCOUNT_ID}, headers=headers) as resp:
            data = await resp.json()
            return data.get('orders', [])


async def cancel_order(order_id):
    global ACCOUNT_ID
    if not ACCOUNT_ID:
        await get_account_id()
    
    url = f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.OrdersService/CancelOrder'
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.post(url, json={'accountId': ACCOUNT_ID, 'orderId': order_id}, headers=headers) as resp:
            return await resp.json()


async def post_order(figi, quantity, direction, price=None, order_type='ORDER_TYPE_LIMIT'):
    global ACCOUNT_ID
    if not ACCOUNT_ID:
        await get_account_id()
    
    url = f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.OrdersService/PostOrder'
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    
    order_data = {
        'figi': figi,
        'quantity': str(quantity),
        'direction': direction,
        'accountId': ACCOUNT_ID,
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


async def get_futures_price_by_figi(figi):
    """Get futures price from order book"""
    url = f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.MarketDataService/GetOrderBook'
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.post(url, json={'figi': figi, 'depth': 1}, headers=headers) as resp:
            data = await resp.json()
            bids = data.get('bids', [])
            asks = data.get('asks', [])
            if bids and asks:
                bid_price = float(format_price(bids[0].get('price', {})))
                ask_price = float(format_price(asks[0].get('price', {})))
                return (bid_price + ask_price) / 2
            return None


async def print_status():
    """Print current status"""
    positions = await get_positions()
    nrh6_qty = 0
    for pos in positions:
        figi = pos.get('figi')
        balance = int(pos.get('balance', 0))
        blocked = int(pos.get('blocked', 0))
        total = balance + blocked
        
        if figi == FIGI_NRH6:
            nrh6_qty = total
    
    orders = await get_orders()
    nrh6_orders = [o for o in orders if o.get('figi') == FIGI_NRH6]
    
    print(f"=== {datetime.now().strftime('%H:%M:%S')} ===")
    print(f"NRH6: позиция={nrh6_qty}, заявок={len(nrh6_orders)}")


async def balance_strategy():
    """Простая балансная стратегия - выставляем ±10 уровней от текущей цены"""
    global last_balance_time, balance_running
    from datetime import datetime
    
    if balance_running:
        return
    
    # Проверяем каждые 10 минут
    if last_balance_time and (datetime.now() - last_balance_time).total_seconds() < 600:
        return
    
    balance_running = True
    orders_placed = False
    total_orders = 0
    
    try:
        now = datetime.now()
        print(f"\n=== {now.strftime('%H:%M:%S')} === Balance Strategy")
        
        nrh6_price = await get_futures_price_by_figi(FIGI_NRH6)
        
        if not nrh6_price:
            print("Не удалось получить цену NRH6")
            balance_running = False
            return
        
        orders = await get_orders()
        nrh6_orders = [o for o in orders if o.get('figi') == FIGI_NRH6]
        total_orders = len(nrh6_orders)
        
        print(f"NRH6: цена={nrh6_price}, заявок={total_orders}")
        
        if total_orders >= 60:
            print(f"Уже {total_orders} заявок, пропускаем")
            balance_running = False
            return
        
        step = 0.010
        base_price = round(nrh6_price - (nrh6_price % step), 3)
        range_levels = 10
        max_orders_per_side = 10
        
        available = 60 - total_orders
        
        # Покупки
        buy_count = min(max_orders_per_side, available)
        print(f"Выставляю {buy_count} покупок...")
        for i in range(1, buy_count + 1):
            price = base_price - step * i
            price = round(price, 3)
            print(f"  BUY: 1 @ {price}")
            try:
                result = await post_order(FIGI_NRH6, 1, 'ORDER_DIRECTION_BUY', price)
                if 'orderId' in result:
                    print(f"    OK: {result.get('orderId')}")
                    orders_placed = True
                    total_orders += 1
                else:
                    print(f"    Ошибка: {result.get('message', str(result))[:50]}")
            except Exception as e:
                print(f"    Исключение: {str(e)[:50]}")
            
            if total_orders >= 60:
                print(f"Достигли {total_orders} заявок, останавливаемся")
                break
        
        # Продажи
        available = 60 - total_orders
        if available > 0:
            sell_count = min(max_orders_per_side, available)
            print(f"Выставляю {sell_count} продаж...")
            for i in range(1, sell_count + 1):
                price = base_price + step * i
                price = round(price, 3)
                print(f"  SELL: 1 @ {price}")
                try:
                    result = await post_order(FIGI_NRH6, 1, 'ORDER_DIRECTION_SELL', price)
                    if 'orderId' in result:
                        print(f"    OK: {result.get('orderId')}")
                        orders_placed = True
                        total_orders += 1
                    else:
                        print(f"    Ошибка: {result.get('message', str(result))[:50]}")
                except Exception as e:
                    print(f"    Исключение: {str(e)[:50]}")
                
                if total_orders >= 60:
                    print(f"Достигли {total_orders} заявок, останавливаемся")
                    break
        
        print(f"Итого заявок: {total_orders}")
        
    except Exception as e:
        import traceback
        print(f"Ошибка в балансной стратегии: {e}")
        print(traceback.format_exc())
    
    finally:
        last_balance_time = datetime.now()
        print(f"Таймер обновлён")
        balance_running = False


async def handle_cancel_all(request):
    password = request.query.get('password', '')
    if password != HTTP_PASSWORD:
        return aiohttp.web.Response(text='Unauthorized', status=401)
    
    try:
        orders = await get_orders()
        nrh6_orders = [o for o in orders if o.get('figi') == FIGI_NRH6]
        
        cancelled = 0
        for order in nrh6_orders:
            order_id = order.get('orderId')
            if order_id:
                await cancel_order(order_id)
                cancelled += 1
        
        return aiohttp.web.Response(text=f'Cancelled {cancelled} orders', status=200)
    except Exception as e:
        return aiohttp.web.Response(text=f'Error: {e}', status=500)


async def handle_status(request):
    try:
        orders = await get_orders()
        positions = await get_positions()
        
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


async def main():
    global ACCOUNT_ID
    
    print("Tinkoff Trading Bot")
    
    await start_http_server()
    await asyncio.sleep(1)
    
    ACCOUNT_ID = await get_account_id()
    print(f"Account ID: {ACCOUNT_ID}")
    
    await print_status()
    
    while True:
        try:
            await balance_strategy()
            
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
