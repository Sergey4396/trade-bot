# Сокет для прослушивания последних сделок (polling)
# При получении новой сделки выставляет встречный ордер с дельтой Y
import os
import asyncio
from datetime import datetime

TOKEN = os.environ.get('FINAM_TOKEN', '')

# Настройки
SYMBOL = 'NRH6@MOEX'
PRICE_DELTA = 0.020  # Дельта для встречного ордера
POLL_INTERVAL = 5  # Интервал опроса в секундах

# Для хранения обработанных сделок
SEEN_TRADES = set()


async def run_socket(api):
    """
    Запускает polling сокет для прослушивания последних сделок
    api - объект FinamAPI
    """
    global SEEN_TRADES
    print(f"Запускаю сокет для {SYMBOL}...")
    
    while True:
        try:
            # Получаем последние сделки
            trades = await api.get_latest_trades()
            
            for t in trades:
                trade_id = t.get('trade_id', '')
                if not trade_id or trade_id in SEEN_TRADES:
                    continue
                
                SEEN_TRADES.add(trade_id)
                # Очищаем старые ID
                if len(SEEN_TRADES) > 100:
                    SEEN_TRADES = set(list(SEEN_TRADES)[-50:])
                
                price = float(t.get('price', {}).get('value', 0))
                qty = float(t.get('size', {}).get('value', 0))
                side = t.get('side', '')
                
                if not all([price, qty, side]):
                    continue
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Сделка: {side} {qty} @ {price}")
                
                # Вычисляем цену для встречного ордера
                if side == 'buy':
                    counter_price = round(price + PRICE_DELTA, 3)
                    counter_side = 'sell'
                else:
                    counter_price = round(price - PRICE_DELTA, 3)
                    counter_side = 'buy'
                
                print(f"  -> Выставляю {counter_side} {int(qty)} @ {counter_price}")
                
                # Выставляем встречный ордер
                try:
                    result = await api.post_order(int(qty), counter_side, counter_price)
                    if 'order_id' in result:
                        print(f"     OK: {result.get('order_id')}")
                    else:
                        print(f"     Ошибка: {result}")
                except Exception as e:
                    print(f"     Исключение: {e}")
                
                break  # Обрабатываем только одну новую сделку за раз
                
        except Exception as e:
            print(f"Ошибка: {e}")
        
        await asyncio.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    # Для тестирования запуска отдельно
    from api import FinamAPI
    api = FinamAPI()
    asyncio.run(run_socket(api))
