from rest_framework import serializers
from .models import AffiliateLink, Click, Conversion
from users.serializers import UserSerializer
from products.serializers import ProductSerializer


class AffiliateLinkSerializer(serializers.ModelSerializer):
    """Serializer for AffiliateLink model with detailed information."""
    
    affiliate_info = UserSerializer(source='affiliate', read_only=True)
    product_info = ProductSerializer(source='product', read_only=True)
    click_count = serializers.ReadOnlyField()
    conversion_count = serializers.ReadOnlyField()
    conversion_rate = serializers.ReadOnlyField()
    tracking_url = serializers.SerializerMethodField()

    class Meta:
        model = AffiliateLink
        fields = [
            'id', 'code', 'affiliate', 'affiliate_info', 'product', 'product_info',
            'custom_slug', 'landing_url', 'is_active', 'created_at', 'updated_at',
            'expires_at', 'click_count', 'conversion_count', 'conversion_rate',
            'tracking_url'
        ]
        read_only_fields = ['id', 'code', 'created_at', 'updated_at']

    def get_tracking_url(self, obj):
        """Get the full tracking URL for the affiliate link."""
        return obj.get_tracking_url()


class AffiliateLinkCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new affiliate links."""
    
    class Meta:
        model = AffiliateLink
        fields = ['product', 'custom_slug', 'landing_url', 'expires_at']

    def validate_product(self, value):
        """Ensure the product is active."""
        if not value.is_active:
            raise serializers.ValidationError("Cannot create links for inactive products.")
        return value

    def validate(self, attrs):
        """Check for duplicate affiliate links."""
        affiliate = self.context['request'].user
        product = attrs['product']
        
        # Check if affiliate link already exists for this user and product
        if AffiliateLink.objects.filter(affiliate=affiliate, product=product).exists():
            raise serializers.ValidationError(
                "You already have an affiliate link for this product."
            )
        
        return attrs

    def create(self, validated_data):
        """Create affiliate link with current user as affiliate."""
        # The affiliate will be set in the view
        return super().create(validated_data)


class ClickSerializer(serializers.ModelSerializer):
    """Serializer for Click model."""
    
    affiliate_link_info = AffiliateLinkSerializer(source='affiliate_link', read_only=True)

    class Meta:
        model = Click
        fields = [
            'id', 'affiliate_link', 'affiliate_link_info', 'ip_address',
            'user_agent', 'referrer', 'country', 'device_type', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class ClickCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating clicks (used internally)."""
    
    class Meta:
        model = Click
        fields = ['affiliate_link', 'ip_address', 'user_agent', 'referrer', 'device_type']

    def create(self, validated_data):
        """Create click record."""
        return Click.objects.create(**validated_data)


class ConversionSerializer(serializers.ModelSerializer):
    """Serializer for Conversion model with detailed information."""
    
    affiliate_link_info = AffiliateLinkSerializer(source='affiliate_link', read_only=True)
    click_info = ClickSerializer(source='click', read_only=True)
    commission_rate = serializers.ReadOnlyField()

    class Meta:
        model = Conversion
        fields = [
            'id', 'affiliate_link', 'affiliate_link_info', 'click', 'click_info',
            'order_id', 'amount', 'commission_amount', 'commission_rate',
            'currency', 'timestamp', 'verified', 'notes'
        ]
        read_only_fields = ['id', 'timestamp', 'commission_amount']


class ConversionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating conversions."""
    
    class Meta:
        model = Conversion
        fields = [
            'affiliate_link', 'click', 'order_id', 'amount', 
            'currency', 'notes'
        ]

    def validate_amount(self, value):
        """Validate conversion amount is positive."""
        if value <= 0:
            raise serializers.ValidationError("Conversion amount must be greater than 0.")
        return value

    def validate_affiliate_link(self, value):
        """Ensure the affiliate link is active."""
        if not value.is_active:
            raise serializers.ValidationError("Cannot create conversions for inactive affiliate links.")
        return value

    def create(self, validated_data):
        """Create conversion with automatic commission calculation."""
        return super().create(validated_data)


class ClickAnalyticsSerializer(serializers.Serializer):
    """Serializer for click analytics data."""
    
    total_clicks = serializers.IntegerField()
    unique_clicks = serializers.IntegerField()
    mobile_clicks = serializers.IntegerField()
    desktop_clicks = serializers.IntegerField()
    top_countries = serializers.ListField()
    daily_clicks = serializers.ListField()


class ConversionAnalyticsSerializer(serializers.Serializer):
    """Serializer for conversion analytics data."""
    
    total_conversions = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_commission = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    conversion_rate = serializers.FloatField()
    daily_conversions = serializers.ListField()


class AffiliateLinkAnalyticsSerializer(serializers.Serializer):
    """Serializer for affiliate link analytics."""
    
    link_id = serializers.IntegerField()
    link_code = serializers.CharField()
    product_name = serializers.CharField()
    total_clicks = serializers.IntegerField()
    total_conversions = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_commission = serializers.DecimalField(max_digits=10, decimal_places=2)
    conversion_rate = serializers.FloatField()
