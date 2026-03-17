#!/usr/bin/env python
"""
Comprehensive Security Testing for Wallet Modules
Tests OTP limits, suspicious activity detection, authentication bypass attempts, and security vulnerabilities
"""
import requests
import json
import sys
import os
import time
from datetime import datetime, timedelta

# Add the IBET directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'IBET'))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_testing_final')
import django
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from django.core.cache import cache
from individual_module.models_wallet import IndividualWallet
from couple_module.models_wallet import CoupleWallet
from dailywage_module.models_wallet import DailyWageWallet
from retiree_module.models_wallet import RetireeWallet

BASE_URL = 'http://127.0.0.1:8000/api'

def setup_test_users():
    """Set up test users for security testing"""
    print("🔧 Setting up test users for security testing...")

    User = get_user_model()

    # Create test users for different modules
    users = {}

    # Individual module user
    individual_user, created = User.objects.get_or_create(
        username='security_test_individual',
        defaults={'email': 'security_individual@test.com', 'persona': 'INDIVIDUAL'}
    )
    individual_user.set_password('testpass123')
    individual_user.save()
    users['individual'] = individual_user

    # Couple module users
    couple_user1, created = User.objects.get_or_create(
        username='security_test_couple1',
        defaults={'email': 'security_couple1@test.com', 'persona': 'INDIVIDUAL'}
    )
    couple_user1.set_password('testpass123')
    couple_user1.save()
    users['couple1'] = couple_user1

    # Second couple user
    couple_user2, created = User.objects.get_or_create(
        username='security_test_couple2',
        defaults={'email': 'security_couple2@test.com', 'persona': 'INDIVIDUAL'}
    )
    couple_user2.set_password('testpass123')
    couple_user2.save()
    users['couple2'] = couple_user2

    # Daily wage user
    dailywage_user, created = User.objects.get_or_create(
        username='security_test_dailywage',
        defaults={'email': 'security_dailywage@test.com', 'persona': 'DAILY_WAGE'}
    )
    dailywage_user.set_password('testpass123')
    dailywage_user.save()
    users['dailywage'] = dailywage_user

    # Unauthorized user
    unauthorized_user, created = User.objects.get_or_create(
        username='security_test_unauthorized',
        defaults={'email': 'security_unauthorized@test.com', 'persona': 'INDIVIDUAL'}
    )
    unauthorized_user.set_password('testpass123')
    unauthorized_user.save()
    users['unauthorized'] = unauthorized_user

    # Create wallets for test users
    print("🔧 Creating wallets for test users...")

    # Individual wallet
    individual_wallet, created = IndividualWallet.objects.get_or_create(
        user=individual_user,
        defaults={'balance': Decimal('1000.00')}
    )
    print(f"   Individual wallet: {'Created' if created else 'Exists'} (Balance: {individual_wallet.balance})")

    # Couple wallet - create directly with partners
    couple_wallet, created = CoupleWallet.objects.get_or_create(
        partner1=couple_user1,
        partner2=couple_user2,
        defaults={'balance': Decimal('2000.00')}
    )
    print(f"   Couple wallet: {'Created' if created else 'Exists'} (Balance: {couple_wallet.balance})")

    # Daily wage wallet
    dailywage_wallet, created = DailyWageWallet.objects.get_or_create(
        user=dailywage_user,
        defaults={'balance': Decimal('500.00'), 'weekly_target': Decimal('1000.00')}
    )
    print(f"   Daily wage wallet: {'Created' if created else 'Exists'} (Balance: {dailywage_wallet.balance})")

    # Retiree wallet for unauthorized user
    retiree_wallet, created = RetireeWallet.objects.get_or_create(
        user=unauthorized_user,
        defaults={'balance': Decimal('5000.00'), 'pension_balance': Decimal('2000.00')}
    )
    print(f"   Retiree wallet: {'Created' if created else 'Exists'} (Balance: {retiree_wallet.balance})")

    print("✅ Security test users and wallets setup complete")
    for module, user in users.items():
        print(f"   {module.title()}: {user.username} (ID: {user.id})")
    return users

