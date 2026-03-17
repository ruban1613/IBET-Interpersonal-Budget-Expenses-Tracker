from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from rest_framework.authtoken.views import obtain_auth_token
from .views import set_language, get_available_languages


# Non-translatable URLs (outside i18n_patterns)
urlpatterns = [
    path('admin/', admin.site.urls),
    # Language switching endpoints (these should be outside i18n_patterns)
    path('api/set-language/', set_language, name='set_language'),
    path('api/languages/', get_available_languages, name='get_available_languages'),
]

# Translatable URLs (inside i18n_patterns)
urlpatterns += i18n_patterns(
    # All API endpoints are grouped under the 'api/' namespace
    path('api/', include([
        path('', include('student_module.urls')),
        path('parent/', include('parent_module.urls')),
        path('individual/', include('individual_module.urls')),
        path('couple/', include('couple_module.urls_final')),
        path('retiree/', include('retiree_module.urls')),
        path('dailywage/', include('dailywage_module.urls')),
        # This path is for getting the authentication token for a user
        path('token-auth/', obtain_auth_token, name='api_token_auth'),
    ])),
    prefix_default_language=False,  # Don't add prefix for default language (English)
)
