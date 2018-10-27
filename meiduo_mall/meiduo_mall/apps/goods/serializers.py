from rest_framework import serializers
from .models import SKU, GoodsCategory, GoodsChannel
from drf_haystack.serializers import HaystackSerializer
from .search_indexes import SKUIndex
from orders.models import OrderGoods

class SKUSerializer(serializers.ModelSerializer):
    """
    SKU序列化器
    """

    class Meta:
        model = SKU
        fields = ('id', 'name', 'price', 'default_image_url', 'comments')


class SKUIndexSerializer(HaystackSerializer):
    """
    SKU索引结果数据序列化器
    """

    class Meta:
        index_classes = [SKUIndex]
        fields = ('text', 'id', 'name', 'price', 'default_image_url', 'comments')


class CategorySerializer(serializers.ModelSerializer):
    """
    类别序列化器
    """

    class Meta:
        model = GoodsCategory
        fields = ('id', 'name')


class ChannelSerializer(serializers.ModelSerializer):
    """
    频道序列化器
    """
    category = CategorySerializer()

    class Meta:
        model = GoodsChannel
        fields = ('category', 'url')


class SKUCommentSerializer(serializers.ModelSerializer):
    """
    商品评论数据序列化器
    """
    username = serializers.CharField(label='用户名')

    class Meta:
        model = OrderGoods
        fields = ('score', 'comment', 'username')
