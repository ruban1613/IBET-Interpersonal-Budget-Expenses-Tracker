#!/usr/bin/env python
"""
Test withdraw and transfer_to_goal endpoints for individual wallet
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

def test_other_wallet_endpoints():
    """Test withdraw and transfer_to_goal endpoints"""
    print("🔧 Testing other wallet endpoints...")

    # Get a test user
    User = get_user_model()
    try:
        user = User.objects.get(username='edge_test_individual')
        print(f"✅ Found test user: {user.username}")
    except User.DoesNotExist:
        print("❌ Test user not found")
        return

    # Get or create token
    token, created = Token.objects.get_or_create(user=user)
    print(f"✅ Token: {token.key}")

    # Create Django test client
    client = Client()
    headers = {'HTTP_AUTHORIZATION': f'Token {token.key}'}

    # First, check balance
    response = client.get('/api/individual/wallet/balance/', **headers)
    print(f"Initial balance: {response.json()}")

    # Test deposit to have funds
    response = client.post('/api/individual/wallet/deposit/', {'amount': 500, 'description': 'Test deposit for withdraw'}, **headers)
    print(f"Deposit response: {response.status_code} - {response.json()}")

    # Test withdraw
    print("\n--- Testing Withdraw Endpoint ---")
    response = client.post('/api/individual/wallet/withdraw/', {'amount': 100, 'description': 'Test withdraw'}, **headers)
    print(f"Withdraw response: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ Withdraw successful: {response.json()}")
    else:
        print(f"❌ Withdraw error: {response.json()}")

    # Test transfer_to_goal
    print("\n--- Testing Transfer to Goal Endpoint ---")
    response = client.post('/api/individual/wallet/transfer_to_goal/', {'amount': 50, 'goal_name': 'Vacation'}, **headers)
    print(f"Transfer response: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ Transfer successful: {response.json()}")
    else:
        print(f"❌ Transfer error: {response.json()}")

    # Test invalid withdraw (insufficient funds)
    print("\n--- Testing Invalid Withdraw (Insufficient Funds) ---")
    response = client.post('/api/individual/wallet/withdraw/', {'amount': 10000, 'description': 'Invalid withdraw'}, **headers)
    print(f"Invalid withdraw response: {response.status_code}")
    if response.status_code == 400:
        print(f"✅ Correctly rejected: {response.json()}")
    else:
        print(f"❌ Unexpected response: {response.json()}")

    # Final balance
    response = client.get('/api/individual/wallet/balance/', **headers)
    print(f"Final balance: {response.json()}")

if __name__ == '__main__':
    test_other_wallet_endpoints()
