# Script to add request-unlock action to SpendingLockViewSet

with open('student_module/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the SpendingLockViewSet class and add request-unlock action
old_class = """class SpendingLockViewSet(viewsets.ModelViewSet):
    \"\"\"
    API endpoint for managing spending locks.
    \"\"\"
    serializer_class = SpendingLockSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SpendingLock.objects.filter(student=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def generate_unlock_otp(self, request, pk=None):"""

new_class = """class SpendingLockViewSet(viewsets.ModelViewSet):
    \"\"\"
    API endpoint for managing spending locks.
    \"\"\"
    serializer_class = SpendingLockSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SpendingLock.objects.filter(student=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def request_unlock(self, request, pk=None):
        \"\"\"
        Student requests unlock from parent. This triggers the parent to generate OTP.
        \"\"\"
        lock = self.get_object()
        
        # Create notification for parent to generate unlock OTP
        from parent_module.models import ParentStudentLink
        try:
            link = ParentStudentLink.objects.filter(student=lock.student, is_active=True).first()
            if link:
                from .models import StudentNotification
                StudentNotification.objects.create(
                    student=link.parent,
                    notification_type='UNLOCK_REQUEST',
                    title=_('Unlock Request'),
                    message=_(f'{lock.student.username} is requesting to unlock their spending. Please generate an OTP from the Parent Dashboard.')
                )
        except Exception as e:
            pass
        
        return Response({'message': _('Unlock request sent to parent.')})

    @action(detail=True, methods=['post'])
    def generate_unlock_otp(self, request, pk=None):"""

content = content.replace(old_class, new_class)

with open('student_module/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done! request-unlock action added to SpendingLockViewSet')
