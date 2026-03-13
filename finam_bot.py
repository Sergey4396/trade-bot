#!/usr/bin/env python3
"""
Finam Trading Bot - Polling version
"""
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta

TOKEN = 'eyJraWQiOiJlYzk3YjU2YS01YWZkLTQ5ZGYtYWExOS0zZDQ0YTAxN2M5OGUiLCJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhcmVhIjoidHQiLCJwYXJlbnQiOiJmN2MyNTZiNC04NGFhLTRmZjMtYmZiOC1lMGY3YTFlNjBmNzYiLCJhcGlUb2tlblByb3BlcnRpZXMiOiJINHNJQUFBQUFBQUFfeldUTVhiVU1CQ0dOMnN2MmJlUGFzcVVvZHYzZUk5TkFxbGxXZkthV0xZanlidGVHamVwb2VBb1BDN0FDYmdCSi1BbzNJQ0NYek9pLWY2Uk5EUFNlTWJiYjdfX192bjFRT3R0Y2ZPejNLNXZWX3ZyM2VhTnIzd3RocTQ4Ry1lekh2ZXZkcVZ5ODhEcTlaeTBVakd3bnB4TmF1YlJKVzNOM0xCYU00bE83T2Zhd0hIREVEWHI2QlZyMUZWV2xfVTU2ZGoyT211YnRjdktlY2JRc0wtUGt0ZFBvck55UVRTWXJMSmZEVTdVVDZLVG5PdktabzJpUm9zNk9UZlJzMXA1Nzl3bzhUcy0yYXhjNzl6VnZXaU82X0o5M1NEN1R0V3N2WkwzOVZMdjNEZDVuZF9kWF9MLVJkYWprdnZEMFdTVi0tSlRTQTFhcWw1ck5uVFZzdWVpMFJIZThKZVJEVFA1aWczbnFrOXM5S1BuYmk1QnQ3d1JuRlA3emE1WWdvU0VNWHVHOGVYQVJ2UW0zRjJ0Zmx5dGQ2dWI3LVcyb0VLWkdRZ200VGtCUzh3RjhKeVFEdkNWcWF5LWZINmhUZUpYS3ZDOUUtQ2dqeTNnVEFJaTljblFkZjJ4N2V1VTFrd3o4VkRSdGJWdWNmNUFwVzE3UmJ0RXQ5UlR2TkRHRHVnX0ZSWlhyUzJpR3VPcE9GcWtSRnVvYU0wRVRQRG85QVZJZDNYcFdXZ0dvQkhoY0ZtSjR2RVU1MDlVb0QyQVN3aHRna3RBZGVoTEFsdUJlSTZwR0lJaUhtR21ZOElEUFNPZVlHYkw3Smk0Ykh3S0ItWTk4d0h1ZUJJUE5CVmU0OFA0V05IR1RfZ0ZxUWhxQUV4SXdGRm9rQUY0Q19ONEJGb0VoWWhDd2htSU5hcU8zWW5LaUpwZ0RrZ1JMMGd4S1J5ZlUtMHpRc28wTmlURGt4YlJNbEhYb2xNWmFZWklKb2hrZnJEWDFJcGtoa2dHaEdRcWJsZl81LUwyOWVIZDNmc1A5X2UtZTN6VV93RGd0aVNvWkFRQUFBIiwic2NvbnRleHQiOiJDaEFJQnhJTWRISmhaR1ZmWVhCcFgzSjFDaWdJQXhJa01UQTJNR1V6TVdFdE5XRTROQzAwWkdNeExXSXdZMkV0WkRGbE5tSTRZelF5TjJVMkNnUUlCUklBQ2drSUFCSUZhSFJ0YkRVS0tBZ0NFaVF5TldVd01HVTJNUzB4WlRJMUxURXhaakV0WWpVNE9DMWpabVJrWlRRNE5EVXhaVGNLQlFnSUVnRXpDZ1FJQ1JJQUNna0lDaElGTWk0MUxqQUtLQWdFRWlSbFl6azNZalUyWVMwMVlXWmtMVFE1WkdZdFlXRXhPUzB6WkRRMFlUQXhOMk01T0dVeVVBb1ZWRkpCUkVWQlVFbGZTMUpCVkU5VFgxUlBTMFZPRUFFWUFTQUJLZ2RGUkU5WVgwUkNPZ0lJQTBvVENnTUlod2NTQlFpSG9aNEJHZ1VJaDViREFWQ3NBbGdCWUFGb0FYSUdWSGhCZFhSbyIsInppcHBlZCI6dHJ1ZSwiY3JlYXRlZCI6IjE3NzMzNTYxODkiLCJyZW5ld0V4cCI6IjE4MDM4NDg0NTkiLCJzZXNzIjoiSDRzSUFBQUFBQUFBLzFPcTVGSXhUTFJJU2pOUE5kZE5TalkxMGpVeFRFclR0VEJMVHROTk0wMU5OVGRQVFRKTHNqUVg0cm13OE1MV2l3MFhObC9ZZW1HbkZOK0ZCUmY3TDJ5OHNPUENYaEJXNGkzV0s5WXJjc2hOek16Ukt5cE5VbkZ5TlRGemRMVjAwVFYzTkhmVE5URnhNdEcxTUhCMTFiVjBNakkxc1RCeE16STBNdHZGeU12Rkd1OFhFT1F2eE9MdjVCOEJBQitaWlg2TEFBQUEiLCJpc3MiOiJ0eHNlcnZlciIsImtleUlkIjoiZWM5N2I1NmEtNWFmZC00OWRmLWFhMTktM2Q0NGEwMTdjOThlIiwidHlwZSI6IkFwaVRva2VuIiwic2VjcmV0cyI6ImpJZnZscndXT3EzbDRGQWpMTThOM3c9PSIsInNjb3BlIjoiIiwidHN0ZXAiOiJmYWxzZSIsInNwaW5SZXEiOmZhbHNlLCJleHAiOjE4MDM4NDgzOTksInNwaW5FeHAiOiIxODAzODQ4NDU5IiwianRpIjoiMTA2MGUzMWEtNWE4NC00ZGMxLWIwY2EtZDFlNmI4YzQyN2U2In0.JyckL_Wafzbpan54YO58lKR9hIk4fiahLz1Tg3crmI6iEzBdnB7iKBHcLoziYmkEPMM3t4bzmXe2RCJ2QMMPpIBH_3GoZjfnupwrzk23JlXzsM0KFXlMl-w0H1v1JyfK1vxHNqGRpU6wnp8vMNX3BHcNA80lV8BVIICk0jp0RRs'
ACCOUNT_ID = '1060e31a-5a84-4dc1-b0ca-d1e6b8c427e6'