def get_auth_token(username, password):
    """Get authentication token for user"""
    url = f"{BASE_URL}/token-auth/"
    data = {'username': username, 'password': password}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json().get('token')
    return None

def test_otp_generation_limits(token, module_name):
    """Test OTP generation rate limiting"""
    print(f"\n🔐 Testing OTP Generation Limits for {module_name}...")

    headers = {'Authorization': f'Token {token}'}

    # Test rapid OTP generation (should be rate limited)
    print("   Testing rapid OTP generation (rate limiting)...")
    otp_requests = []

    for i in range(10):  # Try to generate 10 OTPs rapidly
        data = {
            'operation_type': 'withdrawal',
            'amount': f'{50 + i}.00',
            'description': f'Rate limit test {i+1}'
        }

        start_time = time.time()
        if module_name == 'individual':
            response = requests.post(f"{BASE_URL}/individual/wallet/generate-otp/", headers=headers, json=data)
        elif module_name == 'couple':
            response = requests.post(f"{BASE_URL}/couple/wallet/generate-otp/", headers=headers, json=data)
        elif module_name == 'dailywage':
            response = requests.post(f"{BASE_URL}/dailywage/wallet/generate-otp/", headers=headers, json=data)
        else:
            response = requests.post(f"{BASE_URL}/individual/wallet/generate-otp/", headers=headers, json=data)

        end_time = time.time()
        response_time = end_time - start_time

        otp_requests.append({
            'attempt': i+1,
            'status_code': response.status_code,
            'response_time': response_time,
            'success': response.status_code in [201, 429]  # 429 is rate limit
        })

        print(f"     Attempt {i+1}: Status {response.status_code}, Time: {response_time:.2f}s")

        # Small delay between requests
        time.sleep(0.1)

    # Analyze results
    successful_requests = sum(1 for req in otp_requests if req['status_code'] == 201)
    rate_limited_requests = sum(1 for req in otp_requests if req['status_code'] == 429)

    print(f"   ✅ Successful OTP generations: {successful_requests}")
    print(f"   ✅ Rate limited requests: {rate_limited_requests}")

    if rate_limited_requests > 0:
        print("   ✅ Rate limiting is working correctly")
    else:
        print("   ⚠️  No rate limiting detected - may need investigation")

    return otp_requests

def test_otp_verification_failures(token, module_name):
    """Test OTP verification with various failure scenarios"""
    print(f"\n🔐 Testing OTP Verification Failures for {module_name}...")

    headers = {'Authorization': f'Token {token}'}

    # First generate a valid OTP
    data = {
        'operation_type': 'withdrawal',
        'amount': '100.00',
        'description': 'OTP verification test'
    }

    if module_name == 'individual':
        response = requests.post(f"{BASE_URL}/individual/wallet/generate-otp/", headers=headers, json=data)
    elif module_name == 'couple':
        response = requests.post(f"{BASE_URL}/couple/wallet/generate-otp/", headers=headers, json=data)
    elif module_name == 'dailywage':
        response = requests.post(f"{BASE_URL}/dailywage/wallet/generate-otp/", headers=headers, json=data)
    else:
        response = requests.post(f"{BASE_URL}/individual/wallet/generate-otp/", headers=headers, json=data)

    if response.status_code != 201:
        print(f"   ❌ Failed to generate OTP for testing: {response.status_code}")
        return

    otp_data = response.json()
    otp_request_id = otp_data.get('otp_request_id')

    if not otp_request_id:
        print("   ❌ No OTP request ID returned")
        return

    print(f"   Generated OTP request ID: {otp_request_id}")

    # Test various failure scenarios
    failure_scenarios = [
        {'otp_code': '000000', 'description': 'Wrong OTP code'},
        {'otp_code': '12345', 'description': 'Too short OTP'},
        {'otp_code': '1234567', 'description': 'Too long OTP'},
        {'otp_code': 'abcdef', 'description': 'Non-numeric OTP'},
        {'otp_code': '', 'description': 'Empty OTP'},
        {'otp_code': '999999', 'description': 'Another wrong OTP'},
    ]

    for scenario in failure_scenarios:
        verify_data = {
            'otp_code': scenario['otp_code'],
            'otp_request_id': otp_request_id
        }

        if module_name == 'individual':
            response = requests.post(f"{BASE_URL}/individual/wallet/verify-otp/", headers=headers, json=verify_data)
        elif module_name == 'couple':
            response = requests.post(f"{BASE_URL}/couple/wallet/verify-otp/", headers=headers, json=verify_data)
        elif module_name == 'dailywage':
            response = requests.post(f"{BASE_URL}/dailywage/wallet/verify-otp/", headers=headers, json=verify_data)
        else:
            response = requests.post(f"{BASE_URL}/individual/wallet/verify-otp/", headers=headers, json=verify_data)

        print(f"     {scenario['description']}: Status {response.status_code}")

        if response.status_code == 400:
            print("       ✅ Correctly rejected invalid OTP")
        elif response.status_code == 200:
            print("       ❌ Incorrectly accepted invalid OTP - SECURITY ISSUE!")
        else:
            print(f"       ⚠️  Unexpected response: {response.status_code}")

