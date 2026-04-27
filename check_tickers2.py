#!/usr/bin/env python3
from finam_trade_api import Client, TokenManager
import asyncio

async def main():
    token = input("Введи токен: ").strip()
    if not token:
        print("Нужен токен")
        return
    
    client = Client(TokenManager(token))
    await client.access_tokens.set_jwt_token()
    
    # Получаем все инструменты
    try:
        instruments = await client.market.get_securities()
        print(f"Инструментов: {len(instruments)}")
        for i in instruments[:50]:
            print(i)
    except Exception as e:
        print(f"Ошибка: {e}")

asyncio.run(main())