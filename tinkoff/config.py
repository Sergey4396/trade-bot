"""
Конфигурация ботов
"""

# Токены для разных аккаунтов
TOKENS = {
    'acc1': 't.KNbRWnr_MoKUOuBfzvjyUTUYftgAdZhpZ4zBqfwkgYtd4wnOaYuHCJHAeRXounciZ3N4NSQGPtH-8v5Mw0f_fQ',
}

# Список инструментов
INSTRUMENTS = [
    {
        'account': 'acc1',
        'figi': 'FUTNGM042600',
        'ticker': 'NRJ6',
        'step': 0.001,
        'offset_buy': 0.002,
        'offset_sell': 0.002,
        'lots_per_order': 3,
        'total_orders': 60,
        'interval': 600,
        'min_qty': None,
        'max_qty': None,
        'trade_hours': {
            'start': 9,
            'end': 23,
            'end_minute': 30,
            'skip_hours': [(9, 50, 10, 0)],
        },
    },
]
