#!/usr/bin/env python3
"""
Finam Trading Bot - WebSocket version
"""
import os
import json
import asyncio
import websockets
from datetime import datetime

TOKEN = os.environ.get('FINAM_TOKEN', 'YOUR_TOKEN_HERE')
WS_URL = 'wss://api.finam.ru:443/ws'

OFFSET = 0.024

TRADED_ORDERS = {}


async def send_order(symbol, quantity, direction, price):
    """Send order to Finam"""
    print(f"Отправляю заявку: {symbol} {direction} {quantity} @ {price}")
    

async def handle_trade(symbol, price, quantity, direction):
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
    await send_order(symbol, quantity, counter_direction, counter_price)


async def subscribe_orders(ws, token):
    """Subscribe to orders/trades"""
    subscribe_msg = {
        "action": "SUBSCRIBE",
        "type": "TRADES",
        "data": {
            "symbol": "NRH6@RTSX"
        },
        "token": token
    }
    await ws.send(json.dumps(subscribe_msg))
    print("Подписка на TRADES оформлена")


async def websocket_listener():
    """Main WebSocket loop"""
    global TOKEN
    
    if TOKEN == 'YOUR_TOKEN_HERE':
        print("Установи FINAM_TOKEN в переменной окружения")
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
                                        trade.get('direction', 'BUY')
                                    )
                            
                            if 'orders' in payload:
                                for order in payload['orders']:
                                    await handle_trade(
                                        order.get('symbol'),
                                        float(order.get('price', 0)),
                                        int(order.get('quantity', 0)),
                                        order.get('direction', 'BUY')
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
