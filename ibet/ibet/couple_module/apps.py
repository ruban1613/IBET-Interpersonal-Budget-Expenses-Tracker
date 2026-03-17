from django.apps import AppConfig


class CoupleModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'couple_module'

    def ready(self):
        import couple_module.translation  # noqa
