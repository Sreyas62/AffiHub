from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'products'
    verbose_name = 'Product Management'
    
    def ready(self):
        """Import signals when the app is ready."""
        try:
            import products.signals  # noqa F401
        except ImportError:
            pass
