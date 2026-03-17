import os, sys, django
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_testing_final')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from student_module.models import User, DailySpending

def check_ruki_yesterday():
    user = User.objects.get(username='Ruki16')
    yesterday = timezone.now().date() - timedelta(days=1)
    ds = DailySpending.objects.filter(student=user, date=yesterday).first()
    if ds:
        print(f"Yesterday ({yesterday}): Spent={ds.amount_spent}, Limit={ds.daily_limit}, Locked={ds.is_locked}")
    else:
        print(f"No record for yesterday ({yesterday})")

if __name__ == '__main__':
    check_ruki_yesterday()
