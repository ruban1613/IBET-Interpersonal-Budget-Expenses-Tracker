#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_testing_final')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.contrib.auth import get_user_model

def list_users():
    User = get_user_model()
    users = User.objects.all()
    print("-" * 50)
    print(f"{'Username':<15} | {'UID':<15} | {'Persona':<15}")
    print("-" * 50)
    for user in users:
        print(f"{user.username:<15} | {str(user.uid):<15} | {str(user.persona):<15}")
    print("-" * 50)

if __name__ == '__main__':
    list_users()
