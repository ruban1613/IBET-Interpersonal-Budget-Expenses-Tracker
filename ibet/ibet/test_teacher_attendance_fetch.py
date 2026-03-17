import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from institute_module.views import StudentAttendanceViewSet

User = get_user_model()

def test_attendance_for_teacher(username):
    factory = APIRequestFactory()
    view = StudentAttendanceViewSet.as_view({'get': 'list'})
    
    try:
        user = User.objects.get(username=username)
        print(f"Testing for teacher: {user.username} (Persona: {user.persona})")
        
        request = factory.get('/api/institute/attendance/?month=3&year=2026')
        force_authenticate(request, user=user)
        
        response = view(request)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"Found {len(response.data)} records.")
            for r in response.data:
                print(f" - {r['student_name']} on {r['date']}: {r['status']}")
        else:
            print("Error:", response.data)
                
    except User.DoesNotExist:
        print(f"User {username} not found")
    except Exception as e:
        print(f"Exception: {str(e)}")

if __name__ == "__main__":
    test_attendance_for_teacher('suriya')
