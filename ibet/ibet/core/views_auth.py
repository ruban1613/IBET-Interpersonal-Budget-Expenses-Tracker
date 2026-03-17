from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login, logout
from student_module.models import User
from rest_framework.authtoken.models import Token
from django.utils.translation import gettext as _


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({
            'error': _('Please provide both username and password')
        }, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)

    if user is not None:
        login(request, user)
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'persona': user.persona,
            }
        })
    else:
        return Response({
            'error': _('Invalid credentials')
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    full_name = request.data.get('full_name', '')
    phone = request.data.get('phone', '')
    persona = request.data.get('persona', 'INDIVIDUAL')

    if not username or not email or not password:
        return Response({
            'error': _('Username, email and password are required')
        }, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({
            'error': _('Username already exists')
        }, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({
            'error': _('Email already exists')
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Split full name into first and last name
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            persona=persona,
            phone=phone
        )

        return Response({
            'message': _('User registered successfully')
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        import traceback
        error_details = str(e)
        traceback.print_exc()  # This will print to console for debugging
        return Response({
            'error': _('Registration failed'),
            'details': error_details
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        # Delete the token to logout
        request.user.auth_token.delete()
    except:
        pass

    logout(request)
    return Response({
        'message': _('Logged out successfully')
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    user = request.user
    return Response({
        'id': user.id,
        'uid': user.uid,
        'username': user.username,
        'email': user.email,
        'persona': user.persona,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'date_joined': user.date_joined
    })
