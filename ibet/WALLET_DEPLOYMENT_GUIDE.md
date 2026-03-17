# 🏦 IBET Wallet System - Complete Deployment Guide

## Overview

The IBET Wallet System provides secure, multi-module wallet functionality across all user personas:
- **Student Module**: Parent-to-student transfers with OTP security
- **Couple Module**: Shared wallet with partner transfers
- **Individual Module**: Personal wallet with savings goals
- **Retiree Module**: Pension wallet with emergency funds
- **Daily Wage Module**: Daily earnings tracking with weekly targets

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

### 3. Create Test Users
```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
User = get_user_model()

# Create users for each module
users = [
    ('individual_user', 'individual@test.com', 'INDIVIDUAL'),
    ('retiree_user', 'retiree@test.com', 'RETIREE'),
    ('dailywage_user', 'dailywage@test.com', 'DAILY_WAGE'),
    ('student_user', 'student@test.com', 'STUDENT'),
    ('couple_user1', 'couple1@test.com', 'INDIVIDUAL'),
    ('couple_user2', 'couple2@test.com', 'INDIVIDUAL'),
]

for username, email, persona in users:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={'email': email, 'persona': persona}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"Created {username}")
```

## 📊 Module-Specific Features

### Individual Module Wallet
**Features:**
- Personal wallet with balance tracking
- Monthly budget management
- Savings goals with progress tracking
- Secure deposits and withdrawals
- Transaction history

**API Endpoints:**
```bash
# Get balance
GET /api/individual/wallet/balance/

# Deposit money
POST /api/individual/wallet/deposit/
{
    "amount": "500.00",
    "description": "Salary deposit"
}

# Withdraw money
POST /api/individual/wallet/withdraw/
{
    "amount": "100.00",
    "description": "Grocery shopping"
}

# Transfer to savings
POST /api/individual/wallet/transfer_to_goal/
{
    "amount": "50.00",
    "goal_name": "Emergency Fund"
}
```

### Retiree Module Wallet
**Features:**
- Pension balance tracking
- Emergency fund management
- Monthly expense limits
- Secure pension deposits
- Expense monitoring

**API Endpoints:**
```bash
# Get balance
GET /api/retiree/wallet/balance/

# Deposit pension
POST /api/retiree/wallet/deposit_pension/
{
    "amount": "1000.00",
    "description": "Monthly pension"
}

# Deposit emergency fund
POST /api/retiree/wallet/deposit_emergency/
{
    "amount": "200.00",
    "description": "Emergency savings"
}

# Withdraw money
POST /api/retiree/wallet/withdraw/
{
    "amount": "150.00",
    "description": "Monthly expenses",
    "use_pension_fund": false
}

# Get monthly expenses
GET /api/retiree/wallet/monthly_expenses/
```

### Daily Wage Module Wallet
**Features:**
- Daily earnings tracking
- Weekly target progress
- Emergency reserve fund
- Essential vs non-essential expense tracking
- Weekly summary reports

**API Endpoints:**
```bash
# Get balance
GET /api/dailywage/wallet/balance/

# Add daily earnings
POST /api/dailywage/wallet/add_earnings/
{
    "amount": "300.00",
    "description": "Daily work earnings"
}

# Withdraw money
POST /api/dailywage/wallet/withdraw/
{
    "amount": "50.00",
    "description": "Lunch expense",
    "is_essential": true
}

# Transfer to emergency reserve
POST /api/dailywage/wallet/transfer_to_emergency/
{
    "amount": "25.00",
    "description": "Emergency savings"
}

# Get weekly summary
GET /api/dailywage/wallet/weekly_summary/
```

## 💑 Couple Module Wallet

**Features:**
- Shared wallet for couples
- Joint balance tracking
- Emergency fund management
- Joint goals and savings
- Monthly budget tracking
- Partner-specific transaction history
- Secure OTP-protected operations

**API Endpoints:**
```bash
# Get balance
GET /api/couple/wallet/balance/

# Deposit money
POST /api/couple/wallet/deposit/
{
    "amount": "800.00",
    "description": "Joint salary deposit"
}

# Withdraw money
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

# Get monthly summary
GET /api/couple/wallet/monthly_summary/
```

## 🔐 Security Features

### OTP Protection
All wallet operations require OTP verification for security:

```bash
# Generate OTP
POST /api/{module}/wallet/generate-otp/
{
    "operation_type": "withdrawal",
    "amount": "100.00",
    "description": "Secure withdrawal"
}

# Verify OTP (OTP shared securely outside app)
POST /api/{module}/wallet/verify-otp/
{
    "otp_code": "123456",
    "otp_request_id": 1
}
```

### Rate Limiting
- OTP generation: 5 requests per hour
- OTP verification: 3 attempts per 15 minutes
- Wallet operations: 10 requests per minute
- Sensitive operations: 3 requests per 30 minutes

### Security Monitoring
- Suspicious activity detection
- Failed login attempt tracking
- Unusual transaction pattern detection
- Real-time security event logging

## 🧪 Testing

### Run All Wallet Tests
```bash
# Test individual module
python manage.py test individual_module.tests_wallet

# Test retiree module
python manage.py test retiree_module.tests_wallet

# Test daily wage module
python manage.py test dailywage_module.tests_wallet

# Test couple module
python manage.py test couple_module.tests_wallet

# Test couple wallet specific
python test_couple_wallet.py

# Run comprehensive test script
python test_all_wallets_final.py
```

