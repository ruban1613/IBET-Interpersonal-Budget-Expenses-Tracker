import os
import django
import sys
from decimal import Decimal
from django.utils import timezone

# Set up Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from student_module.models import User, DailySpending

def check_ds():
    u = User.objects.get(username='dinesh')
    today = timezone.localdate()
    ds = DailySpending.objects.filter(student=u, date=today).first()
    if ds:
        print(f"DailySpending ID: {ds.id}")
        print(f"Created at: {ds.created_at}")
        print(f"Daily Limit: {ds.daily_limit}")
        print(f"Remaining: {ds.remaining_amount}")
    else:
        print("No DS record today")

if __name__ == "__main__":
    check_ds()
