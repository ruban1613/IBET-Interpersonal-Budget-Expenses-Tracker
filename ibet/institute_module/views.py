from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Q, Count
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from decimal import Decimal
from .models import Institute, TeacherProfile, InstituteStudentProfile, FeePayment, SalaryPayment, InstituteNotification, StudentAttendance, TeacherAttendance
from .serializers import (
    InstituteSerializer, TeacherProfileSerializer, InstituteStudentProfileSerializer,
    FeePaymentSerializer, SalaryPaymentSerializer, InstituteNotificationSerializer, StudentAttendanceSerializer, TeacherAttendanceSerializer
)

User = get_user_model()

class StudentAttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = StudentAttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = StudentAttendance.objects.all()
        
        # Filtering by date, month, year
        date = self.request.query_params.get('date')
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        
        if date:
            queryset = queryset.filter(date=date)
        if month:
            queryset = queryset.filter(date__month=month)
        if year:
            queryset = queryset.filter(date__year=year)

        if user.persona == 'INSTITUTE_OWNER':
            return queryset.filter(student_profile__institute__owner=user)
        elif user.persona == 'INSTITUTE_TEACHER':
            profiles = TeacherProfile.objects.filter(user=user, is_active=True)
            if not profiles.exists():
                return StudentAttendance.objects.none()
            
            # Get earliest joining date across institutes
            earliest_joining = profiles.order_by('joining_date').first().joining_date
            # Filter by assigned students only
            return queryset.filter(
                student_profile__assigned_teachers__user=user,
                date__gte=earliest_joining
            )
        elif user.persona == 'STUDENT':
            return queryset.filter(student_profile__user=user)
        return StudentAttendance.objects.none()

    @action(detail=False, methods=['post'])
    def mark_bulk(self, request):
        """Mark attendance for multiple students at once"""
        date = request.data.get('date', timezone.localdate())
        records = request.data.get('records', []) # [{'student_profile': id, 'status': 'PRESENT'}]

        if not records:
            return Response({'error': 'No records provided'}, status=400)

        created_records = []
        for rec in records:
            profile_id = rec.get('student_profile')
            status_val = rec.get('status', 'PRESENT')
            
            profile = get_object_or_404(InstituteStudentProfile, id=profile_id)
            
            if self.request.user.persona == 'INSTITUTE_OWNER':
                if profile.institute.owner != self.request.user: continue
            else:
                if not TeacherProfile.objects.filter(user=self.request.user, institute=profile.institute).exists():
                    continue

            attendance, _ = StudentAttendance.objects.update_or_create(
                student_profile=profile,
                date=date,
                defaults={'status': status_val, 'marked_by': self.request.user}
            )
            created_records.append(attendance)

        return Response({'message': f'Attendance marked for {len(created_records)} students'})

class InstituteViewSet(viewsets.ModelViewSet):
    serializer_class = InstituteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Institute.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        if self.request.user.persona != 'INSTITUTE_OWNER':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only users with 'Institute Owner' persona can create an institute.")
        serializer.save(owner=self.request.user)

class TeacherAttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = TeacherAttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.persona == 'INSTITUTE_OWNER':
            return TeacherAttendance.objects.filter(teacher__institute__owner=user)
        elif user.persona == 'INSTITUTE_TEACHER':
            return TeacherAttendance.objects.filter(teacher__user=user)
        return TeacherAttendance.objects.none()

    def create(self, request, *args, **kwargs):
        teacher_id = request.data.get('teacher')
        date = request.data.get('date', timezone.now().date())
        status_val = request.data.get('status', 'PRESENT')
        extra_sessions = request.data.get('extra_sessions', 0)
        remarks = request.data.get('remarks', '')

        teacher = get_object_or_404(TeacherProfile, id=teacher_id, institute__owner=request.user)

        attendance, created = TeacherAttendance.objects.update_or_create(
            teacher=teacher,
            date=date,
            defaults={
                'status': status_val,
                'extra_sessions': extra_sessions,
                'remarks': remarks
            }
        )

        return Response(TeacherAttendanceSerializer(attendance).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def calculate_payout(self, request):
        teacher_id = request.query_params.get('teacher_id')
        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))

        teacher = get_object_or_404(TeacherProfile, id=teacher_id, institute__owner=request.user)
        attendance = TeacherAttendance.objects.filter(teacher=teacher, date__month=month, date__year=year)

        absent_days = attendance.filter(status='ABSENT').count()
        half_days = attendance.filter(status='HALF_DAY').count()
        ot_days = attendance.filter(status='OVERTIME').count()
        total_extra_sessions = attendance.aggregate(total=Sum('extra_sessions'))['total'] or 0

        daily_rate = teacher.daily_rate
        
        # Logic: 
        # - Full deduction for ABSENT
        # - 50% deduction for HALF_DAY
        # - 1.5x bonus for OVERTIME day
        # - Session Rate bonus for extra_sessions
        
        deductions = (Decimal(str(absent_days)) * daily_rate) + (Decimal(str(half_days)) * daily_rate * Decimal('0.5'))
        ot_bonus = (Decimal(str(ot_days)) * daily_rate * Decimal('0.5')) # 0.5 because they already get base for that day if present
        session_bonus = Decimal(str(total_extra_sessions)) * teacher.extra_session_rate
        
        net_salary = teacher.base_monthly_salary - deductions + ot_bonus + session_bonus

        return Response({
            'teacher_name': teacher.user.username,
            'base_salary': float(teacher.base_monthly_salary),
            'daily_rate': float(daily_rate),
            'absent_days': absent_days,
            'half_days': half_days,
            'ot_days': ot_days,
            'extra_sessions': total_extra_sessions,
            'deductions': float(deductions),
            'ot_bonus': float(ot_bonus),
            'session_bonus': float(session_bonus),
            'net_payout': float(net_salary)
        })

class TeacherProfileViewSet(viewsets.ModelViewSet):
    serializer_class = TeacherProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.persona == 'INSTITUTE_OWNER':
            return TeacherProfile.objects.filter(institute__owner=user)
        elif user.persona == 'INSTITUTE_TEACHER':
            teacher_institutes = TeacherProfile.objects.filter(user=user, is_active=True).values_list('institute_id', flat=True)
            return TeacherProfile.objects.filter(institute_id__in=teacher_institutes)
        return TeacherProfile.objects.none()

    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        institute_id = request.data.get('institute')
        base_monthly_salary = request.data.get('base_monthly_salary', 0)
        working_days = request.data.get('working_days_per_month', 26)
        session_rate = request.data.get('extra_session_rate', 0)

        if not all([username, institute_id]):
            return Response({'error': 'username and institute are required'}, status=400)

        institute = get_object_or_404(Institute, id=institute_id, owner=request.user)

        try:
            user = User.objects.get(username=username)
            if user.persona != 'INSTITUTE_TEACHER':
                return Response({'error': f'User "{username}" is not registered as an Institute Teacher.'}, status=400)
        except User.DoesNotExist:
            return Response({'error': f'User "{username}" not found.'}, status=400)

        if TeacherProfile.objects.filter(user=user, institute=institute).exists():
            return Response({'error': f'Teacher "{username}" is already linked.'}, status=400)

        profile = TeacherProfile.objects.create(
            user=user,
            institute=institute,
            base_monthly_salary=base_monthly_salary,
            working_days_per_month=working_days,
            extra_session_rate=session_rate
        )

        return Response({
            'message': 'Teacher linked successfully',
            'profile': TeacherProfileSerializer(profile).data
        }, status=status.HTTP_201_CREATED)

