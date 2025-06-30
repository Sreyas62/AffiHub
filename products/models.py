from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import User


class Category(models.Model):
    """Product category model for organizing products."""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Category name"
    )
    description = models.TextField(
        blank=True,
        help_text="Category description"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this category is active"
    )

    class Meta:
        db_table = 'products_category'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """Product model for items that can be promoted by affiliates."""
    
    name = models.CharField(
        max_length=200,
        help_text="Product name"
    )
    description = models.TextField(
        help_text="Product description"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Product price"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        help_text="Product category"
    )
    merchant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'merchant'},
        related_name='products',
        help_text="Merchant who owns this product"
    )
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0.00), MaxValueValidator(100.00)],
        default=10.00,
        help_text="Commission rate percentage for affiliates"
    )
    image_url = models.URLField(
        blank=True,
        null=True,
        help_text="Product image URL"
    )
    external_url = models.URLField(
        blank=True,
        null=True,
        help_text="External product URL (e.g., merchant's website)"
    )
    sku = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Stock Keeping Unit"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this product is active for promotion"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products_product'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['merchant']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} - ${self.price}"

    @property
    def commission_amount(self):
        """Calculate commission amount based on price and rate."""
        return (self.price * self.commission_rate) / 100

    def get_affiliate_links_count(self):
        """Get count of affiliate links for this product."""
        return self.affiliate_links.count()

    def get_total_clicks(self):
        """Get total clicks for all affiliate links of this product."""
        return sum(link.clicks.count() for link in self.affiliate_links.all())

    def get_total_conversions(self):
        """Get total conversions for all affiliate links of this product."""
        return sum(link.conversions.count() for link in self.affiliate_links.all())
