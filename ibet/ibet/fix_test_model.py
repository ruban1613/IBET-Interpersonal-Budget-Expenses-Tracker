# Script to fix the test to check DailyAllowance instead of DailySpending
with open('test_spending_lock.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the import and query for DailySpending with DailyAllowance
old_code = '''    from student_module.models import SpendingLock, DailySpending, User'''

new_code = '''    from student_module.models import SpendingLock, DailyAllowance, User'''

content = content.replace(old_code, new_code)

# Replace the DailySpending query with DailyAllowance
old_code2 = '''        # Check DailySpending
        today_date = date.today()
        daily_spending = DailySpending.objects.filter(student=student_user, date=today_date)
        if daily_spending.exists():
            ds = daily_spending.first()
            print(f"9.2 Daily Spending Record:")
            print(f"    Daily Limit: {ds.daily_limit}")
            print(f"    Amount Spent: {ds.amount_spent}")
            print(f"    Remaining: {ds.remaining_amount}")
            print(f"    Is Locked: {ds.is_locked}")
            print(f"    Lock Reason: {ds.lock_reason}")

            if ds.is_locked:
                print(f"    ✅ DAILY SPENDING IS LOCKED!")'''

new_code2 = '''        # Check DailyAllowance (NEW model)
        today_date = date.today()
        daily_allowance = DailyAllowance.objects.filter(student=student_user, date=today_date)
        if daily_allowance.exists():
            da = daily_allowance.first()
            print(f"9.2 Daily Allowance Record:")
            print(f"    Daily Limit: {da.daily_amount}")
            print(f"    Amount Spent: {da.amount_spent}")
            print(f"    Remaining: {da.remaining_amount}")
            print(f"    Is Locked: {da.is_locked}")
            print(f"    Lock Reason: {da.lock_reason}")

            if da.is_locked:
                print(f"    ✅ DAILY ALLOWANCE IS LOCKED!")'''

content = content.replace(old_code2, new_code2)

with open('test_spending_lock.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done! Test now checks DailyAllowance model instead of DailySpending.')
