
from . import views
from django.contrib import admin
from django.urls import path, include

app_name="Index"

urlpatterns = [


    path("",views.index,name='index'),
    #Apartado del listado de todos los expedientes
        path("expedientes/",views.expedientesLayout,name='expedientesLayout'), 
        path('expedientes/filtrar/', views.filtrar_expedientes_ajax, name='filtrar_expedientes_ajax'),
        path('expediente/crear/', views.crearExpediente, name='crearExpediente'),
    
    #Apartado en listado de expedientes    
        path("expedientes/editarExpediente/<int:id>/",views.editarExpediente,name='editarExpediente'),
        path("expedientes/actualizarExpediente/<int:id>/",views.actualizarExpediente,name='actualizarExpediente'),
        path('expediente/cambiarAtrasado/<int:id>/', views.cambiarAtrasado, name='cambiarAtrasado'),
        path('expediente/cambiarAnalizar/<int:id>/', views.cambiarAnalizar, name='cambiarAnalizar'),
        #Aprtado dentro de editar expediente
            path('expediente/cambiarStatus/<int:id>/', views.cambiarEstado, name='cambiarEstado'),
            path('expediente/cambiarUsuario/<int:id>/', views.expediente_cambiar_usuario, name='expediente_cambiar_usuario'),
            path('expediente/cambiarUsuarioCredito/<int:id>/', views.cambiarUsuarioCredito, name='cambiarUsuarioCredito'),
            path('expediente/cambiarUsuarioNegocios/<int:id>/', views.cambiarUsuarioNegocios, name='cambiarUsuarioNegocios'),
            
            #Agregar Obligados y Reps 
            path('expediente/agregarObligados/<int:id>/',views.agregarObligados,name ='agregarObligados'),
            path('expediente/agregarRepresentantes/<int:id>/',views.agregarRepresentantes,name ='agregarRepresentantes'),
            path('expediente/eliminarRepresentante/<int:rep>/<int:exp>',views.eliminarRepresentante, name = 'eliminarRepresentante'),
            path('expediente/eliminarObligado/<int:obl>/<int:exp>',views.eliminarObligado, name = 'eliminarObligado'),
            path('expediente/<int:expediente_id>/<int:linea_id>', views.lineaEliminar, name='lineaEliminar'),

            #Citas
            path('expediente/crearCita/<int:id>/',views.crearCita,name ='crearCita'),
            path('expediente/asociarCitaExistente/<int:expedienteId>/<int:citaId>/', views.asociarCitaExistente, name='asociarCitaExistente'),
            path('expediente/desasociarCitaExistente/<int:expedienteId>/<int:citaId>/', views.desasociarCitaExistente, name='desasociarCitaExistente'),
            
            #Apartado de secciones
            path('expediente/agregarRenglonExpediente/<int:expedienteID>/<int:seccionID>/<int:apartadoID>', views.agregarRenglonExpediente, name='agregarRenglonExpediente'),
            path('expediente/eliminarRenglonExpediente/<int:expedienteID>/<int:seccionID>/<int:apartadoID>', views.eliminarRenglonExpediente, name='eliminarRenglonExpediente'),
            path('servirArchivo/', views.servirArchivo, name='servirArchivo'), 
            path('expediente/<int:seccion>/<int:apartado>/<int:secuencial>/', views.checkBoxChange, name='checkBoxChange'),   

            #Botones parte inferior
            path('expediente/eliminar/<int:id>/', views.expediente_eliminar, name='expediente_eliminar'),
            path('expediente/exportarExcel/<int:id>/',views.exportarExcel,name ='exportarExcel'),
            path('expediente/exportarPDF/<int:id>/',views.exportarPDF,name ='exportarPDF'),
            path('expediente/<int:expedienteID>/', views.notificarFaltantes, name='notificarFaltantes'),   
            path('expediente/procesarArchivos/<int:id>/', views.procesarArchivos, name='procesarArchivos'),
            path('expediente/<int:id>/detectar-archivos/', views.detectarArchivos, name='detectarArchivos'),
            path('expediente/expediente_llenar/<int:id>/', views.expediente_llenar, name='expediente_llenar'),

    #Lineas
        path("lineas/",views.lineasLayout,name='lineasLayout'),
        path('lineas/filtrar/', views.filtrar_lineas_ajax, name='filtrar_lineas_ajax'),
        path("lineas/editarLinea/<int:id>/",views.editarLinea,name='editarLinea'),
        path('lineas/crear/<int:id>/', views.lineaCrear, name='lineaCrear'),

    #Avances
        path('avances/', views.avances, name='avances'),
        path('avancesMovimientos/', views.avancesMovimientos, name='avancesMovimientos'),
        path('exportarEjecutivos/', views.exportarEjecutivos, name='exportarEjecutivos'),
        path("reportes/controlExpedientesPDF/", views.controlExpedientesPDF, name="controlExpedientesPDF"),
        path("reportes/control-expedientes/", views.reporte_control_expedientes,name="reporte_control_expedientes"),
    #Admin
        path('admin-usuarios/', views.administrador, name='administrador'),
        path('admin-usuarios/alta/', views.alta_usuario, name='alta_usuario'),
        path('admin-usuarios/editar/<int:user_id>/', views.editar_usuario, name='editar_usuario'),
        path('admin-usuarios/editar_usuario_datos/<int:user_id>/', views.editar_usuario_datos, name='editar_usuario_datos'),
        path('admin-usuarios/editarcontrasena/<int:user_id>/', views.editar_usuario_contrasena, name='editar_usuario_contrasena'),
        path('admin-usuarios/generarLista', views.generarLista, name='generarLista'),
        path('cargaInicial/', views.cargaInicial, name='cargaInicial'),

    #Citas
        path('juntasIndex/',views.juntasIndex,name='juntasIndex'),
        path('junta/editar/<int:cita>/', views.editarJunta, name='editarJunta'),
        path('junta/crear/', views.crearJunta, name='crearJunta'),
        path('junta/eliminar/<int:cita>/', views.eliminarJunta, name='eliminarJunta'),
    #Envio por correo
        path('expediente/recibirExpediente/<int:expedienteID>/<str:observaciones>', views.recepcionExpediente, name='recepcionExpediente'),
        path('expediente/revisionExpediente/<int:expedienteID>/<str:observaciones>', views.revisionExpediente, name='revisionExpediente'),
        path('expediente/enviarExpediente/<int:expedienteID>/<str:reenviado>', views.enviarExpediente, name='enviarExpediente'),
        path('expediente/rechazarExpediente/<int:expedienteID>/', views.rechazarExpediente, name='rechazarExpediente'),
        path('expediente/archivarExpediente/<int:id>/<str:porcentajeLlenado>', views.archivarExpediente, name='archivarExpediente'),
        #Aceptar y rechazar
            path('expedientes/editarExpediente/Rechazar/<int:id>', views.rechazarCita, name='rechazarCita'),
            path('expedientes/editarExpediente/Aceptar/<int:id>', views.aceptarCita, name='aceptarCita'),

    #Ajustes
        path('editar/', views.editar_layout, name='editar_layout'),

    #Ajax Search 
        path('obtener-lineas-socio/<int:socio_id>/',views.obtener_lineas_socio,name ='obtener_lineas_socio'),
        path('obtener-obligado-data/<int:obligado_id>/', views.obtener_obligado_data, name='obtener_obligado_data'),
        path('obtener-socio-data/<int:socio_id>/', views.obtener_socio_data, name='obtener_socio_data'),
        path('obtener-apartado-data/<int:apartado_id>/', views.obtener_apartado_data, name='obtener_apartado_data'),

  

 
] 
