# IBET Student & Parent Module Documentation

## Overview
The IBET (Interpersonal Budget and Expenses Tracker) system includes a Student Module and Parent Module that work together to manage student allowances and spending through a cumulative daily allowance system.

---

## STUDENT MODULE (`ibet/student_module/`)

### Models

#### 1. User (Extended AbstractUser)
- `persona`: User type - STUDENT, PARENT, INDIVIDUAL, COUPLE, RETIREE, DAILY_WAGER

#### 2. Wallet
- `balance`: Decimal - Money stored
- `is_locked`: Boolean - Security lock
- `failed_attempts`: Integer - Failed login attempts
- `locked_until`: DateTime - Lock expiration

#### 3. ParentStudentLink
- Links student to parent (One-to-One relationship)

#### 4. DailyAllowance (Core Feature)
Tracks individual daily allowance for each day of the month:
- `student`: ForeignKey to User
- `date`: Date - Specific day
- `daily_amount`: Decimal - Daily limit (e.g., 166.67 INR)
- `amount_spent`: Decimal - Today's spending
- `remaining_amount`: Decimal - Available today
- `is_available`: Boolean - If day is usable
- `is_locked`: Boolean - If day is locked
- `lock_reason`: String - Why locked

**Logic**: Monthly allowance (e.g., 5000 INR) divided by 30 days = 166.67 INR/day

#### 5. CumulativeSpendingTracker
Tracks cumulative spending across all available days:
- `student`: ForeignKey to User
- `month`, `year`: Current period
- `total_allocated`: Total monthly allowance
- `total_spent`: Amount spent so far
- `total_available`: Remaining amount
- `days_available`: Number of usable days left

#### 6. PendingSpendingRequest
Tracks requests requiring parent approval:
- `student`, `parent`: ForeignKeys
- `amount_requested`: Decimal - Requested amount
- `otp_code`: String - 6-digit verification code
- `status`: PENDING/APPROVED/REJECTED/EXPIRED
- `expires_at`: DateTime - OTP expiration

#### 7. MonthlyAllowance
Parent sets monthly allowance:
- `parent`, `student`: ForeignKeys
- `monthly_amount`: Decimal (e.g., 5000 INR)
- `days_in_month`: Integer (default 30)
- `start_date`, `end_date`: Date range
- `is_active`: Boolean

#### 8. DailySpending
Tracks daily spending:
- `student`: ForeignKey
- `date`: Specific day
- `daily_limit`: Decimal
- `amount_spent`: Decimal
- `remaining_amount`: Decimal
- `is_locked`: Boolean

#### 9. SpendingLock
Locks when student exceeds limits:
- `student`: ForeignKey
- `lock_type`: DAILY_LIMIT, MONTHLY_LIMIT, PARENT_LOCKED
- `amount_locked`: Decimal
- `unlock_otp`: OTP to unlock

#### 10. StudentNotification
Notifications for students:
- `notification_type`: DAILY_80%, MONTHLY_80%, WALLET_LOCKED, PARENT_APPROVAL, NEW_ALLOWANCE
- `title`, `message`: Content
- `is_read`: Boolean

#### 11. MonthlySpendingSummary
Monthly reports:
- `month`, `year`: Period
- `total_allowance`, `total_spent`, `remaining_amount`

### API Endpoints (`/api/student/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `wallet/` | GET, POST | Wallet CRUD |
| `wallet/balance/` | GET | Get balance |
| `wallet/daily-status/` | GET | Daily allowance status |
| `wallet/deposit/` | POST | Deposit money |
| `wallet/withdraw/` | POST | Withdraw (with daily limit) |
| `wallet/verify-parent-otp/` | POST | Verify parent OTP |
| `wallet/request-parent-approval/` | POST | Request extra spending |
| `categories/` | GET, POST | Expense categories |
| `budgets/` | GET, POST | Budget management |
| `transactions/` | GET, POST | Transaction history |
| `reminders/` | GET, POST | Budget reminders |
| `chat-messages/` | GET, POST | Student-Parent chat |
| `monthly-allowances/` | GET, POST | Allowance config |
| `notifications/` | GET | Student notifications |
| `monthly-summaries/` | GET | Monthly reports |
| `users/select-persona/` | PATCH | Select user type |

---

## PARENT MODULE (`ibet/parent_module/`)

### Models

#### 1. ParentDashboard
Parent's main dashboard:
- `parent`: OneToOne to User
- `total_students`: Integer - Linked students count
- `total_alerts_sent`: Integer
- `last_accessed`: DateTime

