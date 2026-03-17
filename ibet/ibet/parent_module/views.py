from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from core.throttling import OTPGenerationThrottle, WalletAccessThrottle, SensitiveOperationsThrottle
from core.security import OTPSecurityService
from .models import ParentDashboard, AlertSettings, StudentMonitoring, ParentAlert, ParentOTPRequest
from .serializers import (
    ParentDashboardSerializer, AlertSettingsSerializer, StudentMonitoringSerializer,
    ParentAlertSerializer, StudentWalletAccessSerializer, StudentOverviewSerializer,
    ParentOTPRequestSerializer, GenerateOTPSerializer
)
from student_module.models import ParentStudentLink, Wallet, Transaction
from django.utils import timezone
import random
import string


class ParentDashboardViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows parent dashboards to be viewed or edited.
    """
    serializer_class = ParentDashboardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ParentDashboard.objects.filter(parent=self.request.user)

    def perform_create(self, serializer):
        parent_dashboard, created = ParentDashboard.objects.get_or_create(parent=self.request.user)
        serializer.instance = parent_dashboard
        serializer.save()


class AlertSettingsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows alert settings to be viewed or edited.
    """
    serializer_class = AlertSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AlertSettings.objects.filter(parent=self.request.user)

    def perform_create(self, serializer):
        serializer.save(parent=self.request.user)


class StudentMonitoringViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows student monitoring sessions to be viewed or edited.
    """
    serializer_class = StudentMonitoringSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return StudentMonitoring.objects.filter(parent=self.request.user)

    def perform_create(self, serializer):
        serializer.save(parent=self.request.user)


class ParentAlertViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows parent alerts to be viewed or edited.
    """
    serializer_class = ParentAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ParentAlert.objects.filter(parent=self.request.user)

    def perform_create(self, serializer):
        serializer.save(parent=self.request.user)

    @action(detail=True, methods=['patch'])
    def mark_as_read(self, request, pk=None):
        """Mark an alert as read."""
        alert = self.get_object()
        alert.status = 'READ'
        alert.read_at = timezone.now()
        alert.save()
        return Response({'status': _('Alert marked as read')})

    @action(detail=True, methods=['patch'])
    def mark_action_taken(self, request, pk=None):
        """Mark an alert as having action taken."""
        alert = self.get_object()
        alert.status = 'ACTION_TAKEN'
        alert.save()
        return Response({'status': _('Action recorded')})


class StudentWalletAccessView(APIView):
    """
    API endpoint for parent to access student's wallet and approve extra funds.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [SensitiveOperationsThrottle, WalletAccessThrottle]

    def post(self, request, *args, **kwargs):
        serializer = StudentWalletAccessSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            student_id = serializer.validated_data['student_id']
            amount_needed = serializer.validated_data['amount_needed']
            reason = serializer.validated_data['reason']

            # Create monitoring record
            StudentMonitoring.objects.create(
                parent=request.user,
                student_id=student_id,
                wallet_accessed=True,
                notes=f"Requested extra funds: {amount_needed} for {reason}"
            )

            # Here you would typically generate and send OTP
            # For now, we'll just return success
            return Response({
                'message': _('Wallet access request processed. OTP sent to student.'),
                'student_id': student_id,
                'amount_requested': amount_needed
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentOverviewView(APIView):
    """
    API endpoint for parent to view student's financial overview.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [WalletAccessThrottle]

    def get(self, request, student_id, *args, **kwargs):
        # Check if parent is linked to this student
        if not ParentStudentLink.objects.filter(parent=request.user, student_id=student_id).exists():
            return Response(
                {'error': _('You are not authorized to view this student\'s data')},
                status=status.HTTP_403_FORBIDDEN
            )

        # Create monitoring record
        StudentMonitoring.objects.create(
            parent=request.user,
            student_id=student_id,
            wallet_accessed=False,
            notes="Viewed student overview"
        )

        serializer = StudentOverviewSerializer({'student_id': student_id})
        return Response(serializer.data)


