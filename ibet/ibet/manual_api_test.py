import requests
import json

# Base URL
BASE_URL = "http://127.0.0.1:8000"

# Tokens (replace with actual tokens from get_token.py)
TOKENS = {
    "individual": "d74275e64b0b839f2f974178c880f00569df9b21",  # security_test_individual
    "couple": "59eaac1485e895db9a0ff262bb8fdc0f73b33494",     # security_test_couple1
    "dailywage": "0e239104632a153bb86bf3850d276dfe7a7906e3"     # security_test_dailywage
}

def test_endpoint(module, endpoint, token):
    # Construct URL based on module-specific routing
    if module == 'individual':
        url = f"{BASE_URL}/api/{module}/balance/"
    elif module == 'couple':
        url = f"{BASE_URL}/api/{module}/wallet/balance/"
    else:  # dailywage
        url = f"{BASE_URL}/api/{module}/balance/"
    headers = {"Authorization": f"Token {token}"}
    try:
        response = requests.get(url, headers=headers)
        print(f"{module.upper()} {endpoint.upper()}: Status {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
        else:
            print(f"  Error: {response.text}")
        return response.status_code
    except Exception as e:
        print(f"  Exception: {e}")
        return None

def main():
    print("Manual API Testing for Wallet Balance Endpoints")
    print("=" * 50)

    # Test balance endpoints
    endpoints = ["balance"]
    modules = ["individual", "couple", "dailywage"]

    for module in modules:
        token = TOKENS.get(module)
        if not token:
            print(f"No token for {module}, skipping")
            continue
        for endpoint in endpoints:
            status = test_endpoint(module, endpoint, token)
            if status == 200:
                print("  ✅ Wallet auto-creation working (200 response)")
            elif status == 404:
                print("  ❌ 404 Error - wallet not found")
            else:
                print(f"  ⚠️  Unexpected status: {status}")

    print("\nTesting completed.")

if __name__ == "__main__":
    main()
