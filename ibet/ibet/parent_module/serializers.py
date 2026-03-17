from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import ParentDashboard, AlertSettings, StudentMonitoring, ParentAlert, ParentOTPRequest
from student_module.models import ParentStudentLink, Transaction, Wallet, DailyAllowance
from django.db.models import Sum


class ParentDashboardSerializer(serializers.ModelSerializer):
    """Serializer for the ParentDashboard model."""
    total_student_spending = serializers.SerializerMethodField()
    linked_students_count = serializers.SerializerMethodField()
    wallet_balance = serializers.SerializerMethodField()
    today_spent = serializers.SerializerMethodField()
    total_funds = serializers.SerializerMethodField()

    class Meta:
        model = ParentDashboard
        fields = [
            'id', 'total_students', 'total_alerts_sent', 'last_accessed',
            'total_student_spending', 'linked_students_count',
            'wallet_balance', 'today_spent', 'total_funds'
        ]
        read_only_fields = ['id', 'last_accessed']

    def get_total_student_spending(self, obj):
        return obj.get_total_student_spending()

    def get_linked_students_count(self, obj):
        return ParentStudentLink.objects.filter(parent=obj.parent).count()

    def get_wallet_balance(self, obj):
        try:
            wallet = Wallet.objects.get(user=obj.parent)
            return float(wallet.balance)
        except Wallet.DoesNotExist:
            return 0.0

    def get_today_spent(self, obj):
        from django.utils import timezone
        today = timezone.localdate()
        # Count all parent's EXPENSE transactions (Personal Expenses + Transfers to Children)
        spent = Transaction.objects.filter(
            user=obj.parent,
            transaction_type='EXP',
            transaction_date=today
        ).aggregate(total=Sum('amount'))['total'] or 0.00
        return float(spent)

    def get_total_funds(self, obj):
        # Total funds available to the parent (their wallet balance)
        try:
            wallet = Wallet.objects.get(user=obj.parent)
            return float(wallet.balance)
        except Wallet.DoesNotExist:
            return 0.0


class AlertSettingsSerializer(serializers.ModelSerializer):
    """Serializer for the AlertSettings model."""
    parent_username = serializers.CharField(source='parent.username', read_only=True)
    student_username = serializers.CharField(source='student.username', read_only=True)

    class Meta:
        model = AlertSettings
        fields = [
            'id', 'parent', 'student', 'parent_username', 'student_username',
            'alert_type', 'is_enabled', 'email_notification', 'sms_notification', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'parent_username', 'student_username']


class StudentMonitoringSerializer(serializers.ModelSerializer):
    """Serializer for the StudentMonitoring model."""
    parent_username = serializers.CharField(source='parent.username', read_only=True)
    student_username = serializers.CharField(source='student.username', read_only=True)

    class Meta:
        model = StudentMonitoring
        fields = [
            'id', 'parent', 'student', 'parent_username', 'student_username',
            'accessed_at', 'wallet_accessed', 'otp_generated', 'notes'
        ]
        read_only_fields = ['id', 'accessed_at', 'parent_username', 'student_username']


class ParentAlertSerializer(serializers.ModelSerializer):
    """Serializer for the ParentAlert model."""
    parent_username = serializers.CharField(source='parent.username', read_only=True)
    student_username = serializers.CharField(source='student.username', read_only=True)

    class Meta:
        model = ParentAlert
        fields = [
            'id', 'parent', 'student', 'parent_username', 'student_username',
            'alert_type', 'message', 'status', 'created_at', 'read_at'
        ]
        read_only_fields = ['id', 'created_at', 'parent_username', 'student_username']


class StudentWalletAccessSerializer(serializers.Serializer):
    """Serializer for parent accessing student's wallet."""
    student_id = serializers.IntegerField()
    amount_needed = serializers.DecimalField(max_digits=10, decimal_places=2)
    reason = serializers.CharField(max_length=255)

    def validate_student_id(self, value):
        request = self.context.get('request')
        if not ParentStudentLink.objects.filter(parent=request.user, student_id=value).exists():
            raise serializers.ValidationError(_("You are not linked to this student."))
        return value


