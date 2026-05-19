from django.contrib import admin
from django.urls import path
from .views import lista_bienes
from apps.bienes import views

urlpatterns = [
    # Bienes
    path('lista/',views.lista_bienes, name='lista_bienes'),
    path('alta/', views.crear_bien, name='crear_bienes'),

    # Sedes
    path('sedes/', views.lista_sedes, name='lista_sedes'),
    path('sedes/crear/', views.crear_sede, name='crear_sede'),
    path('sedes/editar/<int:pk>/', views.editar_sede, name='editar_sede'),
    path('sedes/desactivar/<int:pk>/', views.desactivar_sede, name='desactivar_sede'),
    path('buscar-catalogo/', views.buscar_catalogo, name='buscar_catalogo'),
    path('buscar-bien/', views.buscar_bien, name='buscar_bien'),
    path('movimientos/', views.lista_movimientos, name='lista_movimientos'),
    path('movimientos/crear/', views.crear_movimiento, name='crear_movimiento'),
    path('reportes/', views.reportes, name='reportes'),
    path('importar-excel/', views.importar_bienes_excel, name='importar_bienes_excel'),
    path('bienes/exportar/', views.exportar_bienes_excel, name='exportar_bienes_excel'),
    path('catalogo/crear/', views.crear_item_catalogo, name='crear_item_catalogo'),
    path('api/info-area/<int:area_id>/', views.obtener_info_area, name='obtener_info_area'),
    path('api/datos-origen/<int:bien_id>/', views.datos_origen_bien, name='datos_origen_bien'),
]