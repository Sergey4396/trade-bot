#!/usr/bin/env python3
"""
Tinkoff Trading Bot - Simple polling version
"""
import os
import json
import asyncio
import ssl
import aiohttp
from datetime import datetime

TOKEN = os.environ.get('TINKOFF_TOKEN', 'YOUR_TOKEN_HERE')
ACCOUNT_ID = None

BASE_URL = 'https://invest-public-api.tinkoff.ru'

# SSL context that doesn't verify certificates
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# FIGI codes
FIGI_NRH6 = 'FUTNGM032600'
FIGI_NGH6 = 'FUTNG0326000'
FIGI_NGJ6 = 'FUTNG0426000'
FIGI_VTBR = 'BBG004730ZJ9'
FIGI_IMOEXF = 'FUTIMOEXF000'

OFFSETS = {
    FIGI_NRH6: 0.010,   # NRH6: ±0.010
    FIGI_NGH6: 0.025,   # NGH6: ±0.025
    FIGI_NGJ6: 0.010,   # NGJ6: ±0.010
    FIGI_VTBR: 0.40,    # VTBR: ±0.40
    FIGI_IMOEXF: 7.0,   # IMOEXF: ±7.0
}

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

async def get_prices(figi_list):
    url = f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.MarketDataService/GetLastPrices'
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.post(url, json={'figi': figi_list}, headers=headers) as resp:
            data = await resp.json()
            return data.get('lastPrices', [])

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
    """Get active orders"""
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
    """Cancel an order"""
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
    
    # Add price for limit orders
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

async def get_operations(from_date, to_date):
    """Get operations (trades)"""
    global ACCOUNT_ID
    if not ACCOUNT_ID:
        await get_account_id()
    
    url = f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.OperationsService/GetOperations'
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    
    # Get operations for last N seconds
    from_iso = from_date.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    to_iso = to_date.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    
    operations_data = {
        'accountId': ACCOUNT_ID,
        'from': from_iso,
        'to': to_iso,
        'state': 'OPERATION_STATE_EXECUTED'
    }
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.post(url, json=operations_data, headers=headers) as resp:
            data = await resp.json()
            return data.get('operations', [])

# Track last known operations
last_operation_ids = set()

async def check_new_trades():
    """Check for new executed trades and place counter-orders"""
    global last_operation_ids
    
    from datetime import timedelta
    now = datetime.now()
    operations = await get_operations(now - timedelta(seconds=30), now)
    
    new_trades = []
    for op in operations:
        op_id = op.get('id')
        if op_id and op_id not in last_operation_ids:
            figi = op.get('figi')
            op_type = op.get('type', '')
            trades = op.get('trades', [])
            
            if not figi and trades:
                figi = trades[0].get('figi')
            
            if figi in [FIGI_NRH6, FIGI_NGH6, FIGI_NGJ6, FIGI_VTBR, FIGI_IMOEXF]:
                # Determine direction from operation type
                if 'Покупка' in op_type:
                    direction = 'OPERATION_DIRECTION_BUY'
                elif 'Продажа' in op_type:
                    direction = 'OPERATION_DIRECTION_SELL'
                else:
                    direction = None
                
                if direction:
                    # Process each trade in the operation
                    for trade in trades:
                        price = format_price(trade.get('price', {}))
                        quantity = trade.get('quantity', '1')
                        new_trades.append({
                            'figi': figi,
                            'direction': direction,
                            'price': price,
                            'quantity': quantity
                        })
                        print(f"New trade: {figi} {direction} {quantity} @ {price}")
                    
                    # Mark operation as processed after all trades
                    last_operation_ids.add(op_id)
    
    return new_trades

