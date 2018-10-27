from django.conf.urls import url
from . import views
from rest_framework.routers import DefaultRouter

urlpatterns = [
    url(r'^orders/settlement/$', views.OrderSettlementView.as_view()),
    # url(r'^orders/$', views.SaveOrderView.as_view()),
    url(r'^orders/(?P<order_id>\d+)/uncommentgoods/$', views.UncommentOrderGoodsView.as_view()),  # 未评论商品
    url(r'^orders/(?P<order_id>\d+)/comments/$', views.OrderCommentView.as_view()),  # 商品评论
]
router = DefaultRouter()
router.register(r'orders', views.OrderViewSet, base_name='orders')

urlpatterns += router.urls