"""
Балансная стратегия для Finam
Каждые 10 минут: удаляет все заявки и выставляет новые
"""
import asyncio
from datetime import datetime

# Настройки инструмента
SYMBOL = 'NRH6@MOEX'
STEP = 0.020  # шаг цены
MAX_ORDERS = 60  # макс. заявок всего
INTERVAL = 600  # интервал в секундах (10 минут)

# Глобальные переменные
last_balance_time = None
balance_running = False


async def run_balance_strategy(api):
    """
    Запускает балансную стратегию
    1. Получаем позицию
    2. Получаем последнюю цену
    3. Удаляем все заявки
    4. Выставляем продажу (позиция - 1) заявок по ценам вверх
    5. Выставляем покупку до MAX_ORDERS - позиция заявок по ценам вниз
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
        position = await api.get_position()
        print(f"Позиция: {position}")
        
        # Получаем последнюю сделку для цены
        trades = await api.get_latest_trades()
        if not trades:
            print("Нет сделок для определения цены")
            balance_running = False
            return
        
        price = float(trades[0].get('price', {}).get('value', 0))
        if not price:
            print("Не удалось получить цену")
            balance_running = False
            return
        
        print(f"Текущая цена: {price}")
        
        # TODO: Удаляем все существующие заявки
        # Для этого нужно получить список заявок и отменить каждую
        # Пока пропускаем
        
        # Вычисляем базовую цену
        base_price = round(price - (price % STEP), 3)
        
        # Продажа: выставляем (позиция - 1) заявок, чтобы остался 1 лот
        sell_count = max(0, position - 1)
        
        # Покупка: MAX_ORDERS - позиция
        buy_count = MAX_ORDERS - position
        
        print(f"Выставляю {sell_count} заявок на продажу...")
        for i in range(1, sell_count + 1):
            sell_price = base_price + STEP * i
            sell_price = round(sell_price, 3)
            print(f"  SELL: 1 @ {sell_price}")
            try:
                result = await api.post_order(1, 'sell', sell_price)
                if 'order_id' in result:
                    print(f"    OK: {result.get('order_id')}")
                else:
                    print(f"    Ошибка: {result}")
            except Exception as e:
                print(f"    Исключение: {e}")
        
        print(f"Выставляю {buy_count} заявок на покупку...")
        for i in range(1, buy_count + 1):
            buy_price = base_price - STEP * i
            buy_price = round(buy_price, 3)
            print(f"  BUY: 1 @ {buy_price}")
            try:
                result = await api.post_order(1, 'buy', buy_price)
                if 'order_id' in result:
                    print(f"    OK: {result.get('order_id')}")
                else:
                    print(f"    Ошибка: {result}")
            except Exception as e:
                print(f"    Исключение: {e}")
        
        print("Балансная стратегия завершена")
        
    except Exception as e:
        import traceback
        print(f"Ошибка в балансной стратегии: {e}")
        print(traceback.format_exc())
    
    finally:
        last_balance_time = datetime.now()
        print(f"Таймер обновлён")
        balance_running = False
