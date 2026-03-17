from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import (
    User, UserPersona, Category, Budget, Transaction, Reminder, ChatMessage, DailyLimit, OTPRequest,
    ParentStudentRequest, MonthlyAllowance, DailySpending, SpendingLock, StudentNotification, MonthlySpendingSummary
)

# --- User and Persona Serializers ---

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model, showing basic information including the persona.
    """
    class Meta:
        model = User
        # The 'persona' field is read-only because it should be set via the
        # dedicated 'select-persona' endpoint, not during general updates.
        fields = ['id', 'username', 'email', 'persona', 'transaction_pin']
        read_only_fields = ['id', 'username', 'email', 'persona']
        extra_kwargs = {
            'transaction_pin': {'write_only': True}
        }


class UserPersonaSerializer(serializers.Serializer):
    """
    A simple serializer used only for validating the input
    when a user selects their persona.
    """
    persona = serializers.ChoiceField(choices=UserPersona.choices, error_messages={
        'required': _('Persona selection is required.'),
        'invalid_choice': _('Invalid persona choice.')
    })


# --- Core Budgeting Serializers ---


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for the Category model."""
    class Meta:
        model = Category
        # The user is automatically associated in the view, so it's not needed here.
        fields = ['id', 'name']


class BudgetSerializer(serializers.ModelSerializer):
    """Serializer for the Budget model."""
    # Display the category name in the response for better readability.
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Budget
        fields = ['id', 'category', 'category_name', 'amount', 'start_date', 'end_date']
        # 'category' is the ID used for creating/updating, but we show 'category_name'
        # in the output. 'write_only=True' prevents it from appearing in the response.
        extra_kwargs = {
            'category': {'write_only': True}
        }

class OTPRequestSerializer(serializers.ModelSerializer):
    """Serializer for the OTPRequest model."""
    student_username = serializers.CharField(source='student.username', read_only=True)
    parent_username = serializers.CharField(source='parent.username', read_only=True)

    class Meta:
        model = OTPRequest
        fields = ['id', 'student', 'parent', 'student_username', 'parent_username', 'amount_requested', 'is_used', 'expires_at', 'created_at']
        read_only_fields = ['id', 'expires_at', 'created_at', 'student_username', 'parent_username']

# --- Student-Specific Serializers ---

class ReminderSerializer(serializers.ModelSerializer):
    """Serializer for the Reminder model."""
    class Meta:
        model = Reminder
        fields = ['id', 'budget', 'alert_percentage', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for the ChatMessage model."""
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    receiver_username = serializers.CharField(source='receiver.username', read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'receiver', 'sender_username', 'receiver_username', 'message', 'timestamp', 'is_read']
        read_only_fields = ['id', 'timestamp', 'sender_username', 'receiver_username']


class DailyLimitSerializer(serializers.ModelSerializer):
    """Serializer for the DailyLimit model."""
    class Meta:
        model = DailyLimit
        fields = ['id', 'daily_amount', 'current_spent', 'date']
        read_only_fields = ['id', 'date']


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for the Transaction model."""
    # Display category name instead of ID for better readability.
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'category', 'category_name', 'amount', 'transaction_type',
            'transaction_date', 'description'
        ]
        # The 'user' field is handled automatically in the view's perform_create method.
        read_only_fields = ('user',)
        # Make 'category' write-only so it's used for input but not shown in the
        # output, avoiding redundancy with 'category_name'.
        extra_kwargs = {
            'category': {'write_only': True}
        }


# New Serializers for Student Module with Parent Allowance System

class ParentStudentRequestSerializer(serializers.ModelSerializer):
    """Serializer for ParentStudentRequest model."""
    student_username = serializers.CharField(source='student.username', read_only=True)
    parent_username = serializers.CharField(source='parent.username', read_only=True)

    class Meta:
        model = ParentStudentRequest
        fields = ['id', 'student', 'parent', 'student_username', 'parent_username', 'status', 'created_at', 'processed_at', 'message']
        read_only_fields = ['id', 'student', 'created_at', 'processed_at', 'student_username', 'parent_username']


class MonthlyAllowanceSerializer(serializers.ModelSerializer):
    """Serializer for MonthlyAllowance model."""
    student_username = serializers.CharField(source='student.username', read_only=True)
    parent_username = serializers.CharField(source='parent.username', read_only=True)
    daily_allowance = serializers.SerializerMethodField()
    # Make parent not required - will be set from request in view
    parent = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    # Make start_date not required - will be set automatically
    start_date = serializers.DateField(required=False)

    class Meta:
        model = MonthlyAllowance
        fields = ['id', 'parent', 'student', 'parent_username', 'student_username', 'monthly_amount', 'days_in_month', 'daily_allowance', 'start_date', 'end_date', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'student_username', 'parent_username']

    def get_daily_allowance(self, obj):
        return obj.get_daily_allowance()


class DailySpendingSerializer(serializers.ModelSerializer):
    """Serializer for DailySpending model."""
    student_username = serializers.CharField(source='student.username', read_only=True)

    class Meta:
        model = DailySpending
        fields = ['id', 'student', 'student_username', 'date', 'daily_limit', 'amount_spent', 'remaining_amount', 'is_locked', 'locked_by_parent', 'lock_reason', 'created_at']
        read_only_fields = ['id', 'created_at', 'student_username']


class SpendingLockSerializer(serializers.ModelSerializer):
    """Serializer for SpendingLock model."""
    student_username = serializers.CharField(source='student.username', read_only=True)

    class Meta:
        model = SpendingLock
        fields = ['id', 'student', 'student_username', 'lock_type', 'amount_locked', 'is_active', 'unlock_expires_at', 'created_at', 'unlocked_at']
        read_only_fields = ['id', 'created_at', 'student_username']


class StudentNotificationSerializer(serializers.ModelSerializer):
    """Serializer for StudentNotification model."""
    student_username = serializers.CharField(source='student.username', read_only=True)

    class Meta:
        model = StudentNotification
        fields = ['id', 'student', 'student_username', 'notification_type', 'title', 'message', 'is_read', 'is_sent', 'data', 'created_at', 'read_at']
        read_only_fields = ['id', 'created_at', 'student_username']


class MonthlySpendingSummarySerializer(serializers.ModelSerializer):
    """Serializer for MonthlySpendingSummary model."""
    student_username = serializers.CharField(source='student.username', read_only=True)

    class Meta:
        model = MonthlySpendingSummary
        fields = ['id', 'student', 'student_username', 'month', 'year', 'total_allowance', 'total_spent', 'remaining_amount', 'days_elapsed', 'created_at']
        read_only_fields = ['id', 'created_at', 'student_username']
