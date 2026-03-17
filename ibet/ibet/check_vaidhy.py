import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from institute_module.models import InstituteStudentProfile
from student_module.models import Wallet

User = get_user_model()

print("--- DB INVESTIGATION ---")
users = User.objects.filter(username__icontains='vaidhy')
print(f"Found {users.count()} users matching 'vaidhy'")

for u in users:
    print(f"\nUser: {u.username}")
    print(f"  ID: {u.id}")
    print(f"  Persona: {u.persona}")
    print(f"  Email: {u.email}")
    
    profile = InstituteStudentProfile.objects.filter(user=u).first()
    if profile:
        print(f"  Institute Link: {profile.institute.name}")
        print(f"  Student Name: {profile.student_name}")
    else:
        print(f"  Institute Link: NONE")
        
    wallet = Wallet.objects.filter(user=u).first()
    if wallet:
        print(f"  Wallet: FOUND (Balance: {wallet.balance})")
    else:
        print(f"  Wallet: MISSING")

print("\n--- ALL INSTITUTE STUDENT PROFILES ---")
profiles = InstituteStudentProfile.objects.all()
for p in profiles:
    if 'vaidhy' in p.student_name.lower():
        print(f"Profile for name: {p.student_name}")
        print(f"  User Linked: {p.user.username if p.user else 'NONE'}")
        print(f"  Institute: {p.institute.name}")
