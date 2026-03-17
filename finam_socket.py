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
SEEN_TRADES = set()
fp_provider = None
trade_client = None
ACCOUNT_ID = '2038952'


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
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] СДЕЛКА: {side_name} {int(qty)} лот @ {price}")
    
    # Здесь можно вызывать свою логику
    # on_my_trade(price, qty, side_name)


def on_order(order):
    """Обработчик своих заявок"""
    status_name = "NEW" if order.status == 1 else "FILLED" if order.status == 3 else "CANCELED" if order.status == 5 else str(order.status)
    print(f"ЗАЯВКА: {order.order_id} - {status_name}")


def main():
    global fp_provider
    fp_provider = FinamPy(TOKEN)
    
    print(f"Finam Socket started")
    print(f"Accounts: {fp_provider.account_ids}")
    
    fp_provider.on_trade.subscribe(on_trade)
    fp_provider.on_order.subscribe(on_order)
    Thread(target=fp_provider.subscribe_trades_thread).start()
    Thread(target=fp_provider.subscribe_orders_thread).start()
    
    print(f"Подписка на свои сделки и заявки. Нажми Ctrl+C для выхода.")
    
    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass
    finally:
        fp_provider.close_channel()


if __name__ == '__main__':
    main()
