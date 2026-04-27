#!/usr/bin/env python3
from FinamPy import FinamPy
import os

TOKEN = os.environ.get('FINAM_TOKEN', '')
if not TOKEN:
    print("Нужен FINAM_TOKEN")
    exit(1)

fp = FinamPy(TOKEN)
tickers = list(fp.tickers)
print(f'Всего тикеров: {len(tickers)}')

# Ищем газ
for t in tickers:
    if 'NR' in t or 'GZ' in t or 'GA' in t or 'GAS' in t:
        print(t)