#!/usr/bin/env python3
import logging
import os
from datetime import datetime
from threading import Thread
import time
import random
import asyncio

from FinamPy import FinamPy
import FinamPy.grpc.side_pb2 as side
from finam_trade_api import Client, TokenManager
from google.type.decimal_pb2 import Decimal

TOKEN = os.environ.get('FINAM_TOKEN', '')
SYMBOL = 'NRH6@RTSX'
PRICE_DELTA = 0.020
INITIAL_ORDER_PRICE = 3.030
SEEN_TRADES = set()
fp_provider = None
trade_client = None
ACCOUNT_ID = '2038952'


async def get_trade_client():
    global trade_client
    if not trade_client:
        trade_client = Client(TokenManager(TOKEN))
        await trade_client.access_tokens.set_jwt_token()
    return trade_client


async def place_order_async(qty, side_name, price):
    """Выставляем ордер через finam-trade-api"""
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
        print(f"  -> Результат (async): {result}")
        return result
    except Exception as e:
        print(f"  -> Ошибка (async): {e}")
        return None


def place_initial_order():
    """Выставляем начальную заявку на покупку"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(place_order_async(1, 'BUY', INITIAL_ORDER_PRICE))
    finally:
        loop.close()


def on_trade(trade):
    """Обработчик своих сделок"""
    trade_time = trade.timestamp.seconds if trade.timestamp else 0
    current_time = int(time.time())
    if current_time - trade_time > 10:
        return
    
    trade_id = trade.trade_id
    if not trade_id or trade_id == "0" or trade_id in SEEN_TRADES:
        return
    
    SEEN_TRADES.add(trade_id)
    if len(SEEN_TRADES) > 100:
        SEEN_TRADES.clear()
    
    price = float(trade.price.value)
    qty = float(trade.size.value) if trade.size else 1.0
    
    trade_side = trade.side
    
    side_name = "BUY" if trade_side == 1 else "SELL" if trade_side == 2 else str(trade_side)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Своя сделка: {side_name} {qty} @ {price}")
    
    if price and qty:
        counter_price = round(price + PRICE_DELTA, 3) if trade_side == 1 else round(price - PRICE_DELTA, 3)
        counter_side_name = "SELL" if trade_side == 1 else "BUY"
        
        print(f"  -> Выставляю {counter_side_name} {int(qty)} @ {counter_price}")
        
        # Используем async версию
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(place_order_async(int(qty), counter_side_name, counter_price))
        finally:
            loop.close()


def on_order(order):
    """Обработчик своих заявок"""
    print(f"DEBUG: Заявка: order_id={order.order_id}, status={order.status}")


def main():
    global fp_provider
    fp_provider = FinamPy(TOKEN)
    
    print(f"Finam Trading Bot started")
    print(f"Accounts: {fp_provider.account_ids}")
    
    # Выставляем начальную заявку
    place_initial_order()
    
    fp_provider.on_trade.subscribe(on_trade)
    fp_provider.on_order.subscribe(on_order)
    Thread(target=fp_provider.subscribe_trades_thread).start()
    Thread(target=fp_provider.subscribe_orders_thread).start()
    
    print(f"Подписка на свои сделки. Нажми Ctrl+C для выхода.")
    
    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass
    finally:
        fp_provider.close_channel()


if __name__ == '__main__':
    main()
