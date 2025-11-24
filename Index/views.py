from pyexpat.errors import messages
from urllib import request
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from Index.forms import ExpedienteCrearForm, ObligadosForm, RepresentantesForm
from db.models import *
from django.contrib.auth import authenticate,login,logout
# Create your views here.
from django.contrib.auth.decorators import user_passes_test,login_required
from django.core.paginator import Paginator

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
    expedientes = Expediente.objects.all().order_by('-id')
    estatus = Estado.objects.all()
    usuarios = User.objects.all()
    
    contexto = {
        'expedientes': expedientes,
        'estatus': estatus,
        'usuarios': usuarios,
    }
    return render(request, 'Index/expedientesLayout.html',contexto)


def filtrar_expedientes_ajax(request):
    estatus_id = request.GET.get('estatus', '0')
    usuario_id = request.GET.get('usuarios', '0')
    socio_query = request.GET.get('socio', '').strip()

    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    page_number = request.GET.get('page', 1)

    expedientes = Expediente.objects.all()

    if estatus_id != '0':
        expedientes = expedientes.filter(estatus_id=estatus_id)

    if usuario_id != '0':
        expedientes = expedientes.filter(usuario_id=usuario_id)

    if socio_query:
        expedientes = expedientes.filter(
            Q(socio__nombre__icontains=socio_query) |
            Q(socio__id__icontains=socio_query)
        ).distinct()

    if fecha_inicio and fecha_fin:
        expedientes = expedientes.filter(fecha__range=[fecha_inicio, fecha_fin])
    elif fecha_inicio:
        expedientes = expedientes.filter(fecha__gte=fecha_inicio)
    elif fecha_fin:
        expedientes = expedientes.filter(fecha__lte=fecha_fin)

    expedientes = expedientes.order_by('-id')

    paginator = Paginator(expedientes, 10)
    page_obj = paginator.get_page(page_number)

    context = {
        'expedientes': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator
    }

    return render(request, 'Index/tablaExpedientex.html', context)

@login_required(login_url='/login/')    
def expediente_editar(request, expediente_id):
    expediente = get_object_or_404(Expediente, pk=expediente_id)
    secciones = SeccionesExpediente.objects.filter(expediente=expediente).order_by('tipoDeSeccion', 'pk')

    if request.method == "POST":
        # Guardado simple: los inputs vienen con nombre patrón:
        # registro-<seccion_id>-<apartado_id>-fecha
        # registro-<seccion_id>-<apartado_id>-estatus
        # registro-<seccion_id>-<apartado_id>-comentario
        post = request.POST
        updates = []
        for key, value in post.items():
                if not key.startswith("registro-"):
                    continue
                # key example: registro-5-12-fecha
                parts = key.split('-', 3)
                if len(parts) != 4:
                    continue
                _, seccion_id_s, apartado_id_s, field = parts
                try:
                    seccion_id = int(seccion_id_s)
                    apartado_id = int(apartado_id_s)
                except ValueError:
                    continue
                # ensure the seccion belongs to this expediente
                try:
                    seccion = SeccionesExpediente.objects.get(pk=seccion_id, expediente=expediente)
                except SeccionesExpediente.DoesNotExist:
                    continue

                apartado = ApartadoCatalogo.objects.filter(pk=apartado_id, tipoDeSeccion=seccion.tipoDeSeccion).first()
                if not apartado:
                    continue

                registro, created = RegistroSeccion.objects.get_or_create(
                    seccion=seccion,
                    apartado=apartado,
                    defaults={'fecha': None, 'estatus': '', 'comentario': ''}
                )

                # set the right field
                val = value.strip()
                if field == "fecha":
                    registro.fecha = val or None
                elif field == "estatus":
                    registro.estatus = val
                elif field == "comentario":
                    registro.comentario = val
                registro.save()
                updates.append(registro)

        messages.success(request, "Registros guardados.")
        return redirect(reverse('expediente_editar', args=[expediente.pk]))

    # GET -> preparar datos para plantilla
    context = {
        'expediente': expediente,
        'secciones': [],
    }

    for seccion in secciones:
        apartados = ApartadoCatalogo.objects.filter(tipoDeSeccion=seccion.tipoDeSeccion).order_by('clave')
        filas = []
        for apartado in apartados:
            registro = RegistroSeccion.objects.filter(seccion=seccion, apartado=apartado).first()
            filas.append({
                'apartado': apartado,
                'registro': registro,
            })
        context['secciones'].append({
            'seccion': seccion,
            'filas': filas,
        })

    return render(request, 'db/expediente_editar.html', context)

def expediente_crear(request):

    if request.method == "POST":
        exp_form = ExpedienteCrearForm(request.POST)
        rep_form = RepresentantesForm(request.POST)
        obl_form = ObligadosForm(request.POST)

        if exp_form.is_valid() and rep_form.is_valid() and obl_form.is_valid():

            expediente = exp_form.save(commit=False)
            expediente.estatus_id = 1
            expediente.save()

            SECCIONES = SeccionesExpediente.SECCIONES

            for tipo, titulo in SECCIONES:

                if tipo not in ['B', 'C']:
                    SeccionesExpediente.objects.create(
                        expediente=expediente,
                        tipoDeSeccion=tipo
                    )
                    continue

                if tipo == 'B':
                    lista = rep_form.cleaned_data.get('representantes', '')
                else:
                    lista = obl_form.cleaned_data.get('obligados', '')

                nombres = [x.strip() for x in lista.split("||") if x.strip()]
                if not nombres:
                    nombres = [""]

                for nombre in nombres:
                    titulo_final = titulo if nombre == "" else f"{titulo} - {nombre}"
                    SeccionesExpediente.objects.create(
                        expediente=expediente,
                        tipoDeSeccion=tipo,
                        tituloSeccion=titulo_final
                    )

            return redirect('Index:expedientesLayout')

        return render(
            request,
            'Index/crearExpediente.html',
            {
                'exp_form': exp_form,
                'rep_form': rep_form,
                'obl_form': obl_form,
            }
        )

    return render(
        request,
        'Index/crearExpediente.html',
        {
            'exp_form': ExpedienteCrearForm(),
            'rep_form': RepresentantesForm(),
            'obl_form': ObligadosForm(),
        }
    )
