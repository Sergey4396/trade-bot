import aiohttp
import os
from urllib.parse import quote

TOKEN = os.environ.get('FINAM_TOKEN', '')
BASE_URL = 'https://api.finam.ru'

ssl_context = None

# Известный account_id
KNOWN_ACCOUNT_ID = '1060e31a-5a84-4dc1-b0ca-d1e6b8c427e6'


def init(token, base_url='https://api.finam.ru'):
    global TOKEN, BASE_URL, ssl_context
    import ssl
    TOKEN = token
    BASE_URL = base_url
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE


class FinamAPI:
    # Настройки инструмента
    SYMBOL = 'NRH6@MOEX'  # тикер
    
    def __init__(self):
        self.account_id = KNOWN_ACCOUNT_ID
    
    # Внутренний метод для HTTP запросов к API
    async def _request(self, method, url, data=None):
        headers = {
            'Authorization': f'Bearer {TOKEN}',
            'Content-Type': 'application/json',
            'User-Agent': 'TradeBot/1.0'
        }
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(url, json=data or {}, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    text = await resp.text()
                    print(f"API Error {resp.status}: {text}")
                    return {}
    
    # Получить ID счёта (используем известный)
    async def get_account_id(self):
        self.account_id = KNOWN_ACCOUNT_ID
        return self.account_id
    
    # Получить последние сделки (через стакан - лучший bid/ask)
    async def get_latest_trades(self):
        if not self.account_id:
            await self.get_account_id()
        # Используем URL-encoded символ
        symbol_encoded = quote(self.SYMBOL, safe='')
        
        # Пробуем разные endpoints
        endpoints = [
            f'{BASE_URL}/api/v1/marketdata/{symbol_encoded}/orderbook',
            f'{BASE_URL}/api/v1/instruments/{symbol_encoded}/orderbook',
            f'{BASE_URL}/api/v1/orderbook/{symbol_encoded}',
        ]
        
        for url in endpoints:
            print(f"Trying: {url}")
            data = await self._request('OrderBook', url)
            if data:
                break
        else:
            data = {}
        
        # Получаем лучшие цены из стакана
        bids = data.get('bids', [])
        asks = data.get('asks', [])
        
        # Эмулируем сделки на основе стакана
        trades = []
        if bids:
            for b in bids[:2]:
                price_val = b.get('price', {}).get('value', '0')
                trades.append({
                    'trade_id': f"bid_{price_val}",
                    'price': {'value': price_val},
                    'size': {'value': str(b.get('volume', 1))},
                    'side': 'buy'
                })
        if asks:
            for a in asks[:2]:
                price_val = a.get('price', {}).get('value', '0')
                trades.append({
                    'trade_id': f"ask_{price_val}",
                    'price': {'value': price_val},
                    'size': {'value': str(a.get('volume', 1))},
                    'side': 'sell'
                })
        return trades
    
    # Получить позицию
    async def get_position(self):
        if not self.account_id:
            await self.get_account_id()
        url = f'{BASE_URL}/api/v1/portfolio'
        data = await self._request('Portfolio', url)
        for pos in data.get('positions', []):
            if pos.get('symbol') == self.SYMBOL:
                return int(pos.get('balance', 0))
        return 0
    
    # Выставить заявку
    # side: 'buy' или 'sell'
    # quantity: количество
    # price: цена
    async def post_order(self, quantity, side, price):
        if not self.account_id:
            await self.get_account_id()
        url = f'{BASE_URL}/api/v1/orders'
        order_data = {
            'symbol': self.SYMBOL,
            'quantity': str(quantity),
            'side': side.upper(),
            'type': 'ORDER_TYPE_LIMIT',
            'limit_price': str(price),
            'time_in_force': 'TIME_IN_FORCE_DAY'
        }
        return await self._request('PostOrder', url, order_data)
    
    # Отменить заявку
    async def cancel_order(self, order_id):
        if not self.account_id:
            await self.get_account_id()
        url = f'{BASE_URL}/v1/accounts/{self.account_id}/orders/{order_id}'
        # Finam использует DELETE метод
        headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.delete(url, json={}, headers=headers) as resp:
                return await resp.json()
    
    # Получить текстовый статус (для HTTP)
    async def status_text(self):
        pos = await self.get_position()
        return f'Position: {pos}'
