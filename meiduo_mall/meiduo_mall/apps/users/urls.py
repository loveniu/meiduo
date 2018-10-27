from django.conf.urls import url
from . import views
from rest_framework_jwt.views import obtain_jwt_token
from rest_framework.routers import DefaultRouter

urlpatterns = [
    url(r'^usernames/(?P<username>\w{5,20})/count/$', views.UsernameCountView.as_view()),  # 重名检测
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),  # 手机号检测
    url(r'^users/$', views.UserView.as_view()),  # 注册
    # url(r'authorizations/', obtain_jwt_token, name='authorizations'),  # 登录，获取JWT token
    url(r'authorizations/', views.UserAuthorizeView.as_view(), name='authorizations'),  # 登录，获取JWT token,合并购物车
    url(r'^accounts/(?P<account>\w{4,20})/sms/token/$', views.SMSCodeTokenView.as_view()),  # 获取发送短信验证码的token
    url(r'^accounts/(?P<account>\w{4,20})/password/token/$', views.PasswordTokenView.as_view()),  # 获取修改密码的token
    url(r'users/(?P<pk>\d+)/password/$', views.PasswordView.as_view()),  # 重置密码
    url(r'^user/$', views.UserDetailView.as_view()),  # 用户个人中心数据
    url(r'^emails/$', views.EmailView.as_view()),  # 用户个人中心数据邮箱设置接口
    url(r'^emails/verification/$', views.EmailVerifyView.as_view()),  # 用户个人中心邮箱激活接口
    url(r'^browse_histories/$', views.UserBrowsingHistoryView.as_view()),  # 用户浏览历史记录

]

router = DefaultRouter()
router.register('addresses', views.AddressViewSet, base_name='addresses')
urlpatterns += router.urls
