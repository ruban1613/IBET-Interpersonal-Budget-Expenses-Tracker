#!/usr/bin/env python
"""
Simple test to verify token authentication is working
"""
import requests
import sys
import os

# Add the IBET directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'IBET'))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_testing_final')
import django
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

BASE_URL = 'http://127.0.0.1:8000'

def test_token_auth():
    """Test basic token authentication"""
    print("🔧 Testing token authentication...")

    # Get a test user
    User = get_user_model()
    try:
        user = User.objects.get(username='edge_test_individual')
        print(f"✅ Found test user: {user.username}, active: {user.is_active}, persona: {user.persona}")
    except User.DoesNotExist:
        print("❌ Test user not found")
        return

    # Delete all tokens for user and create a new one to ensure fresh token
    Token.objects.filter(user=user).delete()
    token = Token.objects.create(user=user)
    print(f"✅ Token recreated: {token.key}")

    # Test token authentication with a simple request
    headers = {'Authorization': f'Token {token.key}'}
    print(f"Using token in header: {headers['Authorization']}")

    # Try to access individual wallet balance endpoint
    response = requests.get(f'{BASE_URL}/api/individual/wallet/balance/', headers=headers)
    print(f"Balance endpoint response: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ Balance: {response.json()}")
    else:
        print(f"❌ Error: {response.text}")

    # Try to make a deposit
    test_data = {'amount': 100, 'description': 'Test deposit'}
    response = requests.post(f'{BASE_URL}/api/individual/wallet/deposit/', json=test_data, headers=headers)
    print(f"Deposit endpoint response: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ Deposit successful: {response.json()}")
    else:
        print(f"❌ Deposit error: {response.text}")

if __name__ == '__main__':
    test_token_auth()
