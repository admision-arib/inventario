
from django.urls import path
from . import views

urlpatterns = [
    path('comisiones/', views.lista_comisiones, name='lista_comisiones'),
    path('comisiones/crear/', views.crear_comision, name='crear_comision'),
    path('comisiones/<int:pk>/', views.detalle_comision, name='detalle_comision'),
    path('comisiones/<int:pk>/csv/', views.cargar_csv, name='cargar_csv'),
    path('comisiones/<int:pk>/acta/', views.acta_pdf, name='acta_pdf'),
    path('escanear/', views.escanear_bien, name='escanear_bien'),
    path('actualizar-estado/', views.actualizar_estado, name='actualizar_estado'),
]
