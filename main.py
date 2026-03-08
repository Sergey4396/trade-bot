#!/usr/bin/env python3
"""
Tinkoff Trading Bot with WebSocket
"""
import os
import json
import asyncio
import ssl
import aiohttp
from websockets import connect

TOKEN = os.environ.get('TINKOFF_TOKEN', 'YOUR_TOKEN_HERE')
ACCOUNT_ID = None

BASE_URL = 'https://invest-public-api.tinkoff.ru'
WS_URL = 'wss://invest-public-api.tinkoff.ru/ws'

# SSL context that doesn't verify certificates
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

async def get_account_id():
    """Get account ID"""
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
    """Get current prices for FIGI list"""
    url = f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.MarketDataService/GetLastPrices'
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.post(url, json={'figi': figi_list}, headers=headers) as resp:
            data = await resp.json()
            return data.get('lastPrices', [])

async def get_positions():
    """Get current positions"""
    if not ACCOUNT_ID:
        await get_account_id()
    
    url = f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.OperationsService/GetPositions'
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.post(url, json={'accountId': ACCOUNT_ID}, headers=headers) as resp:
            data = await resp.json()
            return data.get('futures', [])

async def post_order(figi, quantity, direction, order_type='ORDER_TYPE_MARKET'):
    """Place an order"""
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

async def websocket_handler():
    """WebSocket handler for real-time orders"""
    global ACCOUNT_ID
    
    if not ACCOUNT_ID:
        await get_account_id()
    
    print("Connecting to WebSocket...")
    
    # Create SSL context that doesn't verify
    import websockets
    ws = await websockets.connect(WS_URL, ssl=ssl_context)
    
    print("Connected!")
    
    # Send authorization as first message
    auth_msg = json.dumps({
        'headers': {
            'Authorization': f'Bearer {TOKEN}'
        }
    })
    await ws.send(auth_msg)
    
    # Subscribe to account orders
    subscribe_msg = json.dumps({
        'accounts': [ACCOUNT_ID]
    })
    await ws.send(subscribe_msg)
    
    print(f"Subscribed to account: {ACCOUNT_ID}")
    
    # Listen for messages
    async for message in ws:
        data = json.loads(message)
        print(f"Received: {data}")
        
        # Handle different message types
        if 'orderTrades' in data:
            order_trade = data['orderTrades']
            print(f"Order executed! OrderID: {order_trade.get('orderId')}")

async def main():
    print("Tinkoff Trading Bot")
    print(f"Token: {'*' * 20}...")
    
    # Get account
    account_id = await get_account_id()
    print(f"Account ID: {account_id}")
    
    # Get prices
    figi_list = ['FUTNG0326000', 'FUTNG0426000']  # NGH6, NGJ6
    prices = await get_prices(figi_list)
    print(f"Prices: {prices}")
    
    # Get positions
    positions = await get_positions()
    print(f"Positions: {positions}")
    
    # Start WebSocket
    try:
        await websocket_handler()
    except Exception as e:
        print(f"WebSocket error: {e}")

if __name__ == '__main__':
    asyncio.run(main())
