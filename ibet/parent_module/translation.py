from modeltranslation.translator import translator, TranslationOptions
from .models import ParentAlert, ParentOTPRequest, StudentMonitoring

# Translation options for model fields
class ParentAlertTranslationOptions(TranslationOptions):
    fields = ('alert_type', 'message')

class ParentOTPRequestTranslationOptions(TranslationOptions):
    fields = ('reason',)

class StudentMonitoringTranslationOptions(TranslationOptions):
    fields = ('notes',)

# Register translation options
translator.register(ParentAlert, ParentAlertTranslationOptions)
translator.register(ParentOTPRequest, ParentOTPRequestTranslationOptions)
translator.register(StudentMonitoring, StudentMonitoringTranslationOptions)
