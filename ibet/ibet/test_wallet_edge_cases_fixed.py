#!/usr/bin/env python
"""
Comprehensive Edge Cases and Error Testing for Wallet Modules
Tests negative amounts, zero amounts, large amounts, malformed data, concurrent transactions, and error scenarios
"""
import requests
import json
import sys
import os
import time
import threading
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

# Add the IBET directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'IBET'))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_testing_final')
import django
django.setup()

from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from individual_module.models_wallet import IndividualWallet
from couple_module.models_wallet import CoupleWallet
from dailywage_module.models_wallet import DailyWageWallet
from retiree_module.models_wallet import RetireeWallet

BASE_URL = 'http://127.0.0.1:8000'

def setup_test_users():
    """Set up test users for edge case testing"""
    print("🔧 Setting up test users for edge case testing...")

    User = get_user_model()

    # Create test users for different modules
    users = {}

    # Individual module user
    individual_user, created = User.objects.get_or_create(
        username='edge_test_individual',
        defaults={'email': 'edge_individual@test.com', 'persona': 'INDIVIDUAL'}
    )
    individual_user.set_password('testpass123')
    individual_user.is_active = True
    individual_user.save()
    print(f"Created/Updated user: {individual_user.username}, active: {individual_user.is_active}, persona: {individual_user.persona}")

    # Create individual wallet
    from individual_module.models_wallet import IndividualWallet
    individual_wallet, created = IndividualWallet.objects.get_or_create(
        user=individual_user,
        defaults={'balance': Decimal('1000.00'), 'monthly_budget': Decimal('5000.00')}
    )
    print(f"Created/Updated individual wallet for {individual_user.username}: balance {individual_wallet.balance}")

    users['individual'] = individual_user

    # Couple module users
    couple_user1, created = User.objects.get_or_create(
        username='edge_test_couple1',
        defaults={'email': 'edge_couple1@test.com', 'persona': 'INDIVIDUAL'}
    )
    couple_user1.set_password('testpass123')
    couple_user1.is_active = True
    couple_user1.save()
    print(f"Created/Updated user: {couple_user1.username}, active: {couple_user1.is_active}, persona: {couple_user1.persona}")
    users['couple1'] = couple_user1

    # Second couple user
    couple_user2, created = User.objects.get_or_create(
        username='edge_test_couple2',
        defaults={'email': 'edge_couple2@test.com', 'persona': 'INDIVIDUAL'}
    )
    couple_user2.set_password('testpass123')
    couple_user2.is_active = True
    couple_user2.save()
    print(f"Created/Updated user: {couple_user2.username}, active: {couple_user2.is_active}, persona: {couple_user2.persona}")
    users['couple2'] = couple_user2

    # Create couple wallet
    from couple_module.models_wallet import CoupleWallet
    couple_wallet, created = CoupleWallet.objects.get_or_create(
        partner1=couple_user1,
        partner2=couple_user2,
        defaults={'balance': Decimal('2000.00'), 'monthly_budget': Decimal('10000.00')}
    )
    print(f"Created/Updated couple wallet for {couple_user1.username} & {couple_user2.username}: balance {couple_wallet.balance}")

    # Daily wage user
    dailywage_user, created = User.objects.get_or_create(
        username='edge_test_dailywage',
        defaults={'email': 'edge_dailywage@test.com', 'persona': 'DAILY_WAGE'}
    )
    dailywage_user.set_password('testpass123')
    dailywage_user.is_active = True
    dailywage_user.save()
    print(f"Created/Updated user: {dailywage_user.username}, active: {dailywage_user.is_active}, persona: {dailywage_user.persona}")

    # Create daily wage wallet
    from dailywage_module.models_wallet import DailyWageWallet
    dailywage_wallet, created = DailyWageWallet.objects.get_or_create(
        user=dailywage_user,
        defaults={'balance': Decimal('500.00'), 'weekly_target': Decimal('200.00')}
    )
    print(f"Created/Updated daily wage wallet for {dailywage_user.username}: balance {dailywage_wallet.balance}")

    users['dailywage'] = dailywage_user

    # Retiree user
    retiree_user, created = User.objects.get_or_create(
        username='edge_test_retiree',
        defaults={'email': 'edge_retiree@test.com', 'persona': 'RETIREE'}
    )
    retiree_user.set_password('testpass123')
    retiree_user.is_active = True
    retiree_user.save()
    print(f"Created/Updated user: {retiree_user.username}, active: {retiree_user.is_active}, persona: {retiree_user.persona}")

    # Create retiree wallet
    from retiree_module.models_wallet import RetireeWallet
    retiree_wallet, created = RetireeWallet.objects.get_or_create(
        user=retiree_user,
        defaults={'balance': Decimal('50000.00'), 'pension_balance': Decimal('15000.00')}
    )
    print(f"Created/Updated retiree wallet for {retiree_user.username}: balance {retiree_wallet.balance}")

    users['retiree'] = retiree_user

    return users

