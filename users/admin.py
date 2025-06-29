from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for custom User model."""
    
    # Fields to display in the admin list view
    list_display = ['username', 'email', 'role', 'first_name', 'last_name', 'is_verified', 'is_active', 'created_at']
    list_filter = ['role', 'is_verified', 'is_active', 'is_staff', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    # Fields to display in the user detail view
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'bio', 'website')}),
        ('Role & Permissions', {'fields': ('role', 'is_verified', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    
    # Fields to display when adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_login', 'date_joined']
    
    # Enable filtering by date
    date_hierarchy = 'created_at'
    
    # Custom actions
    actions = ['verify_users', 'unverify_users']
    
    def verify_users(self, request, queryset):
        """Mark selected users as verified."""
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} users were successfully verified.')
    verify_users.short_description = "Mark selected users as verified"
    
    def unverify_users(self, request, queryset):
        """Mark selected users as unverified."""
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} users were successfully unverified.')
    unverify_users.short_description = "Mark selected users as unverified"
