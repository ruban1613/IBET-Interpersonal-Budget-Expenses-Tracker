# 🏦 IBET Wallet System - Complete Deployment Guide

## Overview

The IBET Wallet System provides secure, multi-module wallet functionality across all user personas:
- **Student Module**: Daily expense wallet with parent-controlled transfers, budget constraints, and OTP-based account unlocking
- **Parent Module**: Wallet for sending money to students and monitoring expenses with OTP approval system
- **Couple Module**: Shared wallet with partner transfers
- **Individual Module**: Personal wallet with savings goals and anomaly detection
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
    ('parent_user', 'parent@test.com', 'PARENT'),
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

### Student Module Wallet
**Features:**
- **Monthly budget allocation**: Parent transfers fixed amount (e.g., ₹5000) divided into 30 days = ₹166.67 daily budget
- **Daily spending constraints**: Students can only spend within their allocated daily budget
- **Account locking mechanism**: Account automatically locks when:
  - Student spends beyond daily limit
  - Unexpected expenses occur
  - Suspicious transaction patterns detected
- **Parent OTP approval required**: Account only unlocks after parent provides OTP approval
- **Additional money requests**: Students can request extra money from parents via OTP system
- **Real-time budget tracking**: Live tracking of daily spending against allocated budget
- **Expense categorization**: Food, transport, books, entertainment, etc.
- **Parent notifications**: Automatic alerts to parents for account lock/unlock events

**API Endpoints:**
```bash
# Get daily balance and budget status
GET /api/student/wallet/balance/

# Get daily budget details
GET /api/student/wallet/daily_budget/

# Make expense within budget
POST /api/student/wallet/expense/
{
    "amount": "50.00",
    "category": "food",
    "description": "Lunch expense"
}

# Check remaining daily budget
GET /api/student/wallet/remaining_budget/

# Get expense history
GET /api/student/wallet/expense_history/

# Request additional money from parent
POST /api/student/wallet/request_money/
{
    "amount": "100.00",
    "reason": "Medical emergency",
    "description": "Need extra money for medicine"
}

# Check account lock status
GET /api/student/wallet/account_status/

# Get spending categories
GET /api/student/wallet/categories/
```

### Parent Module Wallet
**Features:**
- **Student account management**: Complete control over linked student accounts
- **OTP-based approval system**: Parents provide OTP for:
  - Unlocking locked student accounts
  - Approving additional money requests from students
  - Authorizing budget increases
- **Student expense monitoring**: Real-time oversight of student spending
- **Budget allocation**: Set and modify student daily/weekly budgets
- **Transaction approval**: Approve or reject student money requests
- **Security alerts**: Notifications for suspicious student account activity
- **Multi-student management**: Handle multiple linked student accounts

**API Endpoints:**
```bash
# Get balance
GET /api/parent/wallet/balance/

# Deposit money
POST /api/parent/wallet/deposit/
{
    "amount": "5000.00",
    "description": "Monthly student budget"
}

# Transfer to student (regular allocation)
POST /api/parent/wallet/transfer_to_student/
{
    "student_id": 1,
    "amount": "166.67",
    "description": "Daily budget allocation",
    "is_daily_allocation": true
}

# Approve student money request with OTP
POST /api/parent/wallet/approve_request/
{
    "request_id": 1,
    "otp_code": "123456",
    "approved_amount": "100.00"
}

# Unlock student account with OTP
POST /api/parent/wallet/unlock_student/
{
    "student_id": 1,
    "otp_code": "789012",
    "unlock_reason": "Approved additional spending"
}

# Get student expense overview
GET /api/parent/wallet/student_expenses/{student_id}/

# Get transaction history
GET /api/parent/wallet/transactions/

# Get linked students
GET /api/parent/wallet/linked_students/

# Get pending student requests
GET /api/parent/wallet/pending_requests/

# Set student budget
POST /api/parent/wallet/set_student_budget/
{
    "student_id": 1,
    "daily_budget": "166.67",
    "monthly_budget": "5000.00"
}
```

### Individual Module Wallet
**Features:**
- Personal wallet with balance tracking
- Monthly budget management
- Savings goals with progress tracking
- Secure deposits and withdrawals
- Transaction history
- Anomaly detection for unexpected expenses
- Unusual spending pattern alerts
- Automatic alerts for suspicious transactions

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

# Get anomaly alerts
GET /api/individual/wallet/anomaly_alerts/

# Check spending patterns
GET /api/individual/wallet/spending_analysis/
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

### Student-Parent OTP Security System
- **Account Unlock OTP**: Parents receive OTP to unlock locked student accounts
- **Money Request Approval OTP**: Parents receive OTP to approve additional money requests
- **Budget Modification OTP**: Parents receive OTP for changing student budget limits
- **Emergency Transfer OTP**: Parents receive OTP for emergency fund transfers to students

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
- Anomaly detection for all modules
- Automatic alerts for suspicious transactions

## 🧪 Testing

### Run All Wallet Tests
```bash
# Test individual module
python manage.py test individual_module.tests_wallet

# Test student module
python manage.py test student_module.tests_wallet

# Test parent module
python manage.py test parent_module.tests_wallet

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

# Run parent module specific test
python test_parent_module_final.py

# Run student module specific test
python test_student_wallet.py
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
- ✅ Anomaly detection and alerts
- ✅ Student-parent transfer functionality
- ✅ Budget constraints and limits
- ✅ Account locking and unlocking
- ✅ Parent OTP approval system

## 📱 Usage Examples

### Student Module Usage
```python
# Check daily balance and budget status
response = requests.get('/api/student/wallet/balance/')

