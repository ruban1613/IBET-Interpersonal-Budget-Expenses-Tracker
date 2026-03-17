from modeltranslation.translator import translator, TranslationOptions
from .models import SpendingRequest, SharedTransaction, CoupleAlert

# Translation options for model fields
class SpendingRequestTranslationOptions(TranslationOptions):
    fields = ('description', 'category')

class SharedTransactionTranslationOptions(TranslationOptions):
    fields = ('description',)

class CoupleAlertTranslationOptions(TranslationOptions):
    fields = ('title', 'message')

# Register translation options
translator.register(SpendingRequest, SpendingRequestTranslationOptions)
translator.register(SharedTransaction, SharedTransactionTranslationOptions)
translator.register(CoupleAlert, CoupleAlertTranslationOptions)
