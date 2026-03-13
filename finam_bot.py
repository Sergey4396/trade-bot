#!/usr/bin/env python3
"""
Finam Trading Bot - WebSocket version
"""
import os
import json
import asyncio
import websockets
import aiohttp
from datetime import datetime

TOKEN = os.environ.get('FINAM_TOKEN', 'YOUR_TOKEN_HERE')
# Token is already JWT (starts with eyJ...), no need to exchange

WS_URL = 'wss://api.finam.ru:443/ws'
REST_URL = 'https://api.finam.ru'

OFFSET = 0.024

TRADED_ORDERS = {}
ACCOUNT_ID = None

SYMBOL = os.environ.get('FINAM_SYMBOL', 'NRH6@MOEX')


async def get_account_id(jwt_token):
    """Get account ID"""
    global ACCOUNT_ID
    if ACCOUNT_ID:
        return ACCOUNT_ID
    
    url = f'{REST_URL}/v1/portfolios'
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'User-Agent': 'FinamBot/1.0'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"Portfolios response: {data}")
                accounts = data.get('accounts', [])
                if accounts:
                    ACCOUNT_ID = accounts[0].get('account_id')
                    print(f"Account ID: {ACCOUNT_ID}")
                    return ACCOUNT_ID
            else:
                print(f"Ошибка получения аккаунта: {resp.status}")
                text = await resp.text()
                print(f"Response: {text}")
    return None


async def send_order(symbol, quantity, direction, price, jwt_token):
    """Send order to Finam via REST API"""
    account_id = await get_account_id(jwt_token)
    if not account_id:
        print("Не могу получить account_id")
        return None
    
    url = f'{REST_URL}/v1/accounts/{account_id}/orders'
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'Content-Type': 'application/json',
        'User-Agent': 'FinamBot/1.0'
    }
    
    order_data = {
        'symbol': symbol,
        'quantity': str(quantity),
        'side': 'BUY' if direction == 'BUY' else 'SELL',
        'type': 'LIMIT',
        'limit_price': str(price),
        'time_in_force': 'DAY'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=order_data, headers=headers) as resp:
            result = await resp.json()
            if resp.status == 200:
                order_id = result.get('order_id')
                print(f"Заявка размещена: {order_id}")
                return order_id
            else:
                print(f"Ошибка размещения заявки: {result}")
                return None
    

async def handle_trade(symbol, price, quantity, direction, jwt_token):
    """Handle incoming trade - place counter order"""
    if not symbol or not price or not quantity:
        return
    
    order_key = f"{symbol}_{price}_{quantity}"
    if order_key in TRADED_ORDERS:
        return
    
    TRADED_ORDERS[order_key] = datetime.now()
    
    for old_key in list(TRADED_ORDERS.keys()):
        if (datetime.now() - TRADED_ORDERS[old_key]).total_seconds() > 60:
            del TRADED_ORDERS[old_key]
    
    print(f"\n=== Сделка: {symbol} {direction} {quantity} @ {price} ===")
    
    counter_price = round(price - OFFSET, 3)
    counter_direction = "SELL" if direction == "BUY" else "BUY"
    
    print(f"Выставляю встречную заявку: {symbol} {counter_direction} {quantity} @ {counter_price}")
    await send_order(symbol, quantity, counter_direction, counter_price, jwt_token)


async def get_jwt_token(api_token):
    """Get JWT token from API token"""
    url = f'{REST_URL}/v1/auth'
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'FinamBot/1.0'
    }
    data = {'token': api_token}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                jwt = result.get('token')
                print(f"JWT получен")
                return jwt
            else:
                print(f"Ошибка получения JWT: {resp.status}")
                return None


async def subscribe_orders(ws, token):
    """Subscribe to orders/trades"""
    subscribe_msg = {
        "action": "SUBSCRIBE",
        "type": "TRADES",
        "data": {
            "symbol": SYMBOL
        },
        "token": token
    }
    await ws.send(json.dumps(subscribe_msg))
    print(f"Подписка на TRADES оформлена: {SYMBOL}")


async def websocket_listener():
    """Main WebSocket loop"""
    global TOKEN, ACCOUNT_ID
    
    if TOKEN == 'YOUR_TOKEN_HERE':
        print("Установи FINAM_TOKEN в переменной окружения")
        return
    
    print("Получаю счета...")
    account_id = await get_account_id(TOKEN)
    if not account_id:
        print("Не удалось получить account_id")
        return
    
    print(f"Подключаюсь к Finam WebSocket...")
    
    while True:
        try:
            async with websockets.connect(WS_URL) as ws:
                print("Подключено к Finam")
                
                await subscribe_orders(ws, TOKEN)
                
                async for message in ws:
                    try:
                        data = json.loads(message)
                        msg_type = data.get('type', '')
                        
                        if msg_type == 'DATA':
                            payload = data.get('payload', {})
                            
                            if 'trade' in payload:
                                for trade in payload['trade']:
                                    await handle_trade(
                                        trade.get('symbol'),
                                        float(trade.get('last', 0)),
                                        int(trade.get('last_size', 0)),
                                        trade.get('direction', 'BUY'),
                                        TOKEN
                                    )
                            
                            if 'orders' in payload:
                                for order in payload['orders']:
                                    await handle_trade(
                                        order.get('symbol'),
                                        float(order.get('price', 0)),
                                        int(order.get('quantity', 0)),
                                        order.get('side', 'BUY'),
                                        TOKEN
                                    )
                        
                        elif msg_type == 'ERROR':
                            error = data.get('error_info', {})
                            print(f"Ошибка: {error.get('message', error)}")
                            
                        elif msg_type == 'EVENT':
                            event = data.get('event_info', {})
                            event_type = event.get('event', '')
                            print(f"Событие: {event_type}")
                            
                            if event_type == 'CONNECTION_CLOSED':
                                print("Переподключаюсь...")
                                break
                                
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        print(f"Ошибка обработки: {e}")
                        
        except websockets.exceptions.ConnectionClosed as e:
            print(f"Соединение закрыто: {e}, переподключаюсь через 5 сек...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Ошибка: {e}, переподключаюсь через 5 сек...")
            await asyncio.sleep(5)


async def main():
    print("Finam Trading Bot - WebSocket Version")
    print(f"Токен: {'Установлен' if TOKEN != 'YOUR_TOKEN_HERE' else 'НЕ УСТАНОВЛЕН'}")
    await websocket_listener()


if __name__ == '__main__':
    asyncio.run(main())
