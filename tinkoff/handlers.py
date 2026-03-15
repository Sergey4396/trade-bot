import aiohttp

HTTP_PASSWORD = None


def init(password):
    global HTTP_PASSWORD
    HTTP_PASSWORD = password


async def handle_cancel_all(request, api):
    from balance_strategy import FIGI
    if request.query.get('password', '') != HTTP_PASSWORD:
        return aiohttp.web.Response(text='Unauthorized', status=401)
    orders = await api.get_orders(FIGI)
    for order in orders:
        await api.cancel_order(order.get('orderId', ''))
    return aiohttp.web.Response(text=f'Cancelled {len(orders)} orders', status=200)


async def handle_status(request, api):
    from balance_strategy import FIGI
    return aiohttp.web.Response(text=await api.status_text(FIGI), status=200)


async def handle_health(request):
    return aiohttp.web.Response(text='OK', status=200)
