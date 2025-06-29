from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import EmailValidator


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser with role-based functionality.
    Supports two types of users: affiliates and merchants.
    """
    ROLE_CHOICES = (
        ('affiliate', 'Affiliate'),
        ('merchant', 'Merchant'),
    )
    
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES,
        help_text="User role - either affiliate or merchant"
    )
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        help_text="User's email address - must be unique"
    )
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text="User's phone number"
    )
    bio = models.TextField(
        blank=True, 
        null=True,
        help_text="User's biography or description"
    )
    website = models.URLField(
        blank=True, 
        null=True,
        help_text="User's website URL"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether the user's account has been verified"
    )

    class Meta:
        db_table = 'users_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def is_affiliate(self):
        """Check if user is an affiliate."""
        return self.role == 'affiliate'

    @property
    def is_merchant(self):
        """Check if user is a merchant."""
        return self.role == 'merchant'

    def get_full_name(self):
        """Return the full name of the user."""
        return f"{self.first_name} {self.last_name}".strip() or self.username
