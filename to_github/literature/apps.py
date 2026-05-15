"""
Apps configuration for literature app.
"""
from django.apps import AppConfig


class LiteratureConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'literature'
    verbose_name = '文献管理'

    def ready(self):
        """Import signals when app is ready."""
        try:
            import literature.signals  # noqa
        except ImportError:
            pass