# IBET - Interpersonal Budget and Expenses Tracker
## Project Analysis & Module Overview

### 1. Project Overview
IBET is a Django-based web application for managing interpersonal budgets and expenses across multiple user scenarios. It provides secure wallet management, expense tracking, and financial linking between users (especially parents and students).

### 2. Technology Stack
- **Backend**: Django 5.2.5 + Django REST Framework
- **Frontend**: React 18 + TypeScript + Vite
- **Database**: SQLite (development)
- **Authentication**: Token-based (DRF Authtoken)
- **i18n**: Django-modeltranslation (English & Tamil)
- **Security**: django-otp for OTP verification

### 3. Module Structure

#### 3.1 Core Module (`core/`)
- **settings.py**: Django configuration with installed apps, middleware, CORS, throttling
- **urls.py**: Main URL routing for all modules
- **views.py**: API root, status, language switching endpoints
- **middleware.py**: Security headers, request logging, rate limiting
- **permissions.py**: Custom permissions
- **throttling.py**: Custom throttle classes for OTP operations
- **security.py**: Security monitoring

#### 3.2 Student Module (`student_module/`)
**Models:**
- `User` - Custom user with persona field (STUDENT, PARENT, INDIVIDUAL, COUPLE, RETIREE, DAILY_WAGER)
- `Wallet` - Student wallet with balance tracking
- `ParentStudentLink` - Parent-student relationship
- `SpendingRequest` - Couples spending approval workflow
- `Budget` - Budget planning
- `Category` - Transaction categories
- `Transaction` - Expense/income transactions
- `MonthlyAllowance` - Parent-set monthly allowance
- `DailySpending` - Daily spending tracking
- `SpendingLock` - Spending restrictions
- `StudentNotification` - Notifications
- `MonthlySpendingSummary` - Monthly analytics
- `CumulativeSpendingTracker` - Cumulative daily allowance tracking
- `DailyAllowance` - Individual day allowances
- `PendingSpendingRequest` - Pending spending approvals
- `OTPRequest` - OTP for transactions

**Key Features:**
- Daily spending limit enforcement
- Cumulative daily allowance (carry-over unused daily allowance)
- Parent-student linking
- Spending locks (daily limit, category, time-based)
- Notifications for spending alerts (80%, 100)
- OTP verification% thresholds for exceeding daily limits

#### 3.3 Parent Module (`parent_module/`)
**Models:**
- `ParentDashboard` - Dashboard statistics
- `AlertSettings` - Alert preferences
- `StudentMonitoring` - Monitoring logs
- `ParentAlert` - Alerts generated for parent
- `ParentOTPRequest` - OTP requests for approvals

**Key Features:**
- Link/unlink students
- Set student monthly allowance
- Monitor student spending
- Create spending locks
- Transfer money to students
- Generate/approve OTP for extra spending

#### 3.4 Individual Module (`individual_module/`)
- Personal expense tracking
- Wallet management (deposit/withdraw)
- Budget categories
- Transaction history

#### 3.5 Couple Module (`couple_module/`)
- Shared wallet between partners
- Spending request/approval workflow
- Transaction tracking for both partners

#### 3.6 Retiree Module (`retiree_module/`)
- Retirement expense management
- Wallet with balance tracking
- Category-based spending

#### 3.7 Daily Wage Module (`dailywage_module/`)
- Wage-based income tracking
- Daily/weekly earnings
- Expense tracking for daily wagers

### 4. API Endpoints Summary

#### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `POST /api/token-auth/` - Get auth token

#### Student Endpoints (`/api/student/`)
- `GET /wallet/` - Get wallet balance
- `POST /wallet/deposit/` - Deposit money
- `POST /wallet/withdraw/` - Withdraw money
- `POST /wallet/generate-otp/` - Generate OTP
- `POST /wallet/verify-parent-otp/` - Verify parent OTP
- `GET /monthly-allowances/` - Get allowance
- `POST /monthly-allowances/` - Create allowance (parent)
- `GET /daily-spending/` - Today's spending
- `GET /spending-locks/` - Active locks
- `GET /notifications/` - Student notifications

#### Parent Endpoints (`/api/parent/`)
- `GET /students/` - Get linked students
- `POST /link-student/` - Link a student
- `POST /generate-otp/` - Generate approval OTP
- `GET /alerts/` - Get alerts
- `POST /wallet/transfer/` - Transfer to student

### 5. Frontend Structure (`frontend/`)

#### Pages
- `Login.tsx` - Login page
- `Register.tsx` - Registration page
- `SelectModule.tsx` - Module selection
- `StudentDashboard.tsx` - Student wallet dashboard
- `ParentDashboard.tsx` - Parent monitoring dashboard
- `Dashboard.tsx` - Generic dashboard

#### Services
- `api.ts` - API service for backend communication

### 6. Key Business Logic

#### Daily Allowance System
1. Parent sets monthly allowance (e.g., ₹5000 for 30 days = ₹166.67/day)
2. Student can spend up to daily limit WITHOUT OTP
3. Unused daily allowance carries over to future days
4. If student exceeds daily limit → needs parent OTP
5. Parent OTP allows accessing future days' money early

#### Spending Flow
```
Student Withdrawal Request
    ↓
Check daily remaining amount
    ↓
[If within limit] → Allow withdrawal
[If exceeds limit] → Return 402 (Payment Required)
    ↓
Parent sees alert with OTP
    ↓
Student enters parent OTP
    ↓
Verify OTP → Complete withdrawal
```

### 7. Security Features
- OTP generation and verification
- Rate limiting (throttling)
- Security headers middleware
- Request logging
- Sensitive data masking
- Wallet locking after failed attempts

### 8. Current Implementation Issues & TODOs

#### Known Issues
- Rate limiting (429 errors) during testing
- OTP generation/verification flow
- Daily allowance initialization

#### Pending TODOs
- Daily wage module enhancements
- i18n improvements
- Security fixes
- Testing coverage
- Wallet decimal precision fixes

### 9. Database Models Relationship
```
User (Custom)
├── Wallet (OneToOne)
├── ParentStudentLink (FK as parent or student)
├── Transaction (FK)
├── MonthlyAllowance (FK)
├── DailySpending (FK)
├── SpendingLock (FK)
├── CumulativeSpendingTracker (OneToOne)
└── DailyAllowance (Many)
```

### 10. Testing
- Various test scripts in root directory
- `test_parent_module.py` - Parent module tests
- `test_couple_wallet.py` - Couple wallet tests
- `test_dailywage_*.py` - Daily wage tests

---

## Summary
IBET is a comprehensive budget management system with multi-user support, wallet functionality, OTP security, and parent-child financial oversight. The current focus is on the student daily allowance system with parent OTP approval for exceeding daily limits.
