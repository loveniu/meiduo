from django.conf.urls import url
from . import views
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register('skus/search', views.SKUSearchViewSet, base_name='skus_search')
urlpatterns = [
    url(r'^categories/(?P<category_id>\d+)/hotskus/$', views.HotSKUListView.as_view()),
    url(r'^categories/(?P<category_id>\d+)/skus/$', views.SKUListView.as_view()),
    url(r'^categories/(?P<pk>\d+)/$', views.CategoryView.as_view()), # 列表页三级类别显示
    url(r'^skus/(?P<sku_id>\d+)/comments/$', views.SKUCommentsListView.as_view()), # 商品评价
]
urlpatterns += router.urls
