from rest_framework import serializers
from .models import Product, Category
from users.serializers import UserSerializer


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""
    
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'is_active',
            'products_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_products_count(self, obj):
        """Get count of products in this category."""
        return obj.products.filter(is_active=True).count()


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model with detailed information."""
    
    merchant_info = UserSerializer(source='merchant', read_only=True)
    category_info = CategorySerializer(source='category', read_only=True)
    commission_amount = serializers.ReadOnlyField()
    affiliate_links_count = serializers.SerializerMethodField()
    total_clicks = serializers.SerializerMethodField()
    total_conversions = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'category', 'category_info',
            'merchant', 'merchant_info', 'commission_rate', 'commission_amount',
            'image_url', 'external_url', 'sku', 'is_active',
            'affiliate_links_count', 'total_clicks', 'total_conversions',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_affiliate_links_count(self, obj):
        """Get count of affiliate links for this product."""
        return obj.get_affiliate_links_count()

    def get_total_clicks(self, obj):
        """Get total clicks for this product."""
        return obj.get_total_clicks()

    def get_total_conversions(self, obj):
        """Get total conversions for this product."""
        return obj.get_total_conversions()

    def validate_commission_rate(self, value):
        """Validate commission rate is between 0 and 100."""
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Commission rate must be between 0 and 100 percent."
            )
        return value

    def validate_price(self, value):
        """Validate price is greater than 0."""
        if value <= 0:
            raise serializers.ValidationError(
                "Price must be greater than 0."
            )
        return value


class ProductCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new products."""
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'price', 'category',
            'commission_rate', 'image_url', 'external_url', 'sku'
        ]

    def validate_commission_rate(self, value):
        """Validate commission rate is between 0 and 100."""
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Commission rate must be between 0 and 100 percent."
            )
        return value

    def validate_price(self, value):
        """Validate price is greater than 0."""
        if value <= 0:
            raise serializers.ValidationError(
                "Price must be greater than 0."
            )
        return value

    def create(self, validated_data):
        """Create product with current user as merchant."""
        # The merchant will be set in the view
        return super().create(validated_data)


class ProductUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating products."""
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'price', 'category',
            'commission_rate', 'image_url', 'external_url', 'sku', 'is_active'
        ]

    def validate_commission_rate(self, value):
        """Validate commission rate is between 0 and 100."""
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Commission rate must be between 0 and 100 percent."
            )
        return value

    def validate_price(self, value):
        """Validate price is greater than 0."""
        if value <= 0:
            raise serializers.ValidationError(
                "Price must be greater than 0."
            )
        return value


class ProductListSerializer(serializers.ModelSerializer):
    """Simplified serializer for product lists."""
    
    merchant_name = serializers.CharField(source='merchant.get_full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'price', 'commission_rate',
            'merchant_name', 'category_name', 'is_active',
            'image_url', 'created_at'
        ]
