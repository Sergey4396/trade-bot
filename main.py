#!/usr/bin/env python3
"""
Tinkoff Trading Bot - Simple polling version
"""
import os
import json
import asyncio
import ssl
import aiohttp
import aiohttp.web
from datetime import datetime

TOKEN = os.environ.get('TINKOFF_TOKEN', 'YOUR_TOKEN_HERE')
ACCOUNT_ID = None
HTTP_PORT = int(os.environ.get('HTTP_PORT', '8080'))
HTTP_PASSWORD = os.environ.get('HTTP_PASSWORD', 'secret123')

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

async def get_futures_prices(figi_list):
    """Alternative method for futures prices"""
    url = f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.MarketDataService/GetLastPricesAsync'
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.post(url, json={'figi': figi_list}, headers=headers) as resp:
            data = await resp.json()
            return data.get('lastPrices', [])

async def get_futures_price_by_figi(figi):
    """Get futures price using GetTradingStatus and GetOrderBook"""
    url = f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.MarketDataService/GetOrderBook'
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.post(url, json={'figi': figi, 'depth': 1}, headers=headers) as resp:
            data = await resp.json()
            print(f"DEBUG: GetOrderBook response: {data}")
            bids = data.get('bids', [])
            asks = data.get('asks', [])
            if bids and asks:
                bid_price = float(format_price(bids[0].get('price', {})))
                ask_price = float(format_price(asks[0].get('price', {})))
                return (bid_price + ask_price) / 2
            return None

async def get_orderbook_with_depth(figi, depth=20):
    """Get order book with depth for comparison"""
    url = f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.MarketDataService/GetOrderBook'
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.post(url, json={'figi': figi, 'depth': depth}, headers=headers) as resp:
            return await resp.json()

async def get_last_trade_price(figi):
    """Get price of last executed trade for our account"""
    from datetime import datetime, timedelta
    
    global ACCOUNT_ID
    if not ACCOUNT_ID:
        await get_account_id()
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=4)
    
    url = f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.OperationsService/GetOperations'
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.post(url, json={
            'accountId': ACCOUNT_ID,
            'figi': figi,
            'from': start_time.isoformat() + 'Z',
            'to': end_time.isoformat() + 'Z',
            'operationTypes': ['OPERATION_TYPE_TRADE']
        }, headers=headers) as resp:
            data = await resp.json()
            operations = data.get('operations', [])
            # Ищем последнюю операцию типа TRADE
            trades = [op for op in operations if op.get('operationType') == 'TRADE']
            if trades:
                # Берем последнюю
                last_op = trades[-1]
                price = last_op.get('price', {})
                units = int(price.get('units', 0))
                nano = int(price.get('nano', 0))
                return round(units + nano / 1e9, 3)
            return None
            data = await resp.json()
            print(f"DEBUG: GetOrderBook response: {data}")
            # Get best bid and ask
            bids = data.get('bids', [])
            asks = data.get('asks', [])
            if bids and asks:
                # Use mid price
                bid_price = float(format_price(bids[0].get('price', {})))
                ask_price = float(format_price(asks[0].get('price', {})))
                return (bid_price + ask_price) / 2
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

async def get_future_info(figi_or_ticker):
    """Get futures contract info - currency, basic_asset, etc"""
    url = f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.InstrumentsService/FutureBy'
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    
    # Пробуем разные способы
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        # Сначала пробуем по FIGI
        async with session.post(url, json={
            'idType': 'INSTRUMENT_ID_TYPE_FIGI',
            'id': figi_or_ticker
        }, headers=headers) as resp:
            data = await resp.json()
            if 'ticker' in data:
                print(f"DEBUG FutureBy {figi_or_ticker}: {data}")
                return data
            # Пробуем по UID
            async with session.post(url, json={
                'idType': 'INSTRUMENT_ID_TYPE_UID',
                'id': figi_or_ticker
            }, headers=headers) as resp2:
                data2 = await resp2.json()
                print(f"DEBUG FutureBy {figi_or_ticker}: {data2}")
                return data2

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

