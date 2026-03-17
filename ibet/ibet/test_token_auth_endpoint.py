#!/usr/bin/env python
"""
Test the token authentication endpoint directly
"""
import requests
import os
import sys

# Add the IBET directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'IBET'))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_testing_final')
import django
django.setup()

from django.contrib.auth import get_user_model

BASE_URL = 'http://127.0.0.1:8000'

def test_token_auth_endpoint():
    """Test the token-auth endpoint directly"""
    print("🔧 Testing token-auth endpoint...")

    # Test with form data (as expected by DRF)
    response = requests.post(f'{BASE_URL}/api/token-auth/', data={
        'username': 'edge_test_individual',
        'password': 'testpass123'
    })

    print(f"Token-auth response: {response.status_code}")
    print(f"Response headers: {response.headers}")
    print(f"Response text: {response.text}")

    if response.status_code == 200:
        token_data = response.json()
        print(f"✅ Token received: {token_data.get('token')}")
        return token_data.get('token')
    else:
        print("❌ Token-auth failed")

    return None

if __name__ == '__main__':
    test_token_auth_endpoint()
