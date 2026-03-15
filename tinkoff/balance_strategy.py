"""
Балансная стратегия
Выставляет ±10 уровней от текущей цены, максимум 60 заявок
"""
import asyncio
from datetime import datetime

# Настройки инструмента
FIGI = 'FUTNGM032600'  # NRH6
STEP = 0.010  # шаг цены
MAX_ORDERS = 60  # макс. заявок
RANGE_LEVELS = 10  # ± уровней
MAX_PER_SIDE = 10  # макс. заявок на каждую сторону
INTERVAL = 600  # интервал в секундах (10 минут)

# Глобальные переменные
last_balance_time = None
balance_running = False


async def run_balance_strategy(api):
    """
    Запускает балансную стратегию
    api - объект с методами: get_orders, get_positions, post_order, get_futures_price_by_figi
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
    orders_placed = False
    total_orders = 0
    
    try:
        now = datetime.now()
        print(f"\n=== {now.strftime('%H:%M:%S')} === Balance Strategy")
        
        # Получаем цену из стакана
        price = await api.get_futures_price(FIGI)
        
        if not price:
            print(f"Не удалось получить цену для {FIGI}")
            balance_running = False
            return
        
        # Получаем текущие заявки
        orders = await api.get_orders(FIGI)
        total_orders = len(orders)
        
        print(f"{FIGI}: цена={price}, заявок={total_orders}")
        
        # Если заявок уже MAX_ORDERS - не выставляем новые
        if total_orders >= MAX_ORDERS:
            print(f"Уже {total_orders} заявок, пропускаем")
            balance_running = False
            return
        
        step = STEP
        base_price = round(price - (price % step), 3)
        
        available = MAX_ORDERS - total_orders
        
        # Покупки (вниз от цены)
        buy_count = min(MAX_PER_SIDE, available)
        print(f"Выставляю {buy_count} покупок...")
        for i in range(1, buy_count + 1):
            price = base_price - step * i
            price = round(price, 3)
            print(f"  BUY: 1 @ {price}")
            try:
                result = await api.post_order(FIGI, 1, 'ORDER_DIRECTION_BUY', price)
                if 'orderId' in result:
                    print(f"    OK: {result.get('orderId')}")
                    orders_placed = True
                    total_orders += 1
                else:
                    print(f"    Ошибка: {result.get('message', str(result))[:50]}")
            except Exception as e:
                print(f"    Исключение: {str(e)[:50]}")
            
            if total_orders >= MAX_ORDERS:
                print(f"Достигли {total_orders} заявок, останавливаемся")
                break
        
        # Продажи (вверх от цены)
        available = MAX_ORDERS - total_orders
        if available > 0:
            sell_count = min(MAX_PER_SIDE, available)
            print(f"Выставляю {sell_count} продаж...")
            for i in range(1, sell_count + 1):
                price = base_price + step * i
                price = round(price, 3)
                print(f"  SELL: 1 @ {price}")
                try:
                    result = await api.post_order(FIGI, 1, 'ORDER_DIRECTION_SELL', price)
                    if 'orderId' in result:
                        print(f"    OK: {result.get('orderId')}")
                        orders_placed = True
                        total_orders += 1
                    else:
                        print(f"    Ошибка: {result.get('message', str(result))[:50]}")
                except Exception as e:
                    print(f"    Исключение: {str(e)[:50]}")
                
                if total_orders >= MAX_ORDERS:
                    print(f"Достигли {total_orders} заявок, останавливаемся")
                    break
        
        print(f"Итого заявок: {total_orders}")
        
    except Exception as e:
        import traceback
        print(f"Ошибка в балансной стратегии: {e}")
        print(traceback.format_exc())
    
    finally:
        last_balance_time = datetime.now()
        print(f"Таймер обновлён")
        balance_running = False
