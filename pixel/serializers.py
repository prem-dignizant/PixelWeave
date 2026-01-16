from rest_framework import serializers
from .models import Wardrobe


class WardrobeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wardrobe
        fields = ['id', 'user', 'image', 'bg_color', 'created', 'modified']
        read_only_fields = ['id', 'created', 'modified', 'user']


class WardrobeCreateSerializer(serializers.Serializer):
    """Serializer for creating a wardrobe with input image and color"""
    input_image = serializers.ImageField(required=True)
    bg_color = serializers.CharField(max_length=128)