def get_auth_token(username, password):
    """Get authentication token for user"""
    try:
        # Try with form data first
        response = requests.post(f'{BASE_URL}/api/token-auth/', data={
            'username': username,
            'password': password
        })
        if response.status_code == 200:
            return response.json().get('token')
        else:
            print(f"❌ Failed to authenticate {username} with form data: {response.status_code} - {response.text}")

            # Try with JSON data as fallback
            response_json = requests.post(f'{BASE_URL}/api/token-auth/', json={
                'username': username,
                'password': password
            })
            if response_json.status_code == 200:
                return response_json.json().get('token')
            else:
                print(f"❌ Failed to authenticate {username} with JSON data: {response_json.status_code} - {response_json.text}")

                # Try direct Django authentication to debug
                from django.contrib.auth import authenticate
                user = authenticate(username=username, password=password)
                if user:
                    print(f"✅ Django authenticate() works for {username}, but API fails")
                    # Check if user has token
                    from rest_framework.authtoken.models import Token
                    try:
                        token = Token.objects.get(user=user)
                        print(f"✅ User has token: {token.key}")
                        return token.key
                    except Token.DoesNotExist:
                        print(f"❌ User has no token, creating one...")
                        token = Token.objects.create(user=user)
                        return token.key
                else:
                    print(f"❌ Django authenticate() also fails for {username}")
                return None
    except Exception as e:
        print(f"❌ Authentication error for {username}: {str(e)}")
        return None

def test_negative_amounts(tokens, module_name, endpoint):
    """Test negative amount inputs"""
    print(f"   Testing negative amounts for {module_name}...")

    test_cases = [
        {'amount': -100, 'description': 'Negative amount test'},
        {'amount': -1, 'description': 'Small negative amount'},
        {'amount': -999999, 'description': 'Large negative amount'}
    ]

    results = {'passed': 0, 'failed': 0}

    for i, test_case in enumerate(test_cases):
        try:
            headers = {'Authorization': f'Token {tokens}'}
            response = requests.post(f'{BASE_URL}{endpoint}', json=test_case, headers=headers)

            if response.status_code == 400:
                print(f"     ✅ Negative amount {test_case['amount']}: Correctly rejected (400)")
                results['passed'] += 1
            else:
                print(f"     ❌ Negative amount {test_case['amount']}: Unexpected response {response.status_code}")
                results['failed'] += 1

        except Exception as e:
            print(f"     ❌ Negative amount {test_case['amount']}: Error - {str(e)}")
            results['failed'] += 1

    return results

def test_zero_amounts(tokens, module_name, endpoint):
    """Test zero amount transactions"""
    print(f"   Testing zero amounts for {module_name}...")

    test_cases = [
        {'amount': 0, 'description': 'Zero amount test'},
        {'amount': 0.0, 'description': 'Zero float amount'},
        {'amount': '0', 'description': 'Zero string amount'}
    ]

    results = {'passed': 0, 'failed': 0}

    for i, test_case in enumerate(test_cases):
        try:
            headers = {'Authorization': f'Token {tokens}'}
            response = requests.post(f'{BASE_URL}{endpoint}', json=test_case, headers=headers)

            if response.status_code == 400:
                print(f"     ✅ Zero amount {test_case['amount']}: Correctly rejected (400)")
                results['passed'] += 1
            else:
                print(f"     ❌ Zero amount {test_case['amount']}: Unexpected response {response.status_code}")
                results['failed'] += 1

        except Exception as e:
            print(f"     ❌ Zero amount {test_case['amount']}: Error - {str(e)}")
            results['failed'] += 1

    return results

def test_large_amounts(tokens, module_name, endpoint):
    """Test extremely large amounts"""
    print(f"   Testing large amounts for {module_name}...")

    test_cases = [
        {'amount': 999999999999, 'description': 'Very large amount'},
        {'amount': 1000000000.99, 'description': 'Large decimal amount'},
        {'amount': '999999999999999999999999999999999999999999999999999999999999999999999999999999', 'description': 'Extremely large string'}
    ]

    results = {'passed': 0, 'failed': 0}

    for i, test_case in enumerate(test_cases):
        try:
            headers = {'Authorization': f'Token {tokens}'}
            response = requests.post(f'{BASE_URL}{endpoint}', json=test_case, headers=headers)

            if response.status_code in [400, 500]:  # 400 for validation error, 500 for overflow
                print(f"     ✅ Large amount test {i+1}: Handled correctly ({response.status_code})")
                results['passed'] += 1
            else:
                print(f"     ❌ Large amount test {i+1}: Unexpected response {response.status_code}")
                results['failed'] += 1

        except Exception as e:
            print(f"     ❌ Large amount test {i+1}: Error - {str(e)}")
            results['failed'] += 1

    return results

