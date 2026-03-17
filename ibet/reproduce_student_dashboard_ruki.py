import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from student_module.views import StudentDashboardView

User = get_user_model()

def test_student_dashboard(username):
    factory = APIRequestFactory()
    view = StudentDashboardView.as_view()
    
    try:
        student = User.objects.get(username=username)
        print(f"Testing dashboard for student: {student.username}")
        request = factory.get('/api/student/dashboard/')
        force_authenticate(request, user=student)
        
        response = view(request)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 500:
            print("Error Response:", response.data)
        else:
            print("Success!")
    except Exception as e:
        print(f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_student_dashboard('Ruki16')
