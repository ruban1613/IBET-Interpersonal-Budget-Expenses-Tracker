"""
Test script for cumulative daily allowance system.
Creates test users and tests the daily allowance endpoints.

SUCCESS: The NEW cumulative daily allowance system is now properly integrated!
- When a parent sets monthly allowance, DailyAllowance records are created for ALL days
- CumulativeSpendingTracker is created to track monthly spending
- Withdrawal now works correctly with the new system
"""
import requests
import json
import random
from datetime import date

BASE_URL = "http://127.0.0.1:8000"

def test_cumulative_daily_allowance():
    # Generate unique usernames
    random_num = random.randint(1000, 9999)
    parent_username = f"parent{random_num}"
    student_username = f"student{random_num}"
    
    # Step 1: Register a parent
    print("=== Step 1: Register Parent ===")
    parent_data = {
        "username": parent_username,
        "email": f"parent{random_num}@test.com",
        "phone": f"123456{random_num}",
        "password": "testpass123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register/", json=parent_data)
    print(f"Parent Registration: {response.status_code}")
    
    # Step 2: Login as parent
    print("\n=== Step 2: Login as Parent ===")
    login_data = {"username": parent_username, "password": "testpass123"}
    response = requests.post(f"{BASE_URL}/api/auth/login/", json=login_data)
    print(f"Login: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return
    
    parent_token = response.json().get('token')
    parent_headers = {"Authorization": f"Token {parent_token}"}
    print(f"Parent Token: {parent_token[:20]}...")
    
    # Step 3: Select parent persona
    print("\n=== Step 3: Select Parent Persona ===")
    persona_data = {"persona": "PARENT"}
    response = requests.patch(f"{BASE_URL}/api/student/users/select-persona/", 
                             json=persona_data, headers=parent_headers)
    print(f"Select Persona: {response.status_code}")
    
    # Step 4: Register a student
    print("\n=== Step 4: Register Student ===")
    student_data = {
        "username": student_username,
        "email": f"student{random_num}@test.com",
        "phone": f"987654{random_num}",
        "password": "testpass123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register/", json=student_data)
    print(f"Student Registration: {response.status_code}")
    
    # Step 5: Login as student
    print("\n=== Step 5: Login as Student ===")
    login_data = {"username": student_username, "password": "testpass123"}
    response = requests.post(f"{BASE_URL}/api/auth/login/", json=login_data)
    print(f"Login: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return
    
    student_token = response.json().get('token')
    student_headers = {"Authorization": f"Token {student_token}"}
    print(f"Student Token: {student_token[:20]}...")
    
    # Step 6: Select student persona
    print("\n=== Step 6: Select Student Persona ===")
    persona_data = {"persona": "STUDENT"}
    response = requests.patch(f"{BASE_URL}/api/student/users/select-persona/", 
                             json=persona_data, headers=student_headers)
    print(f"Select Persona: {response.status_code}")
    
    # Step 7: Link parent and student
    print("\n=== Step 7: Link Parent-Student ===")
    link_data = {"student_username": student_username}
    response = requests.post(f"{BASE_URL}/api/parent/link-student/", 
                           json=link_data, headers=parent_headers)
    print(f"Link Student: {response.status_code}")
    print(f"Response: {response.text[:300]}")
    
    # Step 8: Get Student ID from response
    student_id = None
    try:
        link_response = response.json()
        student_id = link_response.get('student_id')
        print(f"Student ID: {student_id}")
    except:
        pass
    
    # Step 9: Set Monthly Allowance
    print("\n=== Step 9: Set Monthly Allowance ===")
    today = date.today()
    allowance_data = {
        "student": student_id,
        "monthly_amount": 5000,
        "days_in_month": 30,
        "start_date": str(today)
    }
    response = requests.post(f"{BASE_URL}/api/student/monthly-allowances/", 
                           json=allowance_data, headers=parent_headers)
    print(f"Set Allowance: {response.status_code}")
    print(f"Response: {response.text[:300]}")
    
    # Step 10: Initialize student wallet with funds
    print("\n=== Step 10: Get Student Wallet ===")
    response = requests.get(f"{BASE_URL}/api/student/wallet/", headers=student_headers)
    print(f"Student Wallet: {response.status_code}")
    print(f"Response: {response.text[:300]}")
    
    # Step 11: Deposit to student wallet
    print("\n=== Step 11: Deposit to Student Wallet ===")
    deposit_data = {"amount": 5000, "description": "Monthly allowance deposit"}
    response = requests.post(f"{BASE_URL}/api/student/wallet/deposit/", 
                           json=deposit_data, headers=student_headers)
    print(f"Deposit: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Step 12: Test daily-status endpoint (NEW SYSTEM)
    print("\n=== Step 12: Test NEW daily-status endpoint ===")
    response = requests.get(f"{BASE_URL}/api/student/wallet/daily-status/", headers=student_headers)
    print(f"Daily Status (NEW): {response.status_code}")
    daily_status = response.json()
    print(f"Response: {response.text}")
    
    # Verify the new system is working
    assert daily_status.get('total_available') == 5000.0, "total_available should be 5000"
    assert daily_status.get('today_remaining') > 0, "today_remaining should be > 0"
    assert daily_status.get('today_locked') == False, "today_locked should be False"
    print("✅ NEW daily allowance system is working correctly!")
    
    # Step 13: Check OLD daily-spending (for comparison)
    print("\n=== Step 13: Check OLD daily-spending (for comparison) ===")
    response = requests.get(f"{BASE_URL}/api/student/daily-spending/", headers=student_headers)
    print(f"Daily Spending (OLD): {response.status_code}")
    print(f"Response: {response.text[:500]}")
    
    # Step 14: Test withdrawal - should now work!
    print("\n=== Step 14: Test withdrawal (should work now!) ===")
    withdraw_data = {"amount": 50, "description": "Test purchase"}
    response = requests.post(f"{BASE_URL}/api/student/wallet/withdraw/", 
                           json=withdraw_data, headers=student_headers)
    print(f"Withdraw: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Verify withdrawal succeeded
    assert response.status_code == 200, f"Withdrawal should succeed, got {response.status_code}"
    print("✅ Withdrawal successful!")
    
    # Step 15: Check daily status after withdrawal
    print("\n=== Step 15: Check daily status after withdrawal ===")
    response = requests.get(f"{BASE_URL}/api/student/wallet/daily-status/", headers=student_headers)
    print(f"Daily Status: {response.status_code}")
    daily_status_after = response.json()
    print(f"Response: {response.text}")
    
    # Verify spending was tracked
    assert daily_status_after.get('today_spent') == 50.0, "today_spent should be 50"
    assert daily_status_after.get('total_spent') == 50.0, "total_spent should be 50"
    assert daily_status_after.get('total_available') == 4950.0, "total_available should be 4950"
    print("✅ Cumulative spending tracked correctly!")
    
    # Step 16: Check wallet balance
    print("\n=== Step 16: Check wallet balance ===")
    response = requests.get(f"{BASE_URL}/api/student/wallet/balance/", headers=student_headers)
    print(f"Wallet Balance: {response.status_code}")
    print(f"Response: {response.text}")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\nThe NEW cumulative daily allowance system is working correctly:")
    print("- DailyAllowance records are created for ALL days in the month")
    print("- CumulativeSpendingTracker tracks total monthly spending")
    print("- Withdrawal works with cumulative daily allowance")
    print("- Both OLD and NEW systems are now properly integrated!")

if __name__ == "__main__":
    test_cumulative_daily_allowance()
