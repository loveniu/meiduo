from django.conf.urls import url
from . import views

urlpatterns = [
    url('cart/$', views.CartView.as_view()),
]
