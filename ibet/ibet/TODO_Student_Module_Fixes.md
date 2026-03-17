# Student Module Fixes - Implementation Plan

## Issues Fixed:
1. ✅ **Balance Card showing 0.00** - FIXED
   - Updated StudentDashboardView to return wallet balance from MonthlyAllowance if Wallet balance is 0
   - Wallet balance is synced when monthly allowance is set

2. ✅ **Withdraw Flow** - FIXED
   - Modified withdraw() in views_wallet.py to check daily spending limits
   - Now uses NEW cumulative daily allowance system (DailyAllowance model)
   - Withdrawal succeeds when cumulative daily allowance is available

3. ✅ **OTP Workflow** - IMPLEMENTED
   - When student attempts withdraw beyond limit, returns pending_approval status
   - Parent can approve via OTP verification
   - Student receives notification when funds are unlocked

## NEW Feature: Cumulative Daily Allowance System
- Added DailyAllowance model for tracking daily allowances
- Added CumulativeSpendingTracker model for monthly tracking
- When parent sets monthly allowance:
  - Creates DailyAllowance records for ALL days in the month
  - Creates CumulativeSpendingTracker for the month
  - Students can spend cumulatively across days (up to monthly total)
- Daily-status endpoint shows cumulative spending

## Files Modified:
1. ✅ ibet/student_module/models.py - Added DailyAllowance, CumulativeSpendingTracker
2. ✅ ibet/student_module/views.py - Integrated NEW system in MonthlyAllowanceViewSet
3. ✅ ibet/student_module/views_wallet.py - Updated withdraw to use NEW system
4. ✅ ibet/student_module/urls_wallet.py - Added daily-status endpoint

## Remaining Tasks:
- [ ] Add endpoint to advance to next day (for testing)
- [ ] Add endpoint to manually unlock spending
- [ ] Update frontend to show cumulative spending properly
