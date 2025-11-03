from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from django.db import IntegrityError

@api_view(['POST'])
def logout_view(request):
    if request.auth:  # If user has a token
        request.auth.delete()  # Delete the token
    return Response(status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_view(request):
    return Response({
        'username': request.user.username,
        'email': request.user.email
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    try:
        user = User.objects.create_user(
            username=request.data.get('username'),
            email=request.data.get('email'),
            password=request.data.get('password')
        )
        return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
    except IntegrityError:
        return Response({'message': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)