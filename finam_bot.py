#!/usr/bin/env python3
import logging
import os
from datetime import datetime
from threading import Thread

from FinamPy import FinamPy
import FinamPy.grpc.side_pb2 as side
from FinamPy.grpc.orders.orders_service_pb2 import Order, OrderType
from google.type.decimal_pb2 import Decimal

TOKEN = os.environ.get('FINAM_TOKEN', '')
SYMBOL = 'NRH6@RTSX'
PRICE_DELTA = 0.020
SEEN_TRADES = set()
fp_provider = None


def on_trade(trade):
    """Обработчик своих сделок"""
    print(f"DEBUG: Своя сделка: {trade}")
    
    trade_id = trade.trade_id
    if not trade_id or trade_id == "0" or trade_id in SEEN_TRADES:
        return
    
    SEEN_TRADES.add(trade_id)
    if len(SEEN_TRADES) > 100:
        SEEN_TRADES.clear()
    
    price = float(trade.price.value)
    qty = float(trade.quantity.value) if trade.quantity else 1.0
    
    trade_side = trade.side  # SIDE_BUY or SIDE_SELL (int)
    
    side_name = "BUY" if trade_side == 1 else "SELL" if trade_side == 2 else str(trade_side)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Своя сделка: {side_name} {qty} @ {price}")
    
    if price and qty:
        counter_price = round(price + PRICE_DELTA, 3) if trade_side == 1 else round(price - PRICE_DELTA, 3)
        counter_side = 2 if trade_side == 1 else 1  # SIDE_SELL=2, SIDE_BUY=1
        
        side_name = "SELL" if counter_side == 2 else "BUY"
        print(f"  -> Выставляю {side_name} {int(qty)} @ {counter_price}")
        order_side = side.SIDE_SELL if counter_side == 2 else side.SIDE_BUY
        order = Order(
            account_id=fp_provider.account_ids[0],
            symbol=SYMBOL,
            quantity=Decimal(value=str(int(qty))),
            side=order_side,
            type=OrderType.ORDER_TYPE_LIMIT,
            limit_price=Decimal(value=str(counter_price)),
        )
        fp_provider.call_function(fp_provider.orders_stub.PlaceOrder, order)


def main():
    global fp_provider
    fp_provider = FinamPy(TOKEN)
    
    print(f"Finam Trading Bot started")
    print(f"Accounts: {fp_provider.account_ids}")
    
    fp_provider.on_trade.subscribe(on_trade)
    Thread(target=fp_provider.subscribe_trades_thread).start()
    
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
