# Script to fix parent_module serializers to use DailyAllowance instead of DailyLimit
with open('parent_module/serializers.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the import
old_import = "from student_module.models import ParentStudentLink, Transaction, Wallet, DailyLimit"
new_import = "from student_module.models import ParentStudentLink, Transaction, Wallet, DailyAllowance"
content = content.replace(old_import, new_import)

# Fix the get_daily_limit method
old_method = '''    def get_daily_limit(self, obj):
        try:
            daily_limit = DailyLimit.objects.get(user_id=obj['student_id'])
            return {
                'monthly_budget': daily_limit.monthly_budget,
                'daily_limit_amount': daily_limit.daily_limit_amount,
                'current_daily_spent': daily_limit.current_daily_spent
            }
        except DailyLimit.DoesNotExist:
            return None'''

new_method = '''    def get_daily_limit(self, obj):
        from django.utils import timezone
        today = timezone.now().date()
        
        # Get all available daily allowances for the student
        daily_allowances = DailyAllowance.objects.filter(
            student_id=obj['student_id'],
            is_available=True
        ).order_by('date')
        
        if not daily_allowances.exists():
            return None
        
        # Calculate totals from available days
        total_monthly = sum(float(da.daily_amount) for da in daily_allowances)
        total_spent = sum(float(da.amount_spent) for da in daily_allowances)
        
        # Get today's allowance specifically
        try:
            today_allowance = DailyAllowance.objects.get(student_id=obj['student_id'], date=today)
            today_limit = float(today_allowance.daily_amount)
            today_spent = float(today_allowance.amount_spent)
        except DailyAllowance.DoesNotExist:
            today_limit = 0
            today_spent = 0
        
        return {
            'monthly_budget': total_monthly,
            'daily_limit_amount': today_limit,
            'current_daily_spent': today_spent
        }'''

content = content.replace(old_method, new_method)

with open('parent_module/serializers.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done! Parent serializer fixed to use DailyAllowance model')
