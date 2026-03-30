"""
Лесенка заявок
Каждые 10 минут: удаляет все заявки и выставляет новую лесенку
"""
import asyncio
from datetime import datetime

# Настройки инструмента
FIGI = 'FUTNGM042600'  # NRJ6
STEP = 0.001  # шаг цены (1 единица)
OFFSET = 0.002  # отступ от рынка
TOTAL_ORDERS = 60  # количество заявок на каждую сторону
INTERVAL = 600  # интервал в секундах (10 минут)

# Глобальные переменные
last_balance_time = None
balance_running = False


async def run_balance_strategy(api):
    """
    Запускает стратегию лесенки
    1. Получаем лучшие bid/ask из стакана
    2. Удаляем все заявки
    3. Выставляем 60 заявок на покупку ниже best_bid - OFFSET
    4. Выставляем 60 заявок на продажу выше best_ask + OFFSET
    """
    global last_balance_time, balance_running
    
    if balance_running:
        print("Стратегия уже выполняется, пропускаю")
        return
    
    # Проверяем каждые INTERVAL секунд
    if last_balance_time and (datetime.now() - last_balance_time).total_seconds() < INTERVAL:
        return
    
    balance_running = True
    
    try:
        now = datetime.now()
        print(f"\n=== {now.strftime('%H:%M:%S')} === Лесенка")
        
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
        # Начинаем от best_bid - OFFSET и идём вниз
        start_buy = round(best_bid - OFFSET, 3)
        print(f"Выставляю {TOTAL_ORDERS} заявок на ПОКУПКУ от {start_buy:.3f} вниз...")
        
        for i in range(TOTAL_ORDERS):
            buy_price = round(start_buy - STEP * i, 3)
            try:
                result = await api.post_order(FIGI, 1, 'ORDER_DIRECTION_BUY', buy_price)
                if 'orderId' in result:
                    if i < 5 or i >= TOTAL_ORDERS - 2:
                        print(f"  BUY {i+1}: 1 @ {buy_price:.3f}")
                    elif i == 5:
                        print(f"  ...")
            except Exception as e:
                print(f"  BUY {i+1} ошибка: {str(e)[:50]}")
        
        # Выставляем лесенку на продажу
        # Начинаем от best_ask + OFFSET и идём вверх
        start_sell = round(best_ask + OFFSET, 3)
        print(f"Выставляю {TOTAL_ORDERS} заявок на ПРОДАЖУ от {start_sell:.3f} вверх...")
        
        for i in range(TOTAL_ORDERS):
            sell_price = round(start_sell + STEP * i, 3)
            try:
                result = await api.post_order(FIGI, 1, 'ORDER_DIRECTION_SELL', sell_price)
                if 'orderId' in result:
                    if i < 5 or i >= TOTAL_ORDERS - 2:
                        print(f"  SELL {i+1}: 1 @ {sell_price:.3f}")
                    elif i == 5:
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