async def place_counter_order(trade_info):
    """Place counter-order at specified price offset"""
    figi = trade_info['figi']
    direction = trade_info['direction']
    price = float(trade_info['price'])
    quantity = int(trade_info['quantity'])
    
    offset = OFFSETS.get(figi, 0.010)
    
    # Determine counter direction
    if direction == 'OPERATION_DIRECTION_BUY':
        counter_direction = 'ORDER_DIRECTION_SELL'
        counter_price = price + offset
    else:  # SELL
        counter_direction = 'ORDER_DIRECTION_BUY'
        counter_price = price - offset
    
    # Round appropriately
    if figi.startswith('FUT'):
        counter_price = round(counter_price, 3)
    else:
        counter_price = round(counter_price, 2)
    
    print(f"Placing counter-order: {figi} {counter_direction} {quantity} @ {counter_price}")
    
    result = await post_order(figi, quantity, counter_direction, counter_price)
    print(f"Order result: {result}")
    return result

def format_price(price_dict):
    """Format price from units/nano"""
    units = price_dict.get('units', 0)
    nano = price_dict.get('nano', 0)
    # nano is in nanounits (10^-9), divide by 10^6 to get 3 decimal places
    # e.g., 3.091 has nano=91000000, 3.910 has nano=910000000
    first_three = nano // 1000000
    return f"{units}.{str(first_three).zfill(3)}"

async def print_status():
    """Print current status"""
    print(f"\n=== {datetime.now().strftime('%H:%M:%S')} ===")
    
    # Get prices
    prices = await get_prices([FIGI_NRH6])
    nrh6_price = 'N/A'
    
    for p in prices:
        if p.get('figi') == FIGI_NRH6:
            nrh6_price = format_price(p.get('price', {}))
    
    print(f"NRH6: {nrh6_price}")
    
    # Get positions
    positions = await get_positions()
    nrh6_qty = 0
    
    for pos in positions:
        figi = pos.get('figi', '')
        balance = int(pos.get('balance', 0))
        blocked = int(pos.get('blocked', 0))
        total = balance + blocked
        
        if figi == FIGI_NRH6:
            nrh6_qty = total
    
    print(f"Positions - NRH6: {nrh6_qty}")


# Track last balance strategy run time
last_balance_time = None
balance_running = False

