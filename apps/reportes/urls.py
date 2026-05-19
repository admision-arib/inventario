from django.contrib import admin
from django.urls import path
from .views import reportes
from apps.bienes import views

urlpatterns = [
path('reportes/', views.reportes, name='reportes'),
]