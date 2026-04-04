"""
Лесенка заявок для нескольких инструментов
"""
import asyncio
from datetime import datetime, timezone, timedelta
from tinkoff.api import TinkoffAPI
from tinkoff.config import TOKENS, INSTRUMENTS

MOSCOW_TZ = timezone(timedelta(hours=3))

apis = {}


def get_api(account_id):
    if account_id not in apis:
        apis[account_id] = TinkoffAPI(TOKENS[account_id])
    return apis[account_id]


def is_trading_time(trade_hours):
    """Проверяет, можно ли торговать"""
    now_utc = datetime.now(timezone.utc)
    now_moscow = now_utc.astimezone(MOSCOW_TZ)
    hour = now_moscow.hour
    minute = now_moscow.minute
    
    start = trade_hours.get('start', 9)
    end = trade_hours.get('end', 23)
    end_minute = trade_hours.get('end_minute', 30)
    skip_hours = trade_hours.get('skip_hours', [])
    
    if hour < start or hour > end or (hour == end and minute > end_minute):
        return False
    
    for skip_start_h, skip_start_m, skip_end_h, skip_end_m in skip_hours:
        if skip_start_h <= hour < skip_end_h:
            if hour == skip_start_h and minute >= skip_start_m:
                return False
            if hour == skip_end_h and minute < skip_end_m:
                return False
            if skip_start_h < hour < skip_end_h:
                return False
    
    return True


async def run_instrument(instrument):
    """Запускает стратегию для одного инструмента"""
    account_id = instrument['account']
    figi = instrument['figi']
    ticker = instrument['ticker']
    
    api = get_api(account_id)
    
    if not await api.get_account_id():
        print(f"[{ticker}] Не удалось получить account_id")
        return
    
    trade_hours = instrument.get('trade_hours', {})
    if not is_trading_time(trade_hours):
        return
    
    step = instrument.get('step', 0.001)
    offset_buy = instrument.get('offset_buy', 0.002)
    offset_sell = instrument.get('offset_sell', 0.002)
    lots = instrument.get('lots_per_order', 1)
    total_orders = instrument.get('total_orders', 60)
    min_qty = instrument.get('min_qty')
    max_qty = instrument.get('max_qty')
    
    try:
        best_bid, best_ask = await api.get_orderbook_prices(figi)
        
        if not best_bid or not best_ask:
            print(f"[{ticker}] Не удалось получить цены")
            return
        
        print(f"\n[{ticker}] Bid: {best_bid:.3f}, Ask: {best_ask:.3f}")
        
        position = await api.get_position(figi)
        print(f"[{ticker}] Позиция: {position}")
        
        skip_buy = max_qty and position > max_qty
        skip_sell = min_qty and position < min_qty
        
        if skip_buy:
            print(f"[{ticker}] BUY пропущен (позиция {position} > max {max_qty})")
        if skip_sell:
            print(f"[{ticker}] SELL пропущен (позиция {position} < min {min_qty})")
        
        orders = await api.get_orders(figi)
        for order in orders:
            order_id = order.get('orderId')
            if order_id:
                await api.cancel_order(order_id)
        print(f"[{ticker}] Удалено заявок: {len(orders)}")
        
        if not skip_buy:
            start_buy = round(best_bid - offset_buy, 3)
            print(f"[{ticker}] BUY: {total_orders} ордеров от {start_buy:.3f} ({lots} лотов)")
            
            for i in range(total_orders):
                price = round(start_buy - step * i, 3)
                try:
                    result = await api.post_order(figi, lots, 'ORDER_DIRECTION_BUY', price)
                    if 'orderId' in result and i < 3:
                        print(f"  BUY {i+1}: {lots} @ {price:.3f}")
                except Exception as e:
                    if i < 3:
                        print(f"  BUY {i+1} ошибка: {str(e)[:30]}")
        
        if not skip_sell:
            start_sell = round(best_ask + offset_sell, 3)
            print(f"[{ticker}] SELL: {total_orders} ордеров от {start_sell:.3f} ({lots} лотов)")
            
            for i in range(total_orders):
                price = round(start_sell + step * i, 3)
                try:
                    result = await api.post_order(figi, lots, 'ORDER_DIRECTION_SELL', price)
                    if 'orderId' in result and i < 3:
                        print(f"  SELL {i+1}: {lots} @ {price:.3f}")
                except Exception as e:
                    if i < 3:
                        print(f"  SELL {i+1} ошибка: {str(e)[:30]}")
        
        print(f"[{ticker}] Готово")
        
    except Exception as e:
        import traceback
        print(f"[{ticker}] Ошибка: {e}")
        print(traceback.format_exc())


async def run_all_strategies():
    """Запускает стратегии для всех инструментов"""
    print(f"\n{'='*50}")
    print(f"{datetime.now(MOSCOW_TZ).strftime('%H:%M:%S')} мск - Запуск стратегий")
    print(f"{'='*50}")
    
    tasks = [run_instrument(inst) for inst in INSTRUMENTS]
    await asyncio.gather(*tasks)
