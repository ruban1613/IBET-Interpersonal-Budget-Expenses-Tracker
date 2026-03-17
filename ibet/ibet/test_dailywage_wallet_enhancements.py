#!/usr/bin/env python
"""
Test daily wage wallet enhancements using Django test client
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_testing_final')
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

def test_dailywage_wallet_enhancements():
    """Test daily wage wallet enhancements"""
    print("🔧 Testing daily wage wallet enhancements...")

    # Get a test user
    User = get_user_model()
    try:
        user = User.objects.get(username='edge_test_dailywage')
        print(f"✅ Found test user: {user.username}, active: {user.is_active}, persona: {user.persona}")
    except User.DoesNotExist:
        print("❌ Test user not found, creating one...")
        user = User.objects.create_user(
            username='edge_test_dailywage',
            password='testpass123',
            email='dailywage@example.com',
            persona='dailywage'
        )
        print(f"✅ Created test user: {user.username}")

    # Get or create token
    token, created = Token.objects.get_or_create(user=user)
    print(f"✅ Token: {token.key} (created: {created})")

    # Create Django test client
    client = Client()

    # Test with token in Authorization header
    headers = {'HTTP_AUTHORIZATION': f'Token {token.key}'}

    # Test monthly summary endpoint
    print("\n--- Testing Monthly Summary Endpoint ---")
    response = client.get('/api/dailywage/wallet/monthly_summary/', **headers)
    print(f"Monthly summary endpoint response: {response.status_code}")
    if response.status_code == 200:
        import json
        data = json.loads(response.content.decode())
        print(f"✅ Monthly summary: earnings={data.get('monthly_earnings')}, expenses={data.get('monthly_expenses')}, alert_triggered={data.get('alert_triggered')}")
    else:
        print(f"❌ Error: {response.content.decode()}")

    # Test weekly summary with alert
    print("\n--- Testing Weekly Summary with Alert ---")
    response = client.get('/api/dailywage/wallet/weekly_summary/', **headers)
    print(f"Weekly summary endpoint response: {response.status_code}")
    if response.status_code == 200:
        import json
        data = json.loads(response.content.decode())
        print(f"✅ Weekly summary: alert_triggered={data.get('alert_triggered')}")
    else:
        print(f"❌ Error: {response.content.decode()}")

    # Test balance endpoint to check alert_threshold is included
    print("\n--- Testing Balance Endpoint ---")
    response = client.get('/api/dailywage/wallet/balance/', **headers)
    print(f"Balance endpoint response: {response.status_code}")
    if response.status_code == 200:
        import json
        data = json.loads(response.content.decode())
        print(f"✅ Balance data includes alert_threshold: {'alert_threshold' in str(data)}")
    else:
        print(f"❌ Error: {response.content.decode()}")

if __name__ == '__main__':
    test_dailywage_wallet_enhancements()
