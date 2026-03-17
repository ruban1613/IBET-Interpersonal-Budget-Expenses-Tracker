import requests
import json

BASE_URL = "http://127.0.0.1:8000"

# Login as student
login_data = {"username": "keeru", "password": "testpass123"}
response = requests.post(f"{BASE_URL}/api/auth/login/", json=login_data)
print(f"Login: {response.status_code}")
if response.status_code == 200:
    token = response.json().get('token')
    print(f"Token: {token[:20]}...")
    
    headers = {"Authorization": f"Token {token}"}
    
    # Test monthly-allowances
    r1 = requests.get(f"{BASE_URL}/api/student/monthly-allowances/", headers=headers)
    print(f"\nmonthly-allowances: {r1.status_code}")
    print(f"Response: {r1.text[:500]}")
    
    # Test monthly-summaries
    r2 = requests.get(f"{BASE_URL}/api/student/monthly-summaries/", headers=headers)
    print(f"\nmonthly-summaries: {r2.status_code}")
    print(f"Response: {r2.text[:500]}")
    
    # Test daily-spending
    r3 = requests.get(f"{BASE_URL}/api/student/daily-spending/", headers=headers)
    print(f"\ndaily-spending: {r3.status_code}")
    print(f"Response: {r3.text[:500]}")
    
    # Test wallet
    r4 = requests.get(f"{BASE_URL}/api/student/wallet/", headers=headers)
    print(f"\nwallet: {r4.status_code}")
    print(f"Response: {r4.text[:500]}")
else:
    print(f"Login failed: {response.text}")
