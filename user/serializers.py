from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Payment


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    """
    password = serializers.CharField(write_only=True, min_length=6, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, min_length=6, style={'input_type': 'password'}, label='Confirm Password')
    
    class Meta:
        model = User
        fields = ['user_name', 'email', 'first_name', 'last_name', 'password', 'password2']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }
    
    def validate(self, attrs):
        """
        Validate that passwords match
        """
        if attrs.get('password') != attrs.get('password2'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        """
        Create and return a new user
        """
        # Remove password2 from validated data
        validated_data.pop('password2', None)
        
        # Create user
        user = User.objects.create_user(
            user_name=validated_data['user_name'],
            email=validated_data.get('email'),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_active=True,
            credit = 5
        )
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    """
    user_name = serializers.CharField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        """
        Validate and authenticate user
        """
        user_name = attrs.get('user_name')
        password = attrs.get('password')
        
        if user_name and password:
            # Authenticate user
            user = authenticate(username=user_name, password=password)
            
            if user:
                if not user.is_active:
                    raise serializers.ValidationError('User account is disabled.')
                attrs['user'] = user
                return attrs
            else:
                raise serializers.ValidationError('Unable to log in with provided credentials.')
        else:
            raise serializers.ValidationError('Must include "user_name" and "password".')


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user details
    """
    class Meta:
        model = User
        fields = ['user_id', 'user_name', 'email', 'first_name', 'last_name', 'credit', 'is_active',  'created']
        read_only_fields = ['user_id', 'credit', 'created']


class CreateCheckoutSessionSerializer(serializers.Serializer):
    """Serializer for creating Stripe checkout session"""
    amount = serializers.IntegerField()


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""
    class Meta:
        model = Payment
        fields = ['id', 'user', 'stripe_session_id', 'amount', 'credits', 'status', 'created', 'modified']
        read_only_fields = ['id', 'user', 'created', 'modified']
