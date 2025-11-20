from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reciclAI"

    def ready(self):
        # Import signals to ensure they are registered when the app is ready
        import reciclAI.signals  # noqa: F401
