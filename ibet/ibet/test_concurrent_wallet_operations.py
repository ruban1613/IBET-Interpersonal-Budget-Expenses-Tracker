#!/usr/bin/env python
"""
Test concurrent wallet operations to verify select_for_update() prevents race conditions
"""
import os
import sys
import threading
import time
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_testing_final')
import django
django.setup()

from django.db import transaction
from django.contrib.auth import get_user_model
from individual_module.models_wallet import IndividualWallet
from couple_module.models_wallet import CoupleWallet
from dailywage_module.models_wallet import DailyWageWallet
from retiree_module.models_wallet import RetireeWallet

def setup_test_wallets():
    """Create test wallets for concurrent testing"""
    User = get_user_model()

    # Create test users if they don't exist
    users = {}
    for persona in ['individual', 'couple', 'dailywage', 'retiree']:
        username = f'concurrent_test_{persona}'
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@test.com',
                'persona': persona,
                'is_active': True
            }
        )
        users[persona] = user
        print(f"{'Created' if created else 'Found'} test user: {username}")

    # Create wallets
    wallets = {}

    # Individual wallet
    wallet, created = IndividualWallet.objects.get_or_create(
        user=users['individual'],
        defaults={'balance': Decimal('1000.00')}
    )
    wallets['individual'] = wallet
    print(f"{'Created' if created else 'Found'} individual wallet with balance: {wallet.balance}")

    # Couple wallet - need two partners
    couple_user1 = users['couple']
    couple_user2, _ = User.objects.get_or_create(
        username='concurrent_test_couple_partner2',
        defaults={
            'email': 'couple_partner2@test.com',
            'persona': 'couple',
            'is_active': True
        }
    )
    wallet, created = CoupleWallet.objects.get_or_create(
        partner1=couple_user1,
        partner2=couple_user2,
        defaults={'balance': Decimal('2000.00')}
    )
    wallets['couple'] = wallet
    print(f"{'Created' if created else 'Found'} couple wallet with balance: {wallet.balance}")

    # Daily wage wallet
    wallet, created = DailyWageWallet.objects.get_or_create(
        user=users['dailywage'],
        defaults={'balance': Decimal('500.00')}
    )
    wallets['dailywage'] = wallet
    print(f"{'Created' if created else 'Found'} daily wage wallet with balance: {wallet.balance}")

    # Retiree wallet
    wallet, created = RetireeWallet.objects.get_or_create(
        user=users['retiree'],
        defaults={'balance': Decimal('3000.00')}
    )
    wallets['retiree'] = wallet
    print(f"{'Created' if created else 'Found'} retiree wallet with balance: {wallet.balance}")

    return wallets

def test_concurrent_deposits(wallet, num_threads=10, amount_per_deposit=Decimal('10.00')):
    """Test concurrent deposits to verify balance consistency"""
    print(f"\n🧪 Testing concurrent deposits on {wallet.__class__.__name__}")
    print(f"Initial balance: {wallet.balance}")
    print(f"Number of threads: {num_threads}, Amount per deposit: {amount_per_deposit}")

    initial_balance = wallet.balance
    expected_final_balance = initial_balance + (num_threads * amount_per_deposit)

    def deposit_worker(thread_id):
        """Worker function for deposit operations"""
        try:
            if isinstance(wallet, IndividualWallet):
                result = wallet.deposit(amount_per_deposit, f"Concurrent deposit {thread_id}")
            elif isinstance(wallet, CoupleWallet):
                result = wallet.deposit(amount_per_deposit, f"Concurrent deposit {thread_id}")
            elif isinstance(wallet, DailyWageWallet):
                result = wallet.add_daily_earnings(amount_per_deposit, f"Concurrent deposit {thread_id}")
            elif isinstance(wallet, RetireeWallet):
                result = wallet.deposit_pension(amount_per_deposit, f"Concurrent deposit {thread_id}")
            else:
                raise ValueError(f"Unsupported wallet type: {type(wallet)}")
            return result
        except Exception as e:
            print(f"❌ Thread {thread_id} failed: {e}")
            return None

    # Run concurrent deposits
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(deposit_worker, i) for i in range(num_threads)]
        results = [future.result() for future in as_completed(futures)]

    end_time = time.time()

    # Refresh wallet from database
    wallet.refresh_from_db()
    final_balance = wallet.balance

    print(f"Expected final balance: {expected_final_balance}")
    print(f"Actual final balance: {final_balance}")
    print(f"Time taken: {end_time - start_time:.2f} seconds")

    if final_balance == expected_final_balance:
        print("✅ Concurrent deposits test PASSED - No race conditions detected")
        return True
    else:
        print("❌ Concurrent deposits test FAILED - Race condition detected!")
        return False