def test_suspicious_activity_detection():
    """Test suspicious activity detection"""
    print("\n🔐 Testing Suspicious Activity Detection...")

    # This would require access to the security monitoring system
    # For now, we'll test the basic functionality

    # Test multiple failed login attempts
    print("   Testing multiple failed authentication attempts...")

    failed_attempts = 0
    for i in range(5):
        # Try to authenticate with wrong password
        response = requests.post(f"{BASE_URL}/token-auth/", json={
            'username': 'security_test_individual',
            'password': 'wrongpassword123'
        })

        if response.status_code == 400:
            failed_attempts += 1
            print(f"     Failed attempt {i+1}: Correctly rejected")
        else:
            print(f"     Failed attempt {i+1}: Unexpected response {response.status_code}")

        time.sleep(0.5)

    print(f"   ✅ Failed authentication attempts: {failed_attempts}/5")

    # Test rapid API calls (potential DoS)
    print("   Testing rapid API calls (DoS protection)...")

    token = get_auth_token('security_test_individual', 'testpass123')
    if token:
        headers = {'Authorization': f'Token {token}'}

        rapid_requests = 0
        blocked_requests = 0

        for i in range(20):  # Make 20 rapid requests
            response = requests.get(f"{BASE_URL}/individual/wallet/balance/", headers=headers)

            if response.status_code == 200:
                rapid_requests += 1
            elif response.status_code == 429:  # Rate limited
                blocked_requests += 1
                print(f"     Request {i+1}: Rate limited (429)")
                break
            else:
                print(f"     Request {i+1}: Unexpected status {response.status_code}")

            time.sleep(0.05)  # Very short delay

        print(f"   ✅ Successful requests: {rapid_requests}")
        print(f"   ✅ Rate limited requests: {blocked_requests}")

        if blocked_requests > 0:
            print("   ✅ DoS protection is working")
        else:
            print("   ⚠️  No DoS protection detected")

def test_unauthorized_access_attempts(unauthorized_token):
    """Test unauthorized access attempts"""
    print("\n🔐 Testing Unauthorized Access Attempts...")

    headers = {'Authorization': f'Token {unauthorized_token}'}

    # Try to access other users' wallet data
    endpoints_to_test = [
        ('Individual Wallet', f"{BASE_URL}/individual/wallet/balance/"),
        ('Couple Wallet', f"{BASE_URL}/couple/wallet/balance/"),
        ('Daily Wage Wallet', f"{BASE_URL}/dailywage/wallet/balance/"),
        ('Retiree Wallet', f"{BASE_URL}/retiree/wallet/balance/"),
    ]

    for endpoint_name, url in endpoints_to_test:
        response = requests.get(url, headers=headers)
        print(f"     {endpoint_name}: Status {response.status_code}")

        if response.status_code in [403, 404]:
            print("       ✅ Correctly denied access")
        elif response.status_code == 200:
            print("       ❌ Incorrectly granted access - SECURITY ISSUE!")
        else:
            print(f"       ⚠️  Unexpected response: {response.status_code}")

