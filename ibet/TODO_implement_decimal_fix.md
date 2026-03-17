# TODO: Implement Decimal Fix for Couple Wallet Views

## Steps to Complete
- [x] Add safe_decimal_conversion helper function to core/security.py
- [x] Update deposit method in CoupleWalletViewSet to use safe conversion
- [x] Update withdraw method in CoupleWalletViewSet to use safe conversion
- [x] Update transfer_to_emergency method in CoupleWalletViewSet to use safe conversion
- [x] Update transfer_to_goals method in CoupleWalletViewSet to use safe conversion
- [x] Update GenerateCoupleWalletOTPView.post() to validate amount using safe conversion
- [x] Test the fixes by running server and verifying endpoints
