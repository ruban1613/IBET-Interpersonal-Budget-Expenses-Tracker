from modeltranslation.translator import register, TranslationOptions
from .models import Institute

@register(Institute)
class InstituteTranslationOptions(TranslationOptions):
    fields = ('name', 'address')
