#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_testing_final')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

def create_edge_test_users():
    User = get_user_model()

    # Create test users for different modules
    users_data = [
        {'username': 'edge_test_individual', 'email': 'edge_individual@test.com', 'persona': 'INDIVIDUAL'},
        {'username': 'edge_test_couple1', 'email': 'edge_couple1@test.com', 'persona': 'INDIVIDUAL'},
        {'username': 'edge_test_couple2', 'email': 'edge_couple2@test.com', 'persona': 'INDIVIDUAL'},
        {'username': 'edge_test_dailywage', 'email': 'edge_dailywage@test.com', 'persona': 'DAILY_WAGE'},
        {'username': 'edge_test_retiree', 'email': 'edge_retiree@test.com', 'persona': 'RETIREE'},
    ]

    for user_data in users_data:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'persona': user_data['persona']
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            # Create token for the user
            Token.objects.get_or_create(user=user)
            print(f'Created user: {user.username}')
        else:
            # Ensure token exists
            Token.objects.get_or_create(user=user)
            print(f'User already exists: {user.username}')

if __name__ == '__main__':
    create_edge_test_users()