async def get_order_state(order_id):
    """Get order state - may return price in points for futures"""
    global ACCOUNT_ID
    if not ACCOUNT_ID:
        await get_account_id()
    
    url = f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.OrdersService/GetOrderState'
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.post(url, json={'accountId': ACCOUNT_ID, 'orderId': order_id}, headers=headers) as resp:
            data = await resp.json()
            print(f"DEBUG GetOrderState: {data}")
            return data

async def post_order(figi, quantity, direction, price=None, order_type='ORDER_TYPE_LIMIT'):
    global ACCOUNT_ID, order_prices_sent
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
    price_sent = None
    if price is not None:
        if figi.startswith('FUT'):
            price_str = f"{price:.3f}"
        else:
            price_str = f"{price:.2f}"
        parts = price_str.split('.')
        units = int(parts[0])
        nano = int(parts[1].ljust(9, '0')[:9])
        order_data['price'] = {'units': units, 'nano': nano}
        price_sent = price
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.post(url, json=order_data, headers=headers) as resp:
            result = await resp.json()
            
            # Сохраняем цену которую отправили
            if price_sent and 'orderId' in result:
                order_prices_sent[result['orderId']] = price_sent
            
            return result

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
    global last_trade_direction
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
    
    # Update last trade direction based on counter direction
    if counter_direction == 'ORDER_DIRECTION_BUY':
        last_trade_direction = 'BUY'
    else:
        last_trade_direction = 'SELL'
    print(f"Обновляю последнюю сделку: {last_trade_direction}")
    
    return result

def format_price(price_dict):
    """Format price from units/nano"""
    if isinstance(price_dict, str):
        return price_dict
    units = price_dict.get('units', 0)
    nano = price_dict.get('nano', 0)
    # nano is in nanounits (10^-9), divide by 10^6 to get 3 decimal places
    # e.g., 3.091 has nano=91000000, 3.910 has nano=910000000
    first_three = nano // 1000000
    return f"{units}.{str(first_three).zfill(3)}"

def parse_price(price_dict):
    """Parse price to float from units/nano"""
    if isinstance(price_dict, (int, float)):
        return float(price_dict)
    units = price_dict.get('units', 0)
    nano = price_dict.get('nano', 0)
    return units + nano / 1e9

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
last_trade_direction = None  # 'BUY' or 'SELL'
last_executed_price = None  # Цена последней исполненной заявки
initial_position = None  # Начальная позиция при первом запуске

# Храним цены которые мы отправили (в USD)
order_prices_sent = {}  # order_id -> price (в долларах)
future_info_fetched = False  # Флаг что инфо о фьючерсе уже получена