class InstituteStudentProfileViewSet(viewsets.ModelViewSet):
    serializer_class = InstituteStudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.persona == 'INSTITUTE_OWNER':
            return InstituteStudentProfile.objects.filter(institute__owner=user)
        elif user.persona == 'INSTITUTE_TEACHER':
            return InstituteStudentProfile.objects.filter(assigned_teachers__user=user)
        return InstituteStudentProfile.objects.none()

    def create(self, request, *args, **kwargs):
        student_name = request.data.get('student_name')
        parent_mobile = request.data.get('parent_mobile')
        institute_id = request.data.get('institute')
        monthly_fee = request.data.get('monthly_fee')
        due_day = request.data.get('due_day', 5)

        if not all([student_name, parent_mobile, institute_id]):
            return Response({'error': 'student_name, parent_mobile, and institute are required'}, status=400)

        institute = get_object_or_404(Institute, id=institute_id, owner=request.user)

        if InstituteStudentProfile.objects.filter(institute=institute, student_name=student_name, parent_mobile=parent_mobile).exists():
            return Response({'error': f'Student "{student_name}" already exists.'}, status=400)

        clean_name = "".join(filter(str.isalnum, student_name.lower().split()[0]))
        generated_username = f"{clean_name}_{parent_mobile[-4:]}"
        
        user, created = User.objects.get_or_create(
            username=generated_username,
            defaults={
                'persona': 'STUDENT',
                'first_name': student_name.split()[0],
                'email': f"{generated_username}@ibet.com"
            }
        )
        if created:
            user.set_password('student123')
            user.save()

        profile = InstituteStudentProfile.objects.create(
            user=user,
            institute=institute,
            student_name=student_name,
            parent_mobile=parent_mobile,
            monthly_fee=monthly_fee,
            due_day=due_day
        )
        
        return Response({
            'message': 'Student registered successfully',
            'username': user.username,
            'temporary_password': 'student123' if created else 'Existing account used',
            'profile': InstituteStudentProfileSerializer(profile).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def link_by_username(self, request):
        """Link an existing student account (Academic) using their username"""
        try:
            username = request.data.get('username')
            institute_id = request.data.get('institute')
            monthly_fee = request.data.get('monthly_fee')
            due_day = request.data.get('due_day', 5)

            if not all([username, institute_id, monthly_fee]):
                return Response({'error': 'username, institute, and monthly_fee are required'}, status=400)

            institute = get_object_or_404(Institute, id=institute_id, owner=request.user)

            try:
                user = User.objects.get(username=username)
                # Allow linking any persona for testing/flexibility
            except User.DoesNotExist:
                return Response({'error': f'User "{username}" not found.'}, status=400)

            # 1. Check if this specific user is already linked
            if InstituteStudentProfile.objects.filter(institute=institute, user=user).exists():
                return Response({'error': f'Student "{username}" is already linked to this institute.'}, status=400)

            # Use student's real name and phone from their account
            student_name = f"{user.first_name} {user.last_name}".strip() or user.username
            parent_mobile = getattr(user, 'phone', 'Not Provided') or 'Not Provided'

            # 2. Check for unique_together constraint [institute, student_name, parent_mobile]
            # If a profile exists with this name and mobile, but different user (or no user)
            existing_profile = InstituteStudentProfile.objects.filter(
                institute=institute, 
                student_name=student_name, 
                parent_mobile=parent_mobile
            ).first()
            
            if existing_profile:
                if existing_profile.user:
                    return Response({'error': f'A profile for "{student_name}" already exists and is linked to another user.'}, status=400)
                # If existing profile has no user, link it now!
                existing_profile.user = user
                existing_profile.monthly_fee = monthly_fee
                existing_profile.due_day = due_day
                existing_profile.save()
                return Response({
                    'message': 'Student linked to existing profile successfully',
                    'username': user.username,
                    'profile': InstituteStudentProfileSerializer(existing_profile).data
                }, status=status.HTTP_200_OK)

            profile = InstituteStudentProfile.objects.create(
                user=user,
                institute=institute,
                student_name=student_name,
                parent_mobile=parent_mobile,
                monthly_fee=monthly_fee,
                due_day=due_day
            )
            
            return Response({
                'message': 'Student linked successfully',
                'username': user.username,
                'profile': InstituteStudentProfileSerializer(profile).data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f"ERROR in link_by_username: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({'error': f'Server Error: {str(e)}'}, status=500)

    @action(detail=True, methods=['post'])
    def send_fee_reminder(self, request, pk=None):
        student = self.get_object()
        now = timezone.now()
        
        fee_record = FeePayment.objects.filter(student_profile=student, month=now.month, year=now.year).first()
        pending_amt = fee_record.pending_amount if fee_record else student.monthly_fee
        
        InstituteNotification.objects.create(
            institute=student.institute,
            recipient=student.user,
            notification_type='FEE_REMINDER',
            message=f"Dear Parent, a tuition fee balance of ₹{pending_amt} for {student.student_name} is pending for {now.strftime('%B %Y')}."
        )
        return Response({'message': f'Reminder for ₹{pending_amt} sent.'})

    @action(detail=True, methods=['post'])
    def send_notice(self, request, pk=None):
        """Send a custom notice to a specific student/parent"""
        student = self.get_object()
        message = request.data.get('message')
        if not message:
            return Response({'error': 'Message is required'}, status=400)
            
        InstituteNotification.objects.create(
            institute=student.institute,
            recipient=student.user,
            notification_type='DUE_ALERT', # Generic notice type
            message=message
        )
        return Response({'message': 'Notice sent successfully'})

class FeePaymentViewSet(viewsets.ModelViewSet):
    serializer_class = FeePaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.persona == 'INSTITUTE_OWNER':
            return FeePayment.objects.filter(student_profile__institute__owner=user)
        elif user.persona in ['STUDENT', 'STUDENT_ACADEMIC']:
            return FeePayment.objects.filter(student_profile__user=user)
        return FeePayment.objects.none()

    @action(detail=False, methods=['post'])
    def mark_paid(self, request):
        student_profile_id = request.data.get('student_profile')
        month = request.data.get('month')
        year = request.data.get('year')
        amount_paid_now = Decimal(str(request.data.get('amount', 0)))

        profile = get_object_or_404(InstituteStudentProfile, id=student_profile_id, institute__owner=request.user)
        
        payment, created = FeePayment.objects.get_or_create(
            student_profile=profile,
            month=month,
            year=year,
            defaults={'total_amount': profile.monthly_fee, 'paid_amount': 0, 'status': 'PENDING'}
        )
        
        payment.paid_amount += amount_paid_now
        payment.payment_date = timezone.now()
        
        if payment.paid_amount >= payment.total_amount:
            payment.status = 'PAID'
        else:
            payment.status = 'PARTIAL'
            
        payment.save()
        return Response(FeePaymentSerializer(payment).data)

    @action(detail=True, methods=['post'])
    def pay_now(self, request, pk=None):
        payment = self.get_object()
        user = request.user
        
        # 1. Permission Check: Allow student or their linked parent
        is_parent = False
        if user.persona == 'PARENT':
            from parent_module.models import ParentStudentLink
            is_parent = ParentStudentLink.objects.filter(parent=user, student=payment.student_profile.user).exists()

        if payment.student_profile.user != user and not is_parent:
            return Response({'error': _('Unauthorized to pay this fee')}, status=403)
            
        if payment.status == 'PAID':
            return Response({'error': _('Fee is already paid')}, status=400)

        # 2. Financial Transaction: Deduct from Wallet
        from student_module.models import Wallet
        from django.db import transaction
        
        try:
            with transaction.atomic():
                wallet = Wallet.objects.select_for_update().get(user=user)
                if wallet.balance < payment.total_amount:
                    return Response({'error': _('Insufficient wallet balance to pay this fee (₹{0})').format(payment.total_amount)}, status=400)
                
                # Deduct funds
                wallet.withdraw_main(payment.total_amount, description=_('Tuition Fee Payment: {0}').format(payment.student_profile.student_name))
                
                # Update Payment Record
                payment.status = 'PAID'
                payment.paid_amount = payment.total_amount
                payment.payment_date = timezone.now()
                payment.remarks = _("Paid via {0} Portal").format(_('Parent') if is_parent else _('Student'))
                payment.save()
                
                # Notify Owner
                InstituteNotification.objects.create(
                    institute=payment.student_profile.institute,
                    recipient=payment.student_profile.institute.owner,
                    notification_type='FEE_REMINDER',
                    message=_("Fee of ₹{0} received from {1}.").format(payment.total_amount, payment.student_profile.student_name)
                )
        except Exception as e:
            return Response({'error': str(e)}, status=400)
        
        return Response({'message': _('Payment successful'), 'status': 'PAID'})

class SalaryPaymentViewSet(viewsets.ModelViewSet):
    serializer_class = SalaryPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.persona == 'INSTITUTE_OWNER':
            return SalaryPayment.objects.filter(teacher_profile__institute__owner=user)
        elif user.persona == 'INSTITUTE_TEACHER':
            return SalaryPayment.objects.filter(teacher_profile__user=user)
        return SalaryPayment.objects.none()

    @action(detail=False, methods=['post'])
    def mark_paid(self, request):
        teacher_profile_id = request.data.get('teacher_profile')
        month = request.data.get('month')
        year = request.data.get('year')
        amount = request.data.get('amount')

        profile = get_object_or_404(TeacherProfile, id=teacher_profile_id, institute__owner=request.user)
        
        payment, created = SalaryPayment.objects.update_or_create(
            teacher_profile=profile,
            month=month,
            year=year,
            defaults={'amount': amount, 'status': 'PAID', 'payment_date': timezone.now()}
        )
        
        InstituteNotification.objects.create(
            institute=profile.institute,
            recipient=profile.user,
            notification_type='SALARY_CREDIT',
            message=f"₹{amount} salary credited for {month}/{year}."
        )
        
        return Response(SalaryPaymentSerializer(payment).data)

class InstituteDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        now = timezone.now()
        
        student_id = request.query_params.get('student_id')
        target_student_user = None
        
        if student_id:
            if user.persona != 'PARENT':
                return Response({'error': 'Only parents can request child data'}, status=403)
            try:
                from student_module.models import ParentStudentLink
                link = ParentStudentLink.objects.filter(parent=user, student_id=student_id).first()
                if not link:
                    return Response({'error': 'Unauthorized'}, status=403)
                target_student_user = link.student
            except Exception as e:
                return Response({'error': str(e)}, status=500)

        # OWNER ROLE
        if user.persona == 'INSTITUTE_OWNER' and not target_student_user:
            total_students = InstituteStudentProfile.objects.filter(institute__owner=user, is_active=True).count()
            total_teachers = TeacherProfile.objects.filter(institute__owner=user, is_active=True).count()
            
            revenue_data = FeePayment.objects.filter(student_profile__institute__owner=user, month=now.month, year=now.year).aggregate(total=Sum('paid_amount'))
            monthly_revenue = revenue_data['total'] or 0
            
            payout_data = SalaryPayment.objects.filter(teacher_profile__institute__owner=user, month=now.month, year=now.year, status='PAID').aggregate(total=Sum('amount'))
            monthly_payout = payout_data['total'] or 0
            
            dues_data = FeePayment.objects.filter(student_profile__institute__owner=user, month=now.month, year=now.year).aggregate(total_due=Sum('total_amount'), total_paid=Sum('paid_amount'))
            pending_dues_total = (dues_data['total_due'] or 0) - (dues_data['total_paid'] or 0)

            today = timezone.localdate()
            attendance_stats = StudentAttendance.objects.filter(student_profile__institute__owner=user, date=today).aggregate(present=Count('id', filter=Q(status='PRESENT')), absent=Count('id', filter=Q(status='ABSENT')))

            teacher_profiles = TeacherProfile.objects.filter(institute__owner=user, is_active=True)
            teacher_payout_status = {}
            for tp in teacher_profiles:
                is_paid = SalaryPayment.objects.filter(teacher_profile=tp, month=now.month, year=now.year, status='PAID').exists()
                teacher_payout_status[tp.id] = 'PAID' if is_paid else 'PENDING'

            paid_fees = FeePayment.objects.filter(student_profile__institute__owner=user, status__in=['PAID', 'PARTIAL']).order_by('-payment_date')[:20]
            paid_salaries = SalaryPayment.objects.filter(teacher_profile__institute__owner=user, status='PAID').order_by('-payment_date')[:20]
            
            student_profiles = InstituteStudentProfile.objects.filter(institute__owner=user, is_active=True)
            student_fee_status = {}
            for sp in student_profiles:
                fee_record = FeePayment.objects.filter(student_profile=sp, month=now.month, year=now.year).first()
                if fee_record:
                    student_fee_status[sp.id] = {'total': float(fee_record.total_amount), 'paid': float(fee_record.paid_amount), 'pending': float(fee_record.pending_amount), 'status': fee_record.status}
                else:
                    student_fee_status[sp.id] = {'total': float(sp.monthly_fee), 'paid': 0.0, 'pending': float(sp.monthly_fee), 'status': 'PENDING'}

            return Response({
                'role': 'OWNER',
                'owner_details': {'username': user.username, 'uid': user.uid},
                'institutes': InstituteSerializer(Institute.objects.filter(owner=user), many=True).data,
                'teacher_payout_status': teacher_payout_status,
                'student_fee_status': student_fee_status,
                'recent_paid_fees': FeePaymentSerializer(paid_fees, many=True).data,
                'recent_paid_salaries': SalaryPaymentSerializer(paid_salaries, many=True).data,
                'stats': {
                    'total_students': total_students,
                    'total_teachers': total_teachers,
                    'monthly_revenue': float(monthly_revenue),
                    'monthly_payout': float(monthly_payout),
                    'pending_fees': float(pending_dues_total),
                    'net_balance': float(monthly_revenue - monthly_payout),
                    'today_attendance': attendance_stats
                }
            })

        # TEACHER ROLE
        elif user.persona == 'INSTITUTE_TEACHER' and not target_student_user:
            profile = TeacherProfile.objects.filter(user=user).first()
            if not profile:
                return Response({'role': 'TEACHER', 'message': 'No teacher profile found.'})
                
            recent_salaries = SalaryPayment.objects.filter(teacher_profile=profile).order_by('-year', '-month')[:5]
            today = timezone.localdate()
            attendance_today = StudentAttendance.objects.filter(student_profile__assigned_teachers__user=user, date=today).count()
            notifications = InstituteNotification.objects.filter(recipient=user).order_by('-sent_at')[:10]

            assigned_students = InstituteStudentProfile.objects.filter(assigned_teachers__user=user, is_active=True)
            student_fee_status = {}
            for sp in assigned_students:
                fee_record = FeePayment.objects.filter(student_profile=sp, month=now.month, year=now.year).first()
                if fee_record:
                    student_fee_status[sp.id] = {'total': float(fee_record.total_amount), 'paid': float(fee_record.paid_amount), 'pending': float(fee_record.pending_amount), 'status': fee_record.status}
                else:
                    student_fee_status[sp.id] = {'total': float(sp.monthly_fee), 'paid': 0.0, 'pending': float(sp.monthly_fee), 'status': 'PENDING'}
            
            return Response({
                'role': 'TEACHER',
                'profile': TeacherProfileSerializer(profile).data,
                'institutes': [InstituteSerializer(profile.institute).data],
                'recent_salaries': SalaryPaymentSerializer(recent_salaries, many=True).data,
                'student_fee_status': student_fee_status,
                'notifications': InstituteNotificationSerializer(notifications, many=True).data,
                'stats': {'students_marked_today': attendance_today}
            })

        # STUDENT role OR PARENT requesting for a student
        if user.persona in ['STUDENT', 'STUDENT_ACADEMIC'] or target_student_user:
            effective_user = target_student_user if target_student_user else user
            profile = InstituteStudentProfile.objects.filter(user=effective_user).first()
            if not profile:
                return Response({'role': 'STUDENT', 'message': 'No institute profile linked.'})
            
            total_days = StudentAttendance.objects.filter(student_profile=profile).count()
            present_days = StudentAttendance.objects.filter(student_profile=profile, status='PRESENT').count()
            attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 100
            recent_attendance = StudentAttendance.objects.filter(student_profile=profile).order_by('-date')[:10]
            
            fee_status, created = FeePayment.objects.get_or_create(
                student_profile=profile, month=now.month, year=now.year,
                defaults={'total_amount': profile.monthly_fee, 'paid_amount': 0, 'status': 'PENDING'}
            )
            
            recent_fees = FeePayment.objects.filter(student_profile=profile).order_by('-year', '-month')
            notifications = InstituteNotification.objects.filter(recipient=effective_user).order_by('-sent_at')[:10]
            
            return Response({
                'role': 'STUDENT',
                'profile': InstituteStudentProfileSerializer(profile).data,
                'institutes': [InstituteSerializer(profile.institute).data],
                'institute_name': profile.institute.name,
                'current_fee_status': FeePaymentSerializer(fee_status).data,
                'recent_fees': FeePaymentSerializer(recent_fees, many=True).data,
                'notifications': InstituteNotificationSerializer(notifications, many=True).data,
                'attendance': {'percentage': round(attendance_percentage, 1), 'recent': StudentAttendanceSerializer(recent_attendance, many=True).data}
            })

        return Response({'error': 'Invalid persona'}, status=400)
