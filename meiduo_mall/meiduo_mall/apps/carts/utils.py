
import pickle
import base64
from django_redis import get_redis_connection


def merge_cart_cookie_to_redis(request, user, response):
    """
    合并请求用户的购物车数据，将未登录保存在cookie里的保存到redis中
    :param request: 用户的请求对象
    :param user: 当前登录的用户
    :param response: 响应对象，用于清楚购物车cookie
    :return:
    """
    cookie_cart = request.COOKIES.get('cart')
    print(cookie_cart)
    if cookie_cart is not None:
        cookie_cart = pickle.loads(base64.b64decode(cookie_cart.encode()))
        redis_conn = get_redis_connection('cart')
        redis_cart = redis_conn.hgetall('cart_%s' % user.id)
        redis_cart_selected = redis_conn.smembers('cart_selected_%s' % user.id)
        cart = {}
        for sku_id, count in redis_cart.items():
            cart[int(sku_id)] = int(count)

        for sku_id, count_selected_dict in cookie_cart.items():
            cart[sku_id] = count_selected_dict['count']
            if count_selected_dict['selected']:
                redis_cart_selected.add(sku_id)

        if cart:
            pl = redis_conn.pipeline()
            pl.hmset('cart_%s' % user.id, cart)
            pl.sadd('cart_selected_%s' % user.id, *redis_cart_selected)
            pl.execute()

        response.delete_cookie('cart')
        print('删除cookie成功')
    return response