# Check daily budget details
response = requests.get('/api/student/wallet/daily_budget/')

# Make expense within budget
response = requests.post('/api/student/wallet/expense/',
    json={'amount': '50.00', 'category': 'food', 'description': 'Lunch'})

# Check remaining daily budget
response = requests.get('/api/student/wallet/remaining_budget/')

# Get expense history
response = requests.get('/api/student/wallet/expense_history/')

# Request additional money from parent
response = requests.post('/api/student/wallet/request_money/',
    json={'amount': '100.00', 'reason': 'Medical emergency', 'description': 'Need extra money for medicine'})

# Check account lock status
response = requests.get('/api/student/wallet/account_status/')
```

### Parent Module Usage
```python
# Deposit money to parent wallet
response = requests.post('/api/parent/wallet/deposit/',
    json={'amount': '5000.00', 'description': 'Monthly student budget'})

# Transfer daily budget to student
response = requests.post('/api/parent/wallet/transfer_to_student/',
    json={'student_id': 1, 'amount': '166.67', 'description': 'Daily budget allocation', 'is_daily_allocation': True})

# Approve student money request with OTP
response = requests.post('/api/parent/wallet/approve_request/',
    json={'request_id': 1, 'otp_code': '123456', 'approved_amount': '100.00'})

# Unlock student account with OTP
response = requests.post('/api/parent/wallet/unlock_student/',
    json={'student_id': 1, 'otp_code': '789012', 'unlock_reason': 'Approved additional spending'})

# Monitor student expenses
response = requests.get('/api/parent/wallet/student_expenses/1/')

# Check transaction history
response = requests.get('/api/parent/wallet/transactions/')

# Get linked students
response = requests.get('/api/parent/wallet/linked_students/')

# Get pending student requests
response = requests.get('/api/parent/wallet/pending_requests/')

# Set student budget
response = requests.post('/api/parent/wallet/set_student_budget/',
    json={'student_id': 1, 'daily_budget': '166.67', 'monthly_budget': '5000.00'})
```

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

# Check for anomaly alerts
response = requests.get('/api/individual/wallet/anomaly_alerts/')

# Analyze spending patterns
response = requests.get('/api/individual/wallet/spending_analysis/')
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

# Student module settings
STUDENT_DAILY_BUDGET_DEFAULT = 166.67
STUDENT_MONTHLY_BUDGET_DEFAULT = 5000.00
STUDENT_BUDGET_RESET_HOUR = 0  # Midnight
STUDENT_ACCOUNT_LOCK_ENABLED = True
STUDENT_PARENT_OTP_REQUIRED = True

# Parent module settings
PARENT_OTP_EXPIRY_MINUTES = 15
PARENT_MAX_OTP_ATTEMPTS = 3
PARENT_APPROVAL_TIMEOUT_MINUTES = 30

# Anomaly detection settings
ANOMALY_DETECTION_ENABLED = True
ANOMALY_THRESHOLD_PERCENTAGE = 150  # 150% of normal spending
ANOMALY_ALERT_EMAIL_ENABLED = True
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

# Anomaly Detection
ANOMALY_DETECTION_MODEL_PATH=/path/to/model
ALERT_EMAIL_FROM=noreply@ibet.com

# Student Module
STUDENT_BUDGET_NOTIFICATION_ENABLED=True
PARENT_ALERT_EMAIL_ENABLED=True
STUDENT_ACCOUNT_LOCK_NOTIFICATION=True

# Parent Module
PARENT_APPROVAL_EMAIL_ENABLED=True
PARENT_SECURITY_ALERTS_ENABLED=True
```

## 📋 Module Comparison

| Feature | Student | Parent | Couple | Individual | Retiree | Daily Wage |
|---------|---------|--------|--------|------------|---------|------------|
| Basic Wallet | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| OTP Security | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Rate Limiting | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Transaction History | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Student Transfers | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Student Monitoring | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Budget Constraints | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Daily Budget | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Account Locking | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Parent OTP Approval | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Anomaly Detection | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Savings Goals | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Pension Tracking | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Emergency Fund | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ |
| Daily Earnings | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Weekly Targets | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Monthly Limits | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |

## 🚨 Security Best Practices

1. **Always use HTTPS** in production
2. **Enable OTP verification** for all sensitive operations
3. **Monitor security events** regularly
4. **Set appropriate rate limits** based on user needs
5. **Regular security audits** of wallet operations
6. **Backup wallet data** regularly
7. **User education** on secure practices
8. **Enable anomaly detection** for suspicious transactions
9. **Monitor spending patterns** for unusual activity
10. **Set up alerts** for security events
11. **Parent monitoring** for student expenses
12. **Budget enforcement** for student spending
13. **OTP-based approval** for account unlocking
14. **Multi-factor authentication** for parent operations

## 📞 Support

For issues or questions:
1. Check the test script output for diagnostics
2. Review security event logs
3. Verify user permissions and throttling
4. Check database migrations are applied
5. Ensure Redis is running for OTP caching
6. Review anomaly detection logs for suspicious activity
7. Check parent-student linking for transfer issues
8. Verify budget constraints are properly configured
9. Check OTP delivery systems for parent notifications
10. Verify account locking mechanisms are working

## 🎉 Conclusion

The IBET Wallet System provides comprehensive, secure wallet functionality across all user modules. Each module has tailored features while maintaining consistent security standards. The system is production-ready with OTP protection, rate limiting, comprehensive monitoring, anomaly detection, and proper parent-student financial management with OTP-based approval systems.

**All wallet modules are now fully functional and secure!** 🚀
