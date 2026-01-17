from django.urls import path
from .views import WardrobeAPIView, MockupAPIView

urlpatterns = [
    path('wardrobe/', WardrobeAPIView.as_view(), name='wardrobe'),
    path('mockup/', MockupAPIView.as_view(), name='mockup'),
]
