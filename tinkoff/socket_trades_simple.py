#!/usr/bin/env python3
import os
import time
import requests
from decimal import Decimal
import urllib3
urllib3.disable_warnings()

TOKEN = 't.KNbRWnr_MoKUOuBfzvjyUTUYftgAdZhpZ4zBqfwkgYtd4wnOaYuHCJHAeRXounciZ3N4NSQGPtH-8v5Mw0f_fQ'

# Настройки
FIGI = 'FUTNGM032600'  # NRH6
PRICE_DELTA = Decimal('0.010')  # Дельта для встречного ордера

HEADERS = {"Authorization": f"Bearer {TOKEN}"}


def get_accounts():
    """Получить список счетов"""
    url = "https://invest-public-api.tbank.ru/accounts"
    resp = requests.get(url, headers=HEADERS, verify=False)
    print(f"Accounts: {resp.status_code} {resp.text[:500]}")
    return resp.json()


def get_orders(account_id):
    """Получить активные заявки"""
    url = f"https://invest-public-api.tbank.ru/orders?brokerAccountId={account_id}"
    resp = requests.get(url, headers=HEADERS, verify=False)
    return resp.json()


def post_order(account_id, figi, quantity, direction, price):
    """Выставить заявку"""
    url = "https://invest-public-api.tbank.ru/orders/limit-order"
    
    price_str = str(price)
    units = price_str.split('.')[0]
    nano = int((float(price) - int(float(price))) * 1_000_000_000) if '.' in price_str else 0
    
    payload = {
        "figi": figi,
        "quantity": quantity,
        "price": {"units": units, "nano": nano},
        "direction": direction,
        "brokerAccountId": account_id
    }
    
    resp = requests.post(url, headers=HEADERS, json=payload, verify=False)
    return resp.json()


def main():
    print("Запускаю сокет (REST polling)...")
    
    # Получаем счёт
    accounts = get_accounts()
    if 'accounts' not in accounts:
        print(f"Ошибка: {accounts}")
        return
    
    account = accounts['accounts'][0]
    account_id = account.get('id') or account.get('brokerAccountId')
    print(f"Счёт: {account_id}")
    
    seen_orders = set()
    
    while True:
        try:
            orders = get_orders(account_id)
            print(f"Заявок: {orders}")
            
            if 'orders' in orders:
                for order in orders['orders']:
                    order_id = order.get('orderId', '')
                    if order_id in seen_orders:
                        continue
                    
                    status = order.get('status', '')
                    print(f"Заявка: {order_id} - {status}")
                    
                    # Проверяем исполненные
                    if status == 'EXECUTE' or order.get('filledLots', 0) > 0:
                        seen_orders.add(order_id)
                        
                        direction = order.get('direction', '')
                        qty = int(order.get('lotsRequested', order.get('quantity', 1)))
                        
                        # Цена
                        price_data = order.get('avgPrice', order.get('initialPrice', {}))
                        if price_data:
                            price = Decimal(str(price_data.get('units', 0))) + Decimal(str(price_data.get('nano', 0))) / Decimal('1_000_000_000')
                        else:
                            price = Decimal('0')
                        
                        if price > 0:
                            if direction == 'SELL':
                                counter_price = price - PRICE_DELTA
                                counter_direction = 'BUY'
                            else:
                                counter_price = price + PRICE_DELTA
                                counter_direction = 'SELL'
                            
                            print(f"Исполнена: {direction} {qty} @ {price}")
                            print(f"  -> Выставляю {counter_direction} {qty} @ {counter_price}")
                            
                            result = post_order(account_id, FIGI, qty, counter_direction, counter_price)
                            print(f"  -> Результат: {result}")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)


if __name__ == '__main__':
    main()
