# Wallet Security Test Fixes TODO

## Overview
This TODO tracks the steps to fix issues identified in the comprehensive wallet security test. The goal is to resolve 500 errors (DoesNotExist), 404 (missing endpoints), 403 (permissions), and ensure all tests pass.

## Steps

### 1. Fix Individual Module Views (Handle Missing Wallet)
- [ ] Update `individual_module/views_wallet.py`:
  - In `deposit`, `withdraw`, `transfer_to_goal`: Wrap `self.get_object()` in try-except for `IndividualWallet.DoesNotExist`.
  - If missing, create wallet with default balance=0, monthly_budget=0, etc.
  - Return 201 if created, or proceed with operation.
- [ ] Test: Rerun test for individual deposit/concurrent ops.

### 2. Fix Dailywage Module Views (Handle Missing Wallet & Permissions)
- [ ] Update `dailywage_module/views_wallet.py`:
  - Similar to individual: Handle `DailyWageWallet.DoesNotExist` in `add_earnings`, `withdraw`, etc.
  - Create wallet if missing with defaults (balance=0, weekly_target=0).
- [ ] Update `core/permissions.py`:
  - In `OTPGenerationPermission`: Allow 'DAILY_WAGE' persona for has_permission.
- [ ] Ensure URL consistency: Check if urls.py includes urls_wallet under 'wallet/' prefix to match test URLs.
- [ ] Test: Rerun test for dailywage OTP generation (should not 403), add_earnings (no 500).

### 3. Fix Couple Module URLs and Views
- [ ] Verify `couple_module/urls.py`: Already includes `path('', include('couple_module.urls_wallet'))`.
- [ ] But test expects /api/couple/wallet/... , current is /api/couple/... (no 'wallet/').
  - [ ] Option: Update `couple_module/urls.py` to `path('wallet/', include('couple_module.urls_wallet'))`.
  - [ ] Or update test script to remove 'wallet/' for couple.
  - Priority: Adjust URLs to match test (add 'wallet/' prefix).
- [ ] Read and verify `couple_module/views_wallet_final.py` has all needed views: CoupleWalletViewSet with @action for balance, deposit; GenerateCoupleWalletOTPView, VerifyCoupleWalletOTPView.
- [ ] Handle missing CoupleWallet in views: Similar to individual, create if partners exist.
- [ ] Test: Rerun test for couple (should not 404).

### 4. General Fixes
- [ ] Ensure all modules have balance endpoint: @action(detail=False, methods=['get']) def balance(self, request).
- [ ] For cross-module unauthorized: Already 404/403, good.
- [ ] Run migrations if model changes: `python manage.py makemigrations && python manage.py migrate`.
- [ ] Rerun full test: `python test_wallet_security_comprehensive.py`.
- [ ] If auth 400: Check user creation in test script matches credentials.

### 5. Verification
- [ ] All modules: No 500 on operations.
- [ ] Couple: No 404 on endpoints.
- [ ] Dailywage: No 403 on OTP.
- [ ] Concurrent ops: Success without race conditions.
- [ ] OTP limits: Rate limiting works across modules.

Progress: Starting with Step 1.
