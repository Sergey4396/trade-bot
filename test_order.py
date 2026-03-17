#!/usr/bin/env python3
import asyncio
import os

from finam_trade_api import Client, TokenManager

TOKEN = os.environ.get('FINAM_TOKEN', '')
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
