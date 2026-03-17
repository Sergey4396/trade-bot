#!/usr/bin/env python3
import asyncio
import os

from finam_trade_api import Client, TokenManager

TOKEN = 'eyJraWQiOiJlYzk3YjU2YS01YWZkLTQ5ZGYtYWExOS0zZDQ0YTAxN2M5OGUiLCJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhcmVhIjoidHQiLCJwYXJlbnQiOiJmN2MyNTZiNC04NGFhLTRmZjMtYmZiOC1lMGY3YTFlNjBmNzYiLCJhcGlUb2tlblByb3BlcnRpZXMiOiJINHNJQUFBQUFBQUFfeldUTVhiVU1CQ0dOMnN2MmJlUGFzcVVvZHYzZUk5TkFxbGxXZkthV0xZanlidGVHamVwb2VBb1BDN0FDYmdCSi1BbzNJQ0NYek9pLWY2Uk5EUFNlTWJiYjdfX192bjFRT3R0Y2ZPejNLNXZWX3ZyM2VhTnIzd3RocTQ4Ry1lekh2ZXZkcVZ5ODhEcTlaeTBVakd3bnB4TmF1YlJKVzNOM0xCYU00bE83T2Zhd0hIREVEWHI2QlZyMUZWV2xfVTU2ZGoyT211YnRjdktlY2JRc0wtUGt0ZFBvck55UVRTWXJMSmZEVTdVVDZLVG5PdktabzJpUm9zNk9UZlJzMXA1Nzl3bzhUcy0yYXhjNzl6VnZXaU82X0o5M1NEN1R0V3N2WkwzOVZMdjNEZDVuZF9kWF9MLVJkYWprdnZEMFdTVi0tSlRTQTFhcWw1ck5uVFZzdWVpMFJIZThKZVJEVFA1aWczbnFrOXM5S1BuYmk1QnQ3d1JuRlA3emE1WWdvU0VNWHVHOGVYQVJ2UW0zRjJ0Zmx5dGQ2dWI3LVcyb0VLWkdRZ200VGtCUzh3RjhKeVFEdkNWcWF5LWZINmhUZUpYS3ZDOUUtQ2dqeTNnVEFJaTljblFkZjJ4N2V1VTFrd3o4VkRSdGJWdWNmNUFwVzE3UmJ0RXQ5UlR2TkRHRHVnX0ZSWlhyUzJpR3VPcE9GcWtSRnVvYU0wRVRQRG85QVZJZDNYcFdXZ0dvQkhoY0ZtSjR2RVU1MDlVb0QyQVN3aHRna3RBZGVoTEFsdUJlSTZwR0lJaUhtR21ZOElEUFNPZVlHYkw3Smk0Ykh3S0ItWTk4d0h1ZUJJUE5CVmU0OFA0V05IR1RfZ0ZxUWhxQUV4SXdGRm9rQUY0Q19ONEJGb0VoWWhDd2htSU5hcU8zWW5LaUpwZ0RrZ1JMMGd4S1J5ZlUtMHpRc28wTmlURGt4YlJNbEhYb2xNWmFZWklKb2hrZnJEWDFJcGtoa2dHaEdRcWJsZl81LUwyOWVIZDNmc1A5X2UtZTN6VV93RGd0aVNvWkFRQUFBIiwic2NvbnRleHQiOiJDaEFJQnhJTWRISmhaR1ZmWVhCcFgzSjFDaWdJQXhJa01UQTJNR1V6TVdFdE5XRTROQzAwWkdNeExXSXdZMkV0WkRGbE5tSTRZelF5TjJVMkNnUUlCUklBQ2drSUFCSUZhSFJ0YkRVS0tBZ0NFaVF5TldVd01HVTJNUzB4WlRJMUxURXhaakV0WWpVNE9DMWpabVJrWlRRNE5EVXhaVGNLQlFnSUVnRXpDZ1FJQ1JJQUNna0lDaElGTWk0MUxqQUtLQWdFRWlSbFl6azNZalUyWVMwMVlXWmtMVFE1WkdZdFlXRXhPUzB6WkRRMFlUQXhOMk01T0dVeVVBb1ZWRkpCUkVWQlVFbGZTMUpCVkU5VFgxUlBTMFZPRUFFWUFTQUJLZ2RGUkU5WVgwUkNPZ0lJQTBvVENnTUlod2NTQlFpSG9aNEJHZ1VJaDViREFWQ3NBbGdCWUFGb0FYSUdWSGhCZFhSbyIsInppcHBlZCI6dHJ1ZSwiY3JlYXRlZCI6IjE3NzMzNTYxODkiLCJyZW5ld0V4cCI6IjE4MDM4NDg0NTkiLCJzZXNzIjoiSDRzSUFBQUFBQUFBLzFPcTVGSXhUTFJJU2pOUE5kZE5TalkxMGpVeFRFclR0VEJMVHROTk0wMU5OVGRQVFRKTHNqUVg0cm13OE1MV2l3MFhObC9ZZW1HbkZOK0ZCUmY3TDJ5OHNPUENYaEJXNGkzV0s5WXJjc2hOek16Ukt5cE5VbkZ5TlRGemRMVjAwVFYzTkhmVE5URnhNdEcxTUhCMTFiVjBNakkxc1RCeE16STBNdHZGeU12Rkd1OFhFT1F2eE9MdjVCOEJBQitaWlg2TEFBQUEiLCJpc3MiOiJ0eHNlcnZlciIsImtleUlkIjoiZWM5N2I1NmEtNWFmZC00OWRmLWFhMTktM2Q0NGEwMTdjOThlIiwidHlwZSI6IkFwaVRva2VuIiwic2VjcmV0cyI6ImpJZnZscndXT3EzbDRGQWpMTThOM3c9PSIsInNjb3BlIjoiIiwidHN0ZXAiOiJmYWxzZSIsInNwaW5SZXEiOmZhbHNlLCJleHAiOjE4MDM4NDgzOTksInNwaW5FeHAiOiIxODAzODQ4NDU5IiwianRpIjoiMTA2MGUzMWEtNWE4NC00ZGMxLWIwY2EtZDFlNmI4YzQyN2U2In0.JyckL_Wafzbpan54YO58lKR9hIk4fiahLz1Tg3crmI6iEzBdnB7iKBHcLoziYmkEPMM3t4bzmXe2RCJ2QMMPpIBH_3GoZjfnupwrzk23JlXzsM0KFXlMl-w0H1v1JyfK1vxHNqGRpU6wnp8vMNX3BHcNA80lV8BVIICk0jp0RRs'
SYMBOL = 'NRH6@RTSX'
ACCOUNT_ID = '2038952'