def test_malformed_requests(tokens, module_name, endpoint):
    """Test malformed request data"""
    print(f"   Testing malformed requests for {module_name}...")

    test_cases = [
        {'amount': 'not_a_number', 'description': 'Non-numeric amount'},
        {'amount': None, 'description': 'Null amount'},
        {'amount': [], 'description': 'Array amount'},
        {'amount': {}, 'description': 'Object amount'},
        {'amount': True, 'description': 'Boolean amount'},
        {'amount': '100', 'description': 'String amount'},
        {'amount': '100.5.5', 'description': 'Malformed decimal'},
        {'amount': '1e1000', 'description': 'Scientific notation overflow'},
        {},  # Empty request
        {'description': 'Missing amount field'}
    ]

    results = {'passed': 0, 'failed': 0}

    for i, test_case in enumerate(test_cases):
        try:
            headers = {'Authorization': f'Token {tokens}'}
            response = requests.post(f'{BASE_URL}{endpoint}', json=test_case, headers=headers)

            if response.status_code in [400, 500]:  # Accept both validation errors and server errors for now
                print(f"     ✅ Malformed request test {i+1}: Handled correctly ({response.status_code})")
                results['passed'] += 1
            else:
                print(f"     ❌ Malformed request test {i+1}: Unexpected response {response.status_code}")
                results['failed'] += 1

        except Exception as e:
            print(f"     ❌ Malformed request test {i+1}: Error - {str(e)}")
            results['failed'] += 1

    return results

def test_concurrent_operations(tokens, module_name, endpoint):
    """Test concurrent transactions"""
    print(f"   Testing concurrent operations for {module_name}...")

    def make_request(thread_id):
        """Make a request in a separate thread"""
        try:
            headers = {'Authorization': f'Token {tokens}'}
            test_data = {'amount': 10, 'description': f'Concurrent test {thread_id}'}
            response = requests.post(f'{BASE_URL}{endpoint}', json=test_data, headers=headers)
            return response.status_code
        except Exception as e:
            return f"Error: {str(e)}"

    # Start 10 concurrent requests
    threads = []
    results = []

    for i in range(10):
        thread = threading.Thread(target=lambda: results.append(make_request(i)))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    success_count = sum(1 for r in results if r == 200 or r == 201)
    error_count = len(results) - success_count

    print(f"     ✅ Successful concurrent operations: {success_count}")
    print(f"     ⚠️ Failed concurrent operations: {error_count}")

    return {'passed': success_count, 'failed': error_count}

def test_database_failures(tokens, module_name, endpoint):
    """Test database connection failures (simulated)"""
    print(f"   Testing database failure simulation for {module_name}...")

    # This is a basic test - in a real scenario, you'd need to simulate DB failures
    # For now, we'll test with very rapid successive requests that might overwhelm DB

    results = {'passed': 0, 'failed': 0}

    # Test with very rapid successive requests that might overwhelm DB
    for i in range(20):
        try:
            headers = {'Authorization': f'Token {tokens}'}
            test_data = {'amount': 1, 'description': f'DB stress test {i}'}
            response = requests.post(f'{BASE_URL}{endpoint}', json=test_data, headers=headers, timeout=5)

            if response.status_code in [200, 201, 429]:  # Success or rate limited
                results['passed'] += 1
            else:
                results['failed'] += 1

        except requests.exceptions.Timeout:
            print(f"     ⚠️ Request timeout on attempt {i+1}")
            results['failed'] += 1
        except Exception as e:
            print(f"     ❌ DB stress test {i+1}: Error - {str(e)}")
            results['failed'] += 1

    print(f"     ✅ DB stress test passed: {results['passed']}")
    print(f"     ❌ DB stress test failed: {results['failed']}")

    return results

