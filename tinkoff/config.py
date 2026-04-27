"""
Конфигурация ботов
"""

#// pkill -f "python main.py"


# Токены для разных аккаунтов
TOKENS = {
    'acc1': 't.KNbRWnr_MoKUOuBfzvjyUTUYftgAdZhpZ4zBqfwkgYtd4wnOaYuHCJHAeRXounciZ3N4NSQGPtH-8v5Mw0f_fQ',
    'gasA': 't.LVCTC-cmUG3rNXBH7-yT7HXpkoOOjkQpHORWyuCQ1TX9lrNLQGJoh9ZD3gZ9Mhz9WEdpiotucVLxrkhSwsKTXw',
    'gasB': 't.QCLXW-qrk_d6lvcxkpsGSNBHJDcI-hjbQwunnBCfo1GUsXL74fV4UK9Imxl3Nkh58kdYTUk2mcnM9BCPbZpUsw',
    'brok': 't.NrbE-4GJQ1iPddozQRlpOEY6q1tCvM_-fa5sLrUf2-KbJEtXaonz_Bn6kbPlQjkremLjYNSPrD_V6q9F7qbovQ',
}

# lots_mode:
#   'fixed'      - фиксированное кол-во (lots_per_order)
#   'increasing'  - увеличивающееся (base_lots + lots_increment * i)
#   'custom'      - кастомные массивы по условиям позиции

# Пример custom режима:
#   'lots_conditions': [
#       {'min': 200, 'max': None, 'array': [3, 3, 3, ...]},   # позиция > 200
#       {'min': 100, 'max': 200, 'array': [2, 2, 2, ...]},    # 100 <= позиция <= 200
#       {'min': None, 'max': 100, 'array': [1, 1, 1, ...]},   # позиция < 100
#   ],
#   'lots_default': [1, 1, 1, ...],

INSTRUMENTS = [


        {
            'account': 'acc1',
            'figi': 'FUTNGM052600',
            'ticker': 'NRK6',
            'step': 0.001,
            'offset_buy': 0.009,
            'offset_sell': 0.009,
            'total_orders': 60,
            'interval': None,
            'min_qty': -5000,
            'max_qty': 5200,
            'trade_hours': {
                'start': 9,
                'end': 23,
                'end_minute': 30,
                'skip_hours': [(9, 50, 10, 0)],
            },
            'lots_mode': 'custom',
            'lots_conditions': [
            {'min': 1601, 'max': 3000, 'buy_array': [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59], 'sell_array': [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59]},
                {'min': -200, 'max': 1600, 'buy_array': [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59], 'sell_array': [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59]},
                {'min': -1600, 'max': -200, 'buy_array': [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59], 'sell_array': [0,0,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,25,25,25,25,25,25]},
            ],
            'lots_default': [1] * 60,
            'run_at': {'weekdays': '09:01', 'weekend': '10:01'},
        },

# {
#     'account': 'acc1',
#     'figi': 'FUTNGM042600',
#     'ticker': 'NRJ6',
#     'step': 0.001,
#     'offset_buy': 0.002,
#     'offset_sell': 0.002,
#     'total_orders': 60,
#     'interval': 600,
#     'min_qty': None,
#     'max_qty': None,
#     'trade_hours': {
#         'start': 9,
#         'end': 23,
#         'end_minute': 30,
#         'skip_hours': [(9, 50, 10, 0)],
#     },
#     'lots_mode': 'fixed',
#     'lots_per_order': 6,
#     'base_lots': 3,
#     'lots_increment': 1,
#     'lots_conditions': [],
#     'lots_default': [1] * 60,
#     'run_at': None,
# },

]

