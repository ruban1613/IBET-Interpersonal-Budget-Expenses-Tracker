import os
import django
from decimal import Decimal
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from student_module.models import User, MonthlyAllowance, Wallet, DailySpending, DailyAllowance, CumulativeSpendingTracker, MonthlySpendingSummary
from rest_framework.test import APIRequestFactory, force_authenticate
from student_module.views import MonthlyAllowanceViewSet

def reproduce():
    factory = APIRequestFactory()
    
    # Get or create a parent and student
    parent = User.objects.filter(username='test_parent').first()
    if not parent:
        parent = User.objects.create(username='test_parent', email='parent@test.com')
    parent.persona = 'PARENT'
    parent.save()
    
    student = User.objects.filter(username='test_student').first()
    if not student:
        student = User.objects.create(username='test_student', email='student@test.com')
    student.persona = 'STUDENT'
    student.save()
    
    # Ensure an allowance exists
    MonthlyAllowance.objects.get_or_create(
        student=student,
        defaults={
            'parent': parent,
            'monthly_amount': Decimal('100.00'),
            'days_in_month': 30,
            'start_date': timezone.now().date(),
            'is_active': True
        }
    )

    # Try to UPDATE allowance
    data = {
        'student': student.id,
        'monthly_amount': '15.00',
        'days_in_month': 30
    }
    
    request = factory.post('/api/student/monthly-allowances/', data, format='json')
    force_authenticate(request, user=parent)
    
    view = MonthlyAllowanceViewSet.as_view({'post': 'create'})
    try:
        response = view(request)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 500:
            print("Reproduced 500 Error")
        else:
            print(f"Response Data: {response.data}")
    except Exception as e:
        print(f"Exception caught: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reproduce()
