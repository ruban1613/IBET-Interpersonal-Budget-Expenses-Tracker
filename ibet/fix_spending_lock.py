# Script to fix spending lock creation in views_wallet_new.py
with open('student_module/views_wallet_new.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the target section
old_code = '''                    print(f"[DEBUG] Total ParentAlert count for parent {parent.id}: {alert_count}")
                    
                    return Response({'''

new_code = '''                    print(f"[DEBUG] Total ParentAlert count for parent {parent.id}: {alert_count}")
                    
                    # CRITICAL: Create SpendingLock when student exceeds daily limit
                    from .models import SpendingLock
                    try:
                        today_allowance = DailyAllowance.objects.get(student=student, date=today)
                        if not today_allowance.is_locked:
                            today_allowance.is_locked = True
                            today_allowance.lock_reason = 'Daily limit exceeded - Parent approval required'
                            today_allowance.save()
                            SpendingLock.objects.create(student=student, lock_type='DAILY_LIMIT', amount_locked=extra_needed)
                            StudentNotification.objects.create(student=student, notification_type='WALLET_LOCKED', title=_('Daily Limit Exceeded'), message=_('Your spending has been locked due to exceeding the daily limit.'))
                    except DailyAllowance.DoesNotExist:
                        pass
                    
                    return Response({'''

# Replace
content = content.replace(old_code, new_code)

# Write back
with open('student_module/views_wallet_new.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done! Spending lock creation code added.')
