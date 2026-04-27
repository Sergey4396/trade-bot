#!/usr/bin/env python3
from FinamPy import FinamPy
import os

TOKEN = os.environ.get('FINAM_TOKEN', '')
if not TOKEN:
    print("Нужен FINAM_TOKEN")
    exit(1)

fp = FinamPy(TOKEN)

# Пробуем получить тикеры разными способами
tickers = []
try:
    for t in fp.tickers:
        tickers.append(t)
except:
    pass

if not tickers:
    try:
        tickers = fp.tickers_list
    except:
        pass

if not tickers:
    # Пробуем через MarketData
    try:
        from FinamPy.Market import Market
        m = Market(TOKEN)
        tkr = m.tickers()
        tickers = list(tkr)
    except Exception as e:
        print(f"Ошибка: {e}")

print(f'Тикеров: {len(tickers)}')
for t in tickers:
    if 'NR' in t or 'GZ' in t or 'GA' in t:
        print(t)