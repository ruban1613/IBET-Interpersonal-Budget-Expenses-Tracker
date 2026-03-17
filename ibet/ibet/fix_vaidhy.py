import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from institute_module.models import InstituteStudentProfile
from student_module.models import Wallet

User = get_user_model()

print("--- FIXING VAIDHY ---")
main_user = User.objects.filter(username='Vaidhy').first()
generated_user = User.objects.filter(username='vaidhy_5100').first()

if main_user and generated_user:
    profile = InstituteStudentProfile.objects.filter(user=generated_user).first()
    if profile:
        print(f"Linking profile '{profile.student_name}' to user 'Vaidhy'")
        profile.user = main_user
        profile.save()
        
        # Ensure wallet exists for main_user
        Wallet.objects.get_or_create(user=main_user)
        print("Wallet checked/created for 'Vaidhy'")
        
        # Optionally delete the generated user to avoid confusion
        print(f"Deleting redundant user '{generated_user.username}'")
        generated_user.delete()
        
        print("SUCCESS: Vaidhy is now correctly linked and can login.")
    else:
        print("Error: Could not find profile for generated user.")
else:
    print(f"Error: Users not found. Main: {main_user}, Gen: {generated_user}")
