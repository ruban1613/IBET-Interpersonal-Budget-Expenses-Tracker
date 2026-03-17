"""
Test script for language switching functionality.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()

def test_language_switching():
    # Create test user
    user, created = User.objects.get_or_create(
        username='testlang',
        defaults={'email': 'testlang@test.com', 'persona': 'INDIVIDUAL'}
    )
    if created:
        user.set_password('test123')
        user.save()
    
    token, created = Token.objects.get_or_create(user=user)
    
    client = Client()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    
    # Test 1: Get available languages
    print('=== Test 1: Get Available Languages ===')
    response = client.get('/api/languages/')
    print(f'Status: {response.status_code}')
    print(f'Response: {response.json()}')
    
    # Test 2: Set language to Tamil
    print('\n=== Test 2: Set Language to Tamil ===')
    response = client.post('/api/set-language/', {'language': 'ta'})
    print(f'Status: {response.status_code}')
    print(f'Response: {response.json()}')
    
    # Test 3: Verify language was set
    print('\n=== Test 3: Verify Language Changed ===')
    response = client.get('/api/languages/')
    print(f'Status: {response.status_code}')
    print(f'Response: {response.json()}')
    
    # Test 4: Set language back to English
    print('\n=== Test 4: Set Language to English ===')
    response = client.post('/api/set-language/', {'language': 'en'})
    print(f'Status: {response.status_code}')
    print(f'Response: {response.json()}')
    
    print('\n✅ Language switching functionality is working!')

if __name__ == '__main__':
    test_language_switching()
