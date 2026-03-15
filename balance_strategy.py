"""
Балансная стратегия для NRH6
Выставляет ±10 уровней от текущей цены, максимум 60 заявок
"""
import asyncio
from datetime import datetime

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
    
    # Проверяем каждые 10 минут
    if last_balance_time and (datetime.now() - last_balance_time).total_seconds() < 600:
        print(f"Балансная стратегия пропущена, прошло {(datetime.now() - last_balance_time).total_seconds():.0f} сек")
        return
    
    balance_running = True
    orders_placed = False
    total_orders = 0
    
    try:
        now = datetime.now()
        print(f"\n=== {now.strftime('%H:%M:%S')} === Balance Strategy")
        
        # Получаем цену из стакана
        nrh6_price = await api.get_futures_price_by_figi(api.FIGI_NRH6)
        
        if not nrh6_price:
            print("Не удалось получить цену NRH6")
            balance_running = False
            return
        
        # Получаем текущие заявки
        orders = await api.get_orders()
        nrh6_orders = [o for o in orders if o.get('figi') == api.FIGI_NRH6]
        total_orders = len(nrh6_orders)
        
        print(f"NRH6: цена={nrh6_price}, заявок={total_orders}")
        
        # Если заявок уже 60 - не выставляем новые
        if total_orders >= 60:
            print(f"Уже {total_orders} заявок, пропускаем")
            balance_running = False
            return
        
        step = 0.010
        base_price = round(nrh6_price - (nrh6_price % step), 3)
        range_levels = 10
        max_orders_per_side = 10
        
        available = 60 - total_orders
        
        # Покупки (вниз от цены)
        buy_count = min(max_orders_per_side, available)
        print(f"Выставляю {buy_count} покупок...")
        for i in range(1, buy_count + 1):
            price = base_price - step * i
            price = round(price, 3)
            print(f"  BUY: 1 @ {price}")
            try:
                result = await api.post_order(api.FIGI_NRH6, 1, 'ORDER_DIRECTION_BUY', price)
                if 'orderId' in result:
                    print(f"    OK: {result.get('orderId')}")
                    orders_placed = True
                    total_orders += 1
                else:
                    print(f"    Ошибка: {result.get('message', str(result))[:50]}")
            except Exception as e:
                print(f"    Исключение: {str(e)[:50]}")
            
            if total_orders >= 60:
                print(f"Достигли {total_orders} заявок, останавливаемся")
                break
        
        # Продажи (вверх от цены)
        available = 60 - total_orders
        if available > 0:
            sell_count = min(max_orders_per_side, available)
            print(f"Выставляю {sell_count} продаж...")
            for i in range(1, sell_count + 1):
                price = base_price + step * i
                price = round(price, 3)
                print(f"  SELL: 1 @ {price}")
                try:
                    result = await api.post_order(api.FIGI_NRH6, 1, 'ORDER_DIRECTION_SELL', price)
                    if 'orderId' in result:
                        print(f"    OK: {result.get('orderId')}")
                        orders_placed = True
                        total_orders += 1
                    else:
                        print(f"    Ошибка: {result.get('message', str(result))[:50]}")
                except Exception as e:
                    print(f"    Исключение: {str(e)[:50]}")
                
                if total_orders >= 60:
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
