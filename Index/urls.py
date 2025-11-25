
from . import views
from django.contrib import admin
from django.urls import path, include

app_name="Index"

urlpatterns = [


    path("",views.index,name='index'),
    path("expedientes/",views.expedientesLayout,name='expedientesLayout'),
    #path('expedientes/', views.lista_expedientes, name='lista_expedientes'),
    path('expedientes/filtrar/', views.filtrar_expedientes_ajax, name='filtrar_expedientes_ajax'),
    path("expedientes/editarExpediente/<int:id>/",views.expediente_editar,name='expediente_editar'),
    path('expediente/crear/', views.expediente_crear, name='expediente_crear'),
    path('expediente/eliminar/<int:id>/', views.expediente_eliminar, name='expediente_eliminar'),
    path('expediente/cambiar-status/<int:id>/', views.expediente_cambiar_status, name='expediente_cambiar_status'),

] 
