"""
Лесенка заявок для нескольких инструментов
"""
import asyncio
from datetime import datetime, timezone, timedelta
from tinkoff.api import TinkoffAPI
from tinkoff.config import TOKENS, INSTRUMENTS

MOSCOW_TZ = timezone(timedelta(hours=3))

apis = {}
last_run_times = {}


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


def should_run_now(instrument):
    """Проверяет, нужно ли запускать сейчас"""
    run_at = instrument.get('run_at')
    interval = instrument.get('interval')
    inst_key = f"{instrument['account']}:{instrument['figi']}"
    last_time = last_run_times.get(inst_key)
    
    now_utc = datetime.now(timezone.utc)
    now_moscow = now_utc.astimezone(MOSCOW_TZ)
    
    print(f"[DEBUG should_run_now] {instrument['ticker']}: now={now_moscow.strftime('%H:%M')}, run_at={run_at}, interval={interval}, last_time={last_time}")
    
    # Если есть run_at - проверяем расписание
    if run_at:
        weekday = now_moscow.weekday()
        if weekday >= 5:
            target_time = run_at.get('weekend')
        else:
            target_time = run_at.get('weekdays')
        
        print(f"[DEBUG should_run_now] weekday={weekday}, target_time={target_time}")
        
        if target_time:
            target_hour, target_minute = map(int, target_time.split(':'))
            if now_moscow.hour < target_hour or (now_moscow.hour == target_hour and now_moscow.minute < target_minute):
                print(f"[DEBUG should_run_now] Before target time, skipping")
                return False
    
    # Проверяем интервал (если указан)
    if interval:
        if last_time:
            elapsed = (datetime.now() - last_time).total_seconds()
            print(f"[DEBUG should_run_now] elapsed={elapsed}s, interval={interval}s")
            if elapsed < interval:
                print(f"[DEBUG should_run_now] Within interval, skipping")
                return False
    elif not run_at:
        # Если нет ни run_at, ни interval - всегда запускаем
        return True
    
    print(f"[DEBUG should_run_now] Should run!")
    return True


def get_lots_for_order(instrument, position, order_index, direction=None):
    """Получает количество лотов для заявки в зависимости от режима"""
    mode = instrument.get('lots_mode', 'fixed')
    
    if mode == 'fixed':
        return instrument.get('lots_per_order', 1)
    
    elif mode == 'increasing':
        base = instrument.get('base_lots', 1)
        increment = instrument.get('lots_increment', 1)
        return base + increment * order_index
    
    elif mode == 'custom':
        conditions = instrument.get('lots_conditions', [])
        default_array = instrument.get('lots_default', [1] * 60)
        lots_array = None
        
        print(f"[DEBUG get_lots] position={position}, direction={direction}, conditions_count={len(conditions)}")
        
        for cond in conditions:
            min_val = cond.get('min')  # None = без ограничения снизу
            max_val = cond.get('max')  # None = без ограничения сверху
            
            min_ok = min_val is None or position >= min_val
            max_ok = max_val is None or position <= max_val
            
            print(f"[DEBUG get_lots]   condition: min={min_val}, max={max_val}, min_ok={min_ok}, max_ok={max_ok}")
            
            if min_ok and max_ok:
                if direction == 'BUY':
                    lots_array = cond.get('buy_array', cond.get('array', default_array))
                    print(f"[DEBUG get_lots]   MATCHED BUY: using buy_array")
                elif direction == 'SELL':
                    lots_array = cond.get('sell_array', cond.get('array', default_array))
                    print(f"[DEBUG get_lots]   MATCHED SELL: using sell_array")
                else:
                    lots_array = cond.get('array', default_array)
                break
        
        if not lots_array:
            lots_array = default_array
            print(f"[DEBUG get_lots]   USING DEFAULT")
        
        print(f"[DEBUG get_lots]   lots_array len={len(lots_array)}, returning lots_array[{order_index}]={lots_array[order_index] if order_index < len(lots_array) else 'N/A'}")
        
        while len(lots_array) < order_index + 1:
            lots_array.append(lots_array[-1] if lots_array else 1)
        
        return lots_array[order_index]
    
    return 1


async def run_instrument(instrument):
    """Запускает стратегию для одного инструмента"""
    account_id = instrument['account']
    figi = instrument['figi']
    ticker = instrument['ticker']
    inst_key = f"{account_id}:{figi}"
    
    api = get_api(account_id)
    
    if not await api.get_account_id():
        print(f"[{ticker}] Не удалось получить account_id")
        return
    
    print(f"[{ticker}] account_id: {api.account_id} (токен: {account_id})")
    
    trade_hours = instrument.get('trade_hours', {})
    if not is_trading_time(trade_hours):
        return
    
    if not should_run_now(instrument):
        return
    
    step = instrument.get('step', 0.001)
    offset_buy = instrument.get('offset_buy', 0.002)
    offset_sell = instrument.get('offset_sell', 0.002)
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
            print(f"[{ticker}] BUY: {total_orders} ордеров от {start_buy:.3f}")
            
            for i in range(total_orders):
                price = round(start_buy - step * i, 3)
                lots = get_lots_for_order(instrument, position, i, 'BUY')
                try:
                    result = await api.post_order(figi, lots, 'ORDER_DIRECTION_BUY', price)
                    if 'orderId' in result and i < 3:
                        print(f"  BUY {i+1}: {lots} @ {price:.3f}")
                except Exception as e:
                    if i < 3:
                        print(f"  BUY {i+1} ошибка: {str(e)[:30]}")
        
        if not skip_sell:
            start_sell = round(best_ask + offset_sell, 3)
            print(f"[{ticker}] SELL: {total_orders} ордеров от {start_sell:.3f}")
            
            for i in range(total_orders):
                price = round(start_sell + step * i, 3)
                lots = get_lots_for_order(instrument, position, i, 'SELL')
                try:
                    result = await api.post_order(figi, lots, 'ORDER_DIRECTION_SELL', price)
                    if 'orderId' in result and i < 3:
                        print(f"  SELL {i+1}: {lots} @ {price:.3f}")
                except Exception as e:
                    if i < 3:
                        print(f"  SELL {i+1} ошибка: {str(e)[:30]}")
        
        print(f"[{ticker}] Готово")
        last_run_times[inst_key] = datetime.now()
        
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
