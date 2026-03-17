#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_testing_final')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from rest_framework.authtoken.models import Token
from student_module.models import User

def get_or_create_token(username=None):
    if username is None and len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        username = 'test_dailywage'  # default

    user = User.objects.filter(username=username).first()
    if not user:
        print(f"User {username} not found")
        return None

    token, created = Token.objects.get_or_create(user=user)
    print(f"Token for {user.username}: {token.key}")
    return token.key

if __name__ == '__main__':
    get_or_create_token()