INSTRUMENTSOLD = [
{
        'account': 'acc1',
        'figi': 'FUTNGM062600',
        'ticker': 'NRM6',
        'step': 0.010,
        'offset_buy': 0.001,
        'offset_sell': 0.001,
        'total_orders': 10,
        'interval': None,
        'min_qty': None,
        'max_qty': None,
        'trade_hours': {
            'start': 9,
            'end': 23,
            'end_minute': 30,
            'skip_hours': [(9, 50, 10, 0)],
        },
        'lots_mode': 'custom',
        'lots_per_order': 1,
        'base_lots': 1,
        'lots_increment': 0,
        'lots_conditions': [
            {'min': -20, 'max': 200, 'buy_array': [1,2,3,4,5,6,7,8,9,10], 'sell_array': [1,2,3,4,5,6,7,8,9,10]},
            {'min': -200, 'max': -20, 'buy_array': [1,2,3,4,5,6,7,8,9,10], 'sell_array': [0,1,2,3,4,5,6,7,8,9]},
        ],
        'lots_default': [1] * 10,
        'run_at': {'weekdays': '09:01', 'weekend': '10:01'},
    },
    {
            'account': 'acc1',
            'figi': 'FUTNGM072600',
            'ticker': 'NRN6',
            'step': 0.010,
            'offset_buy': 0.001,
            'offset_sell': 0.001,
            'total_orders': 10,
            'interval': None,
            'min_qty': None,
            'max_qty': None,
            'trade_hours': {
                'start': 9,
                'end': 23,
                'end_minute': 30,
                'skip_hours': [(9, 50, 10, 0)],
            },
            'lots_mode': 'custom',
            'lots_per_order': 1,
            'base_lots': 1,
            'lots_increment': 0,
            'lots_conditions': [
                {'min': -20, 'max': 200, 'buy_array': [1,2,3,4,5,6,7,8,9,10], 'sell_array': [1,2,3,4,5,6,7,8,9,10]},
                {'min': -200, 'max': -20, 'buy_array': [1,2,3,4,5,6,7,8,9,10], 'sell_array': [0,1,2,3,4,5,6,7,8,9]},
            ],
            'lots_default': [1] * 10,
            'run_at': {'weekdays': '09:01', 'weekend': '10:01'},
        },
        {
                'account': 'acc1',
                'figi': 'FUTNGM082600',
                'ticker': 'NRQ6',
                'step': 0.010,
                'offset_buy': 0.001,
                'offset_sell': 0.001,
                'total_orders': 10,
                'interval': None,
                'min_qty': None,
                'max_qty': None,
                'trade_hours': {
                    'start': 9,
                    'end': 23,
                    'end_minute': 30,
                    'skip_hours': [(9, 50, 10, 0)],
                },
                'lots_mode': 'custom',
                'lots_per_order': 1,
                'base_lots': 1,
                'lots_increment': 0,
                'lots_conditions': [
                    {'min': -20, 'max': 200, 'buy_array': [1,2,3,4,5,6,7,8,9,10], 'sell_array': [1,2,3,4,5,6,7,8,9,10]},
                    {'min': -200, 'max': -20, 'buy_array': [1,2,3,4,5,6,7,8,9,10], 'sell_array': [0,1,2,3,4,5,6,7,8,9]},
                ],
                'lots_default': [1] * 10,
                'run_at': {'weekdays': '09:01', 'weekend': '10:01'},
            },
            {
                    'account': 'acc1',
                    'figi': 'FUTNGM092600',
                    'ticker': 'NRU6',
                    'step': 0.010,
                    'offset_buy': 0.001,
                    'offset_sell': 0.001,
                    'total_orders': 10,
                    'interval': None,
                    'min_qty': None,
                    'max_qty': None,
                    'trade_hours': {
                        'start': 9,
                        'end': 23,
                        'end_minute': 30,
                        'skip_hours': [(9, 50, 10, 0)],
                    },
                    'lots_mode': 'custom',
                    'lots_per_order': 1,
                    'base_lots': 1,
                    'lots_increment': 0,
                    'lots_conditions': [
                        {'min': -20, 'max': 200, 'buy_array': [1,2,3,4,5,6,7,8,9,10], 'sell_array': [1,2,3,4,5,6,7,8,9,10]},
                        {'min': -200, 'max': -20, 'buy_array': [1,2,3,4,5,6,7,8,9,10], 'sell_array': [0,1,2,3,4,5,6,7,8,9]},
                    ],
                    'lots_default': [1] * 10,
                    'run_at': {'weekdays': '09:01', 'weekend': '10:01'},
                },

    {
        'account': 'acc1',
        'figi': 'FUTNGM052600',
        'ticker': 'NRK6',
        'step': 0.002,
        'offset_buy': 0.002,
        'offset_sell': 0.002,
        'total_orders': 20,
        'interval': 1200,
        'min_qty': None,
        'max_qty': None,
        'trade_hours': {
            'start': 9,
            'end': 23,
            'end_minute': 30,
            'skip_hours': [(9, 50, 10, 0)],
        },
        'lots_mode': 'custom',
        'lots_conditions': [
            {'min': -20, 'max': 300, 'buy_array': [1,2,3,4,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5], 'sell_array': [1,2,3,4,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5]},
            {'min': -200, 'max': -20, 'buy_array': [1,2,3,4,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5], 'sell_array': [0,0,1,2,3,4,5,5,5,5,5,5,5,5,5,5,5,5,5,5]},
        ],
        'lots_default': [1] * 20,
        'run_at': {'weekdays': '09:01', 'weekend': '10:01'},
    },
    {
        'account': 'gasA',
        'figi': 'FUTNGM042600',
        'ticker': 'NRJ6',
        'step': 0.001,
        'offset_buy': 0.005,
        'offset_sell': 0.005,
        'total_orders': 60,
        'interval': 6000,
        'min_qty': None,
        'max_qty': None,
        'trade_hours': {
            'start': 9,
            'end': 23,
            'end_minute': 30,
            'skip_hours': [(9, 50, 10, 0)],
        },
        'lots_mode': 'fixed',
        'lots_per_order': 1,
        'base_lots': 3,
        'lots_increment': 1,
        'lots_conditions': [],
        'lots_default': [1] * 60,
        'run_at': None,
    },

    {
        'account': 'gasB',
        'figi': 'FUTNGM042600',
        'ticker': 'NRJ6',
        'step': 0.001,
        'offset_buy': 0.002,
        'offset_sell': 0.002,
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
        'lots_mode': 'fixed',
        'lots_per_order': 1,
        'base_lots': 3,
        'lots_increment': 1,
        'lots_conditions': [],
        'lots_default': [1] * 60,
        'run_at': None,
    },
]
