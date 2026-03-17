#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

try:
    u = User.objects.get(username='admin')
    u.set_password('admin123')
    u.save()
    print('SUCCESS: Password reset for admin user!')
    print('Username: admin')
    print('New Password: admin123')
except User.DoesNotExist:
    print('ERROR: Admin user not found')
except Exception as e:
    print(f'ERROR: {e}')
