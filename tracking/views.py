from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, redirect
from django.core.cache import cache
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.http import HttpResponse
from datetime import datetime, timedelta
import re
from .models import AffiliateLink, Click, Conversion
from .serializers import (
    AffiliateLinkSerializer, AffiliateLinkCreateSerializer,
    ClickSerializer, ConversionSerializer, ConversionCreateSerializer,
    ClickAnalyticsSerializer, ConversionAnalyticsSerializer
)


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def detect_device_type(user_agent):
    """Detect device type from user agent string."""
    if not user_agent:
        return 'unknown'
    
    user_agent = user_agent.lower()
    
    # Mobile patterns
    mobile_patterns = [
        'mobile', 'android', 'iphone', 'ipod', 'blackberry',
        'windows phone', 'palm', 'symbian'
    ]
    
    # Tablet patterns
    tablet_patterns = ['ipad', 'tablet', 'kindle']
    
    for pattern in tablet_patterns:
        if pattern in user_agent:
            return 'tablet'
    
    for pattern in mobile_patterns:
        if pattern in user_agent:
            return 'mobile'
    
    return 'desktop'


class AffiliateLinkViewSet(viewsets.ModelViewSet):
    """ViewSet for managing affiliate links."""
    
    queryset = AffiliateLink.objects.select_related('affiliate', 'product').all()
    serializer_class = AffiliateLinkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return AffiliateLinkCreateSerializer
        return AffiliateLinkSerializer

    def get_queryset(self):
        """Filter affiliate links based on user role and parameters."""
        queryset = AffiliateLink.objects.select_related('affiliate', 'product').all()
        
        # Affiliates can only see their own links
        if self.request.user.is_affiliate:
            queryset = queryset.filter(affiliate=self.request.user)
        
        # Filter by product
        product = self.request.query_params.get('product', None)
        if product:
            queryset = queryset.filter(product_id=product)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Search functionality
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(product__name__icontains=search) |
                Q(custom_slug__icontains=search) |
                Q(affiliate__username__icontains=search)
            )
        
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        """Set the affiliate to the current user when creating a link."""
        if not self.request.user.is_affiliate:
            raise permissions.PermissionDenied("Only affiliates can create affiliate links.")
        serializer.save(affiliate=self.request.user)

    def perform_update(self, serializer):
        """Ensure only the link owner can update."""
        link = self.get_object()
        if link.affiliate != self.request.user and not self.request.user.is_superuser:
            raise permissions.PermissionDenied("You can only update your own affiliate links.")
        serializer.save()

    def perform_destroy(self, instance):
        """Ensure only the link owner can delete."""
        if instance.affiliate != self.request.user and not self.request.user.is_superuser:
            raise permissions.PermissionDenied("You can only delete your own affiliate links.")
        instance.delete()

    @action(detail=False, methods=['get'])
    def my_links(self, request):
        """Get affiliate links for the current user."""
        if not request.user.is_affiliate:
            return Response(
                {'error': 'Only affiliates can access this endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        links = AffiliateLink.objects.filter(affiliate=request.user)
        serializer = self.get_serializer(links, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get analytics for a specific affiliate link."""
        link = self.get_object()
        
        # Check permissions
        if link.affiliate != request.user and not request.user.is_superuser:
            return Response(
                {'error': 'You can only view analytics for your own links'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get date range from query params
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        clicks = Click.objects.filter(affiliate_link=link, timestamp__gte=start_date)
        conversions = Conversion.objects.filter(affiliate_link=link, timestamp__gte=start_date)
        
        analytics = {
            'link_id': link.id,
            'link_code': str(link.code),
            'product_name': link.product.name,
            'total_clicks': clicks.count(),
            'unique_clicks': clicks.values('ip_address').distinct().count(),
            'total_conversions': conversions.count(),
            'total_amount': conversions.aggregate(Sum('amount'))['amount__sum'] or 0,
            'total_commission': conversions.aggregate(Sum('commission_amount'))['commission_amount__sum'] or 0,
            'conversion_rate': link.conversion_rate,
            'device_breakdown': clicks.values('device_type').annotate(count=Count('id')),
            'daily_clicks': [],
            'daily_conversions': []
        }
        
        # Generate daily data
        for i in range(days):
            date = start_date + timedelta(days=i)
            day_clicks = clicks.filter(timestamp__date=date.date()).count()
            day_conversions = conversions.filter(timestamp__date=date.date()).count()
            
            analytics['daily_clicks'].append({
                'date': date.strftime('%Y-%m-%d'),
                'clicks': day_clicks
            })
            analytics['daily_conversions'].append({
                'date': date.strftime('%Y-%m-%d'),
                'conversions': day_conversions
            })
        
        return Response(analytics)


class ClickViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing click data (read-only)."""
    
    queryset = Click.objects.select_related('affiliate_link__affiliate', 'affiliate_link__product').all()
    serializer_class = ClickSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter clicks based on user permissions."""
        queryset = Click.objects.select_related('affiliate_link__affiliate', 'affiliate_link__product').all()
        
        # Affiliates can only see clicks on their links
        if self.request.user.is_affiliate:
            queryset = queryset.filter(affiliate_link__affiliate=self.request.user)
        
        # Filter by affiliate link
        affiliate_link = self.request.query_params.get('affiliate_link', None)
        if affiliate_link:
            queryset = queryset.filter(affiliate_link_id=affiliate_link)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        return queryset.order_by('-timestamp')


class ConversionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing conversions."""
    
    queryset = Conversion.objects.select_related('affiliate_link__affiliate', 'affiliate_link__product').all()
    serializer_class = ConversionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ConversionCreateSerializer
        return ConversionSerializer

    def get_queryset(self):
        """Filter conversions based on user permissions."""
        queryset = Conversion.objects.select_related('affiliate_link__affiliate', 'affiliate_link__product').all()
        
        # Affiliates can only see conversions from their links
        if self.request.user.is_affiliate:
            queryset = queryset.filter(affiliate_link__affiliate=self.request.user)
        # Merchants can see conversions from their products
        elif self.request.user.is_merchant:
            queryset = queryset.filter(affiliate_link__product__merchant=self.request.user)
        
        # Filter by affiliate link
        affiliate_link = self.request.query_params.get('affiliate_link', None)
        if affiliate_link:
            queryset = queryset.filter(affiliate_link_id=affiliate_link)
        
        # Filter by verified status
        verified = self.request.query_params.get('verified', None)
        if verified is not None:
            queryset = queryset.filter(verified=verified.lower() == 'true')
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        return queryset.order_by('-timestamp')

    def perform_create(self, serializer):
        """Additional validation when creating conversions."""
        # Only merchants can create conversions for their products
        affiliate_link = serializer.validated_data['affiliate_link']
        if (self.request.user.is_merchant and 
            affiliate_link.product.merchant != self.request.user):
            raise permissions.PermissionDenied(
                "You can only create conversions for your own products."
            )
        serializer.save()


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def track_click(request, code):
    """Track a click on an affiliate link and redirect to product page."""
    try:
        link = get_object_or_404(AffiliateLink, code=code, is_active=True)
        
        # Check if link has expired
        if link.expires_at and timezone.now() > link.expires_at:
            return HttpResponse("This affiliate link has expired.", status=410)
        
        # Get visitor information
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        referrer = request.META.get('HTTP_REFERER', '')
        device_type = detect_device_type(user_agent)
        
        # Create click record
        Click.objects.create(
            affiliate_link=link,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            device_type=device_type
        )
        
        # Determine redirect URL
        if link.landing_url:
            redirect_url = link.landing_url
        elif link.product.external_url:
            redirect_url = link.product.external_url
        else:
            # Default redirect to product detail page
            redirect_url = f'/api/products/{link.product.id}/'
        
        return redirect(redirect_url)
        
    except AffiliateLink.DoesNotExist:
        return HttpResponse("Invalid affiliate link.", status=404)
    except Exception as e:
        return HttpResponse(f"Error processing click: {str(e)}", status=500)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def record_conversion(request, code):
    """Record a conversion for an affiliate link."""
    try:
        link = get_object_or_404(AffiliateLink, code=code, is_active=True)
        
        # Only the merchant can record conversions for their products
        if request.user != link.product.merchant and not request.user.is_superuser:
            return Response(
                {'error': 'Only the product merchant can record conversions'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get conversion data
        amount = request.data.get('amount')
        order_id = request.data.get('order_id', '')
        notes = request.data.get('notes', '')
        
        if not amount or float(amount) <= 0:
            return Response(
                {'error': 'Valid amount is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create conversion
        conversion = Conversion.objects.create(
            affiliate_link=link,
            amount=amount,
            order_id=order_id,
            notes=notes
        )
        
        serializer = ConversionSerializer(conversion)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except AffiliateLink.DoesNotExist:
        return Response(
            {'error': 'Invalid affiliate link'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Error recording conversion: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
