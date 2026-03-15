"""
Балансная стратегия
Каждые 10 минут: удаляет все заявки и выставляет новые
"""
import asyncio
from datetime import datetime

# Настройки инструмента
FIGI = 'FUTNGM032600'  # NRH6
STEP = 0.010  # шаг цены
MAX_ORDERS = 60  # макс. заявок всего
INTERVAL = 600  # интервал в секундах (10 минут)

# Глобальные переменные
last_balance_time = None
balance_running = False


async def run_balance_strategy(api):
    """
    Запускает балансную стратегию
    1. Получаем позицию
    2. Получаем цену
    3. Удаляем все заявки
    4. Выставляем продажу (позиция - 1) заявок по ценам вверх
    5. Выставляем покупку до 57 заявок по ценам вниз
    """
    global last_balance_time, balance_running
    
    if balance_running:
        print("Балансная стратегия уже выполняется, пропускаю")
        return
    
    # Проверяем каждые INTERVAL секунд
    if last_balance_time and (datetime.now() - last_balance_time).total_seconds() < INTERVAL:
        print(f"Балансная стратегия пропущена, прошло {(datetime.now() - last_balance_time).total_seconds():.0f} сек")
        return
    
    balance_running = True
    
    try:
        now = datetime.now()
        print(f"\n=== {now.strftime('%H:%M:%S')} === Balance Strategy")
        
        # Получаем позицию
        position = await api.get_position(FIGI)
        print(f"Позиция: {position}")
        
        # Получаем цену из стакана
        price = await api.get_futures_price(FIGI)
        
        if not price:
            print(f"Не удалось получить цену для {FIGI}")
            balance_running = False
            return
        
        print(f"Текущая цена: {price}")
        
        # Удаляем все существующие заявки
        print("Удаляю все заявки...")
        orders = await api.get_orders(FIGI)
        cancelled = 0
        for order in orders:
            order_id = order.get('orderId')
            if order_id:
                await api.cancel_order(order_id)
                cancelled += 1
        print(f"Удалено заявок: {cancelled}")
        
        # Вычисляем базовую цену
        base_price = round(price - (price % STEP), 3)
        
        # Продажа: выставляем (позиция - 1) заявок, чтобы остался 1 лот
        sell_count = max(0, position - 1)
        
        # Покупка: 60 - позиция (чтобы всего было 59 заявок, 1 лот всегда в резерве)
        buy_count = MAX_ORDERS - position
        
        print(f"Выставляю {sell_count} заявок на продажу...")
        for i in range(1, sell_count + 1):
            sell_price = base_price + STEP * i
            sell_price = round(sell_price, 3)
            print(f"  SELL: 1 @ {sell_price}")
            try:
                result = await api.post_order(FIGI, 1, 'ORDER_DIRECTION_SELL', sell_price)
                if 'orderId' in result:
                    print(f"    OK: {result.get('orderId')}")
                else:
                    print(f"    Ошибка: {result.get('message', str(result))[:50]}")
            except Exception as e:
                print(f"    Исключение: {str(e)[:50]}")
        
        print(f"Выставляю {buy_count} заявок на покупку...")
        for i in range(1, buy_count + 1):
            buy_price = base_price - STEP * i
            buy_price = round(buy_price, 3)
            print(f"  BUY: 1 @ {buy_price}")
            try:
                result = await api.post_order(FIGI, 1, 'ORDER_DIRECTION_BUY', buy_price)
                if 'orderId' in result:
                    print(f"    OK: {result.get('orderId')}")
                else:
                    print(f"    Ошибка: {result.get('message', str(result))[:50]}")
            except Exception as e:
                print(f"    Исключение: {str(e)[:50]}")
        
        print("Балансная стратегия завершена")
        
    except Exception as e:
        import traceback
        print(f"Ошибка в балансной стратегии: {e}")
        print(traceback.format_exc())
    
    finally:
        last_balance_time = datetime.now()
        print(f"Таймер обновлён")
        balance_running = False
