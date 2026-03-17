#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_testing_final')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

def list_users_and_tokens():
    User = get_user_model()
    users = User.objects.all()
    for user in users:
        token = Token.objects.filter(user=user).first()
        token_key = token.key if token else 'No token'
        print(f"User: {user.username}, Token: {token_key}")

if __name__ == '__main__':
    list_users_and_tokens()
