import aiohttp
from api import TinkoffAPI

HTTP_PASSWORD = None
FIGI_NRH6 = TinkoffAPI.FIGI_NRH6


def init(password):
    global HTTP_PASSWORD
    HTTP_PASSWORD = password


async def handle_cancel_all(request, api):
    if request.query.get('password', '') != HTTP_PASSWORD:
        return aiohttp.web.Response(text='Unauthorized', status=401)
    orders = await api.get_orders(FIGI_NRH6)
    for order in orders:
        await api.cancel_order(order.get('orderId', ''))
    return aiohttp.web.Response(text=f'Cancelled {len(orders)} orders', status=200)


async def handle_status(request, api):
    return aiohttp.web.Response(text=await api.status_text(FIGI_NRH6), status=200)


async def handle_health(request):
    return aiohttp.web.Response(text='OK', status=200)
