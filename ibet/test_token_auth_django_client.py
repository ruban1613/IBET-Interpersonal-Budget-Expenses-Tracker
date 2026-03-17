#!/usr/bin/env python
"""
Test token authentication using Django test client
"""
import os
import sys

# Add the IBET directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'IBET'))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_testing_final')
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

def test_token_auth_django_client():
    """Test token authentication using Django test client"""
    print("🔧 Testing token authentication with Django test client...")

    # Get a test user
    User = get_user_model()
    try:
        user = User.objects.get(username='edge_test_individual')
        print(f"✅ Found test user: {user.username}, active: {user.is_active}, persona: {user.persona}")
    except User.DoesNotExist:
        print("❌ Test user not found")
        return

    # Get or create token
    token, created = Token.objects.get_or_create(user=user)
    print(f"✅ Token: {token.key} (created: {created})")

    # Create Django test client
    client = Client()

    # Test with token in Authorization header
    headers = {'HTTP_AUTHORIZATION': f'Token {token.key}'}

    # Try to access individual wallet balance endpoint
    response = client.get('/api/individual/wallet/balance/', **headers)
    print(f"Balance endpoint response: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ Balance: {response.content.decode()}")
    else:
        print(f"❌ Error: {response.content.decode()}")

    # Try to make a deposit
    response = client.post('/api/individual/wallet/deposit/', {'amount': 100, 'description': 'Test deposit'}, **headers)
    print(f"Deposit endpoint response: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ Deposit successful: {response.content.decode()}")
    else:
        print(f"❌ Deposit error: {response.content.decode()}")

if __name__ == '__main__':
    test_token_auth_django_client()
