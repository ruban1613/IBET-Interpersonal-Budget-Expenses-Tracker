from modeltranslation.translator import translator, TranslationOptions
from .models import Category, Transaction, ChatMessage

# Translation options for model fields
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name',)

class TransactionTranslationOptions(TranslationOptions):
    fields = ('description',)

class ChatMessageTranslationOptions(TranslationOptions):
    fields = ('message',)

# Register translation options
translator.register(Category, CategoryTranslationOptions)
translator.register(Transaction, TransactionTranslationOptions)
translator.register(ChatMessage, ChatMessageTranslationOptions)
