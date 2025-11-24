from django.apps import AppConfig


class DbConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'db'

    def ready(self):
        import db.signals
