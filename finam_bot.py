#!/usr/bin/env python3
import logging
import os
from datetime import datetime
from threading import Thread

from FinamPy import FinamPy
from FinamPy.grpc.marketdata.marketdata_service_pb2 import SubscribeLatestTradesResponse
import FinamPy.grpc.side_pb2 as side
from FinamPy.grpc.orders.orders_service_pb2 import Order, OrderType
from google.type.decimal_pb2 import Decimal

TOKEN = os.environ.get('FINAM_TOKEN', '')
SYMBOL = 'NRH6@RTSX'
PRICE_DELTA = 0.020
SEEN_TRADES = set()
fp_provider = None


def on_trade(trade: SubscribeLatestTradesResponse):
    print(f"DEBUG: Получено {len(trade.trades)} сделок")
    if not trade.trades:
        return
    
    for t in trade.trades:
        print(f"DEBUG: trade = {t}")
        trade_id = t.trade_id
        if not trade_id or trade_id == "0" or trade_id in SEEN_TRADES:
            continue
        
        SEEN_TRADES.add(trade_id)
        if len(SEEN_TRADES) > 100:
            SEEN_TRADES.clear()
        
        price = float(t.price.value)
        qty = float(t.size.value) if t.size else 1.0
        
        trade_side = t.side  # SIDE_BUY or SIDE_SELL
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Сделка: {trade_side.name} {qty} @ {price}")
        
        # Реагируем только на покупки - продаём 1 лот
        if trade_side == side.SIDE_BUY and price and qty:
            counter_price = round(price + PRICE_DELTA, 3)
            print(f"  -> Выставляю SELL 1 @ {counter_price}")
            order = Order(
                account_id=fp_provider.account_ids[0],
                symbol=SYMBOL,
                quantity=Decimal(value="1"),
                side=side.SIDE_SELL,
                type=OrderType.ORDER_TYPE_LIMIT,
                limit_price=Decimal(value=str(counter_price)),
            )
            fp_provider.call_function(fp_provider.orders_stub.PlaceOrder, order)


def main():
    global fp_provider
    fp_provider = FinamPy(TOKEN)
    
    print(f"Finam Trading Bot started")
    print(f"Accounts: {fp_provider.account_ids}")
    
    symbol = SYMBOL
    
    fp_provider.on_latest_trades.subscribe(on_trade)
    Thread(target=fp_provider.subscribe_latest_trades_thread, args=(symbol,)).start()
    
    print(f"Подписка на {symbol}. Нажми Ctrl+C для выхода.")
    
    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass
    finally:
        fp_provider.close_channel()


if __name__ == '__main__':
    main()
