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
FIGI_NGH6 = 'FUTNG0326000'
FIGI_NGJ6 = 'FUTNG0426000'

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

async def post_order(figi, quantity, direction, order_type='ORDER_TYPE_MARKET'):
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
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.post(url, json=order_data, headers=headers) as resp:
            return await resp.json()

def format_price(price_dict):
    """Format price from units/nano"""
    units = price_dict.get('units', '0')
    nano = price_dict.get('nano', 0)
    return f"{units}.{str(nano)[:3].ljust(3, '0')}"

async def print_status():
    """Print current status"""
    print(f"\n=== {datetime.now().strftime('%H:%M:%S')} ===")
    
    # Get prices
    prices = await get_prices([FIGI_NGH6, FIGI_NGJ6])
    ngh6_price = 'N/A'
    ngj6_price = 'N/A'
    
    for p in prices:
        if p.get('figi') == FIGI_NGH6:
            ngh6_price = format_price(p.get('price', {}))
        elif p.get('figi') == FIGI_NGJ6:
            ngj6_price = format_price(p.get('price', {}))
    
    try:
        diff = float(ngh6_price) - float(ngj6_price)
        diff_str = f"+{diff:.3f}" if diff >= 0 else f"{diff:.3f}"
    except:
        diff_str = 'N/A'
    
    print(f"NGH6: {ngh6_price} | NGJ6: {ngj6_price} | Diff: {diff_str}")
    
    # Get positions
    positions = await get_positions()
    ngh6_qty = 0
    ngj6_qty = 0
    
    for pos in positions:
        figi = pos.get('figi', '')
        balance = int(pos.get('balance', 0))
        blocked = int(pos.get('blocked', 0))
        total = balance + blocked
        
        if figi == FIGI_NGH6:
            ngh6_qty = total
        elif figi == FIGI_NGJ6:
            ngj6_qty = total
    
    print(f"Positions - NGH6: {ngh6_qty} | NGJ6: {ngj6_qty}")
    
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
            await print_status()
        except KeyboardInterrupt:
            print("\nStopping...")
            break
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(10)

if __name__ == '__main__':
    asyncio.run(main())
