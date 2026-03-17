from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import RedirectView
from rest_framework.authtoken.views import obtain_auth_token
from .views import api_root, api_status, set_language, get_available_languages
import os


# Frontend HTML files will be served from the frontend dist directory (React build)
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'dist')


# Simple view to serve React app (SPA)
def serve_frontend(request, page):
    from django.http import HttpResponse
    import os
    
    # Serve the React index.html for all frontend routes (SPA)
    filepath = os.path.join(FRONTEND_DIR, 'index.html')
    
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/html')
    else:
        return HttpResponse(f'<h1>Page not found: index.html</h1><p>React build not found at {FRONTEND_DIR}</p>', status=404)


# Non-translatable URLs (outside i18n_patterns)
urlpatterns = [
    path('admin/', admin.site.urls),
    # Language switching endpoints (these should be outside i18n_patterns)
    path('api/set-language/', set_language, name='set_language'),
    path('api/languages/', get_available_languages, name='get_available_languages'),
    path('api/status/', api_status, name='api_status'),
    # Auth endpoints (outside i18n_patterns for language-agnostic access)
    path('api/auth/', include('core.urls_auth')),
    # Frontend routes
    path('', serve_frontend, {'page': 'login'}, name='login_page'),
    path('login/', serve_frontend, {'page': 'login'}, name='login'),
    path('register/', serve_frontend, {'page': 'register'}, name='register'),
    path('register.html', serve_frontend, {'page': 'register'}, name='register_html'),
    path('login.html', serve_frontend, {'page': 'login'}, name='login_html'),
    path('select-module.html', serve_frontend, {'page': 'select-module'}, name='select-module_html'),
    path('dashboard/couple.html', serve_frontend, {'page': 'dashboard/couple'}, name='dashboard_couple_html'),
    path('dashboard/student.html', serve_frontend, {'page': 'dashboard/student'}, name='dashboard_student_html'),
    path('dashboard-individual.html', serve_frontend, {'page': 'dashboard/individual'}, name='dashboard_individual_html_alt'),
    path('dashboard-parent.html', serve_frontend, {'page': 'dashboard/parent'}, name='dashboard_parent_html_alt'),
    path('dashboard-student.html', serve_frontend, {'page': 'dashboard/student'}, name='dashboard_student_html_alt'),
    path('select-module/', serve_frontend, {'page': 'select-module'}, name='select-module'),
    path('dashboard/couple/', serve_frontend, {'page': 'dashboard/couple'}, name='dashboard_couple'),
    path('dashboard/individual/', serve_frontend, {'page': 'dashboard/individual'}, name='dashboard_individual'),
    path('dashboard/parent/', serve_frontend, {'page': 'dashboard/parent'}, name='dashboard_parent'),
    path('dashboard/student/', serve_frontend, {'page': 'dashboard/student'}, name='dashboard_student'),
    path('dashboard/institute/', serve_frontend, {'page': 'dashboard/institute'}, name='dashboard_institute'),

    # API Endpoints (moved outside i18n_patterns for consistency)
    path('api/student/', include('student_module.urls')),
    path('api/parent/', include('parent_module.urls')),
    path('api/individual/', include('individual_module.urls')),
    path('api/couple/', include('couple_module.urls')),
    path('api/institute/', include('institute_module.urls')),
    path('api/token-auth/', obtain_auth_token, name='api_token_auth'),
]

# Translatable URLs (inside i18n_patterns)
urlpatterns += i18n_patterns(
    # Root API endpoint
    path('', api_root, name='api_root'),
    prefix_default_language=False,  # Don't add prefix for default language (English)
)
