from pyexpat.errors import messages
from urllib import request
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from Index.forms import *
from db.models import *
from django.contrib.auth import authenticate,login,logout
# Create your views here.
from django.contrib.auth.decorators import user_passes_test,login_required
from django.core.paginator import Paginator
from django.contrib import messages # <--- ¡Asegúrate de importar esto!
from django.shortcuts import render
from django.db.models import Q

def is_admin(user):
    return user.roles == 'Administrador'

def is_active_user(user):
    return user.is_active == 'True'

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
    secciones = SeccionesExpediente.objects.filter(expediente=expediente).order_by('tipoDeSeccion', 'pk')
    estados = Estado.objects.all()
    usuarios = User.objects.all()
    
    if request.method == "POST":
        post = request.POST
        datos_agrupados = {}

        for key, value in post.items():
            if not key.startswith("registro-"):
                continue
            
            parts = key.split('-', 3)
            if len(parts) != 4:
                continue
            
            _, seccion_id_s, apartado_id_s, field = parts
            
            try:
                ids_tuple = (int(seccion_id_s), int(apartado_id_s))
            except ValueError:
                continue

            if ids_tuple not in datos_agrupados:
                datos_agrupados[ids_tuple] = {}

            datos_agrupados[ids_tuple][field] = value.strip()

        for (seccion_id, apartado_id), campos in datos_agrupados.items():
            try:
                # Solo actualizamos registros que ya pertenecen a este expediente
                registro = RegistroSeccion.objects.get(
                    seccion__id=seccion_id, 
                    seccion__expediente=expediente, 
                    apartado__id=apartado_id
                )
            except RegistroSeccion.DoesNotExist:
                continue
            
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
                        registro.fecha = None
                else:
                    registro.fecha = None
            
            registro.save()

        messages.success(request, 'Datos guardados con éxito.')
        return redirect(reverse('Index:expediente_editar', args=[expediente.pk]))

    context = {
        'estados': estados,
        'usuarios': usuarios,
        'expediente': expediente,
        'secciones': [],
    }
    
    totalRegistros = 0
    totalRegistrosLlenos = 0

    for seccion in secciones:
        # CAMBIO CLAVE: Iteramos sobre los registros que YA existen para esta sección
        registros_existentes = RegistroSeccion.objects.filter(seccion=seccion).select_related('apartado').order_by('apartado__clave')
        
        filas = []
        for registro in registros_existentes:
            totalRegistros += 1

            if registro.estatus and registro.estatus != "": 
                totalRegistrosLlenos += 1

            fecha_html = ""
            if registro.fecha:
                fecha_html = registro.fecha.strftime("%Y-%m-%d")

            filas.append({
                'apartado': registro.apartado,
                'registro': registro,
                'fecha_html': fecha_html,
            })
            
        context['secciones'].append({
            'seccion': seccion,
            'filas': filas,
        })
        
    context['totalRegistros'] = totalRegistros
    context['totalRegistrosLlenos'] = totalRegistrosLlenos

    return render(request, 'Index/editarExpediente.html', context)

@login_required(login_url='/login/')
def expediente_cambiar_usuario(request, id):
    expediente = get_object_or_404(Expediente, pk=id)

    if request.method == "POST":
        nuevo_usuarios_id = request.POST.get("usuario")

        if nuevo_usuarios_id:
            expediente.usuario_id = nuevo_usuarios_id
            expediente.save()


    return redirect('Index:expediente_editar', id=expediente.id)

@login_required(login_url='/login/')
def expediente_llenar(request, id):
    expediente = get_object_or_404(Expediente, pk=id)
    secciones = SeccionesExpediente.objects.filter(expediente=expediente).order_by('tipoDeSeccion', 'pk')
    print(request.method)
    for seccion in secciones:
        apartados = ApartadoCatalogo.objects.filter(tipoDeSeccion=seccion.tipoDeSeccion).order_by('clave')
        for apartado in apartados:
            registro = RegistroSeccion.objects.filter(seccion=seccion, apartado=apartado).first()
            if registro:
                if not registro.estatus:
                    registro.estatus = 'N/A'
                else:
                    registro.estatus = registro.estatus
                registro.save()
    return redirect('Index:expediente_editar', id=expediente.id)


