from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ReciclAI"

    def ready(self):
        # Desativado para centralizar a criação de perfil no formulário de cadastro
        # import core.signals
        pass
