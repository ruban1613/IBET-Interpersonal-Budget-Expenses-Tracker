# IBET Project Fixes TODO List

## Priority 1: Critical Errors (Blockers) ✅ COMPLETED
- [x] Fix missing 'wallet-management' URL pattern in individual_module
- [x] Add 'is_locked' field to Wallet model or remove from parent serializers ✅ COMPLETED
- [x] Fix custom User model configuration in test files

## Priority 2: Authentication & Authorization
- [ ] Resolve 401 authentication errors across all modules
- [ ] Fix 404 URL routing errors for wallet endpoints
- [ ] Correct OTP permission classes (currently too permissive)
- [ ] Fix URL patterns for couple, retiree, dailywage, student modules

## Priority 3: Security Fixes
- [ ] Fix security token generation length (currently 43 chars, should be 32)
- [ ] Correct rate limiting/throttling behavior
- [ ] Review and fix permission logic for all wallet operations
- [ ] Ensure security headers are properly implemented

## Priority 4: Model & Database Issues
- [ ] Check and fix corrupted decimal values in database
- [ ] Ensure all wallet models have consistent fields
- [ ] Verify model relationships and foreign keys
- [ ] Run database integrity checks

## Priority 5: Testing & Validation
- [ ] Re-run full test suite after fixes
- [ ] Verify all wallet endpoints work correctly
- [ ] Test authentication flows
- [ ] Validate security features (OTP, permissions, throttling)

## Priority 6: Documentation & Cleanup
- [ ] Update API documentation
- [ ] Clean up test files and remove obsolete code
- [ ] Document known issues and workarounds
- [ ] Create deployment checklist

## Current Status
- **Tests Run**: 163 total (109 passed, 47 failed, 7 errors)
- **Pass Rate**: 67%
- **Critical Blockers**: 7 errors → 0 errors ✅ FIXED
- **Major Issues**: 47 failures affecting authentication and routing
- **Django Check**: ✅ PASSED - No issues found

## Next Steps
1. ✅ Priority 1 COMPLETED - Django can now start without syntax errors
2. Move to Priority 2: Authentication & Authorization fixes
3. Test after each priority completion
4. Continue with remaining priorities