async def monitor_orders():
    """Мониторинг заявок - просто выводим информацию о стакане"""
    print("Запускаю мониторинг заявок (режим просмотра)")
    
    while True:
        try:
            await asyncio.sleep(10)
            
            # Получаем стакан для NRH6
            ob = await get_orderbook_with_depth(FIGI_NRH6, 20)
            bids = ob.get('bids', [])
            asks = ob.get('asks', [])
            
            # Получаем заявки
            orders = await get_orders()
            nrh6_orders = [o for o in orders if o.get('figi') == FIGI_NRH6]
            
            # Вычисляем курс если есть заявки и есть bid
            usd_to_rub = None
            if nrh6_orders and bids:
                # Берём цену нашей заявки в RUB
                first_order = nrh6_orders[0]
                price_val = first_order.get('initialOrderPrice', {})
                if price_val:
                    rub_units = int(price_val.get('units', 0))
                    rub_nano = int(price_val.get('nano', 0))
                    rub_price = rub_units + rub_nano / 1e9
                    
                    # Берём лучший bid в USD
                    usd_price = float(format_price(bids[0].get('price', {})))
                    
                    if usd_price > 0:
                        usd_to_rub = rub_price / usd_price
            
            # Функция конвертации USD -> RUB
            def usd_to_rub_val(usd_price):
                if usd_to_rub:
                    return usd_price * usd_to_rub
                return None
            
            print(f"\n=== {datetime.now().strftime('%H:%M:%S')} Стакан NRH6 ===")
            if usd_to_rub:
                print(f"Курс USD/RUB: {usd_to_rub:.2f}")
            print("      BID (USD)  | BID (RUB)   |   ASK (USD)  | ASK (RUB)")
            for i in range(min(15, max(len(bids), len(asks)))):
                bid_usd = ""
                bid_rub = ""
                ask_usd = ""
                ask_rub = ""
                
                if i < len(bids):
                    b = bids[i]
                    b_price_usd = float(format_price(b.get('price', {})))
                    b_qty = int(b.get('quantity', 0))
                    b_price_rub = usd_to_rub_val(b_price_usd)
                    bid_usd = f"{b_price_usd:.3f} ({b_qty:>3})"
                    bid_rub = f"{b_price_rub:.2f}" if b_price_rub else "-"
                
                if i < len(asks):
                    a = asks[i]
                    a_price_usd = float(format_price(a.get('price', {})))
                    a_qty = int(a.get('quantity', 0))
                    a_price_rub = usd_to_rub_val(a_price_usd)
                    ask_usd = f"{a_price_usd:.3f} ({a_qty:>3})"
                    ask_rub = f"{a_price_rub:.2f}" if a_price_rub else "-"
                
                print(f"  {bid_usd:<14} {bid_rub:<9} | {ask_usd:<14} {ask_rub}")
            
            print(f"\n=== Наши заявки ({len(nrh6_orders)}) ===")
            
            # Создаём список цен из стакана для поиска
            bid_prices = []
            for b in bids:
                b_price_usd = float(format_price(b.get('price', {})))
                b_price_rub = usd_to_rub_val(b_price_usd) if usd_to_rub else None
                if b_price_rub:
                    bid_prices.append((b_price_usd, b_price_rub, 'BID'))
            
            ask_prices = []
            for a in asks:
                a_price_usd = float(format_price(a.get('price', {})))
                a_price_rub = usd_to_rub_val(a_price_usd) if usd_to_rub else None
                if a_price_rub:
                    ask_prices.append((a_price_usd, a_price_rub, 'ASK'))
            
            all_prices = sorted(bid_prices + ask_prices, key=lambda x: x[1])
            
            for o in nrh6_orders:
                direction = o.get('direction', 'UNKNOWN')
                qty = int(o.get('quantity', 0))
                price_val = o.get('initialOrderPrice', {})
                order_id = o.get('orderId', '')[:10]
                
                if price_val:
                    units = int(price_val.get('units', 0))
                    nano = int(price_val.get('nano', 0))
                    rub_price = units + nano / 1e9
                    
                    # Ищем ближайшую цену в стакане
                    closest_usd = None
                    closest_type = ""
                    min_diff = float('inf')
                    for usd, rub, typ in all_prices:
                        diff = abs(rub_price - rub)
                        if diff < min_diff:
                            min_diff = diff
                            closest_usd = usd
                            closest_type = typ
                    
                    direction_ru = 'BUY ' if direction == 'ORDER_DIRECTION_BUY' else 'SELL'
                    if closest_usd and min_diff < 0.5:
                        print(f"  [{direction_ru}] {qty} лот @ {rub_price:.2f} RUB  => {closest_usd:.3f} USD ({closest_type})")
                    else:
                        print(f"  [{direction_ru}] {qty} лот @ {rub_price:.2f} RUB  (не найдено в стакане)")
            
            if not nrh6_orders:
                print("  (нет активных заявок)")
            
            # Позиция
            positions = await get_positions()
            for pos in positions:
                if pos.get('figi') == FIGI_NRH6:
                    balance = int(pos.get('balance', 0))
                    print(f"Позиция: {balance}")
                    break
                    
        except KeyboardInterrupt:
            print("\nМониторинг остановлен")
            break
        except Exception as e:
            print(f"Ошибка мониторинга: {e}")
            await asyncio.sleep(10)

