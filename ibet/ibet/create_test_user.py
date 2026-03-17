#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from student_module.models import User
from dailywage_module.models_wallet import DailyWageWallet

def create_test_user():
    # Check if test user exists
    user = User.objects.filter(username='test_dailywage').first()
    if user:
        print(f"User already exists: {user.username}")
    else:
        user = User.objects.create_user('test_dailywage', 'test@example.com', 'password123')
        user.persona = 'DAILY_WAGE'
        user.save()
        print(f"Created user: {user.username}")

    # Check if wallet exists
    wallet = DailyWageWallet.objects.filter(user=user).first()
    if wallet:
        print(f"Wallet already exists for user: {user.username}")
        # Delete existing wallet to test creation
        wallet.delete()
        print("Deleted existing wallet to test auto-creation")
    else:
        print(f"No wallet exists for user: {user.username}")

    return user

if __name__ == '__main__':
    create_test_user()
