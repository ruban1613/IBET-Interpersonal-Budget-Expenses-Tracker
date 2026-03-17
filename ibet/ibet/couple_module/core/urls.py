from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = i18n_patterns(
    path('admin/', admin.site.urls),
    # All API endpoints are grouped under the 'api/' namespace
    path('api/', include([
        path('', include('student_module.urls')),
        path('parent/', include('parent_module.urls')),
        path('individual/', include('individual_module.urls')),
        path('couple/', include('couple_module.urls')),
        path('retiree/', include('retiree_module.urls', namespace='retiree')),
        path('dailywage/', include('dailywage_module.urls')),
        # This path is for getting the authentication token for a user
        path('token-auth/', obtain_auth_token, name='api_token_auth'),
    ])),
    prefix_default_language=False
)