async def balance_strategy():
    """Стратегия удержания позиции NRH6 - выставляем заявки в каждом диапазоне"""
    global last_balance_time, balance_running, last_trade_direction, last_executed_price, initial_position
    from datetime import datetime
    
    if balance_running:
        print("Балансная стратегия уже выполняется, пропускаю")
        return
    
    if last_balance_time and (datetime.now() - last_balance_time).total_seconds() < 60:
        print(f"Балансная стратегия пропущена, прошло только {(datetime.now() - last_balance_time).total_seconds():.0f} сек")
        return
    
    balance_running = True
    orders_placed = False
    
    try:
        now = datetime.now()
        
        print(f"\n=== {now.strftime('%H:%M:%S')} === Balance Strategy")
        
        # Получаем текущую цену
        nrh6_price = await get_futures_price_by_figi(FIGI_NRH6)
        
        if not nrh6_price:
            print("Не удалось получить цену NRH6 через GetOrderBook")
            balance_running = False
            return
        
        # Получаем позицию
        positions = await get_positions()
        nrh6_qty = 0
        for pos in positions:
            if pos.get('figi') == FIGI_NRH6:
                balance = int(pos.get('balance', 0))
                blocked = int(pos.get('blocked', 0))
                nrh6_qty = balance + blocked
        
        print(f"NRH6: цена={nrh6_price}, позиция={nrh6_qty}")
        
        # Запоминаем начальную позицию при первом запуске
        if initial_position is None:
            initial_position = nrh6_qty
            print(f"Запоминаю начальную позицию: {initial_position}")
        
        # Текущий диапазон = позиция
        current_range = nrh6_qty
        
        # Получаем существующие заявки
        orders = await get_orders()
        nrh6_orders = [o for o in orders if o.get('figi') == FIGI_NRH6]
        
        # Просто проверяем общее количество заявок - не выставляем если их уже много
        total_orders = len(nrh6_orders)
        max_orders = 30  # Не более 30 заявок
        orders_to_place = 20  # 10 покупок + 10 продаж
        
        if total_orders + orders_to_place > max_orders:
            print(f"Слишком много заявок: {total_orders} + {orders_to_place} > {max_orders}, пропускаем")
            balance_running = False
            return
        
        print(f"Всего заявок: {total_orders}")
        
        # Получаем цену последней сделки для пропуска
        last_trade_price = await get_last_trade_price(FIGI_NRH6)
        if last_trade_price:
            last_executed_price = last_trade_price
            print(f"Последняя сделка по цене: {last_executed_price}")
        
        step = 0.010
        
        # Определяем базовую цену (центр текущего диапазона)
        base_price = round(nrh6_price - (nrh6_price % step), 3)
        
        print(f"Базовая цена: {base_price}, позиция: {current_range}, начальная: {initial_position}")
        
        # Диапазон вокруг начальной позиции
        range_around = 10  # +/- 10 уровней
        
        # Выставляем заявки от initial_position вниз (покупки)
        for i in range(initial_position - 1, max(0, initial_position - range_around - 1), -1):
            # Цена для этого диапазона
            price = base_price - step * (initial_position - 1 - i)
            price = round(price, 3)
            
            # Пропускаем цену последней сделки
            if last_executed_price and abs(price - last_executed_price) < 0.001:
                print(f"ПРОПУСК покупки {price}: последняя сделка была по {last_executed_price}")
                continue
            
            print(f"Выставляю покупку: 1 @ {price}")
            try:
                result = await post_order(FIGI_NRH6, 1, 'ORDER_DIRECTION_BUY', price)
                if 'orderId' in result:
                    print(f"Результат: {result.get('orderId')}")
                    orders_placed = True
                else:
                    print(f"Ошибка: {result.get('message', result)[:50]}")
            except Exception as e:
                print(f"Исключение: {str(e)[:50]}")
        
        # Выставляем заявки от initial_position вверх (продажи)
        for i in range(initial_position + 1, initial_position + range_around + 1):
            # Цена для этого диапазона
            price = base_price + step * (i - initial_position)
            price = round(price, 3)
            
            # Пропускаем цену последней сделки
            if last_executed_price and abs(price - last_executed_price) < 0.001:
                print(f"ПРОПУСК продажи {price}: последняя сделка была по {last_executed_price}")
                continue
            
            print(f"Выставляю продажу: 1 @ {price}")
            try:
                result = await post_order(FIGI_NRH6, 1, 'ORDER_DIRECTION_SELL', price)
                if 'orderId' in result:
                    print(f"Результат: {result.get('orderId')}")
                    orders_placed = True
                else:
                    print(f"Ошибка: {result.get('message', result)[:50]}")
            except Exception as e:
                print(f"Исключение: {str(e)[:50]}")
        
        print("Балансная стратегия завершена")
        
    except Exception as e:
        import traceback
        print(f"Ошибка в балансной стратегии: {e}")
        print(traceback.format_exc())
    
    finally:
        if orders_placed:
            last_balance_time = datetime.now()
            print(f"Заявки выставлены, таймер обновлён")
        else:
            print(f"Заявки НЕ выставлены, таймер НЕ обновлён - повтор через 10 сек")
        balance_running = False


