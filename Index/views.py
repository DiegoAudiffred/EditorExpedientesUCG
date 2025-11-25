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
from django.contrib import messages # <--- ¡Asegúrate de importar esto!
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
    expedientes = Expediente.objects.all().order_by('-id').filter(eliminado = False)
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

    expedientes = expedientes.order_by('-id').filter(eliminado = False)

    paginator = Paginator(expedientes, 10)
    page_obj = paginator.get_page(page_number)

    context = {
        'expedientes': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator
    }

    return render(request, 'Index/tablaExpedientex.html', context)


@login_required(login_url='/login/')    

def expediente_editar(request, id):
    expediente = get_object_or_404(Expediente, pk=id)
    if expediente.estatus_id == 1:
        expediente.estatus_id = 2
        expediente.save()

    secciones = SeccionesExpediente.objects.filter(expediente=expediente).order_by('tipoDeSeccion', 'pk')
    estados = Estado.objects.all()
    if request.method == "POST":
        post = request.POST
        
        # 1. Agrupar los datos para no guardar 3 veces la misma fila
        # Estructura: { (seccion_id, apartado_id): { 'fecha': val, 'estatus': val, 'comentario': val } }
        datos_agrupados = {}

        for key, value in post.items():
            if not key.startswith("registro-"):
                continue
            
            # Desarmamos la llave: registro-IDSECCION-IDAPARTADO-CAMPO
            parts = key.split('-', 3)
            if len(parts) != 4:
                continue
            
            _, seccion_id_s, apartado_id_s, field = parts
            
            try:
                ids_tuple = (int(seccion_id_s), int(apartado_id_s))
            except ValueError:
                continue

            # Inicializamos el diccionario para esta fila si no existe
            if ids_tuple not in datos_agrupados:
                datos_agrupados[ids_tuple] = {}

            # Guardamos el valor limpio
            datos_agrupados[ids_tuple][field] = value.strip()

        # 2. Procesar y guardar CADA FILA una sola vez
        for (seccion_id, apartado_id), campos in datos_agrupados.items():
            
            # Validamos que existan los padres
            try:
                seccion = SeccionesExpediente.objects.get(pk=seccion_id, expediente=expediente)
                # Filtramos el apartado también por el tipo de sección para mayor seguridad
                apartado = ApartadoCatalogo.objects.filter(pk=apartado_id, tipoDeSeccion=seccion.tipoDeSeccion).first()
            except (SeccionesExpediente.DoesNotExist, ValueError):
                continue
            
            if not apartado:
                continue

            # --- LÓGICA SEGURA: Update or Create ---
            # Esto busca el registro exacto. Si no existe, lo crea.
            registro, created = RegistroSeccion.objects.get_or_create(
                seccion=seccion,
                apartado=apartado,
                defaults={ 'estatus': '', 'comentario': '', 'fecha': None }
            )

            # Actualizamos los valores que vienen del formulario
            if 'estatus' in campos:
                registro.estatus = campos['estatus']
            
            if 'comentario' in campos:
                registro.comentario = campos['comentario']

            if 'fecha' in campos:
                val_fecha = campos['fecha']
                if val_fecha:
                    try:
                        registro.fecha = datetime.strptime(val_fecha, "%Y-%m-%d").date()
                    except ValueError:
                        # Intento secundario por si el formato varía
                        try:
                            registro.fecha = datetime.strptime(val_fecha, "%d de %B de %Y").date()
                        except ValueError:
                            registro.fecha = None
                else:
                    registro.fecha = None

            # 3. Guardado Atómico (Una sola vez)
            registro.save()

        messages.success(request, 'Datos guardados con éxito.')
        return redirect(reverse('Index:expediente_editar', args=[expediente.pk]))


    context = {
        'estados': estados,
        'expediente': expediente,
        'secciones': [],
    }

    for seccion in secciones:
        apartados = ApartadoCatalogo.objects.filter(tipoDeSeccion=seccion.tipoDeSeccion).order_by('clave')
        filas = []
        for apartado in apartados:
            registro = RegistroSeccion.objects.filter(seccion=seccion, apartado=apartado).first()
            fecha_html = ""
            if registro and registro.fecha:
                original = str(registro.fecha)
                try:
                    fecha_html = datetime.strptime(original, "%Y-%m-%d").strftime("%Y-%m-%d")
                except:
                    try:
                        fecha_html = datetime.strptime(original, "%d de %B de %Y").strftime("%Y-%m-%d")
                    except:
                        fecha_html = ""
            filas.append({
                'apartado': apartado,
                'registro': registro,
                'fecha_html': fecha_html,
            })
        context['secciones'].append({
            'seccion': seccion,
            'filas': filas,
        })

    return render(request, 'Index/editarExpediente.html', context)



@login_required(login_url='/login/')    
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

                print(lista)
                
                lista_raw = lista.strip().strip("|")
                nombres = [x.strip() for x in lista_raw.split("||") if x.strip()]

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



@login_required(login_url='/login/')    
def expediente_eliminar(request,id):
    expediente = Expediente.objects.get(id=id)
    expediente.eliminado = True
    expediente.save()
    return redirect('Index:expedientesLayout')

@login_required(login_url='/login/')    
def expediente_cambiar_status(request, id):
    expediente = get_object_or_404(Expediente, pk=id)

    if request.method == "POST":
        nuevo_estatus_id = request.POST.get("estatus")

        if nuevo_estatus_id:
            expediente.estatus_id = nuevo_estatus_id
            expediente.save()

    return redirect('Index:expediente_editar', id=expediente.id)