REST_URL = 'https://api.finam.ru'


async def get_trades():
    """Get recent trades"""
    url = f'{REST_URL}/v1/instruments/{SYMBOL}/trades/latest'
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as resp:
            print(f"Trades response status: {resp.status}")
            if resp.status == 200:
                try:
                    data = await resp.json()
                    print(f"Trades response: {data}")
                    return data.get('trades', [])
                except Exception as e:
                    text = await resp.text()
                    print(f"JSON error: {e}, response: {text[:200]}")
                    return []
            text = await resp.text()
            print(f"Ошибка получения сделок: {resp.status} - {text[:200]}")
            return []


async def send_order(quantity, direction, price):
    """Send order to Finam"""
    url = f'{REST_URL}/v1/accounts/{ACCOUNT_ID}/orders'
    
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
        async with session.post(url, json=order_data, headers=HEADERS) as resp:
            result = await resp.json()
            if resp.status in (200, 201):
                order_id = result.get('order_id')
                print(f"Заявка размещена: {order_id}")
                return order_id
            else:
                print(f"Ошибка: {result}")
                return None


async def check_and_trade():
    """Check for new trades and place counter orders"""
    global TRADED_ORDERS
    
    print(f"\n=== {datetime.now().strftime('%H:%M:%S')} === Проверяю сделки...")
    
    trades = await get_trades()
    
    if not trades:
        print("Нет новых сделок")
        return
    
    print(f"Найдено сделок: {len(trades)}")
    
    for trade in trades:
        trade_id = trade.get('trade_id', '')
        if not trade_id or trade_id in TRADED_ORDERS:
            continue
        
        symbol = trade.get('symbol', '')
        if symbol != SYMBOL:
            continue
            
        price = float(trade.get('price', 0))
        quantity = int(trade.get('quantity', 0))
        side = trade.get('side', '')
        
        if not all([price, quantity, side]):
            continue
        
        TRADED_ORDERS.add(trade_id)
        
        # Clean old entries
        if len(TRADED_ORDERS) > 100:
            TRADED_ORDERS = set(list(TRADED_ORDERS)[-50:])
        
        print(f"\n=== Сделка: {side} {quantity} @ {price} ===")
        
        if side == "BUY":
            counter_price = round(price + OFFSET, 3)
            counter_direction = "SELL"
        else:
            counter_price = round(price - OFFSET, 3)
            counter_direction = "BUY"
        
        print(f"Выставляю встречную заявку: {counter_direction} {quantity} @ {counter_price}")
        await send_order(quantity, counter_direction, counter_price)


async def main():
    print("Finam Trading Bot - Polling Version")
    print(f"Токен: Установлен")
    print(f"Account ID: {ACCOUNT_ID}")
    
    while True:
        try:
            await check_and_trade()
            await asyncio.sleep(5)
        except KeyboardInterrupt:
            print("\nОстановка...")
            break
        except Exception as e:
            print(f"Ошибка: {e}")
            await asyncio.sleep(5)


if __name__ == '__main__':
    asyncio.run(main())
