from django.contrib import admin
from .models import AffiliateLink, Click, Conversion


@admin.register(AffiliateLink)
class AffiliateLinkAdmin(admin.ModelAdmin):
    """Admin configuration for AffiliateLink model."""
    
    list_display = [
        'code', 'affiliate', 'product', 'is_active', 
        'click_count', 'conversion_count', 'created_at'
    ]
    list_filter = [
        'is_active', 'created_at', 'affiliate__role', 
        'product__category', 'expires_at'
    ]
    search_fields = [
        'code', 'affiliate__username', 'product__name', 
        'custom_slug', 'affiliate__email'
    ]
    ordering = ['-created_at']
    readonly_fields = ['code', 'created_at', 'updated_at', 'click_count', 'conversion_count']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'affiliate', 'product', 'is_active')
        }),
        ('Customization', {
            'fields': ('custom_slug', 'landing_url', 'expires_at')
        }),
        ('Statistics', {
            'fields': ('click_count', 'conversion_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('affiliate', 'product')
    
    # Custom actions
    actions = ['activate_links', 'deactivate_links']
    
    def activate_links(self, request, queryset):
        """Activate selected affiliate links."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} affiliate links were successfully activated.')
    activate_links.short_description = "Activate selected affiliate links"
    
    def deactivate_links(self, request, queryset):
        """Deactivate selected affiliate links."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} affiliate links were successfully deactivated.')
    deactivate_links.short_description = "Deactivate selected affiliate links"


@admin.register(Click)
class ClickAdmin(admin.ModelAdmin):
    """Admin configuration for Click model."""
    
    list_display = [
        'affiliate_link', 'ip_address', 'device_type', 
        'country', 'timestamp'
    ]
    list_filter = [
        'device_type', 'country', 'timestamp',
        'affiliate_link__affiliate', 'affiliate_link__product'
    ]
    search_fields = [
        'ip_address', 'affiliate_link__code', 'user_agent',
        'affiliate_link__affiliate__username'
    ]
    ordering = ['-timestamp']
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('Click Information', {
            'fields': ('affiliate_link', 'timestamp')
        }),
        ('Visitor Details', {
            'fields': ('ip_address', 'user_agent', 'referrer', 'device_type', 'country')
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('affiliate_link__affiliate', 'affiliate_link__product')
    
    # Custom filters
    date_hierarchy = 'timestamp'


@admin.register(Conversion)
class ConversionAdmin(admin.ModelAdmin):
    """Admin configuration for Conversion model."""
    
    list_display = [
        'affiliate_link', 'amount', 'commission_amount', 
        'verified', 'timestamp', 'order_id'
    ]
    list_filter = [
        'verified', 'currency', 'timestamp',
        'affiliate_link__affiliate', 'affiliate_link__product'
    ]
    search_fields = [
        'order_id', 'affiliate_link__code', 'notes',
        'affiliate_link__affiliate__username'
    ]
    ordering = ['-timestamp']
    readonly_fields = ['timestamp', 'commission_rate']
    
    fieldsets = (
        ('Conversion Information', {
            'fields': ('affiliate_link', 'click', 'timestamp')
        }),
        ('Financial Details', {
            'fields': ('amount', 'commission_amount', 'commission_rate', 'currency')
        }),
        ('Order Details', {
            'fields': ('order_id', 'verified', 'notes')
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'affiliate_link__affiliate', 
            'affiliate_link__product',
            'click'
        )
    
    # Custom actions
    actions = ['verify_conversions', 'unverify_conversions']
    
    def verify_conversions(self, request, queryset):
        """Verify selected conversions."""
        updated = queryset.update(verified=True)
        self.message_user(request, f'{updated} conversions were successfully verified.')
    verify_conversions.short_description = "Verify selected conversions"
    
    def unverify_conversions(self, request, queryset):
        """Unverify selected conversions."""
        updated = queryset.update(verified=False)
        self.message_user(request, f'{updated} conversions were successfully unverified.')
    unverify_conversions.short_description = "Unverify selected conversions"
    
    # Custom filters
    date_hierarchy = 'timestamp'