trade_client = None


async def get_trade_client():
    global trade_client
    if not trade_client:
        trade_client = Client(TokenManager(TOKEN))
        await trade_client.access_tokens.set_jwt_token()
    return trade_client


async def place_order(qty, side_name, price):
    """Выставить ордер"""
    c = await get_trade_client()
    try:
        from finam_trade_api.order import Order, OrderType, TimeInForce
        from finam_trade_api.base_client.models import FinamDecimal, Side
        
        order = Order(
            account_id=ACCOUNT_ID,
            symbol=SYMBOL,
            quantity=FinamDecimal(value=str(qty)),
            side=Side.BUY if side_name == 'BUY' else Side.SELL,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.DAY,
            limit_price=FinamDecimal(value=str(price)),
        )
        result = await c.orders.place_order(order)
        print(f"  -> Ордер выставлен: {result.order_id}, статус: {result.status}")
        return result
    except Exception as e:
        print(f"  -> Ошибка: {e}")
        return None


async def main():
    print("Тест выставления ордера")
    print(f"Символ: {SYMBOL}")
    print(f"Счет: {ACCOUNT_ID}")
    print()
    
    # Пример: выставить ордер на покупку 1 лота по цене 3.030
    await place_order(1, 'BUY', 3.030)


if __name__ == '__main__':
    asyncio.run(main())