class StudentOverviewSerializer(serializers.Serializer):
    """Serializer for parent viewing student's overview."""
    student_id = serializers.IntegerField()
    wallet_balance = serializers.SerializerMethodField()
    daily_limit = serializers.SerializerMethodField()
    current_daily_spent = serializers.SerializerMethodField()
    recent_transactions = serializers.SerializerMethodField()
    allowance_history = serializers.SerializerMethodField()
    has_pin = serializers.SerializerMethodField()

    def get_wallet_balance(self, obj):
        try:
            wallet = Wallet.objects.get(user_id=obj['student_id'])
            return wallet.balance
        except Wallet.DoesNotExist:
            return 0.00

    def get_daily_limit(self, obj):
        from django.utils import timezone
        today = timezone.now().date()
        
        # Get all available daily allowances for the student
        daily_allowances = DailyAllowance.objects.filter(
            student_id=obj['student_id'],
            is_available=True
        ).order_by('date')
        
        if not daily_allowances.exists():
            return None
        
        # Calculate totals from available days
        total_monthly = sum(float(da.daily_amount) for da in daily_allowances)
        total_spent = sum(float(da.amount_spent) for da in daily_allowances)
        
        # Get today's allowance specifically
        try:
            today_allowance = DailyAllowance.objects.get(student_id=obj['student_id'], date=today)
            today_limit = float(today_allowance.daily_amount)
            today_spent = float(today_allowance.amount_spent)
        except DailyAllowance.DoesNotExist:
            today_limit = 0
            today_spent = 0
        
        return {
            'monthly_budget': total_monthly,
            'daily_limit_amount': today_limit,
            'current_daily_spent': today_spent
        }

    def get_current_daily_spent(self, obj):
        # Calculate current day's spending
        from django.utils import timezone
        today = timezone.localdate()
        return Transaction.objects.filter(
            user_id=obj['student_id'],
            transaction_date=today,
            transaction_type='EXP'
        ).aggregate(total=Sum('amount'))['total'] or 0.00

    def get_recent_transactions(self, obj):
        from django.utils import timezone
        from django.contrib.auth import get_user_model
        from student_module.models import WalletTransaction
        User = get_user_model()
        student_id = obj['student_id']
        try:
            student_user = User.objects.get(id=student_id)
        except User.DoesNotExist:
            return []
        
        # 1. Get Wallet Transactions
        wallet_txs = WalletTransaction.objects.filter(wallet__user_id=student_id).order_by('-created_at')[:10]
        
        # 2. Get General Transactions (Allowances, etc.)
        general_txs = Transaction.objects.filter(user_id=student_id).order_by('-id')[:10]
        
        # 3. Get Individual Expenses
        from individual_module.models import IndividualExpense
        expenses = IndividualExpense.objects.filter(user_id=student_id).order_by('-expense_date', '-created_at')[:10]
        
        combined = []
        for t in wallet_txs:
            combined.append({
                'id': f"w_{t.id}",
                'amount': float(t.amount),
                'transaction_type': t.transaction_type,
                'description': t.description,
                'date': t.created_at
            })
            
        for t in general_txs:
            # Include all general transactions (Allowances, Transfers, Spending records)
            dt = timezone.datetime.combine(t.transaction_date, timezone.datetime.min.time())
            combined.append({
                'id': f"g_{t.id}",
                'amount': float(t.amount),
                'transaction_type': t.transaction_type,
                'description': t.description,
                'date': timezone.make_aware(dt)
            })
                
        for e in expenses:
            dt = timezone.datetime.combine(e.expense_date, timezone.datetime.min.time())
            combined.append({
                'id': f"e_{e.id}",
                'amount': float(e.amount),
                'transaction_type': 'EXP',
                'description': f"[{e.category}] {e.description}",
                'date': timezone.make_aware(dt)
            })
            
        combined.sort(key=lambda x: x['date'], reverse=True)
        return combined[:10]

    def get_allowance_history(self, obj):
        from student_module.models import AllowanceContribution
        history = AllowanceContribution.objects.filter(
            student_id=obj['student_id']
        ).order_by('-created_at')[:10]
        return [{
            'id': h.id,
            'amount': float(h.amount),
            'day': h.day,
            'month': h.month,
            'year': h.year,
            'date': h.created_at
        } for h in history]

    def get_has_pin(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return request.user.transaction_pin is not None and request.user.transaction_pin != ''
        return False


class ParentOTPRequestSerializer(serializers.ModelSerializer):
    """Serializer for the ParentOTPRequest model."""
    parent_username = serializers.CharField(source='parent.username', read_only=True)
    student_username = serializers.CharField(source='student.username', read_only=True)
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = ParentOTPRequest
        fields = [
            'id', 'parent', 'student', 'parent_username', 'student_username',
            'otp_code', 'amount_requested', 'reason', 'status', 'created_at',
            'expires_at', 'used_at', 'is_expired'
        ]
        read_only_fields = [
            'id', 'otp_code', 'created_at', 'expires_at', 'used_at',
            'parent_username', 'student_username', 'is_expired'
        ]

    def get_is_expired(self, obj):
        return obj.is_expired()


class GenerateOTPSerializer(serializers.Serializer):
    """Serializer for generating OTP for student wallet access."""
    student_id = serializers.IntegerField()
    amount_requested = serializers.DecimalField(max_digits=10, decimal_places=2)
    reason = serializers.CharField(max_length=255)

    def validate_student_id(self, value):
        request = self.context.get('request')
        if not ParentStudentLink.objects.filter(parent=request.user, student_id=value).exists():
            raise serializers.ValidationError(_("You are not linked to this student."))
        return value


class VerifyOTPSerializer(serializers.Serializer):
    """Serializer for verifying OTP."""
    otp_code = serializers.CharField(max_length=6)
    student_id = serializers.IntegerField()

    def validate_otp_code(self, value):
        if len(value) != 6 or not value.isdigit():
            raise serializers.ValidationError(_("OTP must be 6 digits."))
        return value

    def validate_student_id(self, value):
        request = self.context.get('request')
        if not request or not request.user:
            return value
            
        # If the requester is a parent, they must be linked to the student
        if request.user.persona == 'PARENT':
            if not ParentStudentLink.objects.filter(parent=request.user, student_id=value).exists():
                raise serializers.ValidationError("You are not linked to this student.")
        # If the requester is a student, they must be verifying their own ID
        elif request.user.persona == 'STUDENT':
            if request.user.id != value:
                raise serializers.ValidationError("You can only verify OTPs for your own account.")
                
        return value
