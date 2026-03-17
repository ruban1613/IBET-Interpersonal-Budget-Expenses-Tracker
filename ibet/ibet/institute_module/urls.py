from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InstituteViewSet, TeacherProfileViewSet, InstituteStudentProfileViewSet,
    FeePaymentViewSet, SalaryPaymentViewSet, InstituteDashboardView, StudentAttendanceViewSet, TeacherAttendanceViewSet
)

router = DefaultRouter()
router.register(r'institutes', InstituteViewSet, basename='institute')
router.register(r'teachers', TeacherProfileViewSet, basename='teacher-profile')
router.register(r'teacher-attendance', TeacherAttendanceViewSet, basename='teacher-attendance')
router.register(r'student-profiles', InstituteStudentProfileViewSet, basename='institute-student-profile')
router.register(r'fees', FeePaymentViewSet, basename='fee-payment')
router.register(r'salaries', SalaryPaymentViewSet, basename='salary-payment')
router.register(r'attendance', StudentAttendanceViewSet, basename='student-attendance')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', InstituteDashboardView.as_view(), name='institute-dashboard'),
]
