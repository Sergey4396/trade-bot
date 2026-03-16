# Сокет для прослушивания исполненных ордеров
# При исполнении ордера выставляет встречный ордер с дельтой Y
import os
import asyncio
from decimal import Decimal
from tinkoff.invest import AsyncClient, OrderDirection
from tinkoff.invest.constants import INVEST_GRPC_API
from tinkoff.invest.utils import quotation_to_decimal, decimal_to_quotation, money_to_decimal

TOKEN = os.environ.get('TINKOFF_TOKEN', 'YOUR_TOKEN_HERE')

# Настройки
FIGI = 'FUTNGM032600'  # NRH6
PRICE_DELTA = 0.010  # Дельта для встречного ордера

# Для получения FIGI по тикеру
TICKER_TO_FIGI = {
    'NRH6': 'FUTNGM032600',
    'NGH6': 'FUTNG0326000',
    'NGJ6': 'FUTNG0426000',
}


def get_figi_by_ticker(ticker: str) -> str:
    """Получить FIGI по тикеру"""
    return TICKER_TO_FIGI.get(ticker.upper(), ticker)


async def run_socket(api):
    """
    Запускает сокет для прослушивания исполненных ордеров
    api - объект TinkoffAPI
    """
    print("Запускаю сокет...")
    
    while True:
        try:
            async with AsyncClient(TOKEN, target=INVEST_GRPC_API) as client:
                accounts = await client.users.get_accounts()
                account = accounts.accounts[0]
                print(f"Сокет подключён, счёт: {account.id}")
                
                # Подписываемся на поток ордеров
                async for order_trade in client.orders_stream.trades_stream(accounts=[account.id]):
                    if not order_trade.order_trades or not hasattr(order_trade, 'order_trades'):
                        continue
                    
                    # Получаем данные об исполненном ордере
                    figi = order_trade.order_trades.figi
                    direction = order_trade.order_trades.direction.name
                    trades = order_trade.order_trades.trades
                    
                    # Фильтруем только по нашему FIGI
                    if figi != FIGI:
                        continue
                    
                    print(f"Получено событие: {figi}, {direction}")
                    
                    # Обрабатываем каждую сделку
                    for trade in trades:
                        price = quotation_to_decimal(trade.price)
                        quantity = int(trade.quantity)
                        
                        # Вычисляем цену для встречного ордера
                        if direction == 'ORDER_DIRECTION_SELL':
                            # Продали - покупаем дешевле
                            counter_price = price - Decimal(str(PRICE_DELTA))
                            counter_direction = OrderDirection.ORDER_DIRECTION_BUY
                        else:
                            # Купили - продаем дороже
                            counter_price = price + Decimal(str(PRICE_DELTA))
                            counter_direction = OrderDirection.ORDER_DIRECTION_SELL
                        
                        # Проверяем есть ли уже такие заявки
                        active_orders = await client.orders.get_orders(account_id=account.id)
                        existing = False
                        for order in active_orders.orders:
                            if order.figi == figi:
                                order_price = money_to_decimal(order.executed_order_price) if order.executed_order_price else money_to_decimal(order.initial_order_price)
                                if abs(order_price - counter_price) < Decimal('0.001'):
                                    existing = True
                                    print(f"Заявка уже существует: {order_price}")
                                    break
                        
                        if existing:
                            continue
                        
                        # Выставляем встречный ордер
                        print(f"Выставляю встречный ордер: {counter_direction.name} {quantity} @ {counter_price}")
                        
                        try:
                            result = await client.orders.post_order(
                                figi=figi,
                                quantity=quantity,
                                price=decimal_to_quotation(counter_price),
                                account_id=account.id,
                                order_type=OrderDirection.ORDER_DIRECTION_LIMIT,
                                direction=counter_direction,
                            )
                            print(f"Ордер выставлен: {result.order_id}")
                        except Exception as e:
                            print(f"Ошибка выставления ордера: {e}")
                        
                        break  # Обрабатываем только первый ордер из сделки
                        
        except Exception as e:
            print(f"Ошибка сокета: {e}")
            await asyncio.sleep(10)


if __name__ == '__main__':
    # Для тестирования запуска сокета отдельно
    asyncio.run(run_socket(None))
