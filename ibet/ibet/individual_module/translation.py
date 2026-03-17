from modeltranslation.translator import translator, TranslationOptions
from .models import IncomeSource, ExpenseAlert, FinancialGoal

# Translation options for model fields
class IncomeSourceTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

class ExpenseAlertTranslationOptions(TranslationOptions):
    fields = ('title', 'message')

class FinancialGoalTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

# Register translation options
translator.register(IncomeSource, IncomeSourceTranslationOptions)
translator.register(ExpenseAlert, ExpenseAlertTranslationOptions)
translator.register(FinancialGoal, FinancialGoalTranslationOptions)
