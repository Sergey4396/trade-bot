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

TOKEN = 'eyJraWQiOiJlYzk3YjU2YS01YWZkLTQ5ZGYtYWExOS0zZDQ0YTAxN2M5OGUiLCJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhcmVhIjoidHQiLCJwYXJlbnQiOiJmN2MyNTZiNC04NGFhLTRmZjMtYmZiOC1lMGY3YTFlNjBmNzYiLCJhcGlUb2tlblByb3BlcnRpZXMiOiJINHNJQUFBQUFBQUFfeldUTVhiVU1CQ0dOMnN2MmJlUGFzcVVvZHYzZUk5TkFxbGxXZkthV0xZanlidGVHamVwb2VBb1BDN0FDYmdCSi1BbzNJQ0NYek9pLWY2Uk5EUFNlTWJiYjdfX192bjFRT3R0Y2ZPejNLNXZWX3ZyM2VhTnIzd3RocTQ4Ry1lekh2ZXZkcVZ5ODhEcTlaeTBVakd3bnB4TmF1YlJKVzNOM0xCYU00bE83T2Zhd0hIREVEWHI2QlZyMUZWV2xfVTU2ZGoyT211YnRjdktlY2JRc0wtUGt0ZFBvck55UVRTWXJMSmZEVTdVVDZLVG5PdktabzJpUm9zNk9UZlJzMXA1Nzl3bzhUcy0yYXhjNzl6VnZXaU82X0o5M1NEN1R0V3N2WkwzOVZMdjNEZDVuZF9kWF9MLVJkYWprdnZEMFdTVi0tSlRTQTFhcWw1ck5uVFZzdWVpMFJIZThKZVJEVFA1aWczbnFrOXM5S1BuYmk1QnQ3d1JuRlA3emE1WWdvU0VNWHVHOGVYQVJ2UW0zRjJ0Zmx5dGQ2dWI3LVcyb0VLWkdRZ200VGtCUzh3RjhKeVFEdkNWcWF5LWZINmhUZUpYS3ZDOUUtQ2dqeTNnVEFJaTljblFkZjJ4N2V1VTFrd3o4VkRSdGJWdWNmNUFwVzE3UmJ0RXQ5UlR2TkRHRHVnX0ZSWlhyUzJpR3VPcE9GcWtSRnVvYU0wRVRQRG85QVZJZDNYcFdXZ0dvQkhoY0ZtSjR2RVU1MDlVb0QyQVN3aHRna3RBZGVoTEFsdUJlSTZwR0lJaUhtR21ZOElEUFNPZVlHYkw3Smk0Ykh3S0ItWTk4d0h1ZUJJUE5CVmU0OFA0V05IR1RfZ0ZxUWhxQUV4SXdGRm9rQUY0Q19ONEJGb0VoWWhDd2htSU5hcU8zWW5LaUpwZ0RrZ1JMMGd4S1J5ZlUtMHpRc28wTmlURGt4YlJNbEhYb2xNWmFZWklKb2hrZnJEWDFJcGtoa2dHaEdRcWJsZl81LUwyOWVIZDNmc1A5X2UtZTN6VV93RGd0aVNvWkFRQUFBIiwic2NvbnRleHQiOiJDaEFJQnhJTWRISmhaR1ZmWVhCcFgzSjFDaWdJQXhJa01UQTJNR1V6TVdFdE5XRTROQzAwWkdNeExXSXdZMkV0WkRGbE5tSTRZelF5TjJVMkNnUUlCUklBQ2drSUFCSUZhSFJ0YkRVS0tBZ0NFaVF5TldVd01HVTJNUzB4WlRJMUxURXhaakV0WWpVNE9DMWpabVJrWlRRNE5EVXhaVGNLQlFnSUVnRXpDZ1FJQ1JJQUNna0lDaElGTWk0MUxqQUtLQWdFRWlSbFl6azNZalUyWVMwMVlXWmtMVFE1WkdZdFlXRXhPUzB6WkRRMFlUQXhOMk01T0dVeVVBb1ZWRkpCUkVWQlVFbGZTMUpCVkU5VFgxUlBTMFZPRUFFWUFTQUJLZ2RGUkU5WVgwUkNPZ0lJQTBvVENnTUlod2NTQlFpSG9aNEJHZ1VJaDViREFWQ3NBbGdCWUFGb0FYSUdWSGhCZFhSbyIsInppcHBlZCI6dHJ1ZSwiY3JlYXRlZCI6IjE3NzMzNTYxODkiLCJyZW5ld0V4cCI6IjE4MDM4NDg0NTkiLCJzZXNzIjoiSDRzSUFBQUFBQUFBLzFPcTVGSXhUTFJJU2pOUE5kZE5TalkxMGpVeFRFclR0VEJMVHROTk0wMU5OVGRQVFRKTHNqUVg0cm13OE1MV2l3MFhObC9ZZW1HbkZOK0ZCUmY3TDJ5OHNPUENYaEJXNGkzV0s5WXJjc2hOek16Ukt5cE5VbkZ5TlRGemRMVjAwVFYzTkhmVE5URnhNdEcxTUhCMTFiVjBNakkxc1RCeE16STBNdHZGeU12Rkd1OFhFT1F2eE9MdjVCOEJBQitaWlg2TEFBQUEiLCJpc3MiOiJ0eHNlcnZlciIsImtleUlkIjoiZWM5N2I1NmEtNWFmZC00OWRmLWFhMTktM2Q0NGEwMTdjOThlIiwidHlwZSI6IkFwaVRva2VuIiwic2VjcmV0cyI6ImpJZnZscndXT3EzbDRGQWpMTThOM3c9PSIsInNjb3BlIjoiIiwidHN0ZXAiOiJmYWxzZSIsInNwaW5SZXEiOmZhbHNlLCJleHAiOjE4MDM4NDgzOTksInNwaW5FeHAiOiIxODAzODQ4NDU5IiwianRpIjoiMTA2MGUzMWEtNWE4NC00ZGMxLWIwY2EtZDFlNmI4YzQyN2U2In0.JyckL_Wafzbpan54YO58lKR9hIk4fiahLz1Tg3crmI6iEzBdnB7iKBHcLoziYmkEPMM3t4bzmXe2RCJ2QMMPpIBH_3GoZjfnupwrzk23JlXzsM0KFXlMl-w0H1v1JyfK1vxHNqGRpU6wnp8vMNX3BHcNA80lV8BVIICk0jp0RRs'
ACCOUNT_ID = '1060e31a-5a84-4dc1-b0ca-d1e6b8c427e6'

