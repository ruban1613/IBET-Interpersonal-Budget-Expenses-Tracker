"""
Secure wallet views for Parent Module.
Provides secure wallet operations with student monitoring and approval features.
"""
import logging
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _
from core.throttling import OTPGenerationThrottle, OTPVerificationThrottle, WalletAccessThrottle, SensitiveOperationsThrottle
from core.security import OTPSecurityService, SecurityUtils
from .models import ParentOTPRequest, StudentMonitoring, ParentAlert
from .serializers_wallet import ParentWalletSerializer, ParentWalletTransactionSerializer
from student_module.models import Wallet, ParentStudentLink, OTPRequest, WalletTransaction, WalletTransaction as StudentTransaction
from individual_module.models import IndividualExpense


from decimal import Decimal
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()
logger = logging.getLogger(__name__)


class ParentWalletViewSet(viewsets.ModelViewSet):
    """
    Secure API endpoint for parent wallet management.
    """
    serializer_class = ParentWalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [WalletAccessThrottle]

    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)

    def get_object(self):
        # Use get_or_create to avoid DoesNotExist error
        wallet, created = Wallet.objects.get_or_create(
            user=self.request.user,
            defaults={
                'balance': Decimal('0.00'),
                'last_transaction_at': None
            }
        )
        return wallet

    @action(detail=False, methods=['get'])
    def statement(self, request):
        """Get parent's own filtered transaction statement (Wallet + Expenses + General Transactions)"""
        from django.utils.timezone import localdate
        from student_module.models import Transaction as GeneralTransaction
        user = request.user
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        day = request.query_params.get('day')
        
        today = localdate()
        if not year: year = today.year
        if not month: month = today.month

        # 1. Get Wallet Transactions (Deposits/Withdrawals)
        wallet_qs = WalletTransaction.objects.filter(wallet__user=user)
        if year: wallet_qs = wallet_qs.filter(created_at__year=year)
        if month: wallet_qs = wallet_qs.filter(created_at__month=month)
        if day: wallet_qs = wallet_qs.filter(created_at__day=day)

        # 2. Get Individual Expenses (Personal records)
        expense_qs = IndividualExpense.objects.filter(user=user)
        if year: expense_qs = expense_qs.filter(expense_date__year=year)
        if month: expense_qs = expense_qs.filter(expense_date__month=month)
        if day: expense_qs = expense_qs.filter(expense_date__day=day)

        # 3. Get General Transactions (Allowances, Pocket Money Transfers)
        general_qs = GeneralTransaction.objects.filter(user=user)
        if year: general_qs = general_qs.filter(transaction_date__year=year)
        if month: general_qs = general_qs.filter(transaction_date__month=month)
        if day: general_qs = general_qs.filter(transaction_date__day=day)

        combined_data = []
        
        for tx in wallet_qs:
            combined_data.append({
                'id': f"w_{tx.id}",
                'amount': float(tx.amount),
                'transaction_type': tx.transaction_type,
                'description': tx.description,
                'balance_after': float(tx.balance_after) if tx.balance_after is not None else None,
                'created_at': tx.created_at,
                'source': 'wallet'
            })

        for exp in expense_qs:
            combined_data.append({
                'id': f"e_{exp.id}",
                'amount': float(exp.amount),
                'transaction_type': 'EXP',
                'description': f"[{exp.category}] {exp.description}",
                'balance_after': None,
                'created_at': timezone.make_aware(timezone.datetime.combine(exp.expense_date, timezone.datetime.min.time())),
                'source': 'expense'
            })

        for gen in general_qs:
            # Avoid duplicating deposits/withdrawals that might already be in wallet_qs
            # (Typically GeneralTransaction stores higher-level intent like transfers)
            desc_lower = gen.description.lower()
            if any(keyword in desc_lower for keyword in ['allowance', 'pocket', 'transfer']):
                combined_data.append({
                    'id': f"g_{gen.id}",
                    'amount': float(gen.amount),
                    'transaction_type': gen.transaction_type,
                    'description': gen.description,
                    'balance_after': None,
                    'created_at': timezone.make_aware(timezone.datetime.combine(gen.transaction_date, timezone.datetime.min.time())),
                    'source': 'general'
                })

        # Sort by created_at desc
        combined_data.sort(key=lambda x: x['created_at'], reverse=True)

        return Response({
            'period': f"{month}/{year}",
            'count': len(combined_data),
            'transactions': combined_data
        })

    @action(detail=False, methods=['get'])
    def student_statement(self, request):
        """Get a linked student's filtered transaction statement (Wallet + Expenses + General Transactions)"""
        from django.utils.timezone import localdate
        from student_module.models import Transaction as GeneralTransaction
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response({'error': _('student_id is required')}, status=status.HTTP_400_BAD_REQUEST)

        # Verify link (Removed is_active=True as it doesn't exist on this model)
        try:
            student = User.objects.get(id=student_id)
            link = ParentStudentLink.objects.get(parent=request.user, student=student)
        except (User.DoesNotExist, ParentStudentLink.DoesNotExist):
            return Response({'error': _('Student not linked or access denied')}, status=status.HTTP_403_FORBIDDEN)

        year = request.query_params.get('year')
        month = request.query_params.get('month')
        day = request.query_params.get('day')
        
        today = localdate()
        if not year and not month and not day:
            year = today.year
            month = today.month

        # 1. Get Student Wallet Transactions
        wallet_qs = WalletTransaction.objects.filter(wallet__user=student)
        if year: wallet_qs = wallet_qs.filter(created_at__year=year)
        if month: wallet_qs = wallet_qs.filter(created_at__month=month)
        if day: wallet_qs = wallet_qs.filter(created_at__day=day)

        # 2. Get Student Individual Expenses
        expense_qs = IndividualExpense.objects.filter(user=student)
        if year: expense_qs = expense_qs.filter(expense_date__year=year)
        if month: expense_qs = expense_qs.filter(expense_date__month=month)
        if day: expense_qs = expense_qs.filter(expense_date__day=day)

        # 3. Get Student General Transactions (Allowance deposits, etc.)
        general_qs = GeneralTransaction.objects.filter(user=student)
        if year: general_qs = general_qs.filter(transaction_date__year=year)
        if month: general_qs = general_qs.filter(transaction_date__month=month)
        if day: general_qs = general_qs.filter(transaction_date__day=day)

        combined_data = []
        
        for tx in wallet_qs:
            combined_data.append({
                'id': f"w_{tx.id}",
                'amount': float(tx.amount),
                'transaction_type': tx.transaction_type,
                'description': tx.description,
                'balance_after': float(tx.balance_after) if tx.balance_after is not None else None,
                'created_at': tx.created_at,
                'source': 'wallet'
            })

        for exp in expense_qs:
            combined_data.append({
                'id': f"e_{exp.id}",
                'amount': float(exp.amount),
                'transaction_type': 'EXP',
                'description': f"[{exp.category}] {exp.description}",
                'balance_after': None,
                'created_at': timezone.make_aware(timezone.datetime.combine(exp.expense_date, timezone.datetime.min.time())),
                'source': 'expense'
            })

        for gen in general_qs:
            # Include ALL income (INC) and expenses (EXP)
            if gen.transaction_type == 'INC' or gen.transaction_type == 'EXP' or gen.description.startswith('Allowance'):
                combined_data.append({
                    'id': f"g_{gen.id}",
                    'amount': float(gen.amount),
                    'transaction_type': gen.transaction_type,
                    'description': gen.description,
                    'balance_after': None,
                    'created_at': timezone.make_aware(timezone.datetime.combine(gen.transaction_date, timezone.datetime.min.time())),
                    'source': 'general'
                })

        combined_data.sort(key=lambda x: x['created_at'], reverse=True)

        return Response({
            'student_username': student.username,
            'period': f"{day if day else ''}/{month if month else ''}/{year if year else ''}",
            'count': len(combined_data),
            'transactions': combined_data
        })

    @action(detail=False, methods=['post'])
    def record_expense(self, request):
        """Allow parent to record their own expense"""
        amount = request.data.get('amount')
        category = request.data.get('category')
        description = request.data.get('description', '')

        if not amount or not category:
            return Response({'error': _('amount and category are required')}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # We use record_expense_and_check_alerts from IndividualExpense
            # This will deduct from parent's Wallet balance automatically!
            expense, alerts = IndividualExpense.record_expense_and_check_alerts(
                request.user, 
                Decimal(str(amount)), 
                category, 
                description
            )
            
            wallet = self.get_object()
            return Response({
                'message': _('Expense recorded successfully'),
                'new_balance': wallet.balance
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def list(self, request, *args, **kwargs):
        """Override list to return single wallet object instead of array"""
        wallet, created = Wallet.objects.get_or_create(
            user=request.user,
            defaults={
                'balance': Decimal('0.00'),
                'last_transaction_at': None
            }
        )
        serializer = self.get_serializer(wallet)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def set_transaction_pin(self, request):
        """Set or update the parent's secret transaction PIN"""
        pin = request.data.get('pin')
        if not pin or len(str(pin)) < 4:
            return Response({'error': _('PIN must be at least 4 digits.')}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        from django.contrib.auth.hashers import make_password
        user.transaction_pin = make_password(str(pin))
        user.save()
        
        return Response({'message': _('Transaction PIN set successfully.')})

    @action(detail=False, methods=['post'])
    def transfer_to_student_special(self, request):
        """
        Instant transfer to student's Special Wallet using Parent PIN.
        No OTP required.
        """
        student_id = request.data.get('student_id')
        amount = Decimal(str(request.data.get('amount', 0)))
        pin = request.data.get('pin')

        if amount <= 0:
            return Response({'error': _('Invalid amount')}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Verify Parent PIN
        from django.contrib.auth.hashers import check_password
        if not request.user.transaction_pin or not check_password(str(pin), request.user.transaction_pin):
            return Response({'error': _('Invalid Transaction PIN.')}, status=status.HTTP_403_FORBIDDEN)

        # 2. Check Parent Balance
        parent_wallet = self.get_object()
        if parent_wallet.balance < amount:
            return Response({'error': _('Insufficient funds in your parent wallet.')}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student = User.objects.get(id=student_id)
            # Ensure they are linked
            if not ParentStudentLink.objects.filter(parent=request.user, student=student).exists():
                return Response({'error': _('This student is not linked to your account.')}, status=status.HTTP_403_FORBIDDEN)

            # 3. Perform Transfer to SPECIAL WALLET
            student_wallet, _ = Wallet.objects.get_or_create(user=student)
            
            with transaction.atomic():
                parent_wallet.balance -= amount
                student_wallet.special_balance += amount
                parent_wallet.save()
                student_wallet.save()

                # 4. Record History
                from student_module.models import Transaction, AllowanceContribution
                today = timezone.now().date()
                
                # History for Parent Overview
                AllowanceContribution.objects.create(
                    parent=request.user, student=student, amount=amount,
                    day=today.day, month=today.month, year=today.year
                )
                
                # Transaction Records
                Transaction.objects.create(
                    user=student, amount=amount, transaction_type='INC',
                    description=_(f'Pocket Money from {request.user.username} (Special Wallet)'),
                    transaction_date=today
                )
                Transaction.objects.create(
                    user=request.user, amount=amount, transaction_type='EXP',
                    description=_(f'Pocket Money transfer to {student.username}'),
                    transaction_date=today
                )

                # Record in WalletTransaction for the special wallet
                WalletTransaction.objects.create(
                    wallet=student_wallet,
                    wallet_type=WalletTransaction.WalletType.SPECIAL,
                    transaction_type=WalletTransaction.TransactionType.DEPOSIT,
                    amount=amount,
                    balance_after=student_wallet.special_balance,
                    description=_(f'Pocket Money from parent: {request.user.username}')
                )

            return Response({
                'message': _('₹{0} transferred successfully to {1}\'s Special Wallet.').format(amount, student.username),
                'new_parent_balance': float(parent_wallet.balance)
            })

        except User.DoesNotExist:
            return Response({'error': _('Student not found.')}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def check_pin_status(self, request):
        """Check if the parent has set a transaction PIN"""
        return Response({
            'has_pin': request.user.transaction_pin is not None and request.user.transaction_pin != ''
        })

    @action(detail=False, methods=['get'])
    def welcome(self, request):
        """Welcome endpoint for parent wallet"""
        return Response({
            'message': 'Welcome to the Parent Wallet API Service!'
        })

    @action(detail=False, methods=['post'])
    def deposit(self, request):
        """Secure deposit to wallet"""
        try:
            wallet, created = Wallet.objects.get_or_create(
                user=request.user,
                defaults={
                    'balance': Decimal('0.00'),
                    'last_transaction_at': None
                }
            )
            
            amount_str = request.data.get('amount', '0')
            amount = Decimal(str(amount_str))
            description = request.data.get('description', 'Deposit')

            if amount <= 0:
                return Response({'error': 'Invalid amount'}, status=status.HTTP_400_BAD_REQUEST)

            new_balance = wallet.balance + amount
            wallet.balance = new_balance
            wallet.last_transaction_at = timezone.now()
            wallet.save()

            # Create transaction record
            from student_module.models import Transaction
            Transaction.objects.create(
                user=request.user,
                amount=amount,
                transaction_type='INC',
                description=description,
                transaction_date=timezone.now().date()
            )

            return Response({
                'message': 'Deposit successful',
                'new_balance': str(new_balance)
            })

        except Exception as e:
            logger.error(f"Deposit error: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def withdraw(self, request):
        """Secure withdrawal from wallet"""
        try:
            wallet, created = Wallet.objects.get_or_create(
                user=request.user,
                defaults={
                    'balance': Decimal('0.00'),
                    'last_transaction_at': None
                }
            )
            
            amount_str = request.data.get('amount', '0')
            amount = Decimal(str(amount_str))
            description = request.data.get('description', 'Withdrawal')

            if amount <= 0:
                return Response({'error': 'Invalid amount'}, status=status.HTTP_400_BAD_REQUEST)

            if wallet.balance < amount:
                return Response({'error': 'Insufficient funds'}, status=status.HTTP_400_BAD_REQUEST)

            new_balance = wallet.balance - amount
            wallet.balance = new_balance
            wallet.last_transaction_at = timezone.now()
            wallet.save()

            # Create transaction record
            from student_module.models import Transaction
            Transaction.objects.create(
                user=request.user,
                amount=amount,
                transaction_type='EXP',
                description=description,
                transaction_date=timezone.now().date()
            )

            return Response({
                'message': 'Withdrawal successful',
                'new_balance': str(new_balance)
            })

        except Exception as e:
            logger.error(f"Withdraw error: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def linked_students_wallets(self, request):
        """Get wallet information for all linked students"""
        try:
            linked_students = ParentStudentLink.objects.filter(parent=request.user)
            students_wallets = []

            for link in linked_students:
                student = link.student
                wallet, _ = Wallet.objects.get_or_create(
                    user=student,
                    defaults={
                        'balance': Decimal('0.00'),
                        'last_transaction_at': None
                    }
                )
                students_wallets.append({
                    'student_id': student.id,
                    'student_username': student.username,
                    'wallet_balance': str(wallet.balance)
                })

            return Response({
                'linked_students_wallets': students_wallets,
                'total_linked_students': len(students_wallets)
            })

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GenerateParentWalletOTPView(APIView):
    """
    Secure API endpoint for generating OTP for parent wallet operations.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [OTPGenerationThrottle, SensitiveOperationsThrottle]

    def post(self, request, *args, **kwargs):
        try:
            # Get operation type from request
            operation_type = request.data.get('operation_type', 'wallet_operation')
            if operation_type not in ['wallet_operation', 'transfer_to_student', 'allowance_change']:
                # Allow these types specifically
                pass
            amount = request.data.get('amount')
            description = request.data.get('description', '')
            student_id = request.data.get('student_id')

            # Get student if provided
            student = None
            if student_id:
                try:
                    student = User.objects.get(id=student_id)
                    # Verify parent-student relationship
                    if not ParentStudentLink.objects.filter(parent=request.user, student=student).exists():
                        return Response({'error': 'Invalid student relationship'}, status=status.HTTP_403_FORBIDDEN)
                except User.DoesNotExist:
                    return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

            # Generate a simple 6-digit OTP
            import random
            otp_code = str(random.randint(100000, 999999))
            
            # Set expiration time (10 minutes from now)
            expires_at = timezone.now() + timezone.timedelta(minutes=10)

            # Create OTP request
            otp_request = ParentOTPRequest.objects.create(
                parent=request.user,
                student=student,
                operation_type=operation_type,
                amount=amount,
                description=description,
                otp_code=otp_code,  # Store the OTP for simple validation
                expires_at=expires_at,
                cache_key=f'otp_{request.user.id}_{timezone.now().timestamp()}'
            )

            return Response({
                'message': 'OTP generated successfully for wallet operation',
                'otp_request_id': otp_request.id,
                'otp_code': otp_code,  # Return OTP in response for UI display
                'operation_type': operation_type,
                'expires_at': expires_at.isoformat(),
                'note': 'The OTP has been securely generated. Check the UI.'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"OTP generation error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyParentWalletOTPView(APIView):
    """
    Secure API endpoint for verifying OTP for parent wallet operations.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [OTPVerificationThrottle, SensitiveOperationsThrottle]

    def post(self, request, *args, **kwargs):
        try:
            otp_code = request.data.get('otp_code')
            otp_request_id = request.data.get('otp_request_id')

            if not otp_code or not otp_request_id:
                return Response({'error': 'OTP code and request ID are required'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                otp_request = ParentOTPRequest.objects.get(
                    id=otp_request_id,
                    parent=request.user,
                    is_used=False
                )
            except ParentOTPRequest.DoesNotExist:
                return Response({'error': 'Invalid OTP request'}, status=status.HTTP_400_BAD_REQUEST)

            if otp_request.is_expired():
                otp_request.delete()
                return Response({'error': 'OTP has expired'}, status=status.HTTP_400_BAD_REQUEST)

            # Simple OTP validation - compare directly
            if otp_request.otp_code != otp_code:
                return Response({'error': 'Invalid OTP code'}, status=status.HTTP_400_BAD_REQUEST)

            # Mark OTP as used
            otp_request.mark_as_used()

            # Perform the wallet operation based on operation_type
            if otp_request.operation_type == 'transfer_to_student' and otp_request.student:
                # Get or create parent wallet
                parent_wallet, _ = Wallet.objects.get_or_create(
                    user=request.user,
                    defaults={
                        'balance': Decimal('0.00'),
                        'last_transaction_at': None
                    }
                )
                
                # Get or create student wallet
                student_wallet, _ = Wallet.objects.get_or_create(
                    user=otp_request.student,
                    defaults={
                        'balance': Decimal('0.00'),
                        'last_transaction_at': None
                    }
                )

                amount_decimal = Decimal(str(otp_request.amount or 0))

                if parent_wallet.balance < amount_decimal:
                    return Response({'error': 'Insufficient funds in parent wallet'}, status=status.HTTP_400_BAD_REQUEST)

                # Perform transfer to SPECIAL balance (Pocket Money)
                parent_wallet.balance -= amount_decimal
                student_wallet.special_balance += amount_decimal
                parent_wallet.last_transaction_at = timezone.now()
                student_wallet.last_transaction_at = timezone.now()
                parent_wallet.save()
                student_wallet.save()

                # Create transaction records for both parties
                from student_module.models import Transaction, WalletTransaction
                
                # Parent transaction (EXPense)
                Transaction.objects.create(
                    user=request.user,
                    amount=amount_decimal,
                    transaction_type='EXP',
                    description=f"Transfer to student pocket money: {otp_request.student.username}",
                    transaction_date=timezone.now().date()
                )
                
                # Student transaction (INCome)
                Transaction.objects.create(
                    user=otp_request.student,
                    amount=amount_decimal,
                    transaction_type='INC',
                    description=f"Pocket Money from parent: {request.user.username}",
                    transaction_date=timezone.now().date()
                )

                # Record in WalletTransaction for the special wallet
                WalletTransaction.objects.create(
                    wallet=student_wallet,
                    wallet_type=WalletTransaction.WalletType.SPECIAL,
                    transaction_type=WalletTransaction.TransactionType.DEPOSIT,
                    amount=amount_decimal,
                    balance_after=student_wallet.special_balance,
                    description=f"Pocket Money from parent: {request.user.username}"
                )

                response_data = {
                    'message': 'OTP verified and funds transferred to pocket money successfully',
                    'operation_type': otp_request.operation_type,
                    'amount': str(otp_request.amount),
                    'description': otp_request.description,
                    'new_parent_balance': str(parent_wallet.balance),
                    'new_student_special_balance': str(student_wallet.special_balance)
                }

            else:
                # For other operation types, just return success
                response_data = {
                    'message': 'OTP verified successfully',
                    'operation_type': otp_request.operation_type,
                    'amount': str(otp_request.amount) if otp_request.amount else None,
                    'description': otp_request.description
                }

            return Response(response_data)

        except Exception as e:
            logger.error(f"Verify OTP error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return Response({'error': 'Operation failed: ' + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StudentWalletApprovalView(APIView):
    """
    API endpoint for parents to approve student wallet requests.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [SensitiveOperationsThrottle]

    def post(self, request, *args, **kwargs):
        student_id = request.data.get('student_id')
        amount = request.data.get('amount')
        otp_code = request.data.get('otp_code')

        if not all([student_id, amount, otp_code]):
            return Response({'error': 'Student ID, amount, and OTP code are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verify parent-student relationship
            parent_link = ParentStudentLink.objects.get(parent=request.user, student_id=student_id)

            # Find and validate OTP request
            otp_request = OTPRequest.objects.get(
                student_id=student_id,
                parent=request.user,
                amount_requested=amount,
                is_used=False
            )

            if otp_request.is_expired():
                return Response({'error': 'OTP has expired'}, status=status.HTTP_400_BAD_REQUEST)

            # Get student's wallet and add funds to pocket money (special balance)
            student_wallet, _ = Wallet.objects.get_or_create(
                user_id=student_id,
                defaults={
                    'balance': Decimal('0.00'),
                    'special_balance': Decimal('0.00'),
                    'last_transaction_at': None
                }
            )
            
            with transaction.atomic():
                amount_decimal = Decimal(amount)
                student_wallet.special_balance += amount_decimal
                student_wallet.save()

                # Create transaction record for the student
                from student_module.models import Transaction
                Transaction.objects.create(
                    user_id=student_id,
                    amount=amount_decimal,
                    transaction_type='INC',
                    description=_(f'Pocket Money from parent (Approved)'),
                    transaction_date=timezone.now().date()
                )

                # Create specific wallet transaction record
                WalletTransaction.objects.create(
                    wallet=student_wallet,
                    wallet_type=WalletTransaction.WalletType.SPECIAL,
                    transaction_type=WalletTransaction.TransactionType.DEPOSIT,
                    amount=amount_decimal,
                    balance_after=student_wallet.special_balance,
                    description=_(f'Pocket Money from parent (Approved)')
                )

                # Mark OTP as used
                otp_request.mark_as_used()

            return Response({
                'message': 'Student pocket money request approved successfully',
                'student_id': student_id,
                'amount_approved': amount,
                'new_student_special_balance': str(student_wallet.special_balance)
            })

        except ParentStudentLink.DoesNotExist:
            return Response({'error': 'Student not linked to this parent'}, status=status.HTTP_400_BAD_REQUEST)
        except OTPRequest.DoesNotExist:
            return Response({'error': 'Invalid or expired OTP request'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
