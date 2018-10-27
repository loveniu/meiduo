from rest_framework import serializers

from .models import Area


class AreaSerialier(serializers.ModelSerializer):
    """行政区域信息序列化器"""
    class Meta:
        model = Area
        fields = ('id', 'name')


class SubAreaSerializer(serializers.ModelSerializer):
    """
    子级行政区划信息
    """
    subs = AreaSerialier(many=True, read_only=True) # 关联对象的序列化

    class Meta:
        model = Area
        fields = ('id', 'name', 'subs')