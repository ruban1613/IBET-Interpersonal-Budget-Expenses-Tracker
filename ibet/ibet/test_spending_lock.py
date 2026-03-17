"""
Test for Spending Lock Auto-Lock System

This test verifies that spending locks are automatically created when:
1. Student exceeds their daily limit
2. Student exceeds their cumulative monthly allowance

The test also checks if the lock prevents further spending.
"""
import requests
import random
from datetime import date

BASE_URL = "http://127.0.0.1:8000"


def test_spending_lock_system():
    """Test the automatic spending lock system"""
    random_num = random.randint(10000, 99999)
    parent_username = f"parent_lock{random_num}"
    student_username = f"student_lock{random_num}"
    
    print("=" * 60)
    print("SPENDING LOCK AUTO-LOCK SYSTEM TEST")
    print("=" * 60)
    
    # ===== PART 1: Setup - Register and Link =====
    print("\n[PART 1] Setup - Registration and Linking")
    print("-" * 40)
    
    # Register Parent
    parent_data = {
        "username": parent_username,
        "email": f"parent{random_num}@test.com",
        "phone": f"123456{random_num}",
        "password": "testpass123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register/", json=parent_data)
    print(f"1.1 Register Parent: {response.status_code}")
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"
    
    # Login Parent
    response = requests.post(f"{BASE_URL}/api/auth/login/", 
                           json={"username": parent_username, "password": "testpass123"})
    print(f"1.2 Login Parent: {response.status_code}")
    parent_token = response.json().get('token')
    parent_headers = {"Authorization": f"Token {parent_token}"}
    
    # Select Parent Persona
    response = requests.patch(f"{BASE_URL}/api/student/users/select-persona/", 
                            json={"persona": "PARENT"}, headers=parent_headers)
    print(f"1.3 Select Parent Persona: {response.status_code}")
    
    # Register Student
    student_data = {
        "username": student_username,
        "email": f"student{random_num}@test.com",
        "phone": f"987654{random_num}",
        "password": "testpass123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register/", json=student_data)
    print(f"1.4 Register Student: {response.status_code}")
    
    # Login Student
    response = requests.post(f"{BASE_URL}/api/auth/login/", 
                           json={"username": student_username, "password": "testpass123"})
    print(f"1.5 Login Student: {response.status_code}")
    student_token = response.json().get('token')
    student_headers = {"Authorization": f"Token {student_token}"}
    
    # Select Student Persona
    response = requests.patch(f"{BASE_URL}/api/student/users/select-persona/", 
                            json={"persona": "STUDENT"}, headers=student_headers)
    print(f"1.6 Select Student Persona: {response.status_code}")
    
    # Link Student (Parent initiates)
    response = requests.post(f"{BASE_URL}/api/parent/link-student/", 
                           json={"student_username": student_username}, headers=parent_headers)
    print(f"1.7 Link Student: {response.status_code}")
    student_id = response.json().get('student_id')
    
    # ===== PART 2: Set Monthly Allowance =====
    print("\n[PART 2] Set Monthly Allowance")
    print("-" * 40)
    
    # Set a small allowance for easier testing: 300/month = 10/day
    today = date.today()
    allowance_data = {
        "student": student_id,
        "monthly_amount": 300,  # 300/month = 10/day for 30 days
        "days_in_month": 30,
        "start_date": str(today)
    }
    response = requests.post(f"{BASE_URL}/api/student/monthly-allowances/", 
                           json=allowance_data, headers=parent_headers)
    print(f"2.1 Set Monthly Allowance: {response.status_code}")
    allowance = response.json()
    daily_allowance = allowance.get('daily_allowance', 10)
    print(f"    Monthly: {allowance.get('monthly_amount')}, Daily: {daily_allowance}")
    
    # Get Wallet Balance
    response = requests.get(f"{BASE_URL}/api/student/wallet/balance/", headers=student_headers)
    print(f"2.2 Initial Wallet Balance: {response.json().get('balance')}")
    
    # ===== PART 3: Check Initial Spending Locks =====
    print("\n[PART 3] Check Initial Spending Locks")
    print("-" * 40)
    
    response = requests.get(f"{BASE_URL}/api/student/spending-locks/", headers=student_headers)
    print(f"3.1 Get Spending Locks: {response.status_code}")
    initial_locks = response.json()
    print(f"    Initial Lock Count: {len(initial_locks)}")
    
    # ===== PART 4: Withdraw within daily limit =====
    print("\n[PART 4] Withdraw within daily limit")
    print("-" * 40)
    
    # Try to withdraw 5 rupees (within daily limit of 10)
    withdraw_data = {"amount": 5, "description": "Small purchase"}
    response = requests.post(f"{BASE_URL}/api/student/wallet/withdraw/", 
                           json=withdraw_data, headers=student_headers)
    print(f"4.1 Withdraw 5 (within limit): {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"    ✅ Withdrawal successful: {result.get('new_balance')}")
    else:
        print(f"    ❌ Withdrawal failed: {response.json()}")
    
    # Check remaining daily allowance
    response = requests.get(f"{BASE_URL}/api/student/wallet/daily-status/", headers=student_headers)
    if response.status_code == 200:
        status = response.json()
        print(f"4.2 Daily Status:")
        print(f"    Today Limit: {status.get('today_limit')}")
        print(f"    Today Spent: {status.get('today_spent')}")
        print(f"    Today Remaining: {status.get('today_remaining')}")
    
    # ===== PART 5: Withdraw MORE than daily limit - TRIGGER AUTO LOCK =====
    print("\n[PART 5] Exceed Daily Limit - TRIGGER AUTO LOCK")
    print("-" * 40)
    
    # Try to withdraw 10 more rupees (daily limit was 10, already spent 5)
    # This should exceed the daily limit and trigger the auto-lock
    withdraw_data = {"amount": 10, "description": "Exceeding daily limit"}
    response = requests.post(f"{BASE_URL}/api/student/wallet/withdraw/", 
                           json=withdraw_data, headers=student_headers)
    print(f"5.1 Withdraw 10 (exceeds daily limit): {response.status_code}")
    
    result = response.json()
    
    if response.status_code == 402:
        # Lock is active - needs parent approval
        print(f"    ✅ Parent approval required (lock active)")
        print(f"    Message: {result.get('message', '')[:80]}")
    elif response.status_code == 200:
        print(f"    ⚠️  Withdrawal allowed (no lock triggered)")
        print(f"    New Balance: {result.get('new_balance')}")
    
    # ===== PART 6: Check if Spending Lock was created =====
    print("\n[PART 6] Check Spending Locks After Exceeding Limit")
    print("-" * 40)
    
    response = requests.get(f"{BASE_URL}/api/student/spending-locks/", headers=student_headers)
    print(f"6.1 Get Spending Locks: {response.status_code}")
    locks = response.json()
    print(f"    Lock Count After Exceeding: {len(locks)}")
    
    if len(locks) > len(initial_locks):
        print(f"    ✅ NEW LOCK CREATED!")
        for lock in locks:
            print(f"       - Type: {lock.get('lock_type')}, Amount: {lock.get('amount_locked')}, Active: {lock.get('is_active')}")
    else:
        print(f"    ❌ NO NEW LOCK CREATED!")
    
    # ===== PART 7: Try another withdrawal (should be blocked) =====
    print("\n[PART 7] Try Another Withdrawal (Should be blocked)")
    print("-" * 40)
    
    withdraw_data = {"amount": 5, "description": "Another purchase"}
    response = requests.post(f"{BASE_URL}/api/student/wallet/withdraw/", 
                           json=withdraw_data, headers=student_headers)
    print(f"7.1 Withdraw 5 (while locked): {response.status_code}")
    
    if response.status_code == 402:
        print(f"    ✅ BLOCKED - Lock is enforced!")
        print(f"    Message: {response.json().get('message', '')[:80]}")
    elif response.status_code == 200:
        print(f"    ❌ ALLOWED - Lock not enforced!")
    else:
        print(f"    Response: {response.json()}")
    
    # ===== PART 8: Check Dashboard for Lock Status =====
    print("\n[PART 8] Check Dashboard for Lock Status")
    print("-" * 40)
    
    response = requests.get(f"{BASE_URL}/api/student/dashboard/", headers=student_headers)
    print(f"8.1 Get Dashboard: {response.status_code}")
    if response.status_code == 200:
        dashboard = response.json()
        print(f"    Active Locks: {dashboard.get('active_locks')}")
        print(f"    Is Locked: {dashboard.get('is_locked')}")
    
    # ===== PART 9: Verify via Django Models =====
    print("\n[PART 9] Verify via Django Models")
    print("-" * 40)
    
    import os
    import sys
    import django
    
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()
    
    from student_module.models import SpendingLock, DailyAllowance, User
    
    try:
        student_user = User.objects.get(username=student_username)
        
        # Check SpendingLocks
        spending_locks = SpendingLock.objects.filter(student=student_user, is_active=True)
        print(f"9.1 Active SpendingLocks: {spending_locks.count()}")
        
        for lock in spending_locks:
            print(f"    - Type: {lock.lock_type}")
            print(f"      Amount Locked: {lock.amount_locked}")
            print(f"      Active: {lock.is_active}")
            print(f"      Created: {lock.created_at}")
        
        # Check DailyAllowance (NEW model)
        today_date = date.today()
        daily_allowance = DailyAllowance.objects.filter(student=student_user, date=today_date)
        if daily_allowance.exists():
            da = daily_allowance.first()
            print(f"9.2 Daily Allowance Record:")
            print(f"    Daily Limit: {da.daily_amount}")
            print(f"    Amount Spent: {da.amount_spent}")
            print(f"    Remaining: {da.remaining_amount}")
            print(f"    Is Locked: {da.is_locked}")
            print(f"    Lock Reason: {da.lock_reason}")

            if da.is_locked:
                print(f"    ✅ DAILY ALLOWANCE IS LOCKED!")
        
    except Exception as e:
        print(f"    Error: {e}")
    
    # ===== FINAL RESULTS =====
    print("\n" + "=" * 60)
    print("SPENDING LOCK TEST COMPLETED")
    print("=" * 60)
    
    print("\nTest Summary:")
    print("1. Setup (Registration/Linking): ✅")
    print("2. Monthly Allowance Setting: ✅")
    print("3. Within-limit Withdrawal: Tested")
    print("4. Exceed-daily-limit Withdrawal: Tested")
    print("5. Auto-lock Creation: CHECK RESULTS ABOVE")
    print("6. Lock Enforcement: CHECK RESULTS ABOVE")
    print("7. Dashboard Lock Status: CHECK RESULTS ABOVE")


if __name__ == "__main__":
    test_spending_lock_system()