# HTTP Handlers
async def handle_cancel_all(request):
    """Cancel all orders"""
    password = request.query.get('password', '')
    if password != HTTP_PASSWORD:
        return aiohttp.web.Response(text='Unauthorized', status=401)
    
    try:
        orders = await get_orders()
        if not orders:
            return aiohttp.web.Response(text='No active orders', status=200)
        
        cancelled = 0
        for order in orders:
            order_id = order.get('orderId')
            if order_id:
                await cancel_order(order_id)
                cancelled += 1
                print(f"HTTP: Cancelled order {order_id}")
        
        return aiohttp.web.Response(text=f'Cancelled {cancelled} orders', status=200)
    except Exception as e:
        return aiohttp.web.Response(text=f'Error: {e}', status=500)

async def handle_status(request):
    """Get bot status"""
    password = request.query.get('password', '')
    if password != HTTP_PASSWORD:
        return aiohttp.web.Response(text='Unauthorized', status=401)
    
    try:
        orders = await get_orders()
        positions = await get_positions()
        
        nrh6_qty = 0
        for pos in positions:
            if pos.get('figi') == FIGI_NRH6:
                nrh6_qty = int(pos.get('balance', 0)) + int(pos.get('blocked', 0))
        
        return aiohttp.web.Response(
            text=f'Orders: {len(orders)}, NRH6 position: {nrh6_qty}',
            status=200
        )
    except Exception as e:
        return aiohttp.web.Response(text=f'Error: {e}', status=500)

async def handle_health(request):
    """Health check endpoint"""
    return aiohttp.web.Response(text='OK', status=200)

async def start_http_server():
    """Start HTTP server"""
    app = aiohttp.web.Application()
    app.router.add_get('/health', handle_health)
    app.router.add_get('/cancel-all', handle_cancel_all)
    app.router.add_get('/status', handle_status)
    
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, '0.0.0.0', HTTP_PORT)
    await site.start()
    print(f"HTTP server started on port {HTTP_PORT}")

async def main():
    global ACCOUNT_ID
    
    print("Tinkoff Trading Bot - Polling Version")
    
    # Start HTTP server in background
    http_task = asyncio.create_task(start_http_server())
    
    # Wait for HTTP server to start
    await asyncio.sleep(1)
    
    # Get account
    ACCOUNT_ID = await get_account_id()
    print(f"Account ID: {ACCOUNT_ID}")
    
    # Print initial status
    await print_status()
    
    # Запускаем мониторинг (только смотрим, не выставляем)
    # Это бесконечный цикл, дальше код не выполняется
    await monitor_orders()

if __name__ == '__main__':
    asyncio.run(main())
