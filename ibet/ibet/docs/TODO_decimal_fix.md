# TODO: Fix decimal.InvalidOperation Error in Couple Wallet Views

## Steps to Complete
- [x] Add helper function for safe Decimal conversion with validation
- [x] Update deposit method to use safe conversion
- [x] Update withdraw method to use safe conversion
- [x] Update transfer_to_emergency method to use safe conversion
- [x] Update transfer_to_goals method to use safe conversion
- [x] Update GenerateCoupleWalletOTPView.post() to validate amount
- [x] Test the fixes by running server and verifying endpoints (System check passed with no issues)