#### 2. AlertSettings
Configurable alert thresholds:
- `parent`, `student`: ForeignKeys
- `alert_type`: 50%, 70%, 100%, DAILY_LIMIT, WEEKLY_HIGH
- `is_enabled`: Boolean
- `email_notification`, `sms_notification`: Boolean

#### 3. StudentMonitoring
Logs parent access to student accounts:
- `parent`, `student`: ForeignKeys
- `wallet_accessed`: Boolean
- `otp_generated`: Boolean
- `notes`: Text

#### 4. ParentAlert
Alerts received by parent:
- `parent`, `student`: ForeignKeys
- `alert_type`: String
- `message`: Text
- `status`: SENT, READ, ACTION_TAKEN
- `created_at`, `read_at`: DateTime

**Note**: When student requests extra spending, an `EXTRA_SPENDING_REQUEST` alert is created here with the OTP.

#### 5. ParentOTPRequest
OTP for parent approvals:
- `parent`, `student`: ForeignKeys
- `otp_code`: 6-digit code
- `amount_requested`: Decimal
- `status`: PENDING, USED, EXPIRED
- `expires_at`: DateTime

### API Endpoints (`/api/parent/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `dashboard/` | GET | Parent dashboard |
| `alert-settings/` | GET, POST | Configure alerts |
| `monitoring/` | GET | Access logs |
| `alerts/` | GET | Parent alerts |
| `otp-requests/` | GET, POST | OTP management |
| `wallet-access/` | POST | Access student wallet |
| `students/` | GET | List linked students |
| `students/<id>/overview/` | GET | Student details |
| `generate-otp/` | POST | Generate approval OTP |
| `link-student/` | POST | Link student account |
| `wallet/balance/` | GET | Wallet balance |
| `wallet/transfer/` | POST | Transfer to student |

---

## Daily Allowance Flow

### Step 1: Parent Sets Allowance
Parent creates MonthlyAllowance:
- Monthly amount: 5000 INR
- Days: 30
- Daily limit: 5000/30 = 166.67 INR/day

### Step 2: System Creates Daily Allowances
System automatically creates 30 DailyAllowance records:
- Day 1-30: Each has 166.67 INR available

### Step 3: Student Withdrawal (Normal)
Student withdraws ≤ 166.67 INR:
```
✅ SUCCESS - No OTP needed
- Amount deducted from today's allowance
- Wallet balance reduced
```

### Step 4: Student Withdrawal (Exceeds Limit)
Student withdraws > 166.67 INR:
```
⚠️ 402 PAYMENT REQUIRED
- PendingSpendingRequest created with OTP
- ParentAlert created for parent dashboard
- Example: Student wants 300 INR (needs 133.33 extra from future days)
```

### Step 5: Parent Approval
Parent sees alert on dashboard with OTP:
- OTP shared with student via phone/chat
- Student enters OTP + request ID

### Step 6: Withdrawal Complete
```
✅ SUCCESS - OTP verified
- Amount processed from current + future days' allowances
- Future days locked if fully spent
```

---

## Security Features

1. **OTP System**
   - 6-digit codes
   - 10-minute expiration
   - Rate limiting

2. **Rate Limiting**
   - OTP generation: 100/hour
   - Wallet access: 100/minute
   - Sensitive operations: 200/hour

3. **Suspicious Activity Detection**
   - Multiple rapid transactions
   - Unusual amounts

4. **Audit Logging**
   - All wallet operations logged
   - Security events tracked

---

## File Structure

```
ibet/
├── student_module/
│   ├── models.py          # All student models
│   ├── views.py           # Main views
│   ├── views_wallet_new.py # Wallet with daily allowance
│   ├── urls.py             # API routes
│   ├── serializers.py     # DRF serializers
│   └── ...
│
├── parent_module/
│   ├── models.py          # All parent models
│   ├── views.py           # Main views
│   ├── urls.py            # API routes
│   ├── serializers.py    # DRF serializers
│   └── ...
│
└── frontend/src/pages/
    ├── StudentDashboard.tsx
    └── ParentDashboard.tsx
```

---

## Summary

| Feature | Student | Parent |
|---------|---------|--------|
| View Balance | ✅ | ✅ (linked students) |
| Withdraw | ✅ (daily limit) | Transfer to student |
| Set Allowance | ❌ | ✅ |
| Monitor Spending | ❌ | ✅ |
| Request Extra | ✅ | Approve/Deny |
| View Alerts | ✅ | ✅ |
| Chat | ✅ | ✅ |
