from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.core.cache import cache
from django.db.models import Q
from .models import User
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer, 
    PasswordChangeSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users with CRUD operations.
    Provides endpoints for user registration, profile management, and authentication.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'login']:
            # Allow anyone to register or login
            permission_classes = [permissions.AllowAny]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Only allow users to modify their own profile
            permission_classes = [permissions.IsAuthenticated]
        else:
            # Default to authenticated users
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filter queryset based on user permissions and search parameters."""
        queryset = User.objects.all()
        
        # Cache the queryset for better performance
        cache_key = f"users_queryset_{self.request.user.id if self.request.user.is_authenticated else 'anonymous'}"
        cached_queryset = cache.get(cache_key)
        
        if cached_queryset is None:
            # Filter by role if specified
            role = self.request.query_params.get('role', None)
            if role:
                queryset = queryset.filter(role=role)
            
            # Search functionality
            search = self.request.query_params.get('search', None)
            if search:
                queryset = queryset.filter(
                    Q(username__icontains=search) |
                    Q(first_name__icontains=search) |
                    Q(last_name__icontains=search) |
                    Q(email__icontains=search)
                )
            
            # Cache the result for 5 minutes
            cache.set(cache_key, queryset, 300)
            return queryset
        
        return cached_queryset

    def perform_update(self, serializer):
        """Ensure users can only update their own profile."""
        if self.request.user != self.get_object():
            raise permissions.PermissionDenied("You can only update your own profile.")
        serializer.save()

    def perform_destroy(self, instance):
        """Ensure users can only delete their own profile."""
        if self.request.user != instance:
            raise permissions.PermissionDenied("You can only delete your own profile.")
        instance.delete()

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Get current user's profile information."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def login(self, request):
        """Authenticate user and return JWT tokens."""
        from rest_framework_simplejwt.tokens import RefreshToken
        
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Username and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(request, username=username, password=password)
        
        if user:
            refresh = RefreshToken.for_user(user)
            serializer = UserSerializer(user)
            return Response({
                'message': 'Login successful',
                'user': serializer.data,
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        """Logout current user by blacklisting refresh token."""
        from rest_framework_simplejwt.tokens import RefreshToken
        
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response(
                {'message': 'Logout successful'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        """Change user password."""
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Password changed successfully'},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def affiliates(self, request):
        """Get all affiliate users."""
        affiliates = User.objects.filter(role='affiliate')
        serializer = self.get_serializer(affiliates, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def merchants(self, request):
        """Get all merchant users."""
        merchants = User.objects.filter(role='merchant')
        serializer = self.get_serializer(merchants, many=True)
        return Response(serializer.data)
