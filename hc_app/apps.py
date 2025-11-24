from django.apps import AppConfig


class HcAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hc_app'
    def ready(self):
        # Import signal handlers to wire automatic task creation and other hooks
        try:
            import hc_app.signals  # noqa: F401
        except Exception:
            # don't raise on import errors here; signals are best-effort
            pass
        try:
            from django.db.utils import OperationalError
            from .models import Category
            defaults = [
                ("Fashion", "fashion"),
                ("Needlework", "needlework"),
                ("Wood Crafts", "wood-crafts"),
                ("Textile", "textile"),
                ("Pottery & Ceramics", "pottery-ceramics"),
            ]
            for name, slug in defaults:
                try:
                    Category.objects.get_or_create(slug=slug, defaults={"name": name})
                except Exception:
                
        except Exception:
            pass
