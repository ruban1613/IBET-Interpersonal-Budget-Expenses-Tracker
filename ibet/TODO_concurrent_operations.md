# Concurrent Operations Security Fix TODO

## Task: Improve concurrent operation handling to prevent race conditions (add atomic transactions and locking)

## Current Status
- ✅ COMPLETED: All wallet model methods now have @transaction.atomic decorators with select_for_update() for row-level locking
- ✅ COMPLETED: Added select_for_update() to all critical wallet operations across all modules
- ✅ COMPLETED: Tested concurrent operations to verify race condition prevention
- This prevents race conditions in high-concurrency scenarios

## Required Changes

### 1. Couple Module (ibet/couple_module/models_wallet.py)
- [ ] Add select_for_update() to deposit() method
- [ ] Add select_for_update() to withdraw() method
- [ ] Add select_for_update() to transfer_to_emergency() method
- [ ] Add select_for_update() to transfer_to_goals() method

### 2. Individual Module (ibet/individual_module/models_wallet.py)
- [ ] Add select_for_update() to deposit() method
- [ ] Add select_for_update() to withdraw() method
- [ ] Add select_for_update() to transfer_to_goal() method

### 3. Daily Wage Module (ibet/dailywage_module/models_wallet.py)
- [ ] Add select_for_update() to add_daily_earnings() method
- [ ] Add select_for_update() to withdraw() method
- [ ] Add select_for_update() to transfer_to_emergency() method

### 4. Retiree Module (ibet/retiree_module/models_wallet.py)
- [ ] Add select_for_update() to deposit_pension() method
- [ ] Add select_for_update() to deposit_emergency() method
- [ ] Add select_for_update() to withdraw() method

## Implementation Details
- Use `wallet = CoupleWallet.objects.select_for_update().get(pk=self.pk)` at the start of each method
- This ensures the wallet row is locked during the entire transaction
- Prevents race conditions where multiple operations could modify balance simultaneously

## Testing
- [ ] Test concurrent operations using threading/multiprocessing
- [ ] Verify balance consistency under high load
- [ ] Run existing wallet tests to ensure no regressions

## Follow-up
- [ ] Update security_fixes_todo.md with completion status
- [ ] Update wallet_security_review_todo.md with completion status
