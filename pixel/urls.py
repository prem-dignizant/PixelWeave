from django.urls import path
from .views import WardrobeAPIView

urlpatterns = [
    path('wardrobe/', WardrobeAPIView.as_view(), name='wardrobe'),
]
