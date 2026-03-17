"""
Updated parent module views with enhanced security features.
This file contains the secure versions of views that use the new security services.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from core.throttling import OTPGenerationThrottle, WalletAccessThrottle, SensitiveOperationsThrottle
from core.security import OTPSecurityService, SecurityUtils
from core.security_monitoring import SecurityEventManager, AuditService
from core.permissions import OTPGenerationPermission
from .models import ParentDashboard, AlertSettings, StudentMonitoring, ParentAlert, ParentOTPRequest
from .serializers import (
    ParentDashboardSerializer, AlertSettingsSerializer, StudentMonitoringSerializer,
    ParentAlertSerializer, StudentWalletAccessSerializer, StudentOverviewSerializer,
    ParentOTPRequestSerializer, GenerateOTPSerializer
)
from student_module.models import ParentStudentLink, Wallet, Transaction
from django.utils import timezone


class SecureGenerateOTPView(APIView):
    """
    Secure API endpoint for parent to generate OTP for student wallet access.
    Uses enhanced security and removes OTP from response.
    """
    permission_classes = [permissions.IsAuthenticated, OTPGenerationPermission]
    throttle_classes = [OTPGenerationThrottle, SensitiveOperationsThrottle]

    def post(self, request, *args, **kwargs):
        serializer = GenerateOTPSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            student_id = serializer.validated_data['student_id']
            amount_requested = serializer.validated_data['amount_requested']
            reason = serializer.validated_data['reason']

            # Validate parent-student relationship
            if not SecurityUtils.validate_user_access(request.user, User.objects.get(id=student_id)):
                SecurityEventManager.log_event(
                    SecurityEventManager.EVENT_TYPES['UNAUTHORIZED_ACCESS'],
                    request.user.id,
                    {'reason': 'Invalid parent-student relationship', 'student_id': student_id}
                )
                return Response(
                    {'error': _('You are not authorized to access this student\'s wallet.')},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Check for suspicious activity
            if SecurityEventManager.detect_suspicious_activity(
                request.user.id, 'otp_generation', threshold=5, time_window_minutes=30
            ):
                return Response(
                    {'error': _('Suspicious activity detected. Please try again later.')},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            # Generate secure OTP using our security service
            otp_request_data = OTPSecurityService.create_otp_request(
                request.user.id,
                'parent_student_transfer'
            )

            # Set expiration time (10 minutes from now)
            expires_at = timezone.now() + timezone.timedelta(minutes=10)

            # Create OTP request in database (without storing the actual OTP)
            otp_request = ParentOTPRequest.objects.create(
                parent=request.user,
                student_id=student_id,
                otp_code='',  # Don't store the actual OTP code
                amount_requested=amount_requested,
                reason=reason,
                expires_at=expires_at,
                cache_key=otp_request_data['cache_key']
            )

            # Create monitoring record
            StudentMonitoring.objects.create(
                parent=request.user,
                student_id=student_id,
                otp_generated=True,
                notes=f"Generated secure OTP for {amount_requested} - {reason}"
            )

            # Audit the OTP generation
            AuditService.audit_otp_operation(
                request.user.id,
                'generate',
                True,
                {
                    'student_id': student_id,
                    'amount_requested': amount_requested,
                    'reason': reason
                }
            )

            # Log the OTP generation event
            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['OTP_GENERATED'],
                request.user.id,
                {
                    'student_id': student_id,
                    'amount_requested': amount_requested,
                    'reason': reason,
                    'expires_at': expires_at.isoformat()
                }
            )

            # Return response WITHOUT the actual OTP code
            return Response({
                'message': _('OTP generated successfully. Please share this OTP with your student.'),
                'otp_request_id': otp_request.id,
                'expires_at': otp_request.expires_at,
                'student_id': student_id,
                'amount_requested': amount_requested,
                'note': _('The OTP has been securely generated and must be shared with the student directly.')
            }, status=status.HTTP_201_CREATED)

        # Log validation errors
        SecurityEventManager.log_event(
            SecurityEventManager.EVENT_TYPES['OTP_FAILED'],
            request.user.id,
            {'reason': 'Validation failed', 'errors': serializer.errors}
        )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
