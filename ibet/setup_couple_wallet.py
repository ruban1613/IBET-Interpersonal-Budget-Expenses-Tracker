#!/usr/bin/env python
"""
Setup script to create couple wallet records for testing.
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Setup Django
django.setup()

from django.contrib.auth import get_user_model
from couple_module.models_wallet import CoupleWallet
from decimal import Decimal

User = get_user_model()

def setup_couple_wallet():
    """Create couple wallet for test users"""
    print("🔧 Setting up couple wallet for test users...")

    # Get or create test users
    user1, created1 = User.objects.get_or_create(
        username='test_couple1',
        defaults={
            'email': 'test_couple1@example.com',
            'first_name': 'Test',
            'last_name': 'Couple1'
        }
    )
    if created1:
        user1.set_password('testpass123')
        user1.save()
        print(f"✅ Created user: {user1.username}")

    user2, created2 = User.objects.get_or_create(
        username='test_couple2',
        defaults={
            'email': 'test_couple2@example.com',
            'first_name': 'Test',
            'last_name': 'Couple2'
        }
    )
    if created2:
        user2.set_password('testpass123')
        user2.save()
        print(f"✅ Created user: {user2.username}")

    # Create couple wallet
    wallet, created = CoupleWallet.objects.get_or_create(
        partner1=user1,
        partner2=user2,
        defaults={
            'balance': Decimal('1000.00'),
            'emergency_fund': Decimal('200.00'),
            'joint_goals': Decimal('300.00'),
            'monthly_budget': Decimal('2000.00'),
            'is_locked': False
        }
    )

    if created:
        print("✅ Created couple wallet with initial balance: $1000.00")
        print(f"   Emergency Fund: ${wallet.emergency_fund}")
        print(f"   Joint Goals: ${wallet.joint_goals}")
        print(f"   Monthly Budget: ${wallet.monthly_budget}")
    else:
        print("✅ Couple wallet already exists")
        print(f"   Current Balance: ${wallet.balance}")
        print(f"   Emergency Fund: ${wallet.emergency_fund}")
        print(f"   Joint Goals: ${wallet.joint_goals}")

    print("✅ Couple wallet setup complete!")
    return wallet

if __name__ == '__main__':
    setup_couple_wallet()
