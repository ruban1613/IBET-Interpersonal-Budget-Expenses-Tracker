from rest_framework import serializers
from .models import Institute, TeacherProfile, InstituteStudentProfile, FeePayment, SalaryPayment, InstituteNotification, StudentAttendance, TeacherAttendance
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class InstituteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institute
        fields = ['id', 'owner', 'name', 'address', 'contact_number', 'created_at', 'updated_at']
        read_only_fields = ['owner']

class InstituteStudentProfileSerializer(serializers.ModelSerializer):
    user_details = UserSimpleSerializer(source='user', read_only=True)
    
    class Meta:
        model = InstituteStudentProfile
        fields = '__all__'

class TeacherProfileSerializer(serializers.ModelSerializer):
    user_details = UserSimpleSerializer(source='user', read_only=True)
    assigned_student_details = InstituteStudentProfileSerializer(source='assigned_students', many=True, read_only=True)
    daily_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = TeacherProfile
        fields = [
            'id', 'user', 'institute', 'base_monthly_salary', 'working_days_per_month', 
            'extra_session_rate', 'is_active', 'joining_date', 'user_details', 
            'assigned_students', 'assigned_student_details', 'daily_rate'
        ]
        read_only_fields = ['joining_date', 'user', 'institute']

class TeacherAttendanceSerializer(serializers.ModelSerializer):
    teacher_name = serializers.ReadOnlyField(source='teacher.user.username')
    
    class Meta:
        model = TeacherAttendance
        fields = '__all__'

class FeePaymentSerializer(serializers.ModelSerializer):
    student_name = serializers.ReadOnlyField(source='student_profile.student_name')
    pending_amount = serializers.ReadOnlyField()
    
    class Meta:
        model = FeePayment
        fields = '__all__'

class SalaryPaymentSerializer(serializers.ModelSerializer):
    teacher_name = serializers.ReadOnlyField(source='teacher_profile.user.username')
    
    class Meta:
        model = SalaryPayment
        fields = '__all__'

class InstituteNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstituteNotification
        fields = '__all__'

class StudentAttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.ReadOnlyField(source='student_profile.student_name')
    
    class Meta:
        model = StudentAttendance
        fields = '__all__'
        read_only_fields = ['marked_by', 'created_at']
