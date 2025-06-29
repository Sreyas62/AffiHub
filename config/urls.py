
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

def health_check(request):
    return JsonResponse({'status': 'healthy', 'message': 'API is running'})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    
    # JWT Authentication endpoints
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # API endpoints
    path('api/users/', include('users.urls')),
    path('api/products/', include('products.urls')),
    path('api/tracking/', include('tracking.urls')),
    path('api/', include('commissions.urls')),
]
