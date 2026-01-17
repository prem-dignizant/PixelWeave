from django.urls import path 
from .views import (
    RegisterAPIView, LoginAPIView, UserProfileAPIView, HealthCheck,
    CreateCheckoutSessionAPIView, StripeWebhookView
)

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('profile/', UserProfileAPIView.as_view(), name='profile'),
    path('payment/create-checkout/', CreateCheckoutSessionAPIView.as_view(), name='create-checkout'),
    path('payment/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
]
