from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reciclAI"

    def ready(self):
        # Importa os signals para que eles sejam registrados
        # quando a aplicação for iniciada.
        import reciclAI.signals
