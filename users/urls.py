from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register('', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
]
