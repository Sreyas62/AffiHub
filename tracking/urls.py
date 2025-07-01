from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AffiliateLinkViewSet, ClickViewSet, ConversionViewSet,
    track_click, record_conversion
)

# Create router and register viewsets
router = DefaultRouter()
router.register('links', AffiliateLinkViewSet, basename='affiliate-links')
router.register('clicks', ClickViewSet, basename='clicks')
router.register('conversions', ConversionViewSet, basename='conversions')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Custom endpoints
    path('click/<uuid:code>/', track_click, name='track-click'),
    path('convert/<uuid:code>/', record_conversion, name='record-conversion'),
]