WS_URL = 'wss://api.finam.ru:443/ws'
REST_URL = 'https://api.finam.ru'

OFFSET = 0.024

TRADED_ORDERS = {}

SYMBOL = 'NRH6'


async def get_account_id(jwt_token):
    """Get account ID"""
    global ACCOUNT_ID
    
    if ACCOUNT_ID:
        print(f"Using configured account ID: {ACCOUNT_ID}")
        return ACCOUNT_ID
    
    url = f'{REST_URL}/v1/sessions/details'
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'User-Agent': 'FinamBot/1.0',
        'Content-Type': 'application/json'
    }
    data = {'token': jwt_token}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=headers) as resp:
            if resp.status == 200:
                try:
                    data = await resp.json()
                    account_ids = data.get('account_ids', [])
                    if account_ids:
                        ACCOUNT_ID = account_ids[0]
                        print(f"Account ID from session: {ACCOUNT_ID}")
                        return ACCOUNT_ID
                except:
                    pass
            else:
                print(f"Ошибка получения аккаунта: {resp.status}")
    return None


async def send_order(quantity, direction, price):
    """Send order to Finam via REST API"""
    url = f'{REST_URL}/v1/accounts/{ACCOUNT_ID}/orders'
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json',
        'User-Agent': 'FinamBot/1.0'
    }
    
    order_data = {
        'symbol': SYMBOL,
        'quantity': str(quantity),
        'side': direction,
        'type': 'LIMIT',
        'limit_price': str(price),
        'time_in_force': 'DAY'
    }
    
    print(f"Отправляю заявку: {order_data}")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=order_data, headers=headers) as resp:
            result = await resp.json()
            if resp.status in (200, 201):
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
    
    if direction == "BUY":
        counter_price = round(price + 0.020, 3)
        counter_direction = "SELL"
    else:  # SELL
        counter_price = round(price - 0.020, 3)
        counter_direction = "BUY"
    
    print(f"Выставляю встречную заявку: {counter_direction} {quantity} @ {counter_price}")
    await send_order(quantity, counter_direction, counter_price)


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
            "symbol": "NRH6@MOEX"
        }
    }
    msg_str = json.dumps(subscribe_msg)
    print(f"Отправляю: {msg_str}")
    await ws.send(msg_str)
    print(f"Подписка на TRADES оформлена")


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
            async with websockets.connect(WS_URL, additional_headers={'Authorization': f'Bearer {TOKEN}'}) as ws:
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
