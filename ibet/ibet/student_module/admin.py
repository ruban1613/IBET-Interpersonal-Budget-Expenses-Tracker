from django.contrib import admin
from .models import User, Budget, Category, Transaction, Reminder, ChatMessage, DailyLimit, OTPRequest

admin.site.register(User)
admin.site.register(Budget)
admin.site.register(Category)
admin.site.register(Transaction)
admin.site.register(Reminder)
admin.site.register(ChatMessage)
admin.site.register(DailyLimit)
admin.site.register(OTPRequest)
