from rest_framework import serializers
from .models import Wardrobe, Studio


class WardrobeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wardrobe
        fields = ['id', 'user', 'image', 'bg_color', 'created', 'modified', 'status', 'error_message']
        read_only_fields = ['id', 'created', 'modified', 'user', 'status', 'error_message']


class WardrobeCreateSerializer(serializers.Serializer):
    """Serializer for creating a wardrobe with input image and color"""
    input_image = serializers.ImageField(required=True)
    bg_color = serializers.CharField(max_length=128)


# Studio Nested Serializers
class BackgroundSerializer(serializers.Serializer):
    """Nested serializer for background parameters"""
    location = serializers.CharField(max_length=255, required=False, allow_blank=True)
    lighting = serializers.CharField(max_length=255, required=False, allow_blank=True)


class ModelSerializer(serializers.Serializer):
    """Nested serializer for model parameters"""
    gender = serializers.ChoiceField(choices=['male', 'female', 'unisex'], required=True)
    age_group = serializers.CharField(max_length=50, required=False, allow_blank=True)
    model_region = serializers.CharField(max_length=100, required=False, allow_blank=True)
    model_color = serializers.CharField(max_length=100, required=False, allow_blank=True)
    model_type = serializers.CharField(max_length=100, required=False, allow_blank=True)
    mood = serializers.CharField(max_length=100, required=False, allow_blank=True)
    body_type = serializers.CharField(max_length=100, required=False, allow_blank=True)
    hair_style = serializers.CharField(max_length=100, required=False, allow_blank=True)
    hair_color = serializers.CharField(max_length=100, required=False, allow_blank=True)
    pose = serializers.CharField(max_length=255, required=False, allow_blank=True)


class ExtraSerializer(serializers.Serializer):
    """Nested serializer for extra parameters"""
    camera_angle = serializers.CharField(max_length=255, required=False, allow_blank=True)
    style = serializers.CharField(max_length=255, required=False, allow_blank=True)


class StudioCreateSerializer(serializers.Serializer):
    """Serializer for creating a studio mockup"""
    # Image source (either direct upload or from wardrobe)
    input_image = serializers.ImageField(required=False)
    wardrobe_id = serializers.IntegerField(required=False)
    
    # Required fields
    garment_type = serializers.CharField(max_length=100, required=True)
    image_size = serializers.CharField(max_length=50, required=True)
    
    # Nested parameters as JSON - works with form-data
    background = serializers.JSONField(required=False, default=dict)
    model = serializers.JSONField(required=True)
    extra = serializers.JSONField(required=False, default=dict)
    
    def validate_background(self, value):
        """Validate background parameters"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Background must be a valid JSON object")
        
        # Validate optional string fields
        allowed_fields = ['location', 'lighting']
        for field in value.keys():
            if field not in allowed_fields:
                raise serializers.ValidationError(f"Unknown field '{field}' in background")
            if not isinstance(value[field], str):
                raise serializers.ValidationError(f"{field} must be a string")
        
        return value
    
    def validate_model(self, value):
        """Validate model parameters - gender is required"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Model must be a valid JSON object")
        
        # Validate required gender field
        if 'gender' not in value:
            raise serializers.ValidationError("'gender' is required in model parameters")
        
        if value['gender'] not in ['male', 'female', 'unisex']:
            raise serializers.ValidationError("gender must be one of: male, female, unisex")
        
        # Validate optional fields
        allowed_fields = [
            'gender', 'age_group', 'model_region', 'model_color', 
            'model_type', 'mood', 'body_type', 'hair_style', 
            'hair_color', 'pose'
        ]
        
        for field in value.keys():
            if field not in allowed_fields:
                raise serializers.ValidationError(f"Unknown field '{field}' in model")
            if not isinstance(value[field], str):
                raise serializers.ValidationError(f"{field} must be a string")
        
        return value
    
    def validate_extra(self, value):
        """Validate extra parameters"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Extra must be a valid JSON object")
        
        # Validate optional string fields
        allowed_fields = ['camera_angle', 'style']
        for field in value.keys():
            if field not in allowed_fields:
                raise serializers.ValidationError(f"Unknown field '{field}' in extra")
            if not isinstance(value[field], str):
                raise serializers.ValidationError(f"{field} must be a string")
        
        return value
    
    def validate(self, data):
        """Ensure either input_image or wardrobe_id is provided"""
        input_image = data.get('input_image')
        wardrobe_id = data.get('wardrobe_id')
        
        if not input_image and not wardrobe_id:
            raise serializers.ValidationError(
                "Either 'input_image' or 'wardrobe_id' must be provided"
            )
        
        if input_image and wardrobe_id:
            raise serializers.ValidationError(
                "Provide either 'input_image' or 'wardrobe_id', not both"
            )
        
        return data


class StudioSerializer(serializers.ModelSerializer):
    """Serializer for Studio model responses"""
    class Meta:
        model = Studio
        fields = ['id', 'user', 'wardrobe', 'image', 'mockup', 'status', 'error_message', 'created', 'modified']
        read_only_fields = ['id', 'created', 'modified', 'user', 'status', 'error_message']
