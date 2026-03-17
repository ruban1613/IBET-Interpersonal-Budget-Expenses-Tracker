"""
Updated student module views with enhanced security features.
This file contains the secure versions of views that use the new security services.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _
from core.throttling import OTPGenerationThrottle, OTPVerificationThrottle, WalletAccessThrottle, SensitiveOperationsThrottle
from core.security import OTPSecurityService, SecurityUtils
from core.security_monitoring import SecurityEventManager, AuditService
from core.permissions import OTPVerificationPermission
from .models import Budget, Category, Transaction, User, UserPersona, Reminder, ChatMessage, DailyLimit, OTPRequest
from django.db.models import Sum, Q
from django.utils import timezone
from .serializers import (
    BudgetSerializer, CategorySerializer, TransactionSerializer, UserSerializer, UserPersonaSerializer,
    ReminderSerializer, ChatMessageSerializer, DailyLimitSerializer, OTPRequestSerializer
)


class SecureVerifyOTPView(APIView):
    """
    Secure API endpoint for student to verify OTP and receive extra funds from parent.
    Uses enhanced security validation and monitoring.
    """
    permission_classes = [permissions.IsAuthenticated, OTPVerificationPermission]
    throttle_classes = [OTPVerificationThrottle, SensitiveOperationsThrottle]

    def post(self, request, *args, **kwargs):
        from parent_module.models import ParentOTPRequest
        from parent_module.serializers import VerifyOTPSerializer
        from .models import Wallet

        serializer = VerifyOTPSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            otp_code = serializer.validated_data['otp_code']
            student_id = serializer.validated_data['student_id']

            # Log the verification attempt
            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['OTP_VERIFIED'],
                request.user.id,
                {
                    'student_id': student_id,
                    'ip_address': request.META.get('REMOTE_ADDR'),
                    'user_agent': request.META.get('HTTP_USER_AGENT')
                }
            )

            # Find the OTP request using cache-based secure validation
            try:
                # Get all pending OTP requests for this student
                otp_requests = ParentOTPRequest.objects.filter(
                    student_id=student_id,
                    status='PENDING'
                )

                valid_request = None
                for otp_request in otp_requests:
                    # Use secure validation from our security service
                    cache_key = f"otp_request_{otp_request.id}"
                    is_valid, error_message = OTPSecurityService.validate_otp(
                        request.user.id,
                        otp_code,
                        cache_key,
                        'parent_student_transfer'
                    )

                    if is_valid:
                        valid_request = otp_request
                        break

                if not valid_request:
                    # Log failed attempt
                    SecurityEventManager.log_event(
                        SecurityEventManager.EVENT_TYPES['OTP_FAILED'],
                        request.user.id,
                        {'reason': 'Invalid OTP or request not found'}
                    )
                    return Response(
                        {'error': _('Invalid OTP or OTP request not found.')},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            except ParentOTPRequest.DoesNotExist:
                # Log failed attempt
                SecurityEventManager.log_event(
                    SecurityEventManager.EVENT_TYPES['OTP_FAILED'],
                    request.user.id,
                    {'reason': 'OTP request not found'}
                )
                return Response(
                    {'error': _('Invalid OTP or OTP request not found.')},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if OTP is expired
            if valid_request.is_expired():
                valid_request.mark_as_expired()
                SecurityEventManager.log_event(
                    SecurityEventManager.EVENT_TYPES['OTP_FAILED'],
                    request.user.id,
                    {'reason': 'OTP expired'}
                )
                return Response(
                    {'error': _('OTP has expired.')},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verify that the requesting user is the correct student
            if valid_request.student_id != request.user.id:
                SecurityEventManager.log_event(
                    SecurityEventManager.EVENT_TYPES['UNAUTHORIZED_ACCESS'],
                    request.user.id,
                    {'reason': 'User not authorized for this OTP'}
                )
                return Response(
                    {'error': _('You are not authorized to use this OTP.')},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Check for suspicious activity
            if SecurityEventManager.detect_suspicious_activity(
                request.user.id, 'otp_verification', threshold=3, time_window_minutes=10
            ):
                return Response(
                    {'error': _('Suspicious activity detected. Please try again later.')},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            # Add funds to student's wallet
            try:
                wallet = Wallet.objects.get(user=request.user)
                wallet.balance += valid_request.amount_requested
                wallet.save()

                # Audit the wallet operation
                AuditService.audit_wallet_operation(
                    request.user.id,
                    'parent_transfer',
                    valid_request.amount_requested,
                    {'parent_id': valid_request.parent.id, 'reason': valid_request.reason}
                )

            except Wallet.DoesNotExist:
                # Create wallet if it doesn't exist
                wallet = Wallet.objects.create(
                    user=request.user,
                    balance=valid_request.amount_requested
                )

                # Audit wallet creation
                AuditService.audit_wallet_operation(
                    request.user.id,
                    'wallet_created',
                    valid_request.amount_requested,
                    {'parent_id': valid_request.parent.id, 'reason': valid_request.reason}
                )

            # Mark OTP as used
            valid_request.mark_as_used()

            # Create transaction record
            Transaction.objects.create(
                user=request.user,
                amount=valid_request.amount_requested,
                transaction_type='INC',
                description=_(f'Extra funds from parent: {valid_request.reason}'),
                category=None  # Parent transfers don't need a category
            )

            # Log successful verification
            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['OTP_VERIFIED'],
                request.user.id,
                {
                    'success': True,
                    'amount': valid_request.amount_requested,
                    'parent_id': valid_request.parent.id
                }
            )

            return Response({
                'message': _('Successfully received funds from parent.'),
                'new_balance': wallet.balance,
                'reason': valid_request.reason
            }, status=status.HTTP_200_OK)

        # Log validation errors
        SecurityEventManager.log_event(
            SecurityEventManager.EVENT_TYPES['OTP_FAILED'],
            request.user.id,
            {'reason': 'Validation failed', 'errors': serializer.errors}
        )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