### Test Script Features
The comprehensive test script (`test_all_wallets_final.py`) tests:
- ✅ User authentication for all modules
- ✅ Wallet balance retrieval
- ✅ Deposit operations
- ✅ Withdrawal operations
- ✅ Module-specific features
- ✅ OTP generation and verification
- ✅ Security features and rate limiting
- ✅ Error handling and edge cases

## 📱 Usage Examples

### Individual Module Usage
```python
# Deposit salary
response = requests.post('/api/individual/wallet/deposit/',
    json={'amount': '3000.00', 'description': 'Monthly salary'})

# Set savings goal
response = requests.post('/api/individual/wallet/transfer_to_goal/',
    json={'amount': '500.00', 'goal_name': 'Vacation Fund'})

# Check balance
response = requests.get('/api/individual/wallet/balance/')
```

### Retiree Module Usage
```python
# Deposit pension
response = requests.post('/api/retiree/wallet/deposit_pension/',
    json={'amount': '2500.00', 'description': 'Monthly pension'})

# Add to emergency fund
response = requests.post('/api/retiree/wallet/deposit_emergency/',
    json={'amount': '300.00', 'description': 'Emergency savings'})

# Check monthly expenses
response = requests.get('/api/retiree/wallet/monthly_expenses/')
```

### Daily Wage Module Usage
```python
# Add daily earnings
response = requests.post('/api/dailywage/wallet/add_earnings/',
    json={'amount': '450.00', 'description': 'Daily work'})

# Essential expense
response = requests.post('/api/dailywage/wallet/withdraw/',
    json={'amount': '75.00', 'description': 'Groceries', 'is_essential': True})

# Check weekly progress
response = requests.get('/api/dailywage/wallet/weekly_summary/')
```

### Couple Module Usage
```python
# Deposit joint income
response = requests.post('/api/couple/wallet/deposit/',
    json={'amount': '1500.00', 'description': 'Joint salary'})

# Withdraw for household expenses
response = requests.post('/api/couple/wallet/withdraw/',
    json={'amount': '300.00', 'description': 'Groceries'})

# Transfer to emergency fund
response = requests.post('/api/couple/wallet/transfer_to_emergency/',
    json={'amount': '200.00', 'description': 'Emergency savings'})

# Transfer to joint goals
response = requests.post('/api/couple/wallet/transfer_to_goals/',
    json={'amount': '100.00', 'goal_name': 'Vacation Fund'})

# Check monthly summary
response = requests.get('/api/couple/wallet/monthly_summary/')
```

## 🔧 Configuration

### Settings
Add to `settings.py`:
```python
# Wallet settings
WALLET_OTP_EXPIRY_MINUTES = 10
WALLET_MAX_OTP_ATTEMPTS = 3
WALLET_SUSPICIOUS_THRESHOLD = 5
WALLET_RATE_LIMITS = {
    'deposit': 10,
    'withdrawal': 5,
    'transfer': 3,
}

# Security settings
SECURITY_EVENT_RETENTION_DAYS = 90
AUDIT_LOG_RETENTION_DAYS = 365
```

### Environment Variables
```bash
# Security
OTP_SECRET_KEY=your-secret-key-here
SECURITY_MONITORING_ENABLED=True

# Cache
REDIS_URL=redis://localhost:6379/1
CACHE_TIMEOUT=300

# Database
DATABASE_URL=postgresql://user:pass@localhost/ibet
```

## 📋 Module Comparison

| Feature | Student | Couple | Individual | Retiree | Daily Wage |
|---------|---------|--------|------------|---------|------------|
| Basic Wallet | ✅ | ✅ | ✅ | ✅ | ✅ |
| OTP Security | ✅ | ✅ | ✅ | ✅ | ✅ |
| Rate Limiting | ✅ | ✅ | ✅ | ✅ | ✅ |
| Transaction History | ✅ | ✅ | ✅ | ✅ | ✅ |
| Savings Goals | ❌ | ❌ | ✅ | ❌ | ❌ |
| Pension Tracking | ❌ | ❌ | ❌ | ✅ | ❌ |
| Emergency Fund | ❌ | ✅ | ❌ | ✅ | ✅ |
| Daily Earnings | ❌ | ❌ | ❌ | ❌ | ✅ |
| Weekly Targets | ❌ | ❌ | ❌ | ❌ | ✅ |
| Monthly Limits | ✅ | ✅ | ❌ | ✅ | ❌ |

## 🚨 Security Best Practices

1. **Always use HTTPS** in production
2. **Enable OTP verification** for all sensitive operations
3. **Monitor security events** regularly
4. **Set appropriate rate limits** based on user needs
5. **Regular security audits** of wallet operations
6. **Backup wallet data** regularly
7. **User education** on secure practices

## 📞 Support

For issues or questions:
1. Check the test script output for diagnostics
2. Review security event logs
3. Verify user permissions and throttling
4. Check database migrations are applied
5. Ensure Redis is running for OTP caching

## 🎉 Conclusion

The IBET Wallet System provides comprehensive, secure wallet functionality across all user modules. Each module has tailored features while maintaining consistent security standards. The system is production-ready with OTP protection, rate limiting, and comprehensive monitoring.

**All wallet modules are now fully functional and secure!** 🚀
