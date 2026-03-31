# IBET Project - Model Analysis Report

## Overview
The IBET project is a multi-persona budget management system with **6 user types** and multiple wallet implementations.

---

## User Personas (Defined in student_module/models.py)
| Persona | Description |
|---------|-------------|
| STUDENT | Student user with daily allowance system |
| PARENT | Parent who can manage children's allowances |
| INDIVIDUAL | Individual user with personal finance management |
| COUPLE | Couple users with shared wallet |
| RETIREE | Retiree user with pension management |
| DAILY_WAGER | Daily wage worker with daily earnings tracking |

---

## Module-wise Model Breakdown

### 1. Core Module (student_module/models.py)
| Model | Purpose |
|-------|---------|
| `User` | Extended AbstractUser with persona field |
| `Wallet` | Central wallet for student |
| `ParentStudentLink` | Links parent to student |
| `Transaction` | Wallet transactions |
| `DailyAllowance` | Cumulative daily allowance tracking |
| `CumulativeSpendingTracker` | Tracks cumulative spending |
| `PendingSpendingRequest` | Pending spending requests from students |
| `SpendingLock` | Locks on student spending |
| `StudentNotification` | Student notifications |
| `MonthlySpendingSummary` | Monthly spending summaries |

### 2. Parent Module (parent_module/models.py)
| Model | Purpose |
|-------|---------|
| `ParentDashboard` | Parent dashboard stats |
| `AlertSettings` | Alert configuration per student |
| `StudentMonitoring` | Monitoring sessions |
| `ParentAlert` | Alerts sent to parents |
| `ParentOTPRequest` | OTP requests for parent operations |

### 3. Individual Module (individual_module/models.py)
| Model | Purpose |
|-------|---------|
| `IncomeSource` | Multiple income sources |
| `EmergencyFund` | Emergency fund tracking |
| `IndividualDashboard` | Dashboard for individual |
| `ExpenseAlert` | Expense alerts |
| `FinancialGoal` | Financial goals tracking |

### 4. Individual Wallet (individual_module/models_wallet.py)
| Model | Purpose |
|-------|---------|
| `IndividualWallet` | Personal wallet with balance, budget, savings |
| `IndividualWalletTransaction` | Transaction history |
| `IndividualWalletOTPRequest` | OTP for wallet operations |

### 5. Couple Module (couple_module/models.py)
| Model | Purpose |
|-------|---------|
| `CoupleLink` | Links two users as a couple |
| `SharedWallet` | Shared wallet between partners |
| `SpendingRequest` | Spending request between partners |
| `SharedTransaction` | Shared transaction history |
| `CoupleDashboard` | Dashboard for couple |
| `CoupleAlert` | Couple-specific alerts |

### 6. Couple Wallet (couple_module/models_wallet.py)
| Model | Purpose |
|-------|---------|
| `CoupleWallet` | Shared wallet with dual partner access |
| `CoupleWalletTransaction` | Transaction history |
| `CoupleWalletOTPRequest` | OTP for couple wallet ops |

### 7. Retiree Module (retiree_module/models.py)
| Model | Purpose |
|-------|---------|
| `IncomeSource` | Multiple income sources (pension, etc.) |
| `ExpenseCategory` | Budget categories |
| `Forecast` | Financial forecasting |
| `Alert` | Budget alerts |
| `RetireeProfile` | Retiree profile |
| `RetireeTransaction` | Transaction records |
| `RetireeAlert` | Alerts for retirees |

### 8. Retiree Wallet (retiree_module/models_wallet.py)
| Model | Purpose |
|-------|---------|
| `RetireeWallet` | Wallet with pension, emergency fund |
| `RetireeWalletTransaction` | Transaction history |
| `RetireeWalletOTPRequest` | OTP for wallet operations |

### 9. Daily Wage Module (dailywage_module/models.py)
| Model | Purpose |
|-------|---------|
| `DailySalary` | Daily salary records |
| `ExpenseTracking` | Expense tracking with categories |
| `DailySummary` | Daily financial summary |
| `UserProfile` | User profile with persona |

### 10. Daily Wage Wallet (dailywage_module/models_wallet.py)
| Model | Purpose |
|-------|---------|
| `DailyWageWallet` | Wallet with daily earnings tracking |
| `DailyWageWalletTransaction` | Transaction history |
| `DailyWageWalletOTPRequest` | OTP for wallet operations |

---

## Model Statistics

| Module | Business Models | Wallet Models | Total |
|--------|-----------------|---------------|-------|
| student_module | 8 | 0 | 8 |
| parent_module | 5 | 0 | 5 |
| individual_module | 4 | 3 | 7 |
| couple_module | 6 | 3 | 9 |
| retiree_module | 7 | 3 | 10 |
| dailywage_module | 4 | 3 | 7 |
| **Total** | **34** | **12** | **46** |

---

## Key Features by Module

### Student-Parent Module
- Cumulative daily allowance system
- Parent-student linking
- Spending locks and limits
- OTP-based spending approvals
- Real-time notifications

### Individual Module  
- Multiple income sources
- Emergency fund tracking
- Financial goals with progress
- Expense alerts

### Couple Module
- Partner linking
- Shared wallet with dual access
- Spending requests between partners
- Joint financial goals

### Retiree Module
- Pension management
- Budget forecasting
- Expense categories
- Low balance alerts

### Daily Wage Module
- Daily earnings tracking
- Essential vs non-essential expenses
- Weekly/monthly goals
- Daily summaries

---

## Wallet Security Features
All wallet models include:
- OTP protection for transactions
- Transaction history with balance tracking
- Lock/unlock functionality
- Last transaction timestamps
- Atomic transactions with row locking
