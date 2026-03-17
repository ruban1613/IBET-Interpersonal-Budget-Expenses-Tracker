# 💑 IBET Couple Module Wallet - Deployment Guide

## Overview

The Couple Module Wallet provides secure, shared wallet functionality for couples with:
- **Joint wallet management** with partner access control
- **Emergency fund tracking** for unexpected expenses
- **Joint goals and savings** for shared financial objectives
- **Monthly budget monitoring** with spending limits
- **OTP-protected operations** for enhanced security
- **Comprehensive transaction history** with partner attribution

## 🚀 Quick Start

### 1. Prerequisites
```bash
# Python 3.8+
# Django 4.2+
# PostgreSQL or MySQL
# Redis (for caching and OTP)
```

### 2. Installation
```bash
cd IBET
pip install -r requirements.txt
python manage.py migrate
python manage.py createcachetable
python manage.py runserver
```

### 3. Create Couple Users
```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
User = get_user_model()

# Create couple users
couple_users = [
    ('couple_user1', 'couple1@test.com', 'INDIVIDUAL'),
    ('couple_user2', 'couple2@test.com', 'INDIVIDUAL'),
]

for username, email, persona in couple_users:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={'email': email, 'persona': persona}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"Created {username}")
```

## 📊 Couple Module Features

### Core Features
- **Shared Wallet**: Joint balance accessible by both partners
- **Emergency Fund**: Separate tracking for emergency savings
- **Joint Goals**: Shared savings goals with progress tracking
- **Monthly Budget**: Budget limits with utilization monitoring
- **Partner Access**: Both partners can access and manage the wallet
- **Transaction History**: Complete audit trail of all operations

### Security Features
- **OTP Protection**: All operations require OTP verification
- **Rate Limiting**: Prevents abuse with intelligent throttling
- **Suspicious Activity Detection**: Monitors for unusual patterns
- **Security Event Logging**: Comprehensive audit trail
- **Partner Authorization**: Both partners must be verified users

## 🔐 API Endpoints

### Wallet Operations
```bash
# Get wallet balance and details
GET /api/couple/wallet/balance/

# Deposit money to joint wallet
POST /api/couple/wallet/deposit/
{
    "amount": "800.00",
    "description": "Joint salary deposit"
}

# Withdraw money from joint wallet
POST /api/couple/wallet/withdraw/
{
    "amount": "200.00",
    "description": "Household expenses"
}

# Transfer to emergency fund
POST /api/couple/wallet/transfer_to_emergency/
{
    "amount": "100.00",
    "description": "Emergency savings"
}

# Transfer to joint goals
POST /api/couple/wallet/transfer_to_goals/
{
    "amount": "50.00",
    "goal_name": "Vacation Fund"
}

# Get monthly transaction summary
GET /api/couple/wallet/monthly_summary/
```

### OTP Security
```bash
# Generate OTP for operations
POST /api/couple/wallet/generate-otp/
{
    "operation_type": "withdrawal",
    "amount": "100.00",
    "description": "Secure withdrawal"
}

# Verify OTP (OTP shared securely outside app)
POST /api/couple/wallet/verify-otp/
{
    "otp_code": "123456",
    "otp_request_id": 1
}
```

## 🧪 Testing

### Run Couple Wallet Tests
```bash
# Test couple module specifically
python manage.py test couple_module.tests_wallet

# Run couple wallet specific test script
python test_couple_wallet.py
```

### Test Script Features
The couple wallet test script (`test_couple_wallet.py`) tests:
- ✅ User authentication for couple users
- ✅ Wallet balance retrieval
- ✅ Joint deposit operations
- ✅ Joint withdrawal operations
- ✅ Emergency fund transfers
- ✅ Joint goal transfers
- ✅ Monthly summary reports
- ✅ OTP generation and verification
- ✅ Security features and rate limiting
- ✅ Error handling and edge cases

## 📱 Usage Examples

### Basic Wallet Operations
```python
import requests

# Setup authentication
headers = {'Authorization': f'Token {couple_token}'}

# Check joint balance
response = requests.get('/api/couple/wallet/balance/', headers=headers)
print(f"Joint Balance: {response.json().get('balance')}")

# Deposit joint income
response = requests.post('/api/couple/wallet/deposit/',
    headers=headers,
    json={'amount': '1500.00', 'description': 'Joint salary'})

# Withdraw for household expenses
response = requests.post('/api/couple/wallet/withdraw/',
    headers=headers,
    json={'amount': '300.00', 'description': 'Groceries'})
```

