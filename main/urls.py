"""
URL configuration for main project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from apps.usuarios.views import CustomLoginView


def redirigir_login(request):
    return redirect('login')


urlpatterns = [
    path('', redirigir_login),
    path('admin/', admin.site.urls),
    path('bienes/', include('apps.bienes.urls')),
    path('inventario/', include('apps.inventario.urls')),
    path('usuarios/', include('apps.usuarios.urls')),
    path('login/', CustomLoginView.as_view(template_name='login.html',redirect_authenticated_user=True), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
