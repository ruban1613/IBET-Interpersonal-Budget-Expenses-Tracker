import os
import django
import sys
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from student_module.views import MonthlyAllowanceViewSet

User = get_user_model()

def test_monthly_allowance_create(username, student_id):
    factory = APIRequestFactory()
    view = MonthlyAllowanceViewSet.as_view({'post': 'create'})
    
    try:
        user = User.objects.get(username=username)
        print(f"Testing allowance create for user: {user.username} student_id: {student_id}")
        
        # Simulated frontend data
        data = {
            'student': student_id,
            'monthly_amount': 10000,
            'daily_allowance': 210,
            'days_in_month': 30
        }
        
        request = factory.post('/api/student/monthly-allowances/', data, format='json')
        force_authenticate(request, user=user)
        
        response = view(request)
        print(f"Status Code: {response.status_code}")
        if response.status_code in [200, 201, 202]:
            print("Success! Data:", response.data)
        else:
            print("Error Response:", response.data if hasattr(response, 'data') else "No data")
                
    except Exception as e:
        print(f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # From the user's logs: student_id 49 (Ruki16)
    test_monthly_allowance_create('keeru', 49)