### Emergency Fund Management
```python
# Transfer to emergency fund
response = requests.post('/api/couple/wallet/transfer_to_emergency/',
    headers=headers,
    json={'amount': '200.00', 'description': 'Emergency savings'})

# Check emergency fund balance
balance_response = requests.get('/api/couple/wallet/balance/', headers=headers)
emergency_fund = balance_response.json().get('emergency_fund')
```

### Joint Goals
```python
# Transfer to vacation fund
response = requests.post('/api/couple/wallet/transfer_to_goals/',
    headers=headers,
    json={
        'amount': '100.00',
        'goal_name': 'Europe Vacation',
        'description': 'Vacation savings'
    })

# Check joint goals balance
balance_response = requests.get('/api/couple/wallet/balance/', headers=headers)
joint_goals = balance_response.json().get('joint_goals')
```

### Monthly Summary
```python
# Get monthly spending summary
response = requests.get('/api/couple/wallet/monthly_summary/', headers=headers)
summary = response.json()
print(f"Monthly Deposits: {summary.get('total_deposits')}")
print(f"Monthly Withdrawals: {summary.get('total_withdrawals')}")
print(f"Budget Utilization: {summary.get('budget_utilization')}%")
```

## 🔧 Configuration

### Settings
Add to `settings.py`:
```python
# Couple wallet specific settings
COUPLE_WALLET_OTP_EXPIRY_MINUTES = 10
COUPLE_WALLET_MAX_OTP_ATTEMPTS = 3
COUPLE_WALLET_SUSPICIOUS_THRESHOLD = 5
COUPLE_WALLET_RATE_LIMITS = {
    'deposit': 10,
    'withdrawal': 5,
    'transfer': 3,
}

# Partner verification settings
COUPLE_WALLET_PARTNER_VERIFICATION_REQUIRED = True
COUPLE_WALLET_TRANSACTION_HISTORY_DAYS = 365
```

### Environment Variables
```bash
# Couple wallet security
COUPLE_OTP_SECRET_KEY=your-couple-secret-key-here
COUPLE_SECURITY_MONITORING_ENABLED=True

# Cache settings
COUPLE_REDIS_URL=redis://localhost:6379/2
COUPLE_CACHE_TIMEOUT=300
```

## 📋 Features Comparison

| Feature | Couple Module | Individual | Retiree | Daily Wage |
|---------|---------------|------------|---------|------------|
| Joint Wallet | ✅ | ❌ | ❌ | ❌ |
| Partner Access | ✅ | ❌ | ❌ | ❌ |
| Emergency Fund | ✅ | ❌ | ✅ | ✅ |
| Joint Goals | ✅ | ❌ | ❌ | ❌ |
| Monthly Budget | ✅ | ❌ | ✅ | ❌ |
| OTP Security | ✅ | ✅ | ✅ | ✅ |
| Rate Limiting | ✅ | ✅ | ✅ | ✅ |
| Transaction History | ✅ | ✅ | ✅ | ✅ |

## 🚨 Security Best Practices

1. **Partner Verification**: Both partners must be authenticated users
2. **OTP for All Operations**: Every transaction requires OTP verification
3. **Rate Limiting**: Prevent abuse with intelligent throttling
4. **Suspicious Activity Monitoring**: Detect unusual transaction patterns
5. **Secure OTP Sharing**: OTP should be shared outside the application
6. **Regular Security Audits**: Monitor wallet operations regularly
7. **Partner Communication**: Both partners should discuss major transactions

## 📞 Support

For couple wallet issues:
1. Check OTP generation and verification logs
2. Verify both partners have proper authentication
3. Review security event logs for suspicious activity
4. Check database migrations are applied
5. Ensure Redis is running for OTP caching
6. Verify couple wallet models are properly migrated

## 🎉 Conclusion

The Couple Module Wallet provides comprehensive, secure shared wallet functionality for couples. With joint balance management, emergency funds, shared goals, and robust security features, couples can effectively manage their finances together while maintaining individual security controls.

**The Couple Wallet Module is fully functional and secure!** 🚀
