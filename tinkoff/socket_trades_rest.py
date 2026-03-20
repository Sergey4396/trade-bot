#!/usr/bin/env python3
# Сокет для прослушивания исполненных ордеров через REST API
# При исполнении ордера выставляет встречный ордер с дельтой Y
import os
import asyncio
import aiohttp
from decimal import Decimal
import time
import json

TOKEN = 't.KNbRWnr_MoKUOuBfzvjyUTUYftgAdZhpZ4zBqfwkgYtd4wnOaYuHCJHAeRXounciZ3N4NSQGPtH-8v5Mw0f_fQ'

# Настройки
FIGI = 'FUTNGM032600'  # NRH6
PRICE_DELTA = Decimal('0.010')  # Дельта для встречного ордера

# figi для разных инструментов
TICKER_TO_FIGI = {
    'NRH6': 'FUTNGM032600',
    'NGH6': 'FUTNG0326000',
    'NGJ6': 'FUTNG0426000',
}


def get_figi_by_ticker(ticker: str) -> str:
    return TICKER_TO_FIGI.get(ticker.upper(), ticker)


async def get_accounts(session):
    """Получить список счетов"""
    url = "https://api-invest.tinkoff.ru/openapi/accounts"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    async with session.get(url, headers=headers, allow_redirects=False) as resp:
        print(f"Status: {resp.status}, URL: {resp.headers.get('Location', 'none')}")
        text = await resp.text()
        print(f"Response: {text[:500]}")
        return await resp.json()


async def get_orders(session, account_id):
    """Получить активные заявки"""
    url = f"https://api-invest.tinkoff.ru/openapi/orders?brokerAccountId={account_id}"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    async with session.get(url, headers=headers) as resp:
        return await resp.json()


async def post_order(session, account_id, figi, quantity, direction, price):
    """Выставить заявку"""
    url = "https://api-invest.tinkoff.ru/openapi/orders/limit-order"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    price_str = str(price)
    
    payload = {
        "figi": figi,
        "quantity": quantity,
        "price": {
            "units": price_str.split('.')[0],
            "nano": int(f"{(price - int(price)) * 1_000_000_000:.0f}") if '.' in price_str else 0
        },
        "direction": direction,
        "accountId": account_id
    }
    
    async with session.post(url, headers=headers, json=payload) as resp:
        return await resp.json()


def quotation_to_decimal(units, nano):
    """Конвертировать котировку в Decimal"""
    return Decimal(str(units)) + Decimal(str(nano)) / Decimal('1_000_000_000')


def decimal_to_units_nano(value):
    """Конвертировать Decimal в units и nano"""
    units = int(value)
    nano = int((value - units) * 1_000_000_000)
    return {"units": units, "nano": nano}


async def run_socket():
    """Запускает сокет через polling"""
    print("Запускаю сокет (polling)...")
    
    seen_orders = set()  # Отслеживаем обработанные заявки
    
    async with aiohttp.ClientSession() as session:
        # Получаем счёт
        accounts = await get_accounts(session)
        if 'accounts' not in accounts:
            print(f"Ошибка получения счетов: {accounts}")
            return
        
        account = accounts['accounts'][0]
        account_id = account['id']
        print(f"Подключено, счёт: {account_id}")
        
        while True:
            try:
                # Получаем заявки
                orders_response = await get_orders(session, account_id)
                
                if 'orders' in orders_response:
                    for order in orders_response['orders']:
                        order_id = order.get('orderId', '')
                        
                        if order_id in seen_orders or order.get('figi') != FIGI:
                            continue
                        
                        # Проверяем статус - исполнена?
                        if order.get('status') == 'ORDER_STATUS_EXECUTED' or order.get('filledQuantity', '0') != '0':
                            seen_orders.add(order_id)
                            
                            # Получаем данные
                            direction = order.get('direction', '')
                            qty = int(order.get('requestedLots', order.get('quantity', '1')))
                            
                            # Получаем цену исполнения
                            exec_price = order.get('avgPrice', {})
                            if exec_price:
                                price = quotation_to_decimal(
                                    exec_price.get('units', 0),
                                    exec_price.get('nano', 0)
                                )
                            else:
                                init_price = order.get('initialPrice', {})
                                price = quotation_to_decimal(
                                    init_price.get('units', 0),
                                    init_price.get('nano', 0)
                                )
                            
                            if price > 0:
                                if direction == 'ORDER_DIRECTION_SELL':
                                    counter_price = price - PRICE_DELTA
                                    counter_direction = 'ORDER_DIRECTION_BUY'
                                    action = "BUY"
                                else:
                                    counter_price = price + PRICE_DELTA
                                    counter_direction = 'ORDER_DIRECTION_SELL'
                                    action = "SELL"
                                
                                print(f"Исполнена заявка: {direction} {qty} @ {price}")
                                print(f"  -> Выставляю {action} {qty} @ {counter_price}")
                                
                                result = await post_order(
                                    session, account_id, FIGI, qty, counter_direction, counter_price
                                )
                                
                                if 'orderId' in result:
                                    print(f"  -> Ордер выставлен: {result['orderId']}")
                                else:
                                    print(f"  -> Ошибка: {result}")
                
                await asyncio.sleep(1)  # Проверяем каждую секунду
                
            except Exception as e:
                print(f"Ошибка: {e}")
                await asyncio.sleep(5)


if __name__ == '__main__':
    asyncio.run(run_socket())
