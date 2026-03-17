from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from django.conf import settings


@api_view(['GET'])
def api_root(request):
    """
    Root API endpoint that provides information about available endpoints.
    """
    return Response({
        'message': 'Welcome to IBET Wallet API',
        'version': '1.0.0',
        'endpoints': {
            'auth': '/api/auth/',
            'student': '/api/',
            'parent': '/api/parent/',
            'individual': '/api/individual/',
            'couple': '/api/couple/',
            'retiree': '/api/retiree/',
            'dailywage': '/api/dailywage/',
            'token_auth': '/api/token-auth/',
            'set_language': '/api/set-language/',
            'languages': '/api/languages/',
        },
        'documentation': 'API documentation available at /admin/ (admin access required)'
    })


@api_view(['GET'])
def api_status(request):
    """
    API status endpoint that provides detailed system status information.
    """
    from django.db import connection
    from django.conf import settings
    
    # Check database connectivity
    db_status = 'unknown'
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    # Get project stats
    stats = {}
    try:
        from student_module.models import Wallet as StudentWallet
        from couple_module.models import CoupleWallet
        from individual_module.models import IndividualWallet
        from retiree_module.models import RetireeWallet
        from dailywage_module.models import DailyWageWallet
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        stats = {
            'total_users': User.objects.count(),
            'student_wallets': StudentWallet.objects.count(),
            'couple_wallets': CoupleWallet.objects.count(),
            'individual_wallets': IndividualWallet.objects.count(),
            'retiree_wallets': RetireeWallet.objects.count(),
            'dailywage_wallets': DailyWageWallet.objects.count(),
        }
    except Exception as e:
        stats = {'error': str(e)}
    
    return Response({
        'status': 'online',
        'version': '1.0.0',
        'database': db_status,
        'debug_mode': settings.DEBUG,
        'available_languages': [lang[0] for lang in settings.LANGUAGES],
        'modules': {
            'student': 'Student wallet module - allowance tracking, parent connections',
            'parent': 'Parent module - child monitoring, allowance management',
            'individual': 'Individual wallet - personal expense tracking',
            'couple': 'Couple wallet - shared budgeting for couples',
            'retiree': 'Retiree wallet - retirement expense management',
            'dailywage': 'Daily wage module - wage-based income tracking',
        },
        'security_features': {
            'otp_verification': 'Email-based OTP for transactions',
            'rate_limiting': 'Throttling on sensitive operations',
            'permissions': 'Role-based access control',
        },
        'statistics': stats,
        'message': 'IBET Wallet API is running'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_language(request):
    """
    API endpoint to set the user's language preference.
    Accepts a POST request with 'language' field, e.g. {"language": "ta"}
    """
    language = request.data.get('language')

    if not language:
        return Response(
            {'error': _('Language code is required.')},
            status=status.HTTP_400_BAD_REQUEST
        )

    if language not in [lang[0] for lang in settings.LANGUAGES]:
        return Response(
            {'error': _('Unsupported language code.')},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Set the language for the current session
    translation.activate(language)
    request.session[settings.LANGUAGE_SESSION_KEY] = language

    # Optionally save language preference to user profile
    # if hasattr(request.user, 'language_preference'):
    #     request.user.language_preference = language
    #     request.user.save(update_fields=['language_preference'])

    return Response({
        'message': _('Language changed successfully.'),
        'language': language,
        'language_name': dict(settings.LANGUAGES).get(language, language)
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_languages(request):
    """
    API endpoint to get list of available languages.
    """
    languages = [
        {
            'code': lang[0],
            'name': lang[1],
            'current': lang[0] == translation.get_language()
        }
        for lang in settings.LANGUAGES
    ]

    return Response({
        'languages': languages,
        'current_language': translation.get_language()
    }, status=status.HTTP_200_OK)
