
from . import views
from django.contrib import admin
from django.urls import path, include

app_name="Index"

urlpatterns = [


    path("",views.index,name='index'),

    path("expedientes/",views.expedientesLayout,name='expedientesLayout'),

    path('expedientes/filtrar/', views.filtrar_expedientes_ajax, name='filtrar_expedientes_ajax'),
    path('expediente/crear/', views.crearExpediente, name='crearExpediente'),
    path('expediente/eliminar/<int:id>/', views.expediente_eliminar, name='expediente_eliminar'),
    path("expedientes/editarExpediente/<int:id>/",views.editarExpediente,name='editarExpediente'),
    path('expediente/cambiarStatus/<int:id>/', views.expediente_cambiar_status, name='expediente_cambiar_status'),
    path('expediente/cambiarUsuario/<int:id>/', views.expediente_cambiar_usuario, name='expediente_cambiar_usuario'),
    path('expediente/exportarExcel/<int:id>/',views.exportarExcel,name ='exportarExcel'),
    path('expediente/exportarPDF/<int:id>/',views.exportarPDF,name ='exportarPDF'),
    path('obtener-lineas-socio/<int:socio_id>/',views.obtener_lineas_socio,name ='obtener_lineas_socio'),
    #Agregar Obligados y Reps
    path('expediente/agregarObligados/<int:id>/',views.agregarObligados,name ='agregarObligados'),
    path('expediente/agregarRepresentantes/<int:id>/',views.agregarRepresentantes,name ='agregarRepresentantes'),

    path('editar/', views.editar_layout, name='editar_layout'),


    path('obtener-socio-data/<int:socio_id>/', views.obtener_socio_data, name='obtener_socio_data'),
    
    path('avances/', views.avances, name='avances'),
    
    #Administrador
    path('admin-usuarios/', views.administrador, name='administrador'),
    path('admin-usuarios/alta/', views.alta_usuario, name='alta_usuario'),
    path('admin-usuarios/editar/<int:user_id>/', views.editar_usuario, name='editar_usuario'),
    path('admin-usuarios/editar_usuario_datos/<int:user_id>/', views.editar_usuario_datos, name='editar_usuario_datos'),
    path('admin-usuarios/editarcontrasena/<int:user_id>/', views.editar_usuario_contrasena, name='editar_usuario_contrasena'),

    path('obtener-apartado-data/<int:apartado_id>/', views.obtener_apartado_data, name='obtener_apartado_data'),

    path('servirArchivo/', views.servirArchivo, name='servirArchivo'),    path('expediente/expediente_llenar/<int:id>/', views.expediente_llenar, name='expediente_llenar'),
    
    #Lineas
    path("lineas/",views.lineasLayout,name='lineasLayout'),
    path('lineas/filtrar/', views.filtrar_lineas_ajax, name='filtrar_lineas_ajax'),
    path('lineas/crear/', views.lineaCrear, name='lineaCrear'),
    path("lineas/editarLinea/<int:id>/",views.editarLinea,name='editarLinea'),
    #path('lineas/eliminar/<int:id>/', views.expediente_cambiar_status, name='expediente_cambiar_status'),
    #path('lineas/cambiarUsuario/<int:id>/', views.expediente_cambiar_usuario, name='expediente_cambiar_usuario'),

] 
