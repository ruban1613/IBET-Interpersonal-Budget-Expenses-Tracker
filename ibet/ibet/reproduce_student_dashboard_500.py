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

def test_student_dashboard():
    factory = APIRequestFactory()
    view = StudentDashboardView.as_view()
    
    # Test for Student
    student = User.objects.filter(persona='STUDENT').first()
    if student:
        print(f"Testing dashboard for student: {student.username}")
        request = factory.get('/api/student/dashboard/')
        force_authenticate(request, user=student)
        try:
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
    else:
        print("No student user found")

if __name__ == "__main__":
    test_student_dashboard()
