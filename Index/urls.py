
from . import views
from django.contrib import admin
from django.urls import path, include

app_name="Index"

urlpatterns = [


    path("",views.index,name='index'),
    path("expedientes/",views.expedientesLayout,name='expedientesLayout'),
    #path('expedientes/', views.lista_expedientes, name='lista_expedientes'),
    path('expedientes/filtrar/', views.filtrar_expedientes_ajax, name='filtrar_expedientes_ajax'),

] 
