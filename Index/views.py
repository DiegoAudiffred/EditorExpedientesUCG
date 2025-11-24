from pyexpat.errors import messages
from urllib import request
from django.http import HttpResponse
from django.shortcuts import redirect, render
from db.models import *
from django.contrib.auth import authenticate,login,logout
# Create your views here.
from django.contrib.auth.decorators import user_passes_test,login_required

from django.shortcuts import render
from django.db.models import Q


@login_required(login_url='/login/')    
def index(request):

    context = {
     #   'doctors': doctors,
     #   'services':services,
        
    }
    return render(request, 'Index/index.html')

@login_required(login_url='/login/')    
def expedientesLayout(request):
    expedientes = Expediente.objects.all()
    estatus = Estado.objects.all()
    usuarios = User.objects.all()
    
    contexto = {
        'expedientes': expedientes,
        'estatus': estatus,
        'usuarios': usuarios,
    }
    return render(request, 'Index/expedientesLayout.html',contexto)


# views.py de tu_app

# ... (otras importaciones)

def filtrar_expedientes_ajax(request):
    estatus_id = request.GET.get('estatus', '0')
    usuario_id = request.GET.get('usuarios', '0')
    socio_query = request.GET.get('socio', '').strip()
    
    # NUEVOS PARÁMETROS DE FECHA
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    expedientes = Expediente.objects.all()
    
    # Aplicar filtros existentes
    if estatus_id != '0':
        expedientes = expedientes.filter(estatus_id=estatus_id)
        
    if usuario_id != '0':
        # Asumiendo que el campo correcto es 'usuario' o 'usuario_id'
        # Reemplaza 'usuario' con 'creado' si ese es el campo correcto, como se discutió antes.
        expedientes = expedientes.filter(usuario_id=usuario_id) 

    if socio_query:
        expedientes = expedientes.filter(
            Q(socio__nombre__icontains=socio_query) |  
            Q(socio__id__icontains=socio_query)        
        ).distinct()

    # APLICAR FILTRO DE FECHA (RANGO)
    if fecha_inicio and fecha_fin:
        # Filtrar expedientes cuya 'fecha' esté entre fecha_inicio y fecha_fin (inclusivo)
        expedientes = expedientes.filter(fecha__range=[fecha_inicio, fecha_fin])
    elif fecha_inicio:
        # Si solo hay fecha de inicio, busca desde esa fecha en adelante
        expedientes = expedientes.filter(fecha__gte=fecha_inicio)
    elif fecha_fin:
        # Si solo hay fecha de fin, busca hasta esa fecha
        expedientes = expedientes.filter(fecha__lte=fecha_fin)


    context = {'expedientes': expedientes}
    return render(request, 'Index/tablaExpedientex.html', context)
