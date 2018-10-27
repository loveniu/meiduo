from django.shortcuts import render
from rest_framework.viewsets import ReadOnlyModelViewSet
from .models import Area
from . import serializers
from rest_framework_extensions.cache.mixins import CacheResponseMixin

# Create your views here.
# 不加缓存形式
# class AreasViewSet(ReadOnlyModelViewSet):
#     def get_queryset(self):
#         if self.action == 'list':
#             return Area.objects.filter(parent=None)
#         return Area.objects.all()
#
#     def get_serializer_class(self):
#         if self.action == 'list':
#             return serializers.AreaSerialier
#         return serializers.SubAreaSerializer

# 添加缓存形式


class AreasViewSet(CacheResponseMixin, ReadOnlyModelViewSet):
    """
    list:
    返回所有省份的信息

    retrieve:
    返回特定省或市的下属行政规划区域
    """
    # 关闭分页处理
    pagination_class = None  # 不设置分页

    # queryset = Area.objects.all()
    def get_queryset(self):
        if self.action == 'list':
            return Area.objects.filter(parent=None)
        else:
            return Area.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.AreaSerialier
        else:
            return serializers.SubAreaSerializer