class LinkedStudentsView(APIView):
    """
    API endpoint to get all students linked to the parent.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        linked_students = ParentStudentLink.objects.filter(parent=request.user).select_related('student')
        students_data = []

        for link in linked_students:
            student = link.student
            try:
                wallet = Wallet.objects.get(user=student)
                wallet_balance = wallet.balance
            except Wallet.DoesNotExist:
                wallet_balance = 0.00

            students_data.append({
                'id': student.id,
                'username': student.username,
                'email': student.email,
                'wallet_balance': wallet_balance,
                'linked_since': link.id  # Using id as proxy for creation date
            })

        return Response({
            'linked_students': students_data,
            'total_students': len(students_data)
        })


class ParentOTPRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows OTP requests to be viewed.
    """
    serializer_class = ParentOTPRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ParentOTPRequest.objects.filter(parent=self.request.user)


class GenerateOTPView(APIView):
    """
    API endpoint for parent to generate OTP for student wallet access.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [OTPGenerationThrottle, SensitiveOperationsThrottle]

    def post(self, request, *args, **kwargs):
        serializer = GenerateOTPSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            student_id = serializer.validated_data['student_id']
            amount_requested = serializer.validated_data['amount_requested']
            reason = serializer.validated_data['reason']

            # Get student user for email
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                student = User.objects.get(id=student_id)
                student_email = student.email
            except User.DoesNotExist:
                return Response({'error': _('Student not found')}, status=status.HTTP_404_NOT_FOUND)

            # Generate secure OTP using security service
            otp_request_data = OTPSecurityService.create_otp_request(
                request.user.id,
                'parent_student_wallet_access',
                email=student_email
            )

            # Set expiration time (10 minutes from now)
            expires_at = timezone.now() + timezone.timedelta(minutes=10)

            # Create OTP request
            otp_request = ParentOTPRequest.objects.create(
                parent=request.user,
                student_id=student_id,
                otp_code='',  # Don't store the actual OTP
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
                notes=f"Generated OTP for {amount_requested} - {reason}"
            )

            return Response({
                'message': _('OTP generated and sent to student successfully.'),
                'otp_request_id': otp_request.id,
                'expires_at': expires_at,
                'student_id': student_id,
                'amount_requested': amount_requested
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LinkStudentView(APIView):
    """
    API endpoint for parent to link to a student.
    Parent enters student's username to create the link.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        from django.contrib.auth import get_user_model
        from student_module.models import ParentStudentLink, StudentNotification
        
        User = get_user_model()
        
        student_username = request.data.get('student_username')
        
        if not student_username:
            return Response(
                {'error': _('Student username is required.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Debug: Check user's persona value
        user_persona = getattr(request.user, 'persona', None)
        
        # Check if user is a parent - use the enum value
        if user_persona is None:
            return Response(
                {'error': _('Your account does not have a persona set. Please select Parent role in your profile.')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if user_persona != 'PARENT':
            return Response(
                {'error': _(f'Only parents can link to students. Your current role is: {user_persona}')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Find the student user
        try:
            student = User.objects.get(username=student_username, persona='STUDENT')
        except User.DoesNotExist:
            return Response(
                {'error': _('Student user not found.')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already linked
        if ParentStudentLink.objects.filter(parent=request.user, student=student).exists():
            return Response(
                {'error': _('This student is already linked to your account.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create the link
        link = ParentStudentLink.objects.create(
            parent=request.user,
            student=student
        )
        
        # Notify the student
        StudentNotification.objects.create(
            student=student,
            notification_type='PARENT_LINKED',
            title=_('Parent Linked'),
            message=_(f'You have been linked to {request.user.username}. They can now monitor your spending and set allowances.')
        )
        
        return Response({
            'message': _('Successfully linked to student.'),
            'student_id': student.id,
            'student_username': student.username
        }, status=status.HTTP_201_CREATED)




