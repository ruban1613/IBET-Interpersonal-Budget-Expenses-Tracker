#!/usr/bin/env python
"""
Debug script to check URL patterns and test endpoints
"""
import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework import status

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_wallet_test')
django.setup()

User = get_user_model()

def test_urls():
    """Test URL patterns and endpoints"""
    print("=== URL Debug Test ===")

    # Create test user
    try:
        user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass123',
            persona='INDIVIDUAL'
        )
        token = Token.objects.create(user=user)
        print(f"✓ Created test user: {user.username}")
    except Exception as e:
        print(f"✗ Error creating test user: {e}")
        return

    # Create authenticated client
    client = Client()
    client.login(username='test_user', password='testpass123')

    # Test the balance endpoint
    print("\n=== Testing Endpoints ===")
    test_endpoints = [
        '/api/individual/wallet/balance/',
        '/api/individual/wallet/deposit/',
        '/api/individual/wallet/withdraw/',
    ]

    for endpoint in test_endpoints:
        print(f"\nTesting: {endpoint}")
        try:
            response = client.get(endpoint)
            print(f"  Status: {response.status_code}")
            if response.status_code == 404:
                print("  ✗ 404 Not Found - URL pattern not matched")
            elif response.status_code == 200:
                print("  ✓ 200 OK - Endpoint found")
            elif response.status_code == 401:
                print("  ⚠ 401 Unauthorized - Authentication required")
            else:
                print(f"  ? {response.status_code} - Other status")
        except Exception as e:
            print(f"  ✗ Error: {e}")

    # Clean up
    user.delete()
    token.delete()
    print("\n✓ Cleanup completed")

if __name__ == '__main__':
    test_urls()