@login_required(login_url='/login/')
def expediente_crear(request):
    if request.method == "POST":
        exp_form = ExpedienteCrearForm(request.POST)
        rep_form = RepresentantesForm(request.POST)
        obl_form = ObligadosForm(request.POST)

        if exp_form.is_valid() and rep_form.is_valid() and obl_form.is_valid():
            try:
                socio_existente = exp_form.cleaned_data.get('socio')
                nombre_manual = exp_form.cleaned_data.get('socio_manual_nombre')
                tipo_manual = exp_form.cleaned_data.get('socio_manual_tipo')
                
                socio_a_asignar = None
                if socio_existente:
                    socio_a_asignar = socio_existente
                elif nombre_manual and tipo_manual:
                    socio_a_asignar = Socio.objects.create(nombre=nombre_manual, tipoPersona=tipo_manual)
                
                if not socio_a_asignar:
                    return JsonResponse({'success': False, 'error': "No se encontró socio."}, status=400)

                tipo_persona = socio_a_asignar.tipoPersona
                tipo_persona_map = {'F': 'Fisicas', 'M': 'Morales'}
                area_socio = tipo_persona_map.get(tipo_persona)

                print(f"\n================ INICIO CREACION EXPEDIENTE ================")
                print(f"SOCIO: {socio_a_asignar.nombre} | TIPO: {tipo_persona} | AREA_FILTRO: {area_socio}")

                reps_raw = rep_form.cleaned_data.get('representantes', '').strip().strip("|")
                nombres_reps = [x.strip() for x in reps_raw.split("||") if x.strip()]
                obls_raw = obl_form.cleaned_data.get('obligados', '').strip().strip("|")
                nombres_obls = [x.strip() for x in obls_raw.split("||") if x.strip()]

                if tipo_persona == 'M' and (not nombres_reps or not nombres_obls):
                    return JsonResponse({'success': False, 'error': "Faltan representantes u obligados para Persona Moral."}, status=400)

                expediente = exp_form.save(commit=False)
                expediente.socio = socio_a_asignar
                expediente.estatus_id = 1
                expediente.save()
                print(f"EXPEDIENTE CREADO ID: {expediente.id}")

                SECCIONES = SeccionesExpediente.SECCIONES
                for tipo_sec, titulo_sec in SECCIONES:
                    if tipo_sec == 'B':
                        for nombre in nombres_reps:
                            nueva = SeccionesExpediente.objects.create(expediente=expediente, tipoDeSeccion=tipo_sec, tituloSeccion=f"{titulo_sec} - {nombre}")
                            _generar_con_debug_extremo(nueva, area_socio)
                    elif tipo_sec == 'C':
                        for nombre in nombres_obls:
                            nueva = SeccionesExpediente.objects.create(expediente=expediente, tipoDeSeccion=tipo_sec, tituloSeccion=f"{titulo_sec} - {nombre}")
                            _generar_con_debug_extremo(nueva, area_socio)
                    else:
                        nueva = SeccionesExpediente.objects.create(expediente=expediente, tipoDeSeccion=tipo_sec)
                        _generar_con_debug_extremo(nueva, area_socio)

                print(f"================ FIN CREACION EXPEDIENTE ================\n")
                return JsonResponse({'success': True, 'redirect_url': reverse('Index:expedientesLayout')})

            except Exception as e:
                print(f"!!! ERROR: {str(e)}")
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
                
        return JsonResponse({'success': False, 'error': "Formulario no válido."}, status=400)

    return render(request, 'Index/crearExpediente.html', {'exp_form': ExpedienteCrearForm(), 'rep_form': RepresentantesForm(), 'obl_form': ObligadosForm()})

