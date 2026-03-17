from django.apps import AppConfig


class StudentModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'student_module'

    def ready(self):
        import student_module.translation  # noqa
        import student_module.signals  # noqa
