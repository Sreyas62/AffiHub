from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.core.cache import cache
from django.db.models import Q, Count, Sum
from .models import Product, Category
from .serializers import (
    ProductSerializer, ProductCreateSerializer, ProductUpdateSerializer,
    ProductListSerializer, CategorySerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing product categories."""
    
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter categories based on search and active status."""
        queryset = Category.objects.all()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Search functionality
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('name')


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for managing products with comprehensive CRUD operations."""
    
    queryset = Product.objects.select_related('merchant', 'category').all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ProductCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ProductUpdateSerializer
        elif self.action == 'list':
            return ProductListSerializer
        return ProductSerializer

    def get_queryset(self):
        """Filter products based on various parameters with caching."""
        cache_key = f"products_queryset_{self.request.user.id}_{hash(str(self.request.query_params))}"
        cached_queryset = cache.get(cache_key)
        
        if cached_queryset is None:
            queryset = Product.objects.select_related('merchant', 'category').all()
            
            # Filter by merchant (for merchants to see only their products)
            if self.request.user.is_merchant:
                merchant_filter = self.request.query_params.get('all', None)
                if not merchant_filter:
                    queryset = queryset.filter(merchant=self.request.user)
            
            # Filter by category
            category = self.request.query_params.get('category', None)
            if category:
                queryset = queryset.filter(category_id=category)
            
            # Filter by merchant
            merchant = self.request.query_params.get('merchant', None)
            if merchant:
                queryset = queryset.filter(merchant_id=merchant)
            
            # Filter by active status
            is_active = self.request.query_params.get('is_active', None)
            if is_active is not None:
                queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
            # Price range filtering
            min_price = self.request.query_params.get('min_price', None)
            max_price = self.request.query_params.get('max_price', None)
            if min_price:
                queryset = queryset.filter(price__gte=min_price)
            if max_price:
                queryset = queryset.filter(price__lte=max_price)
            
            # Commission rate filtering
            min_commission = self.request.query_params.get('min_commission', None)
            if min_commission:
                queryset = queryset.filter(commission_rate__gte=min_commission)
            
            # Search functionality
            search = self.request.query_params.get('search', None)
            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) |
                    Q(description__icontains=search) |
                    Q(sku__icontains=search)
                )
            
            # Ordering
            ordering = self.request.query_params.get('ordering', '-created_at')
            queryset = queryset.order_by(ordering)
            
            # Cache for 5 minutes
            cache.set(cache_key, queryset, 300)
            return queryset
        
        return cached_queryset

    def perform_create(self, serializer):
        """Set the merchant to the current user when creating a product."""
        if not self.request.user.is_merchant:
            raise permissions.PermissionDenied("Only merchants can create products.")
        serializer.save(merchant=self.request.user)

    def perform_update(self, serializer):
        """Ensure only the product owner can update."""
        product = self.get_object()
        if product.merchant != self.request.user and not self.request.user.is_superuser:
            raise permissions.PermissionDenied("You can only update your own products.")
        serializer.save()

    def perform_destroy(self, instance):
        """Delete the product and clear relevant cache."""
        if instance.merchant != self.request.user and not self.request.user.is_superuser:
            raise PermissionDenied("You can only delete your own products.")
        
        # Invalidate cache before deletion
        self._invalidate_product_cache(instance)
        instance.delete()
    
    def _invalidate_product_cache(self, product):
        """Invalidate all cache entries related to a product."""
        from django.core.cache import cache
        from django.core.cache.utils import make_template_fragment_key
        
        # Invalidate individual product cache
        cache.delete(f'product_{product.id}')
        
        # Invalidate product list caches
        cache.delete_many(cache.keys(f'products_queryset_*'))
        
        # Invalidate popular products
        cache.delete('popular_products')

    @action(detail=False, methods=['get'])
    def my_products(self, request):
        """Get products belonging to the current merchant."""
        if not request.user.is_merchant:
            return Response(
                {'error': 'Only merchants can access this endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        products = Product.objects.filter(merchant=request.user)
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular products based on affiliate link count."""
        cache_key = "popular_products"
        cached_products = cache.get(cache_key)
        
        if cached_products is None:
            products = Product.objects.filter(is_active=True).annotate(
                links_count=Count('affiliate_links')
            ).order_by('-links_count')[:10]
            
            serializer = ProductListSerializer(products, many=True)
            cached_products = serializer.data
            cache.set(cache_key, cached_products, 3600)  # Cache for 1 hour
        
        return Response(cached_products)

    @action(detail=False, methods=['get'])
    def high_commission(self, request):
        """Get products with high commission rates."""
        min_rate = request.query_params.get('min_rate', 15.0)
        products = Product.objects.filter(
            is_active=True,
            commission_rate__gte=min_rate
        ).order_by('-commission_rate')
        
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get analytics for a specific product."""
        product = self.get_object()
        
        # Check permissions
        if product.merchant != request.user and not request.user.is_superuser:
            return Response(
                {'error': 'You can only view analytics for your own products'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        analytics = {
            'product_id': product.id,
            'product_name': product.name,
            'total_affiliate_links': product.get_affiliate_links_count(),
            'total_clicks': product.get_total_clicks(),
            'total_conversions': product.get_total_conversions(),
            'conversion_rate': 0,
            'total_commission_paid': 0
        }
        
        # Calculate conversion rate
        if analytics['total_clicks'] > 0:
            analytics['conversion_rate'] = (
                analytics['total_conversions'] / analytics['total_clicks']
            ) * 100
        
        # Calculate total commission paid
        total_commission = sum(
            conversion.commission.amount 
            for link in product.affiliate_links.all()
            for conversion in link.conversions.all()
            if hasattr(conversion, 'commission')
        )
        analytics['total_commission_paid'] = total_commission
        
        return Response(analytics)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get overall product statistics."""
        cache_key = f"product_stats_{request.user.id}"
        cached_stats = cache.get(cache_key)
        
        if cached_stats is None:
            if request.user.is_merchant:
                # Stats for merchant's products
                queryset = Product.objects.filter(merchant=request.user)
            else:
                # Stats for all products (for affiliates)
                queryset = Product.objects.filter(is_active=True)
            
            stats = {
                'total_products': queryset.count(),
                'active_products': queryset.filter(is_active=True).count(),
                'average_price': queryset.aggregate(avg_price=Sum('price'))['avg_price'] or 0,
                'average_commission_rate': queryset.aggregate(
                    avg_commission=Sum('commission_rate')
                )['avg_commission'] or 0,
            }
            
            # Calculate average commission rate properly
            if stats['total_products'] > 0:
                stats['average_commission_rate'] = stats['average_commission_rate'] / stats['total_products']
            
            cache.set(cache_key, stats, 1800)  # Cache for 30 minutes
            cached_stats = stats
        
        return Response(cached_stats)