def _generar_con_debug_extremo(seccion_obj, area_socio):
    filtro_permitido = [area_socio, 'Ambas']
    # Traemos todos para comparar uno por uno en el print
    todos_los_apartados = ApartadoCatalogo.objects.filter(tipoDeSeccion=seccion_obj.tipoDeSeccion)
    
    print(f"\n--- SECCION: {seccion_obj.tipoDeSeccion} (ID: {seccion_obj.id}) ---")
    print(f"Filtro permitido: {filtro_permitido}")
    
    for ap in todos_los_apartados:
        # Forzamos string para evitar problemas de tipos
        area_en_db = str(ap.areaDondeAplica).strip()
        condicion = area_en_db in filtro_permitido
        
        print(f"  > Evaluando Apartado [{ap.clave}]: DB_VAL='{area_en_db}' | ¿Entra en filtro?: {condicion}")
        
        if condicion:
            reg = RegistroSeccion.objects.create(seccion=seccion_obj, apartado=ap)
            print(f"    [CREADO] RegistroSeccion ID: {reg.id} para Apartado: {ap.clave}")
        else:
            print(f"    [SALTADO] No se crea registro para {ap.clave}")

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

    # CORRECCIÓN: Usar el nombre de la URL ('name') configurado en urls.py
    # Reemplaza 'editarExpediente' si tu nombre de URL es diferente.
    return redirect('Index:expediente_editar', id=expediente.id)

@login_required(login_url='/login/')    
def editar_layout(request):
    formset = EstadoFormSet(queryset=Estado.objects.all())
    formSocios = EditarSocio()
    formApartado = ModificarApartado()
    formSelectorApartado = SelectorApartadoForm()

    if request.method == 'POST':
        form_name = request.POST.get('form_name')

        if form_name == 'estado_form':
            formset = EstadoFormSet(request.POST)
            if formset.is_valid():
                formset.save()
                messages.success(request, "Los estados se actualizaron con éxito.")
                return redirect('Index:editar_layout')
            else:
                messages.error(request, f"Error en estados: {formset.errors.as_text()}")
        
        elif form_name == 'socio_form':
            socio_id = request.POST.get('socio_id')
            if socio_id and socio_id.strip() != "":
                instance = get_object_or_404(Socio, pk=socio_id)
                formSocios = EditarSocio(request.POST, instance=instance)
                accion = "actualizado"
            else:
                formSocios = EditarSocio(request.POST)
                accion = "creado"
                
            if formSocios.is_valid():
                formSocios.save()
                messages.success(request, f"Socio {accion} con éxito.")
                return redirect('Index:editar_layout')
            else:
                errores = " / ".join([f"{v[0]}" for k, v in formSocios.errors.items()])
                messages.error(request, f"Error al guardar socio: {errores}")
        
        elif form_name == 'apartado_form':
            apartado_id = request.POST.get('apartado_id')
            if apartado_id and apartado_id.strip() != "":
                instance = get_object_or_404(ApartadoCatalogo, pk=apartado_id)
                formApartado = ModificarApartado(request.POST, instance=instance)
                accion = "actualizado"
            else:
                formApartado = ModificarApartado(request.POST)
                accion = "creado"
                
            if formApartado.is_valid():
                formApartado.save()
                messages.success(request, f"Apartado de catálogo {accion} con éxito.")
                return redirect('Index:editar_layout')
            else:
                errores = " / ".join([f"{v[0]}" for k, v in formApartado.errors.items()])
                messages.error(request, f"Error en el apartado: {errores}")

    context = {
        'formset': formset,
        'formSocios': formSocios,
        'formApartado': formApartado,
        'formSelectorApartado': formSelectorApartado,
    }
    return render(request, 'Index/ajustes.html', context)

def obtener_apartado_data(request, apartado_id):
    apartado = get_object_or_404(ApartadoCatalogo, pk=apartado_id)
    data = {
        'tipoDeSeccion': apartado.tipoDeSeccion,
        'clave': apartado.clave,
        'descripcion': apartado.descripcion,
        'areaDondeAplica': apartado.areaDondeAplica,
    }
    return JsonResponse(data)


