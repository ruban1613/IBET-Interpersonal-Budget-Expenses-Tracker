from django.db import models, transaction
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from modeltranslation.translator import translator, TranslationOptions
from django.db.models import Sum, Avg, Count

User = get_user_model()


class IncomeSource(models.Model):
    """
    Model to track different income sources for individuals
    """
    INCOME_TYPES = [
        ('SALARY', 'Salary'),
        ('FREELANCE', 'Freelance'),
        ('BUSINESS', 'Business'),
        ('RENTAL', 'Rental Income'),
        ('INVESTMENT', 'Investment'),
        ('OTHER', 'Other'),
    ]

    FREQUENCY_CHOICES = [
        ('WEEKLY', 'Weekly'),
        ('BIWEEKLY', 'Bi-weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('YEARLY', 'Yearly'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='income_sources')
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    income_type = models.CharField(max_length=20, choices=INCOME_TYPES, default='SALARY')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='MONTHLY')
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.amount})"


class EmergencyFund(models.Model):
    """
    Model to track emergency funds for individuals
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='emergency_fund')
    target_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Target emergency fund amount")
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    monthly_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    target_months = models.PositiveIntegerField(help_text="Number of months the fund should cover", default=6)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def progress_percentage(self):
        """Calculate progress towards emergency fund goal"""
        if self.target_amount > 0:
            return min((self.current_amount / self.target_amount) * 100, 100)
        return 0

    @property
    def months_covered(self):
        """Calculate how many months the current fund can cover"""
        if self.monthly_contribution > 0:
            return self.current_amount / self.monthly_contribution
        return 0

    def __str__(self):
        return f"{self.user.username} Emergency Fund - {self.current_amount}/{self.target_amount}"


class IndividualDashboard(models.Model):
    """
    Dashboard model for individual users to track their financial overview
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='individual_dashboard')
    total_income = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    monthly_budget = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    savings_goal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    current_savings = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    last_updated = models.DateTimeField(auto_now=True)

    @property
    def remaining_budget(self):
        """Calculate remaining budget for the month"""
        return self.monthly_budget - self.total_expenses

    @property
    def savings_progress(self):
        """Calculate savings goal progress"""
        if self.savings_goal > 0:
            return min((self.current_savings / self.savings_goal) * 100, 100)
        return 0

    def __str__(self):
        return f"{self.user.username} Dashboard"


