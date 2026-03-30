import aiohttp

TOKEN = None
BASE_URL = 'https://invest-public-api.tbank.ru'

ssl_context = None


# Инициализация API: токен и базовый URL
def init(token, base_url='https://invest-public-api.tbank.ru'):
    global TOKEN, BASE_URL, ssl_context
    import ssl
    TOKEN = token
    BASE_URL = base_url
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE


# Обёртка над Tinkoff Invest API
class TinkoffAPI:
    
    def __init__(self):
        self.account_id = None
    
    # Внутренний метод для HTTP запросов к API
    async def _request(self, method, url, data=None):
        headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(url, json=data or {}, headers=headers) as resp:
                return await resp.json()
    
    # Получить ID счёта
    async def get_account_id(self):
        data = await self._request('GetAccounts', f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.UsersService/GetAccounts')
        accounts = data.get('accounts', [])
        if accounts:
            self.account_id = accounts[0]['id']
        return self.account_id
    
    # Получить список активных заявок
    # figi: если указан - фильтрует только по этому инструменту
    async def get_orders(self, figi=None):
        if not self.account_id:
            await self.get_account_id()
        data = await self._request('GetOrders', f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.OrdersService/GetOrders', {'accountId': self.account_id})
        orders = data.get('orders', [])
        if figi:
            orders = [o for o in orders if o.get('figi') == figi]
        return orders
    
    # Отменить заявку по ID
    async def cancel_order(self, order_id):
        if not self.account_id:
            await self.get_account_id()
        return await self._request('CancelOrder', f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.OrdersService/CancelOrder', {'accountId': self.account_id, 'orderId': order_id})
    
    # Выставить заявку
    # figi: идентификатор инструмента
    # quantity: количество лотов
    # direction: 'ORDER_DIRECTION_BUY' или 'ORDER_DIRECTION_SELL'
    # price: цена (для лимитных заявок)
    async def post_order(self, figi, quantity, direction, price=None):
        if not self.account_id:
            await self.get_account_id()
        order_data = {'figi': figi, 'quantity': str(quantity), 'direction': direction, 'accountId': self.account_id, 'orderType': 'ORDER_TYPE_LIMIT'}
        if price:
            price_str = f"{price:.3f}" if figi.startswith('FUT') else f"{price:.2f}"
            parts = price_str.split('.')
            order_data['price'] = {'units': int(parts[0]), 'nano': int(parts[1].ljust(9, '0')[:9])}
        return await self._request('PostOrder', f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.OrdersService/PostOrder', order_data)
    
    # Получить цену фьючерса из стакана (среднее между bid и ask)
    async def get_futures_price(self, figi):
        data = await self._request('GetOrderBook', f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.MarketDataService/GetOrderBook', {'figi': figi, 'depth': 1})
        bids, asks = data.get('bids', []), data.get('asks', [])
        if bids and asks:
            return (self._parse_price(bids[0].get('price', {})) + self._parse_price(asks[0].get('price', {}))) / 2
        return None
    
    # Получить лучшие цены bid и ask из стакана
    async def get_orderbook_prices(self, figi):
        data = await self._request('GetOrderBook', f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.MarketDataService/GetOrderBook', {'figi': figi, 'depth': 1})
        bids, asks = data.get('bids', []), data.get('asks', [])
        best_bid = self._parse_price(bids[0].get('price', {})) if bids else None
        best_ask = self._parse_price(asks[0].get('price', {})) if asks else None
        return best_bid, best_ask
    
    # Конвертировать цену из units/nano в float
    def _parse_price(self, price_dict):
        units, nano = price_dict.get('units', 0), price_dict.get('nano', 0)
        return float(f"{units}.{str(nano // 1000000).zfill(3)}")
    
    # Получить позицию по инструменту (баланс + заблокировано)
    async def get_position(self, figi):
        if not self.account_id:
            await self.get_account_id()
        data = await self._request('GetPositions', f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.OperationsService/GetPositions', {'accountId': self.account_id})
        for pos in data.get('futures', []):
            if pos.get('figi') == figi:
                return int(pos.get('balance', 0)) + int(pos.get('blocked', 0))
        return 0
    
    # Получить текстовый статус (для HTTP)
    async def status_text(self, figi):
        orders = await self.get_orders(figi)
        pos = await self.get_position(figi)
        return f'Orders: {len(orders)}, position: {pos}'
