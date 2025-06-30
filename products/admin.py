from django.contrib import admin
from .models import Product, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin configuration for Category model."""
    
    list_display = ['name', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {'fields': ('name', 'description', 'is_active')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin configuration for Product model."""
    
    list_display = [
        'name', 'merchant', 'category', 'price', 
        'commission_rate', 'is_active', 'created_at'
    ]
    list_filter = [
        'is_active', 'category', 'merchant__role', 'created_at'
    ]
    search_fields = ['name', 'description', 'sku', 'merchant__username']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'commission_amount']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'merchant')
        }),
        ('Pricing & Commission', {
            'fields': ('price', 'commission_rate', 'commission_amount')
        }),
        ('URLs & Media', {
            'fields': ('image_url', 'external_url')
        }),
        ('Inventory', {
            'fields': ('sku', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Custom filters
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('merchant', 'category')
    
    # Custom actions
    actions = ['activate_products', 'deactivate_products']
    
    def activate_products(self, request, queryset):
        """Activate selected products."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} products were successfully activated.')
    activate_products.short_description = "Activate selected products"
    
    def deactivate_products(self, request, queryset):
        """Deactivate selected products."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} products were successfully deactivated.')
    deactivate_products.short_description = "Deactivate selected products"
