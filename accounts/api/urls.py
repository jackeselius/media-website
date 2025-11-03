from django.urls import path
from rest_framework.authtoken import views as token_views
from . import views

urlpatterns = [
    # path('signup/', views.signup, name='api_signup'),  # Signup disabled for now
    path('login/', token_views.obtain_auth_token, name='api_token_auth'),
    path('logout/', views.logout_view, name='api_logout'),
]