def test_malformed_requests(token, module_name):
    """Test malformed and malicious requests"""
    print(f"\n🔐 Testing Malformed Requests for {module_name}...")

    headers = {'Authorization': f'Token {token}'}

    # Test various malformed requests
    malformed_scenarios = [
        {
            'description': 'Negative amount',
            'data': {'amount': '-100.00', 'description': 'Negative test'},
            'endpoint': 'deposit'
        },
        {
            'description': 'Zero amount',
            'data': {'amount': '0.00', 'description': 'Zero test'},
            'endpoint': 'deposit'
        },
        {
            'description': 'Extremely large amount',
            'data': {'amount': '999999999999.99', 'description': 'Large amount test'},
            'endpoint': 'deposit'
        },
        {
            'description': 'Non-numeric amount',
            'data': {'amount': 'abc', 'description': 'Non-numeric test'},
            'endpoint': 'deposit'
        },
        {
            'description': 'Missing amount',
            'data': {'description': 'Missing amount test'},
            'endpoint': 'deposit'
        },
        {
            'description': 'SQL injection attempt',
            'data': {'amount': '100.00', 'description': "'; DROP TABLE users; --"},
            'endpoint': 'deposit'
        },
        {
            'description': 'XSS attempt',
            'data': {'amount': '100.00', 'description': '<script>alert("xss")</script>'},
            'endpoint': 'deposit'
        }
    ]

    for scenario in malformed_scenarios:
        if module_name == 'individual':
            if scenario['endpoint'] == 'deposit':
                url = f"{BASE_URL}/individual/wallet/deposit/"
            else:
                url = f"{BASE_URL}/individual/wallet/withdraw/"
        elif module_name == 'couple':
            if scenario['endpoint'] == 'deposit':
                url = f"{BASE_URL}/couple/wallet/deposit/"
            else:
                url = f"{BASE_URL}/couple/wallet/withdraw/"
        elif module_name == 'dailywage':
            # Daily wage uses different endpoint names
            if scenario['endpoint'] == 'deposit':
                url = f"{BASE_URL}/dailywage/wallet/add_earnings/"
            else:
                url = f"{BASE_URL}/dailywage/wallet/withdraw/"
        else:
            url = f"{BASE_URL}/individual/wallet/deposit/"

        response = requests.post(url, headers=headers, json=scenario['data'])
        print(f"     {scenario['description']}: Status {response.status_code}")

        if response.status_code == 400:
            print("       ✅ Correctly rejected malformed request")
        elif response.status_code == 200:
            print("       ⚠️  Accepted potentially dangerous request")
        else:
            print(f"       ℹ️  Response: {response.status_code}")

