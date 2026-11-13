import aiohttp
from datetime import datetime, timedelta, timezone

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
    
    def __init__(self, token=None):
        import ssl
        self.account_id = None
        self.token = token or TOKEN
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
    
    # Внутренний метод для HTTP запросов к API
    async def _request(self, method, url, data=None):
        headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
        connector = aiohttp.TCPConnector(ssl=self.ssl_context)
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
            # FUT и FNGM — газ (обычный и мини), 3 знака; остальные — 2
            price_str = f"{price:.3f}" if (figi.startswith('FUT') or figi.startswith('FNG')) else f"{price:.2f}"
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
        units = int(price_dict.get('units', 0) or 0)
        nano = int(price_dict.get('nano', 0) or 0)
        sign = -1 if units < 0 or nano < 0 else 1
        return sign * (abs(units) + abs(nano) / 1_000_000_000)
    
    # Получить позицию по инструменту (баланс + заблокировано)
    async def get_position(self, figi):
        if not self.account_id:
            await self.get_account_id()
        data = await self._request('GetPositions', f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.OperationsService/GetPositions', {'accountId': self.account_id})
        for pos in data.get('futures', []):
            if pos.get('figi') == figi:
                return int(pos.get('balance', 0)) + int(pos.get('blocked', 0))
        return 0
    
    # Получить последнюю цену (это последняя СДЕЛКА, а не цена закрытия!)
    async def get_last_price(self, figi):
        data = await self._request('GetLastPrices', f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.MarketDataService/GetLastPrices', {'figi': [figi]})
        prices = data.get('lastPrices', [])
        if prices:
            return self._parse_price(prices[0].get('price', {}))
        return None

    # Получить цену закрытия предыдущего торгового дня (именно close дневной свечи)
    async def get_prev_close(self, figi):
        now = datetime.now(timezone.utc)
        data = await self._request('GetCandles',
            f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.MarketDataService/GetCandles',
            {
                'figi': figi,
                'from': (now - timedelta(days=14)).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'to': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'interval': 'CANDLE_INTERVAL_DAY',
            })
        candles = data.get('candles') or []
        # Дневная свеча датируется началом торгового дня (00:00Z), сегодняшняя ещё не закрыта — пропускаем её
        today_moscow = (now + timedelta(hours=3)).date().isoformat()
        for candle in reversed(candles):
            if str(candle.get('time', ''))[:10] >= today_moscow:
                continue
            price = self._parse_price(candle.get('close') or {})
            if price:
                return price
        return None

    # Разобрать ISO-время из REST (суффикс Z, до 9 знаков дробной части)
    def _parse_time(self, value):
        if not value:
            return None
        s = str(value).strip().replace('Z', '+00:00')
        if '.' in s:
            base, rest = s.split('.', 1)
            i = 0
            while i < len(rest) and rest[i].isdigit():
                i += 1
            s = f"{base}.{(rest[:i] + '000000')[:6]}{rest[i:]}"
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            return None

    # Получить цену последней СВОЕЙ исполненной сделки по инструменту (любой давности)
    async def get_last_trade_price(self, figi):
        if not self.account_id:
            await self.get_account_id()
        trade_types = [
            'OPERATION_TYPE_BUY', 'OPERATION_TYPE_SELL',
            'OPERATION_TYPE_BUY_CARD', 'OPERATION_TYPE_SELL_CARD',
        ]
        cursor = None
        best_time = None
        best_price = None
        fallback_time = None
        fallback_price = None
        empty_pages = 0

        # ВАЖНО: item['date'] — это дата ПОРУЧЕНИЯ, а не исполнения. Заявка, выставленная
        # давно и исполненная сейчас, остаётся на старом месте в списке. Поэтому реальную
        # дату и цену исполнения берём из tradesInfo.trades — у каждой сделки своя дата.
        for _ in range(100):
            payload = {
                'accountId': self.account_id,
                'instrumentId': figi,
                'limit': 1000,
                'operationTypes': trade_types,
            }
            if cursor:
                payload['cursor'] = cursor
            data = await self._request('GetOperationsByCursor',
                f'{BASE_URL}/rest/tinkoff.public.invest.api.contract.v1.OperationsService/GetOperationsByCursor',
                payload)

            found_new = False
            for item in data.get('items', []):
                trades = ((item.get('tradesInfo') or {}).get('trades') or [])
                for trade in trades:
                    trade_time = self._parse_time(trade.get('date'))
                    price = self._parse_price(trade.get('price') or {})
                    if trade_time and price and (best_time is None or trade_time > best_time):
                        best_time, best_price = trade_time, price
                        found_new = True

                # Старые операции могут прийти без tradesInfo — берём цену поручения как fallback
                if not trades and item.get('state') == 'OPERATION_STATE_EXECUTED':
                    item_time = self._parse_time(item.get('date'))
                    price = self._parse_price(item.get('price') or {})
                    if item_time and price and (fallback_time is None or item_time > fallback_time):
                        fallback_time, fallback_price = item_time, price

            # Останавливаемся, когда уже нашли исполнение и ещё 2 страницы (около 20 дней
            # при лимите 1000) не дали ничего новее. Если исполнений не было — идём до конца.
            if found_new:
                empty_pages = 0
            elif best_price:
                empty_pages += 1
                if empty_pages >= 2:
                    break

            if not data.get('hasNext'):
                break
            cursor = data.get('nextCursor')
            if not cursor:
                break

        return best_price or fallback_price

    # Получить текстовый статус (для HTTP)
    async def status_text(self, figi):
        orders = await self.get_orders(figi)
        pos = await self.get_position(figi)
        return f'Orders: {len(orders)}, position: {pos}'
