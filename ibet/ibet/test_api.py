#!/usr/bin/env python
import requests
import json

BASE_URL = 'http://127.0.0.1:8000'
TOKEN = 'c9dfd93eaea058a9e763a214a03833b5b7bb289c'
HEADERS = {
    'Authorization': f'Token {TOKEN}',
    'Content-Type': 'application/json'
}

def test_add_earnings():
    """Test add earnings endpoint - should create wallet if not exists"""
    url = f'{BASE_URL}/api/dailywage/wallet/add-earnings/'
    data = {
        'amount': '100.00',
        'description': 'Test earnings'
    }

    print("Testing add-earnings endpoint...")
    response = requests.post(url, headers=HEADERS, data=json.dumps(data))
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    return response

def test_balance():
    """Test balance endpoint"""
    url = f'{BASE_URL}/api/dailywage/wallet/balance/'

    print("Testing balance endpoint...")
    response = requests.get(url, headers=HEADERS)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    return response

def test_withdraw():
    """Test withdraw endpoint"""
    url = f'{BASE_URL}/api/dailywage/wallet/withdraw/'
    data = {
        'amount': '50.00',
        'description': 'Test withdrawal'
    }

    print("Testing withdraw endpoint...")
    response = requests.post(url, headers=HEADERS, data=json.dumps(data))
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    return response

def test_transfer_to_emergency():
    """Test transfer to emergency fund endpoint"""
    url = f'{BASE_URL}/api/dailywage/wallet/transfer-to-emergency/'
    data = {
        'amount': '20.00'
    }

    print("Testing transfer-to-emergency endpoint...")
    response = requests.post(url, headers=HEADERS, data=json.dumps(data))
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    return response

def test_weekly_summary():
    """Test weekly summary endpoint"""
    url = f'{BASE_URL}/api/dailywage/wallet/weekly-summary/'

    print("Testing weekly-summary endpoint...")
    response = requests.get(url, headers=HEADERS)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    return response

if __name__ == '__main__':
    print("Starting API tests for daily wage wallet...")
    print("=" * 50)

    # Test 1: Add earnings (should create wallet)
    test_add_earnings()
    print()

    # Test 2: Check balance
    test_balance()
    print()

    # Test 3: Withdraw
    test_withdraw()
    print()

    # Test 4: Transfer to emergency
    test_transfer_to_emergency()
    print()

    # Test 5: Weekly summary
    test_weekly_summary()
    print()

    print("API tests completed!")
