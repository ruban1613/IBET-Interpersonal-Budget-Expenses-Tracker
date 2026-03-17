import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from parent_module.models import ParentAlert
from django.contrib.auth import get_user_model

User = get_user_model()

# Get all alerts
alerts = ParentAlert.objects.all().order_by('-created_at')[:10]
print('Total ParentAlert count:', ParentAlert.objects.count())
print()
for a in alerts:
    print(f'ID: {a.id}')
    print(f'  Parent: {a.parent.username} (id={a.parent.id})')
    print(f'  Student: {a.student.username} (id={a.student.id})')
    print(f'  Type: {a.alert_type}')
    print(f'  Status: {a.status}')
    print(f'  Message: {a.message[:100]}...')
    print(f'  Created: {a.created_at}')
    print()
