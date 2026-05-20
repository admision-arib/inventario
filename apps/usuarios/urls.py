
from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_usuarios, name='lista_usuarios'),
    path('crear/', views.crear_usuario, name='crear_usuario'),
    path('editar/<int:pk>/', views.editar_usuario, name='editar_usuario'),
    path('toggle/<int:pk>/', views.toggle_usuario, name='toggle_usuario'),  # mejor nombre
    path('api/area-usuario/<int:usuario_id>/', views.obtener_area_usuario, name='obtener_area_usuario'),
    path('cambiar-password/', views.cambiar_password_obligatorio, name='cambiar_password_obligatorio'),

]