async def balance_strategy():
    """Стратегия удержания позиции NRH6 в диапазоне [-1, -201]"""
    global last_balance_time, balance_running
    from datetime import datetime, timedelta
    
    # Блокировка - не запускаем если уже работает
    if balance_running:
        print("Балансная стратегия уже выполняется, пропускаю")
        return
    
    # Проверяем когда последний раз запускали (минимум 5 минут назад)
    if last_balance_time and (datetime.now() - last_balance_time).total_seconds() < 300:
        print(f"Балансная стратегия пропущена, прошло только {(datetime.now() - last_balance_time).total_seconds():.0f} сек")
        return
    
    balance_running = True
    
    try:
        now = datetime.now()
        
        print(f"\n=== {now.strftime('%H:%M:%S')} === Balance Strategy")
        
        # Отменяем все существующие заявки для NRH6
        orders = await get_orders()
        nrh6_orders = [o for o in orders if o.get('figi') == FIGI_NRH6]
        print(f"Активных заявок до отмены: {len(nrh6_orders)}")
        
        cancelled = 0
        for order in nrh6_orders:
            order_id = order.get('orderId')
            print(f"Отменяю заявку {order_id}")
            result = await cancel_order(order_id)
            cancelled += 1
        
        # Ждём чтобы отмены успели обработаться
        if cancelled > 0:
            print(f"Отменено {cancelled} заявок, жду 3 секунды...")
            await asyncio.sleep(3)
            
            # Проверяем сколько осталось
            orders_after = await get_orders()
            nrh6_after = [o for o in orders_after if o.get('figi') == FIGI_NRH6]
            print(f"Активных заявок после отмены: {len(nrh6_after)}")
        
        print("Получаю цену...")
        
        # Получаем цену NRH6
        prices = await get_prices([FIGI_NRH6])
        nrh6_price = None
        for p in prices:
            if p.get('figi') == FIGI_NRH6:
                nrh6_price = float(format_price(p.get('price', {})))
        
        if not nrh6_price:
            print("Не удалось получить цену NRH6")
            return
        
        # Получаем позицию NRH6
        positions = await get_positions()
        nrh6_qty = 0
        for pos in positions:
            if pos.get('figi') == FIGI_NRH6:
                balance = int(pos.get('balance', 0))
                blocked = int(pos.get('blocked', 0))
                nrh6_qty = balance + blocked
        
        print(f"NRH6: цена={nrh6_price}, позиция={nrh6_qty}")
        
        # Диапазон: от -1 до -1201
        min_pos = -1
        max_pos = -1201
        step = 0.003
        first_lot = 1  # первая заявка - 1 лотов
        
        # Вычисляем сколько можем купить (не выйти за -1)
        can_buy = max(0, min_pos - nrh6_qty)
        # Вычисляем сколько можем продать (не выйти за -1201)
        can_sell = max(0, nrh6_qty - max_pos)
        
        print(f"Можем купить: {can_buy}, можем продать: {can_sell}")
        
        # Выставляем заявки на покупку (10, 11, 12, ...)
        if can_buy > 0:
            remaining = can_buy
            level = 0
            while remaining > 0:
                qty = first_lot + level  # 10, 11, 12, ...
                if qty > remaining:
                    qty = remaining
                price = nrh6_price - step * (level + 1)
                price = round(price, 3)
                print(f"Выставляю покупку: {qty} @ {price}")
                try:
                    result = await post_order(FIGI_NRH6, qty, 'ORDER_DIRECTION_BUY', price)
                    if 'orderId' in result:
                        print(f"Результат: {result.get('orderId')}")
                    else:
                        print(f"Ошибка (пропускаю): {result.get('message', result)[:50]}")
                except Exception as e:
                    print(f"Исключение (пропускаю): {str(e)[:50]}")
                remaining -= qty
                level += 1
                if level >= 40:  # максимум 40 уровней
                    break
        
        # Выставляем заявки на продажу (10, 11, 12, ...)
        if can_sell > 0:
            remaining = can_sell
            level = 0
            while remaining > 0:
                qty = first_lot + level  # 10, 11, 12, ...
                if qty > remaining:
                    qty = remaining
                price = nrh6_price + step * (level + 1)
                price = round(price, 3)
                print(f"Выставляю продажу: {qty} @ {price}")
                try:
                    result = await post_order(FIGI_NRH6, qty, 'ORDER_DIRECTION_SELL', price)
                    if 'orderId' in result:
                        print(f"Результат: {result.get('orderId')}")
                    else:
                        print(f"Ошибка (пропускаю): {result.get('message', result)[:50]}")
                except Exception as e:
                    print(f"Исключение (пропускаю): {str(e)[:50]}")
                remaining -= qty
                level += 1
                if level >= 40:  # максимум 40 уровней
                    break
        
        print("Балансная стратегия завершена")
        
    except Exception as e:
        print(f"Ошибка в балансной стратегии: {e}")
    
    finally:
        last_balance_time = datetime.now()
        balance_running = False


async def main():
    global ACCOUNT_ID
    
    print("Tinkoff Trading Bot - Polling Version")
    
    # Get account
    ACCOUNT_ID = await get_account_id()
    print(f"Account ID: {ACCOUNT_ID}")
    
    # Print initial status
    await print_status()
    
    # Запускаем балансную стратегию сразу при старте
    await balance_strategy()
    
    # Poll every 10 seconds
    while True:
        try:
            await asyncio.sleep(10)
            
            # Балансная стратегия каждые 5 минут
            await balance_strategy()
            
            await print_status()
        except KeyboardInterrupt:
            print("\nStopping...")
            break
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(10)

if __name__ == '__main__':
    asyncio.run(main())
