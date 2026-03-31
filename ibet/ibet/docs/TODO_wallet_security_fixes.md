# Wallet Security Fixes TODO

## Overview
Fix wallet security issues identified in comprehensive testing: 500 errors (DoesNotExist), 404 errors (missing endpoints), 403 errors (permissions).

## Steps

### 1. Fix Individual Module Balance Endpoint
- [x] Update `individual_module/views_wallet.py` balance action to create wallet if missing (instead of 404)

### 2. Fix Dailywage OTP Permissions
- [x] Update `core/permissions.py` OTPGenerationPermission to include 'DAILY_WAGE' persona

### 3. Fix OTP Verification Permissions
- [x] Update `core/permissions.py` OTPVerificationPermission to allow wallet owners instead of just 'STUDENT'

### 4. Verify Couple Module
- [ ] Check couple module URLs and views are correct
- [ ] Ensure wallet creation logic handles partners properly

### 5. Critical Path Testing
- [ ] Test individual balance endpoint (should create wallet, not 404)
- [ ] Test dailywage OTP generation (should not 403)
- [ ] Test OTP verification for all wallet types
- [ ] Test couple wallet endpoints

### 6. Full Comprehensive Testing
- [ ] Run `test_wallet_security_comprehensive.py` to verify all fixes
- [ ] Ensure no 500, 404, or 403 errors remain

Progress: Starting with Step 1.
