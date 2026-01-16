from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserSerializer
from pixelweave_app.utils import wrap_response

class HealthCheck(APIView):
    def get(self, request):
        return wrap_response(True, "service_running")

class RegisterAPIView(APIView):
    """
    API view for user registration
    POST: Register a new user and return JWT tokens
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Serialize user data
            user_serializer = UserSerializer(user)
            
            return wrap_response(success=True, code="user_registered", data={
                'user': user_serializer.data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            })
        
        return wrap_response(success=False, code="invalid_data", message=serializer.errors)


class LoginAPIView(APIView):
    """
    API view for user login
    POST: Authenticate user and return JWT tokens
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Serialize user data
            user_serializer = UserSerializer(user)
            
            return wrap_response(success=True, code="login_successful", data={
                'user': user_serializer.data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            })
        
        return wrap_response(success=False, code="invalid_data", message=serializer.errors)


class UserProfileAPIView(APIView):
    """
    API view to get authenticated user profile
    GET: Return current user details
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return wrap_response(success=True, code="user_profile", data=serializer.data)
