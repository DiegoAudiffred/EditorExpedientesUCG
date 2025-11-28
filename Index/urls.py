
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
    path('expediente/cambiarStatus/<int:id>/', views.expediente_cambiar_status, name='expediente_cambiar_status'),
    path('expediente/cambiarUsuario/<int:id>/', views.expediente_cambiar_usuario, name='expediente_cambiar_usuario'),
    path('editar/', views.editar_layout, name='editar_layout'),
    path('obtener-socio-data/<int:socio_id>/', views.obtener_socio_data, name='obtener_socio_data'),
    path('avances/', views.avances, name='avances'),
    path('admin-usuarios/', views.administrador, name='administrador'),
    path('admin-usuarios/editar/<int:user_id>/', views.editar_usuario, name='editar_usuario'),
    path('expediente/expediente_llenar/<int:id>/', views.expediente_llenar, name='expediente_llenar'),

] 
