"""MediaWebsite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic.base import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    path('admin/', admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path('accounts/', include('django.contrib.auth.urls')),
    path('media/', include('media.urls')),
    path("aboutme/", include("aboutme.urls")),
    # Serve the React SPA entry for the root path
    path('', TemplateView.as_view(template_name='index.html'), name='home'),

    # Catch-all for client-side routes (exclude API/admin/static/media/accounts/router prefixes)
    re_path(r'^(?!admin/|accounts/|media/|static/|router/).*$', TemplateView.as_view(template_name='index.html'), name='spa'),

    path('router/', include('quickstart.urls')),
    
    # API endpoints
    path('api/auth/login/', obtain_auth_token, name='api_token_auth'),
    path('api/auth/', include('accounts.api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)    #jsut for dev dont use in production