def obtener_socio_data(request, socio_id):
    try:
        socio = Socio.objects.get(pk=socio_id)
        data = {
            'nombre': socio.nombre,
            'tipoPersona': socio.tipoPersona, 
        }
        return JsonResponse(data)
    except Socio.DoesNotExist:
        return JsonResponse({'error': 'Socio no encontrado'}, status=404)

@login_required(login_url='/login/')    
def avances(request):
    usuarios = User.objects.all()
    estados = Estado.objects.all().order_by('id')
    data_por_usuario = {}
    
    for us in usuarios:
        expedientes_totales = Expediente.objects.filter(usuario=us, eliminado=False)
        numExpedientes = expedientes_totales.count()
        
        # Inicializa el conteo por estado y total
        conteo_por_estado = {}
        for estado in estados:
            conteo_por_estado[estado.nombre] = {
                'count': 0,
                'color': estado.color,
                'id': estado.id
            }

        # Cuenta los expedientes en cada estado
        for exp in expedientes_totales:
            if exp.estatus and exp.estatus.nombre in conteo_por_estado:
                conteo_por_estado[exp.estatus.nombre]['count'] += 1
            
        # Calcula el progreso general (basado en el estado con ID=3, si existe)
        expedientes_completados = expedientes_totales.filter(estatus__id=3).count()
        
        if numExpedientes > 0:
            porcentaje_completado = (expedientes_completados / numExpedientes) * 100
        else:
            porcentaje_completado = 0
            
        data_por_usuario[us.username] = {
            'total': numExpedientes,
            'porcentaje': round(porcentaje_completado, 2),
            'estados': conteo_por_estado 
        }
            
    context = {
        'data_por_usuario': data_por_usuario,
        'estados_list': estados
    }
    
    return render(request, 'Index/avancesLayout.html', context)

@login_required(login_url='/login/')
#@user_passes_test(is_admin)
def administrador(request):

 
    form = UserAdminPassForm()
    usuarios = User.objects.all().order_by('username')
    context = {
        "usuarios": usuarios,
        "current_user_id": request.user.id,
        "form":form,
    }
    return render(request, "Index/administradorPage.html", context)




@login_required(login_url='/login/')
def alta_usuario(request):
    if request.method == 'POST':
        form = UserAdminPassForm(request.POST) 
        if form.is_valid():
            user = form.save() 

            return redirect('Index:administrador')
        else:
            usuarios = User.objects.all().order_by('username')
            
            context = {
                "usuarios": usuarios,
                "current_user_id": request.user.id,
                "form": form,  
                "show_modal_error": True 
            }
            return render(request, 'Index/administradorPage.html', context)
    else:
        return redirect('Index:administrador')

@login_required(login_url='/login/')
#@user_passes_test(is_admin)
def editar_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    form = UserAdminForm(instance=usuario)
    formpassowrd = UserPasswordForm()
    context = {
        'form': form,
        'usuario': usuario,
        'formpassowrd':formpassowrd
    }
    return render(request, "Index/editar_usuario.html", context)

def editar_usuario_datos(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserAdminForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f"Usuario {usuario.username} actualizado correctamente.")
            return redirect('Index:administrador')
        else:

            formpassowrd = UserPasswordForm()
            context = {
                'form': form,
                'usuario': usuario,
                'formpassowrd':formpassowrd
            }
            return render(request, "Index/editar_usuario.html", context)


def editar_usuario_contrasena(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = UserPasswordForm(request.POST) 
        
        if form.is_valid():
            nueva_contrasena = form.cleaned_data['nueva_contrasena']
            
            usuario.set_password(nueva_contrasena)
            usuario.save()
            
            messages.success(request, f"Contraseña del usuario {usuario.username} actualizada correctamente.")
            return redirect('Index:administrador')
        else:
            # Si falla la validación de contraseña, renderizamos la página con el error.
            form_datos = UserAdminForm(instance=usuario)
            context = {
                'form': form_datos,
                'usuario': usuario,
                'formpassowrd':form
            }
            return render(request, "Index/editar_usuario.html", context)