def test_concurrent_operations(token, module_name):
    """Test concurrent wallet operations"""
    print(f"\n🔐 Testing Concurrent Operations for {module_name}...")

    import threading
    import queue

    headers = {'Authorization': f'Token {token}'}
    results = queue.Queue()

    def perform_operation(operation_id):
        """Perform a wallet operation"""
        try:
            if module_name == 'individual':
                # Deposit operation
                data = {'amount': '10.00', 'description': f'Concurrent test {operation_id}'}
                response = requests.post(f"{BASE_URL}/individual/wallet/deposit/", headers=headers, json=data)
            elif module_name == 'couple':
                # Deposit operation
                data = {'amount': '10.00', 'description': f'Concurrent test {operation_id}'}
                response = requests.post(f"{BASE_URL}/couple/wallet/deposit/", headers=headers, json=data)
            elif module_name == 'dailywage':
                # Add earnings
                data = {'amount': '10.00', 'description': f'Concurrent test {operation_id}'}
                response = requests.post(f"{BASE_URL}/dailywage/wallet/add_earnings/", headers=headers, json=data)
            else:
                response = requests.get(f"{BASE_URL}/individual/wallet/balance/", headers=headers)

            results.put({
                'operation_id': operation_id,
                'status_code': response.status_code,
                'success': response.status_code == 200
            })
        except Exception as e:
            results.put({
                'operation_id': operation_id,
                'error': str(e),
                'success': False
            })

    # Start multiple concurrent operations
    threads = []
    num_operations = 5

    print(f"   Starting {num_operations} concurrent operations...")

    for i in range(num_operations):
        thread = threading.Thread(target=perform_operation, args=(i+1,))
        threads.append(thread)
        thread.start()

    # Wait for all operations to complete
    for thread in threads:
        thread.join()

    # Collect results
    successful_ops = 0
    failed_ops = 0

    while not results.empty():
        result = results.get()
        if result.get('success'):
            successful_ops += 1
            print(f"     Operation {result['operation_id']}: ✅ Success")
        else:
            failed_ops += 1
            error = result.get('error', f"Status {result.get('status_code', 'unknown')}")
            print(f"     Operation {result['operation_id']}: ❌ Failed ({error})")

    print(f"   ✅ Successful operations: {successful_ops}")
    print(f"   ❌ Failed operations: {failed_ops}")

    if successful_ops == num_operations:
        print("   ✅ All concurrent operations succeeded")
    elif failed_ops > 0:
        print("   ⚠️  Some concurrent operations failed - check for race conditions")

def main():
    """Main security testing function"""
    print("🚨 Starting Comprehensive Wallet Security Testing")
    print("=" * 70)

    # Setup test users
    users = setup_test_users()

    # Get authentication tokens
    tokens = {}
    for user_type, user in users.items():
        token = get_auth_token(user.username, 'testpass123')
        if token:
            tokens[user_type] = token
            print(f"✅ Authentication successful for {user_type}")
        else:
            print(f"❌ Failed to authenticate {user_type}")

    # Test security features for each module
    test_modules = [
        ('individual', 'individual'),
        ('couple', 'couple1'),
        ('dailywage', 'dailywage')
    ]

    for module_name, user_key in test_modules:
        if user_key in tokens:
            print(f"\n{'='*50}")
            print(f"Testing {module_name.upper()} Module Security")
            print(f"{'='*50}")

            # Test OTP generation limits
            test_otp_generation_limits(tokens[user_key], module_name)

            # Test OTP verification failures
            test_otp_verification_failures(tokens[user_key], module_name)

            # Test malformed requests
            test_malformed_requests(tokens[user_key], module_name)

            # Test concurrent operations
            test_concurrent_operations(tokens[user_key], module_name)
        else:
            print(f"❌ Skipping {module_name} module - no authentication token")

    # Test cross-module security features
    print(f"\n{'='*50}")
    print("Testing Cross-Module Security Features")
    print(f"{'='*50}")

    # Test suspicious activity detection
    test_suspicious_activity_detection()

    # Test unauthorized access attempts
    if 'unauthorized' in tokens:
        test_unauthorized_access_attempts(tokens['unauthorized'])

    print("\n" + "=" * 70)
    print("🎯 Comprehensive Wallet Security Testing Complete!")
    print("\n📋 Security Test Summary:")
    print("   ✅ OTP Generation Limits: Rate limiting tested")
    print("   ✅ OTP Verification Failures: Invalid OTP handling tested")
    print("   ✅ Suspicious Activity Detection: Failed auth attempts tested")
    print("   ✅ Unauthorized Access: Cross-user access prevention tested")
    print("   ✅ Malformed Requests: Input validation tested")
    print("   ✅ Concurrent Operations: Race condition testing")
    print("\n🔒 SECURITY TESTING COMPLETED - REVIEW RESULTS ABOVE FOR ANY ISSUES!")

if __name__ == '__main__':
    main()
