
import os
import django
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from student_module.models import User, Wallet, DailyAllowance, PendingSpendingRequest, ParentStudentLink
from rest_framework.test import APIRequestFactory, force_authenticate
from student_module.views_wallet_new import StudentWalletViewSet

def reproduce():
    factory = APIRequestFactory()
    
    # Get or create a parent and student
    parent, _ = User.objects.get_or_create(username='test_parent_err', defaults={'email': 'parent_err@test.com'})
    student, _ = User.objects.get_or_create(username='test_student_err', defaults={'email': 'student_err@test.com'})
    
    # Ensure link
    ParentStudentLink.objects.get_or_create(parent=parent, student=student)
    
    # Ensure wallet
    wallet, _ = Wallet.objects.get_or_create(user=student, defaults={'balance': Decimal('1000.00'), 'is_locked': True})
    
    # Ensure today's allowance
    today = timezone.now().date()
    DailyAllowance.objects.get_or_create(
        student=student, 
        date=today,
        defaults={'daily_amount': Decimal('100.00'), 'remaining_amount': Decimal('0.00'), 'is_locked': True}
    )
    
    # Create OTP request
    req = PendingSpendingRequest.objects.create(
        student=student,
        parent=parent,
        amount_requested=Decimal('50.00'),
        otp_code='123456',
        expires_at=timezone.now() + timedelta(minutes=15),
        status='PENDING'
    )
    
    # Try to verify OTP
    data = {
        'otp_code': '123456',
        'request_id': req.id
    }
    
    request = factory.post('/api/student/wallet/verify-parent-otp/', data, format='json')
    force_authenticate(request, user=student)
    
    view = StudentWalletViewSet.as_view({'post': 'verify_parent_otp'})
    try:
        response = view(request)
        print(f"Status Code: {response.status_code}")
        print(f"Response Data: {response.data}")
    except Exception as e:
        print(f"Exception caught: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reproduce()