def test_concurrent_withdrawals(wallet, num_threads=10, amount_per_withdrawal=Decimal('5.00')):
    """Test concurrent withdrawals to verify balance consistency"""
    print(f"\n🧪 Testing concurrent withdrawals on {wallet.__class__.__name__}")
    print(f"Initial balance: {wallet.balance}")
    print(f"Number of threads: {num_threads}, Amount per withdrawal: {amount_per_withdrawal}")

    initial_balance = wallet.balance
    expected_final_balance = initial_balance - (num_threads * amount_per_withdrawal)

    def withdrawal_worker(thread_id):
        """Worker function for withdrawal operations"""
        try:
            if isinstance(wallet, IndividualWallet):
                result = wallet.withdraw(amount_per_withdrawal, f"Concurrent withdrawal {thread_id}")
            elif isinstance(wallet, CoupleWallet):
                result = wallet.withdraw(amount_per_withdrawal, f"Concurrent withdrawal {thread_id}")
            elif isinstance(wallet, DailyWageWallet):
                result = wallet.withdraw(amount_per_withdrawal, f"Concurrent withdrawal {thread_id}")
            elif isinstance(wallet, RetireeWallet):
                result = wallet.withdraw(amount_per_withdrawal, f"Concurrent withdrawal {thread_id}")
            else:
                raise ValueError(f"Unsupported wallet type: {type(wallet)}")
            return result
        except Exception as e:
            print(f"❌ Thread {thread_id} failed: {e}")
            return None

    # Run concurrent withdrawals
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(withdrawal_worker, i) for i in range(num_threads)]
        results = [future.result() for future in as_completed(futures)]

    end_time = time.time()

    # Refresh wallet from database
    wallet.refresh_from_db()
    final_balance = wallet.balance

    print(f"Expected final balance: {expected_final_balance}")
    print(f"Actual final balance: {final_balance}")
    print(f"Time taken: {end_time - start_time:.2f} seconds")

    if final_balance == expected_final_balance:
        print("✅ Concurrent withdrawals test PASSED - No race conditions detected")
        return True
    else:
        print("❌ Concurrent withdrawals test FAILED - Race condition detected!")
        return False

