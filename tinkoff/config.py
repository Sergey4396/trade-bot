"""
Конфигурация ботов
"""

# Токены для разных аккаунтов
TOKENS = {
    'acc1': 't.KNbRWnr_MoKUOuBfzvjyUTUYftgAdZhpZ4zBqfwkgYtd4wnOaYuHCJHAeRXounciZ3N4NSQGPtH-8v5Mw0f_fQ',
    'gasA': 't.LVCTC-cmUG3rNXBH7-yT7HXpkoOOjkQpHORWyuCQ1TX9lrNLQGJoh9ZD3gZ9Mhz9WEdpiotucVLxrkhSwsKTXw',
    'gasB': 't.QCLXW-qrk_d6lvcxkpsGSNBHJDcI-hjbQwunnBCfo1GUsXL74fV4UK9Imxl3Nkh58kdYTUk2mcnM9BCPbZpUsw',
    'brok': 't.NrbE-4GJQ1iPddozQRlpOEY6q1tCvM_-fa5sLrUf2-KbJEtXaonz_Bn6kbPlQjkremLjYNSPrD_V6q9F7qbovQ',


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
        'lots_per_order': 6,
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

    {
            'account': 'gasA',
            'figi': 'FUTNGM042600',
            'ticker': 'NRJ6',
            'step': 0.001,
            'offset_buy': 0.002,
            'offset_sell': 0.002,
            'lots_per_order': 1,
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

        {
                    'account': 'gasB',
                    'figi': 'FUTNGM042600',
                    'ticker': 'NRJ6',
                    'step': 0.001,
                    'offset_buy': 0.002,
                    'offset_sell': 0.002,
                    'lots_per_order': 1,
                    'total_orders': 60,
                    'interval': 4000,
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
