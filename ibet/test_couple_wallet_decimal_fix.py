import requests
import json
import time

# Base URL
BASE_URL = "http://127.0.0.1:8000"

# Token for couple user
TOKEN = "59eaac1485e895db9a0ff262bb8fdc0f73b33494"
HEADERS = {"Authorization": f"Token {TOKEN}", "Content-Type": "application/json"}

def test_endpoint(method, endpoint, data=None, expected_status=200, description=""):
    url = f"{BASE_URL}/api/couple/wallet/{endpoint}/"
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=HEADERS)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=HEADERS, data=json.dumps(data) if data else None)
        else:
            print(f"Unsupported method: {method}")
            return False

        print(f"{description}: Status {response.status_code} (Expected: {expected_status})")
        if response.status_code == expected_status:
            if response.status_code == 200:
                print(f"  Response: {response.json()}")
            elif response.status_code in [400, 404, 429]:
                print(f"  Error: {response.json()}")
            print("  ✅ PASS")
            return True
        else:
            print(f"  ❌ FAIL - Unexpected status")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"  Exception: {e}")
        return False

def main():
    print("Thorough Testing for Couple Wallet Decimal Fix")
    print("=" * 60)

    all_passed = True

    # 1. Test balance endpoint
    print("\n1. Testing balance endpoint")
    all_passed &= test_endpoint('GET', 'balance', description="Get balance")

    # 2. Test deposit endpoint - Happy path
    print("\n2. Testing deposit endpoint")
    all_passed &= test_endpoint('POST', 'deposit', data={"amount": "100.50", "description": "Test deposit"}, description="Deposit valid amount")

    # Edge cases for deposit
    all_passed &= test_endpoint('POST', 'deposit', data={"amount": "0", "description": "Zero deposit"}, expected_status=400, description="Deposit zero amount")
    all_passed &= test_endpoint('POST', 'deposit', data={"amount": "-10", "description": "Negative deposit"}, expected_status=400, description="Deposit negative amount")
    all_passed &= test_endpoint('POST', 'deposit', data={"amount": "abc", "description": "Invalid string"}, expected_status=400, description="Deposit invalid string")
    all_passed &= test_endpoint('POST', 'deposit', data={"amount": "1.2.3", "description": "Malformed decimal"}, expected_status=400, description="Deposit malformed decimal")
    all_passed &= test_endpoint('POST', 'deposit', data={"amount": "0.0000001", "description": "Very small decimal"}, description="Deposit very small decimal")
    all_passed &= test_endpoint('POST', 'deposit', data={"amount": "999999999999.99", "description": "Large decimal"}, description="Deposit large decimal")

    # 3. Test withdraw endpoint - Happy path
    print("\n3. Testing withdraw endpoint")
    all_passed &= test_endpoint('POST', 'withdraw', data={"amount": "50.25", "description": "Test withdrawal"}, description="Withdraw valid amount")

    # Edge cases for withdraw
    all_passed &= test_endpoint('POST', 'withdraw', data={"amount": "0", "description": "Zero withdrawal"}, expected_status=400, description="Withdraw zero amount")
    all_passed &= test_endpoint('POST', 'withdraw', data={"amount": "-5", "description": "Negative withdrawal"}, expected_status=400, description="Withdraw negative amount")
    all_passed &= test_endpoint('POST', 'withdraw', data={"amount": "xyz", "description": "Invalid string"}, expected_status=400, description="Withdraw invalid string")
    all_passed &= test_endpoint('POST', 'withdraw', data={"amount": "1000000", "description": "Insufficient funds"}, expected_status=400, description="Withdraw insufficient funds")
    all_passed &= test_endpoint('POST', 'withdraw', data={"amount": "0.0000001", "description": "Very small decimal"}, description="Withdraw very small decimal")

    # 4. Test transfer_to_emergency endpoint - Happy path
    print("\n4. Testing transfer_to_emergency endpoint")
    all_passed &= test_endpoint('POST', 'transfer_to_emergency', data={"amount": "20.00", "description": "Emergency transfer"}, description="Transfer to emergency valid")

    # Edge cases
    all_passed &= test_endpoint('POST', 'transfer_to_emergency', data={"amount": "0", "description": "Zero transfer"}, expected_status=400, description="Transfer zero to emergency")
    all_passed &= test_endpoint('POST', 'transfer_to_emergency', data={"amount": "-1", "description": "Negative transfer"}, expected_status=400, description="Transfer negative to emergency")
    all_passed &= test_endpoint('POST', 'transfer_to_emergency', data={"amount": "invalid", "description": "Invalid amount"}, expected_status=400, description="Transfer invalid to emergency")
    all_passed &= test_endpoint('POST', 'transfer_to_emergency', data={"amount": "50000", "description": "Insufficient funds"}, expected_status=400, description="Transfer insufficient to emergency")

    # 5. Test transfer_to_goals endpoint - Happy path
    print("\n5. Testing transfer_to_goals endpoint")
    all_passed &= test_endpoint('POST', 'transfer_to_goals', data={"amount": "30.00", "goal_name": "Vacation"}, description="Transfer to goals valid")

    # Edge cases
    all_passed &= test_endpoint('POST', 'transfer_to_goals', data={"amount": "0", "goal_name": "Zero goal"}, expected_status=400, description="Transfer zero to goals")
    all_passed &= test_endpoint('POST', 'transfer_to_goals', data={"amount": "-2", "goal_name": "Negative goal"}, expected_status=400, description="Transfer negative to goals")
    all_passed &= test_endpoint('POST', 'transfer_to_goals', data={"amount": "bad", "goal_name": "Invalid goal"}, expected_status=400, description="Transfer invalid to goals")
    all_passed &= test_endpoint('POST', 'transfer_to_goals', data={"amount": "100000", "goal_name": "Insufficient goal"}, expected_status=400, description="Transfer insufficient to goals")

    # 6. Test generate-otp endpoint
    print("\n6. Testing generate-otp endpoint")
    otp_response = test_endpoint('POST', 'generate-otp', data={"operation_type": "deposit", "amount": "10.00", "description": "OTP for deposit"}, description="Generate OTP for deposit")
    all_passed &= otp_response
    if otp_response:
        # Assuming response has otp_request_id, but since it's not returned in response, we can't verify easily without parsing
        # For simplicity, assume it works if status 201
        pass

    # Edge cases for generate-otp
    all_passed &= test_endpoint('POST', 'generate-otp', data={"operation_type": "", "amount": "10.00"}, expected_status=400, description="Generate OTP no operation type")
    all_passed &= test_endpoint('POST', 'generate-otp', data={"operation_type": "deposit", "amount": "invalid"}, expected_status=400, description="Generate OTP invalid amount")

    # 7. Test welcome endpoint
    print("\n7. Testing welcome endpoint")
    all_passed &= test_endpoint('GET', 'welcome', description="Welcome endpoint")

    # 8. Test monthly_summary endpoint
    print("\n8. Testing monthly_summary endpoint")
    all_passed &= test_endpoint('GET', 'monthly_summary', description="Monthly summary")

    # 9. Test transactions endpoint
    print("\n9. Testing transactions endpoint")
    all_passed &= test_endpoint('GET', 'transactions', description="Get transactions")

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed! Decimal fix is working correctly.")
    else:
        print("❌ Some tests failed. Review the output above.")

if __name__ == "__main__":
    main()
