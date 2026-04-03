"""
Лесенка заявок
Каждые 10 минут: удаляет все заявки и выставляет новую лесенку
"""
import asyncio
from datetime import datetime, timezone, timedelta

# Настройки инструмента
FIGI = 'FUTNGM042600'  # NRJ6
STEP = 0.001  # шаг цены (1 единица)
OFFSET = 0.002  # отступ от рынка
TOTAL_ORDERS = 60  # количество заявок на каждую сторону
LOTS_PER_ORDER = 3  # количество лотов в каждой заявке
INTERVAL = 600  # интервал в секундах (10 минут)

# Глобальные переменные
last_balance_time = None
balance_running = False

# Москва UTC+3
MOSCOW_TZ = timezone(timedelta(hours=3))


def is_trading_time():
    """Проверяет, можно ли торговать (9:00-23:30 мск, кроме 9:50-10:00)"""
    now_utc = datetime.now(timezone.utc)
    now_moscow = now_utc.astimezone(MOSCOW_TZ)
    hour = now_moscow.hour
    minute = now_moscow.minute
    
    # Проверяем диапазон 9:00 - 23:30
    if hour < 9 or (hour == 23 and minute > 30) or hour >= 24:
        return False
    if hour < 9:
        return False
    
    # Пропускаем 9:50 - 10:00
    if hour == 9 and minute >= 50:
        return False
    if hour == 10 and minute < 1:
        return False
    
    return True


async def run_balance_strategy(api):
    """
    Запускает стратегию лесенки
    1. Проверяем время
    2. Получаем лучшие bid/ask из стакана
    3. Удаляем все заявки
    4. Выставляем 60 заявок на покупку ниже best_bid - OFFSET
    5. Выставляем 60 заявок на продажу выше best_ask + OFFSET
    """
    global last_balance_time, balance_running
    
    if balance_running:
        print("Стратегия уже выполняется, пропускаю")
        return
    
    # Проверяем каждые INTERVAL секунд
    if last_balance_time and (datetime.now() - last_balance_time).total_seconds() < INTERVAL:
        return
    
    # Проверяем время торговли
    if not is_trading_time():
        return
    
    balance_running = True
    
    try:
        now_utc = datetime.now(timezone.utc)
        now_moscow = now_utc.astimezone(MOSCOW_TZ)
        print(f"\n=== {now_moscow.strftime('%H:%M:%S')} мск === Лесенка")
        
        # Получаем лучшие цены из стакана
        best_bid, best_ask = await api.get_orderbook_prices(FIGI)
        
        if not best_bid or not best_ask:
            print(f"Не удалось получить цены стакана")
            balance_running = False
            return
        
        print(f"Лучший Bid: {best_bid:.3f}, лучший Ask: {best_ask:.3f}")
        
        # Удаляем все существующие заявки
        print("Удаляю все заявки...")
        orders = await api.get_orders(FIGI)
        cancelled = 0
        for order in orders:
            order_id = order.get('orderId')
            if order_id:
                await api.cancel_order(order_id)
                cancelled += 1
        print(f"Удалено: {cancelled}")
        
        # Выставляем лесенку на покупку
        start_buy = round(best_bid - OFFSET, 3)
        print(f"Выставляю {TOTAL_ORDERS} заявок на ПОКУПКУ от {start_buy:.3f} вниз ({LOTS_PER_ORDER} лота)...")
        
        for i in range(TOTAL_ORDERS):
            buy_price = round(start_buy - STEP * i, 3)
            try:
                result = await api.post_order(FIGI, LOTS_PER_ORDER, 'ORDER_DIRECTION_BUY', buy_price)
                if 'orderId' in result:
                    if i < 3 or i >= TOTAL_ORDERS - 1:
                        print(f"  BUY {i+1}: {LOTS_PER_ORDER} @ {buy_price:.3f}")
                    elif i == 3:
                        print(f"  ...")
            except Exception as e:
                print(f"  BUY {i+1} ошибка: {str(e)[:50]}")
        
        # Выставляем лесенку на продажу
        start_sell = round(best_ask + OFFSET, 3)
        print(f"Выставляю {TOTAL_ORDERS} заявок на ПРОДАЖУ от {start_sell:.3f} вверх ({LOTS_PER_ORDER} лота)...")
        
        for i in range(TOTAL_ORDERS):
            sell_price = round(start_sell + STEP * i, 3)
            try:
                result = await api.post_order(FIGI, LOTS_PER_ORDER, 'ORDER_DIRECTION_SELL', sell_price)
                if 'orderId' in result:
                    if i < 3 or i >= TOTAL_ORDERS - 1:
                        print(f"  SELL {i+1}: {LOTS_PER_ORDER} @ {sell_price:.3f}")
                    elif i == 3:
                        print(f"  ...")
            except Exception as e:
                print(f"  SELL {i+1} ошибка: {str(e)[:50]}")
        
        print("Лесенка выставлена")
        
    except Exception as e:
        import traceback
        print(f"Ошибка: {e}")
        print(traceback.format_exc())
    
    finally:
        last_balance_time = datetime.now()
        balance_running = False
