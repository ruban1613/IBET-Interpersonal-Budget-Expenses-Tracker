import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from institute_module.views import TeacherAttendanceViewSet
from institute_module.models import TeacherProfile

User = get_user_model()

def test_teacher_attendance_creation():
    factory = APIRequestFactory()
    view = TeacherAttendanceViewSet.as_view({'post': 'create'})
    
    # Find an owner user
    owner = User.objects.filter(persona='INSTITUTE_OWNER').first()
    if not owner:
        print("No owner user found.")
        return

    # Find a teacher linked to this owner
    teacher = TeacherProfile.objects.filter(institute__owner=owner).first()
    if not teacher:
        print(f"No teacher found for owner {owner.username}.")
        return

    print(f"Testing teacher attendance for: {teacher.user.username} by owner: {owner.username}")
    
    data = {
        'teacher': teacher.id,
        'date': '2026-03-04',
        'status': 'PRESENT',
        'extra_sessions': 2,
        'remarks': 'Testing'
    }
    
    request = factory.post('/api/institute/teacher-attendance/', data, format='json')
    force_authenticate(request, user=owner)
    
    try:
        response = view(request)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 500:
            print("Received 500 error.")
            if hasattr(response, 'data'):
                print("Response data:", response.data)
        else:
            print("Success! Response:", response.data)
    except Exception as e:
        print(f"Caught Exception: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_teacher_attendance_creation()