def test_mixed_operations(wallet, num_threads=20):
    """Test mixed concurrent operations (deposits and withdrawals)"""
    print(f"\n🧪 Testing mixed concurrent operations on {wallet.__class__.__name__}")
    print(f"Initial balance: {wallet.balance}")
    print(f"Number of threads: {num_threads}")

    initial_balance = wallet.balance
    deposit_amount = Decimal('15.00')
    withdrawal_amount = Decimal('10.00')

    # Calculate expected balance change
    # Half threads do deposits, half do withdrawals
    num_deposits = num_threads // 2
    num_withdrawals = num_threads - num_deposits
    expected_balance_change = (num_deposits * deposit_amount) - (num_withdrawals * withdrawal_amount)
    expected_final_balance = initial_balance + expected_balance_change

    def mixed_operation_worker(thread_id):
        """Worker function for mixed operations"""
        try:
            if thread_id % 2 == 0:  # Even threads do deposits
                if isinstance(wallet, IndividualWallet):
                    result = wallet.deposit(deposit_amount, f"Mixed deposit {thread_id}")
                elif isinstance(wallet, CoupleWallet):
                    result = wallet.deposit(deposit_amount, f"Mixed deposit {thread_id}")
                elif isinstance(wallet, DailyWageWallet):
                    result = wallet.add_daily_earnings(deposit_amount, f"Mixed deposit {thread_id}")
                elif isinstance(wallet, RetireeWallet):
                    result = wallet.deposit_pension(deposit_amount, f"Mixed deposit {thread_id}")
                else:
                    raise ValueError(f"Unsupported wallet type: {type(wallet)}")
            else:  # Odd threads do withdrawals
                if isinstance(wallet, IndividualWallet):
                    result = wallet.withdraw(withdrawal_amount, f"Mixed withdrawal {thread_id}")
                elif isinstance(wallet, CoupleWallet):
                    result = wallet.withdraw(withdrawal_amount, f"Mixed withdrawal {thread_id}")
                elif isinstance(wallet, DailyWageWallet):
                    result = wallet.withdraw(withdrawal_amount, f"Mixed withdrawal {thread_id}")
                elif isinstance(wallet, RetireeWallet):
                    result = wallet.withdraw(withdrawal_amount, f"Mixed withdrawal {thread_id}")
                else:
                    raise ValueError(f"Unsupported wallet type: {type(wallet)}")
            return result
        except Exception as e:
            print(f"❌ Thread {thread_id} failed: {e}")
            return None

    # Run mixed concurrent operations
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(mixed_operation_worker, i) for i in range(num_threads)]
        results = [future.result() for future in as_completed(futures)]

    end_time = time.time()

    # Refresh wallet from database
    wallet.refresh_from_db()
    final_balance = wallet.balance

    print(f"Expected final balance: {expected_final_balance}")
    print(f"Actual final balance: {final_balance}")
    print(f"Time taken: {end_time - start_time:.2f} seconds")

    if final_balance == expected_final_balance:
        print("✅ Mixed operations test PASSED - No race conditions detected")
        return True
    else:
        print("❌ Mixed operations test FAILED - Race condition detected!")
        return False

def run_concurrent_tests():
    """Run all concurrent operation tests"""
    print("🚀 Starting Concurrent Wallet Operations Tests")
    print("=" * 60)

    # Setup test wallets
    wallets = setup_test_wallets()

    test_results = []

    # Test each wallet type
    for wallet_type, wallet in wallets.items():
        print(f"\n{'='*20} Testing {wallet_type.upper()} Wallet {'='*20}")

        # Test concurrent deposits
        deposit_test = test_concurrent_deposits(wallet, num_threads=20, amount_per_deposit=Decimal('5.00'))
        test_results.append(("deposits", wallet_type, deposit_test))

        # Reset wallet balance for next test
        wallet.balance = Decimal('1000.00') if wallet_type == 'individual' else \
                         Decimal('2000.00') if wallet_type == 'couple' else \
                         Decimal('500.00') if wallet_type == 'dailywage' else \
                         Decimal('3000.00')
        wallet.save()

        # Test concurrent withdrawals
        withdrawal_test = test_concurrent_withdrawals(wallet, num_threads=15, amount_per_withdrawal=Decimal('10.00'))
        test_results.append(("withdrawals", wallet_type, withdrawal_test))

        # Reset wallet balance for next test
        wallet.balance = Decimal('1000.00') if wallet_type == 'individual' else \
                         Decimal('2000.00') if wallet_type == 'couple' else \
                         Decimal('500.00') if wallet_type == 'dailywage' else \
                         Decimal('3000.00')
        wallet.save()

        # Test mixed operations
        mixed_test = test_mixed_operations(wallet, num_threads=30)
        test_results.append(("mixed", wallet_type, mixed_test))

    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)

    passed = 0
    total = len(test_results)

    for operation, wallet_type, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{wallet_type.capitalize()} {operation}: {status}")
        if result:
            passed += 1

    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Concurrent operations are properly locked.")
        return True
    else:
        print("\n⚠️  SOME TESTS FAILED! Race conditions may still exist.")
        return False

if __name__ == '__main__':
    success = run_concurrent_tests()
    sys.exit(0 if success else 1)
