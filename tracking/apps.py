from django.apps import AppConfig


class TrackingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tracking'
    verbose_name = 'Link Tracking'
    
    def ready(self):
        """Import signals when the app is ready."""
        try:
            import tracking.signals  # noqa F401
        except ImportError:
            pass
