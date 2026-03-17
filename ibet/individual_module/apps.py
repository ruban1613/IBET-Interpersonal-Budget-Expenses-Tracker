from django.apps import AppConfig


class IndividualModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'individual_module'

    def ready(self):
        import individual_module.translation  # noqa