class ExpenseAlert(models.Model):
    """
    Model for expense alerts and notifications
    """
    ALERT_TYPES = [
        ('BUDGET_50', '50% Budget Used'),
        ('BUDGET_75', '75% Budget Used'),
        ('BUDGET_100', '100% Budget Used'),
        ('EMERGENCY_LOW', 'Emergency Fund Low'),
        ('SAVINGS_GOAL', 'Savings Goal Reminder'),
        ('CUSTOM', 'Custom Alert'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expense_alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    title = models.CharField(max_length=100)
    message = models.TextField()
    threshold_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def mark_as_read(self):
        """Mark alert as read"""
        self.is_read = True
        self.read_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class FinancialGoal(models.Model):
    """
    Model for tracking financial goals
    """
    GOAL_TYPES = [
        ('SHORT_TERM', 'Short Term (1-6 months)'),
        ('MEDIUM_TERM', 'Medium Term (6-18 months)'),
        ('LONG_TERM', 'Long Term (1+ years)'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('PAUSED', 'Paused'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='financial_goals')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES, default='SHORT_TERM')
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    target_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def progress_percentage(self):
        """Calculate progress towards goal"""
        if self.target_amount > 0:
            return min((self.current_amount / self.target_amount) * 100, 100)
        return 0

    @property
    def days_remaining(self):
        """Calculate days remaining to reach target date"""
        if self.target_date:
            return (self.target_date - timezone.now().date()).days
        return 0

    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.progress_percentage:.1f}%)"


# ============== NEW MODELS FOR ENHANCED INDIVIDUAL MODULE ==============

class IndividualSavingsWallet(models.Model):
    """
    Separate Savings Wallet for individuals.
    Money can be transferred from main wallet to savings with OTP verification.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='individual_savings_wallet'
    )
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_deposits = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_withdrawals = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_transaction_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Savings Wallet: {self.user.username} - Balance: {self.balance}"

    @transaction.atomic
    def deposit(self, amount, description="Savings Deposit"):
        """Deposit money into savings wallet"""
        wallet = IndividualSavingsWallet.objects.select_for_update().get(pk=self.pk)
        
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        
        wallet.balance += amount
        wallet.total_deposits += amount
        wallet.last_transaction_at = timezone.now()
        wallet.save()
        
        # Create transaction record
        SavingsTransaction.objects.create(
            savings_wallet=self,
            amount=amount,
            transaction_type='DEPOSIT',
            description=description,
            balance_after=wallet.balance
        )
        return wallet.balance

    @transaction.atomic
    def withdraw(self, amount, description="Savings Withdrawal"):
        """Withdraw money from savings wallet"""
        wallet = IndividualSavingsWallet.objects.select_for_update().get(pk=self.pk)
        
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        
        if wallet.balance < amount:
            raise ValueError("Insufficient savings balance")
        
        wallet.balance -= amount
        wallet.total_withdrawals += amount
        wallet.last_transaction_at = timezone.now()
        wallet.save()
        
        # Create transaction record
        SavingsTransaction.objects.create(
            savings_wallet=self,
            amount=amount,
            transaction_type='WITHDRAWAL',
            description=description,
            balance_after=wallet.balance
        )
        return wallet.balance


class SavingsTransaction(models.Model):
    """Transaction history for savings wallet"""
    TRANSACTION_TYPES = [
        ('DEPOSIT', _('Deposit')),
        ('WITHDRAWAL', _('Withdrawal')),
    ]
    
    savings_wallet = models.ForeignKey(
        IndividualSavingsWallet, 
        on_delete=models.CASCADE, 
        related_name='transactions'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.TextField()
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.savings_wallet.user.username} - {self.transaction_type}: {self.amount}"


class IndividualExpense(models.Model):
    """
    Expense tracking with categories for individual users.
    Tracks spending against deposited amount.
    """
    CATEGORY_CHOICES = [
        ('FOOD', 'Food & Dining'),
        ('TRANSPORT', 'Transportation'),
        ('UTILITIES', 'Utilities'),
        ('ENTERTAINMENT', 'Entertainment'),
        ('SHOPPING', 'Shopping'),
        ('HEALTH', 'Healthcare'),
        ('EDUCATION', 'Education'),
        ('BILLS', 'Bills & Payments'),
        ('OTHER', 'Other'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='individual_expenses'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True, default='')
    expense_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-expense_date', '-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.category}: {self.amount}"

    @classmethod
    def check_spending_threshold(cls, user):
        """
        Check if spending has crossed 50% or 80% threshold.
        Returns list of triggered alerts.
        """
        from individual_module.models_wallet import IndividualWallet
        
        try:
            wallet = IndividualWallet.objects.get(user=user)
            total_deposited = wallet.total_deposits
            
            if wallet.monthly_budget > 0:
                total_deposited = wallet.monthly_budget
            
            total_spent = IndividualExpense.objects.filter(
                user=user
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            if total_deposited <= 0:
                return []
            
            spent_percentage = (total_spent / total_deposited) * 100
            alerts_created = []
            
            if spent_percentage >= 50:
                alert, created = SpendingAlert.objects.get_or_create(
                    user=user,
                    alert_type='SPENT_50',
                    is_active=True,
                    defaults={
                        'title': '50% Spending Alert',
                        'message': f'You have spent 50% (₹{total_spent}) of your total budget/deposits (₹{total_deposited}).',
                        'amount_spent': total_spent,
                        'total_deposited': total_deposited,
                        'percentage': spent_percentage
                    }
                )
                if created:
                    alerts_created.append(alert)
            
            if spent_percentage >= 80:
                alert, created = SpendingAlert.objects.get_or_create(
                    user=user,
                    alert_type='SPENT_80',
                    is_active=True,
                    defaults={
                        'title': '80% Spending Alert',
                        'message': f'Warning! You have spent 80% (₹{total_spent}) of your total budget/deposits (₹{total_deposited}).',
                        'amount_spent': total_spent,
                        'total_deposited': total_deposited,
                        'percentage': spent_percentage
                    }
                )
                if created:
                    alerts_created.append(alert)
            
            return alerts_created
        except IndividualWallet.DoesNotExist:
            return []

    @classmethod
    @transaction.atomic
    def record_expense_and_check_alerts(cls, user, amount, category, description=''):
        """
        Record an expense and check for alerts.
        Uses the correct wallet based on the user's persona.
        """
        from individual_module.models_wallet import IndividualWallet
        from student_module.models import Wallet as CoreWallet, Transaction as GeneralTransaction
        from django.utils.timezone import localdate
        
        # 1. Deduct from the appropriate wallet based on persona
        persona = getattr(user, 'persona', 'INDIVIDUAL')
        # Normalize persona string just in case
        if persona:
            persona = persona.upper().strip()
        
        if persona in ['PARENT', 'STUDENT', 'INSTITUTE_OWNER', 'INSTITUTE_TEACHER']:
            # Use Core Wallet
            try:
                wallet = CoreWallet.objects.select_for_update().get(user=user)
                wallet.withdraw_main(amount, description=f"Expense ({category}): {description}")
                
                GeneralTransaction.objects.create(
                    user=user, amount=amount, transaction_type='EXP',
                    description=f"[{category}] {description}",
                    transaction_date=localdate()
                )
            except CoreWallet.DoesNotExist:
                raise ValueError(f"Core wallet not found for persona {persona}.")
            except ValueError as e:
                raise ValueError(f"Core Wallet Error: {str(e)}")
        else:
            # Assume INDIVIDUAL persona or other
            try:
                wallet = IndividualWallet.objects.select_for_update().get(user=user)
                wallet.withdraw(amount, description=f"Expense ({category}): {description}")
            except IndividualWallet.DoesNotExist:
                # If individual wallet doesn't exist, try one last time with core wallet as a catch-all
                try:
                    wallet = CoreWallet.objects.select_for_update().get(user=user)
                    wallet.withdraw_main(amount, description=f"Expense ({category}): {description}")
                except:
                    raise ValueError(f"No wallet found for user with persona {persona}")
            except ValueError as e:
                raise ValueError(f"Individual Wallet Error: {str(e)}")

        # 2. Create individual expense record for reporting/history
        expense = IndividualExpense.objects.create(
            user=user,
            amount=amount,
            category=category,
            description=description,
            expense_date=localdate()
        )
        
        # 3. Update dashboard stats
        dashboard, _ = IndividualDashboard.objects.get_or_create(user=user)
        dashboard.total_expenses += amount
        dashboard.save()
        
        # 4. Check thresholds (Only if it's an individual wallet)
        alerts = []
        try:
            alerts = cls.check_spending_threshold(user)
        except:
            pass
            
        return expense, alerts


class SpendingAlert(models.Model):
    """
    Alerts for spending thresholds and anomalies.
    """
    ALERT_TYPES = [
        ('SPENT_50', '50% Spent'),
        ('SPENT_80', '80% Spent'),
        ('SPENT_100', '100% Spent'),
        ('ANOMALY', 'Unusual Spending Detected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='individual_spending_alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    title = models.CharField(max_length=100)
    message = models.TextField()
    amount_spent = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_deposited = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def mark_as_read(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.user.username} - {self.alert_type}"


class SpendingAnomalyDetector:
    ANOMALY_MULTIPLIER = 3.0
    MIN_TRANSACTIONS = 3
    
    @classmethod
    def detect_anomaly(cls, user, amount):
        expenses = IndividualExpense.objects.filter(user=user)
        if expenses.count() < cls.MIN_TRANSACTIONS:
            return False
        avg_spending = expenses.aggregate(avg=Avg('amount'))['avg'] or Decimal('0')
        if avg_spending == 0:
            return False
        return amount > avg_spending * Decimal(str(cls.ANOMALY_MULTIPLIER))
    
    @classmethod
    def get_average_spending(cls, user):
        result = IndividualExpense.objects.filter(user=user).aggregate(
            avg=Avg('amount'), total=Sum('amount'), count=Count('id')
        )
        return {
            'average': result['avg'] or Decimal('0'),
            'total': result['total'] or Decimal('0'),
            'count': result['count'] or 0
        }


class InvestmentSuggestion(models.Model):
    PLAN_TYPES = [
        ('GOLD', 'Gold Plan'),
        ('INSURANCE', 'Insurance'),
        ('FD', 'Fixed Deposit'),
        ('RD', 'Recurring Deposit'),
        ('MUTUAL_FUND', 'Mutual Funds'),
        ('STOCK', 'Stock Market'),
    ]
    title = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    description = models.TextField()
    benefits = models.TextField()
    risk_level = models.CharField(max_length=50, default="Low to Medium")
    minimum_investment = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('500.00'))
    current_scenario_analysis = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.plan_type})"


# Translation options
class IncomeSourceTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

class ExpenseAlertTranslationOptions(TranslationOptions):
    fields = ('title', 'message')

class FinancialGoalTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

class InvestmentSuggestionTranslationOptions(TranslationOptions):
    fields = ('title', 'description', 'benefits', 'current_scenario_analysis')