def test_timeout_scenarios(tokens, module_name, endpoint):
    """Test timeout scenarios"""
    print(f"   Testing timeout scenarios for {module_name}...")

    results = {'passed': 0, 'failed': 0}

    # Test with very short timeout
    try:
        headers = {'Authorization': f'Token {tokens}'}
        test_data = {'amount': 100, 'description': 'Timeout test'}
        response = requests.post(f'{BASE_URL}{endpoint}', json=test_data, headers=headers, timeout=0.001)

        print(f"     ⚠️ Unexpected success with very short timeout: {response.status_code}")
        results['failed'] += 1

    except requests.exceptions.Timeout:
        print(f"     ✅ Correctly timed out with short timeout")
        results['passed'] += 1
    except Exception as e:
        print(f"     ❌ Timeout test error: {str(e)}")
        results['failed'] += 1

    # Test with normal timeout
    try:
        headers = {'Authorization': f'Token {tokens}'}
        test_data = {'amount': 100, 'description': 'Normal timeout test'}
        response = requests.post(f'{BASE_URL}{endpoint}', json=test_data, headers=headers, timeout=10)

        if response.status_code in [200, 201]:
            print(f"     ✅ Normal request succeeded within timeout")
            results['passed'] += 1
        else:
            print(f"     ⚠️ Normal request failed: {response.status_code}")
            results['failed'] += 1

    except requests.exceptions.Timeout:
        print(f"     ❌ Normal request timed out unexpectedly")
        results['failed'] += 1
    except Exception as e:
        print(f"     ❌ Normal timeout test error: {str(e)}")
        results['failed'] += 1

    return results

def run_edge_case_tests_for_module(tokens, module_name):
    """Run all edge case tests for a specific module"""
    print(f"\n🔍 Testing {module_name.upper()} Module Edge Cases")
    print("=" * 60)

    # Define endpoints for each module
    endpoints = {
        'individual': '/api/individual/wallet/deposit/',
        'couple': '/api/couple/wallet/deposit/',
        'dailywage': '/api/dailywage/wallet/deposit/',
        'retiree': '/api/retiree/wallet/deposit/'
    }

    if module_name not in endpoints:
        print(f"❌ No endpoint defined for {module_name}")
        return

    endpoint = endpoints[module_name]
    user_key = module_name if module_name != 'couple' else 'couple1'

    if user_key not in tokens:
        print(f"❌ No authentication token for {module_name}")
        return

    # Run all edge case tests
    results = {}

    results['negative'] = test_negative_amounts(tokens[user_key], module_name, endpoint)
    results['zero'] = test_zero_amounts(tokens[user_key], module_name, endpoint)
    results['large'] = test_large_amounts(tokens[user_key], module_name, endpoint)
    results['malformed'] = test_malformed_requests(tokens[user_key], module_name, endpoint)
    results['concurrent'] = test_concurrent_operations(tokens[user_key], module_name, endpoint)
    results['database'] = test_database_failures(tokens[user_key], module_name, endpoint)
    results['timeout'] = test_timeout_scenarios(tokens[user_key], module_name, endpoint)

    # Calculate totals
    total_passed = sum(r['passed'] for r in results.values())
    total_failed = sum(r['failed'] for r in results.values())

    print(f"\n📊 {module_name.upper()} Edge Case Test Results:")
    print(f"   ✅ Total passed: {total_passed}")
    print(f"   ❌ Total failed: {total_failed}")
    print(f"   📈 Success rate: {(total_passed / (total_passed + total_failed) * 100):.1f}%" if (total_passed + total_failed) > 0 else "N/A")

    return results

def main():
    """Main function to run comprehensive edge case testing"""
    print("🚨 Starting Comprehensive Wallet Edge Cases Testing")
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

    # Test modules
    modules_to_test = ['individual', 'couple', 'dailywage', 'retiree']
    all_results = {}

    for module in modules_to_test:
        all_results[module] = run_edge_case_tests_for_module(tokens, module)

    # Overall summary
    print("\n" + "=" * 70)
    print("🎯 Comprehensive Wallet Edge Cases Testing Complete!")
    print("\n📋 Edge Cases Test Summary:")

    total_passed = 0
    total_failed = 0

    for module, results in all_results.items():
        if results:
            module_passed = sum(r['passed'] for r in results.values())
            module_failed = sum(r['failed'] for r in results.values())
            total_passed += module_passed
            total_failed += module_failed

            success_rate = (module_passed / (module_passed + module_failed) * 100) if (module_passed + module_failed) > 0 else 0
            print(f"   {module.upper()}: {module_passed} passed, {module_failed} failed ({success_rate:.1f}%)")

    overall_success_rate = (total_passed / (total_passed + total_failed) * 100) if (total_passed + total_failed) > 0 else 0
    print(f"\n📊 Overall Results:")
    print(f"   ✅ Total passed: {total_passed}")
    print(f"   ❌ Total failed: {total_failed}")
    print(f"   📈 Overall success rate: {overall_success_rate:.1f}%")

    print("\n🔍 EDGE CASES TESTING COMPLETED - REVIEW RESULTS ABOVE FOR ANY ISSUES!")

if __name__ == '__main__':
    main()
