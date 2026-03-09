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
    
    # Debug: show all operations with trades
    for op in operations:
        figi = op.get('figi')
        trades = op.get('trades', [])
        if not figi and trades:
            figi = trades[0].get('figi')
        if figi and 'NGM' in figi:
            op_type = op.get('type', '')
            print(f"DEBUG: id={op.get('id')}, type={op_type}, figi={figi}, in_set={op.get('id') in last_operation_ids}")
    
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
    print(f"Order result: {result}")
    return result

def format_price(price_dict):
    """Format price from units/nano"""
    units = price_dict.get('units', '0')
    nano = price_dict.get('nano', 0)
    return f"{units}.{str(nano)[:3].ljust(3, '0')}"

async def print_status():
    """Print current status"""
    print(f"\n=== {datetime.now().strftime('%H:%M:%S')} ===")
    
    # Get prices
    prices = await get_prices([FIGI_NRH6, FIGI_NGH6, FIGI_NGJ6, FIGI_VTBR, FIGI_IMOEXF])
    nrh6_price = 'N/A'
    ngh6_price = 'N/A'
    ngj6_price = 'N/A'
    
    for p in prices:
        if p.get('figi') == FIGI_NRH6:
            nrh6_price = format_price(p.get('price', {}))
        elif p.get('figi') == FIGI_NGH6:
            ngh6_price = format_price(p.get('price', {}))
        elif p.get('figi') == FIGI_NGJ6:
            ngj6_price = format_price(p.get('price', {}))
    
    try:
        diff = float(ngh6_price) - float(ngj6_price)
        diff_str = f"+{diff:.3f}" if diff >= 0 else f"{diff:.3f}"
    except:
        diff_str = 'N/A'
    
    print(f"NRH6: {nrh6_price} | NGH6: {ngh6_price} | NGJ6: {ngj6_price} | Diff: {diff_str}")
    
    # Get positions
    positions = await get_positions()
    nrh6_qty = 0
    ngh6_qty = 0
    ngj6_qty = 0
    
    for pos in positions:
        figi = pos.get('figi', '')
        balance = int(pos.get('balance', 0))
        blocked = int(pos.get('blocked', 0))
        total = balance + blocked
        
        if figi == FIGI_NRH6:
            nrh6_qty = total
        elif figi == FIGI_NGH6:
            ngh6_qty = total
        elif figi == FIGI_NGJ6:
            ngj6_qty = total
    
    print(f"Positions - NRH6: {nrh6_qty} | NGH6: {ngh6_qty} | NGJ6: {ngj6_qty}")
    
    # Get orders
    orders = await get_orders()
    print(f"Active orders: {len(orders)}")
    for order in orders:
        figi = order.get('figi', '')
        direction = order.get('direction', '')
        qty = order.get('quantity', '')
        print(f"  - {figi} {direction} {qty}")

async def main():
    global ACCOUNT_ID
    
    print("Tinkoff Trading Bot - Polling Version")
    
    # Get account
    ACCOUNT_ID = await get_account_id()
    print(f"Account ID: {ACCOUNT_ID}")
    
    # Print initial status
    await print_status()
    
    # Poll every 10 seconds
    while True:
        try:
            await asyncio.sleep(10)
            
            # Check for new trades and place counter-orders
            new_trades = await check_new_trades()
            for trade in new_trades:
                await place_counter_order(trade)
            
            await print_status()
        except KeyboardInterrupt:
            print("\nStopping...")
            break
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(10)

if __name__ == '__main__':
    asyncio.run(main())
