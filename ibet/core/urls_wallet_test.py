"""
Main URL configuration for the IBET project - Wallet Testing Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('rest_framework.urls')),

    # Module-specific URLs
    path('api/individual/', include('individual_module.urls_wallet_test')),
    path('api/couple/', include('couple_module.urls_wallet_test')),
    path('api/retiree/', include('retiree_module.urls_wallet_test')),
    path('api/dailywage/', include('dailywage_module.urls_wallet_test')),
    path('api/student/', include('student_module.urls_wallet_test')),
    path('api/parent/', include('parent_module.urls_wallet_test')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
