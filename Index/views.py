import csv
import ctypes
import email
from io import BytesIO
import mimetypes
import os
from pyexpat.errors import messages
from urllib import request
from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from openpyxl import load_workbook
import openpyxl
from Index.forms import *
from db.models import *
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import user_passes_test,login_required
from django.core.paginator import Paginator
from django.contrib import messages 
from django.shortcuts import render
from django.db.models import Q, Count, Prefetch
from openpyxl.styles import *
from openpyxl.styles.borders import Border, Side
import smtplib
from email.message import EmailMessage
from django.db.models.functions import Cast
from django.db import transaction
from django.core.mail import EmailMessage, SafeMIMEText, get_connection
from icalendar import Calendar, Event
from datetime import date, datetime, time, timedelta
from django.db.models import FloatField
import re
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from xhtml2pdf import pisa
#LOS STATUS DEBEN SER 1="Nuevo" y 2="Completado" por temas de compatiblidad
def is_admin(user):
    return user.roles == 'Administrador'

def is_active_user(user):
    return user.is_active == 'True'

@login_required(login_url='/login/')    
def index(request):
    estados = Estado.objects.all()
    context = {
   
        'estados':estados,
    }
    return render(request, 'Index/index.html',context)
def preguntasIndex(request):
    estados = Estado.objects.all()
    context = {
   
        'estados':estados,
    }
    return render(request, 'Index/preguntasIndex.html',context)

@login_required(login_url='/login/')
def expedientesLayout(request):
    expedientes = Expediente.objects.all().order_by('-id').filter(eliminado = False)
    estatus = Estado.objects.all()
    usuarios = User.objects.exclude(roles__in=['Administrador', 'Credito', 'Gerente de Credito','Ejecutivo de Negocios'])   
    usuariosCredito = User.objects.filter(roles__in=['Credito','Gerente de Credito']) 
    usuariosNegocios = User.objects.filter(roles__in=['Ejecutivo de Negocios','Gerente Centro de Negocios']) 
    contexto = {
            'expedientes': expedientes,
            'estatus': estatus,
            'usuarios': usuarios,
            'usuariosCredito': usuariosCredito,
            'usuariosNegocios':usuariosNegocios,
        }
    return render(request, 'Index/expedientesLayout.html',contexto)


def filtrar_expedientes_ajax(request):
    estatus_id = request.GET.get('estatus', '0')
    usuario_id = request.GET.get('usuarios', '0')
    usuarioNegocios_id = request.GET.get('usuariosNegocios', '0')
    usuarioCredito_id = request.GET.get('usuariosCredito', '0')
    socio_query = request.GET.get('socio', '').strip()

    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    expediente_resagado = request.GET.get('expedienteResagado', '0')
    contemplado = request.GET.get('contemplado', '0')
    archivado_faltantes = request.GET.get('archivadoFaltantes', '0')

    page_number = request.GET.get('page', 1)

    expedientes = Expediente.objects.all()

    if estatus_id != '0':
        expedientes = expedientes.filter(estatus_id=estatus_id)

    if usuario_id != '0':
        expedientes = expedientes.filter(usuario_id=usuario_id)
    if usuarioNegocios_id != '0':
        expedientes = expedientes.filter(usuarioNegocios_id=usuarioNegocios_id)

    if usuarioCredito_id != '0':
        expedientes = expedientes.filter(usuarioCredito_id=usuarioCredito_id)

    if expediente_resagado == '1':
        expedientes = expedientes.filter(expedienteResagado=True)

    if contemplado == '1':
        expedientes = expedientes.filter(contemplado=True)

    if archivado_faltantes == '1':
        expedientes = expedientes.filter(
            estatus__nombre='Archivado',
            seccionesexpediente__registroseccion__estatus='pendiente'
        ).distinct()

    if socio_query:
        expedientes = expedientes.filter(
            Q(socio__nombre__icontains=socio_query) |
            Q(socio__id__icontains=socio_query)
        ).distinct()

    if fecha_inicio and fecha_fin:
        expedientes = expedientes.filter(fechaCreacion__range=[fecha_inicio, fecha_fin])
    elif fecha_inicio:
        expedientes = expedientes.filter(fechaCreacion__gte=fecha_inicio)
    elif fecha_fin:
        expedientes = expedientes.filter(fechaCreacion__lte=fecha_fin)

    expedientes = expedientes.order_by('-id').filter(eliminado=False)

    paginator = Paginator(expedientes, 10)
    page_obj = paginator.get_page(page_number)

    context = {
        'expedientes': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator
    }

    return render(request, 'Index/tablaExpedientex.html', context)
import json
from django.http import JsonResponse

def agregarRepresentantes(request, id):
    if request.method == 'POST':
        try:
            expediente = Expediente.objects.get(id=id)
            reps_raw = request.POST.get('representantes', '').strip().strip("|")
            items_reps = [x.strip() for x in reps_raw.split("||") if x.strip()]
            
            tipo_persona_map = {'F': 'Fisicas', 'M': 'Morales'}
            area_socio = tipo_persona_map.get(expediente.socio.tipoPersona)

            for item in items_reps:
                rep_data = json.loads(item)
                rep_id = rep_data.get('id')
                rep_nombre = rep_data.get('nombre', '').strip()

                if rep_id:
                    representante = RepresentanteLegal.objects.get(id=rep_id)
                else:
                    representante, created_rep = RepresentanteLegal.objects.get_or_create(
                        nombre=rep_nombre
                    )
                
                representante.expedientes.add(expediente)
                
                nueva, created_sec = SeccionesExpediente.objects.get_or_create(
                    expediente=expediente,
                    tipoDeSeccion='B',
                    tituloSeccion=f"Representante legal - {representante.nombre}"
                )
                
                if created_sec:
                    _generar_con_debug_extremo(nueva, area_socio)
                
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            print(f"Error en agregarRepresentantes: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error'}, status=400)

def agregarObligados(request, id):
    if request.method == 'POST':
        try:
            expediente = Expediente.objects.get(id=id)
            obls_raw = request.POST.get('obligados', '').strip().strip("|")
            elementos_obls = [x.strip() for x in obls_raw.split("||") if x.strip()]
            
            tipo_persona_map = {'F': 'Fisicas', 'M': 'Morales'}
            area_socio = tipo_persona_map.get(expediente.socio.tipoPersona)

            for item in elementos_obls:
                try:
                    data = json.loads(item)
                    id_existente = data.get('id')
                    nombre = data.get('nombre')
                    tipo_persona = data.get('tipo_persona')
                    id_rep = data.get('representante')
                    nombre_rep_input = data.get('representante_texto')
                except json.JSONDecodeError:
                    id_existente = ""
                    nombre = item
                    tipo_persona = "F"
                    id_rep = ""
                    nombre_rep_input = ""

                representante = None

                if id_existente:
                    obligado = ObligadoSolidario.objects.get(id=id_existente)
                    obligado.expedientes.add(expediente)
                    tipo_persona = getattr(obligado, 'tipoPersona', tipo_persona)
                    nombre = obligado.nombre
                    
                    if tipo_persona == 'M' and getattr(obligado, 'representante', None):
                        representante = obligado.representante
                else:
                    obligado, created_obl = ObligadoSolidario.objects.get_or_create(
                        nombre=nombre,
                        defaults={'tipoPersona': tipo_persona}
                    )
                    obligado.expedientes.add(expediente)

                nueva, created_sec = SeccionesExpediente.objects.get_or_create(
                    expediente=expediente,
                    tipoDeSeccion='C',
                    tituloSeccion=f"Obligado solidario y garantes - {nombre}"
                )
                
                if created_sec:
                    _generar_con_debug_extremo(nueva, area_socio)

                if tipo_persona == 'M':
                    if not representante:
                        if id_rep:
                            representante = RepresentanteLegal.objects.get(id=id_rep)
                        elif nombre_rep_input:
                            representante, created_rep = RepresentanteLegal.objects.get_or_create(
                                nombre=nombre_rep_input
                            )

                    if representante:
                        representante.expedientes.add(expediente)
                        obligado.representante = representante
                        obligado.save()

                        nombre_rep = representante.nombre if hasattr(representante, 'nombre') else nombre_rep_input
                        
                        nueva_sec_rep, created_sec_rep = SeccionesExpediente.objects.get_or_create(
                            expediente=expediente,
                            tipoDeSeccion='B',
                            tituloSeccion=f"Representante legal - {nombre_rep}"
                        )
                        
                        if created_sec_rep:
                            _generar_con_debug_extremo(nueva_sec_rep, area_socio)
                
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            print(f"Error en agregarObligados: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error'}, status=400)
    
@login_required(login_url='/login/')
def editarExpediente(request, id):
    expediente = get_object_or_404(Expediente, pk=id)
    lineasLista = Linea.objects.filter(expediente=expediente)
    secciones = SeccionesExpediente.objects.filter(expediente=expediente).order_by('tipoDeSeccion', 'pk')
    estados = Estado.objects.all()
    usuarios = User.objects.filter(roles__in=['Ejecutivo de Servicios', 'Gerente Centro de Negocios'])
    usuariosCreditos = User.objects.filter(roles__in=['Credito','Gerente de Credito'])
    usuariosNegocios = User.objects.filter(roles__in=['Ejecutivo de Negocios'])
    rep_form = CrearRepresentante()
    obl_form = CrearObligado()
    lin_form = LineaCrearForm(expedienteInstance=expediente)
    cita_form = CitaForm(user=request.user)
    ahora_local = timezone.localtime(timezone.now())
    hoy = ahora_local.date()
    hora_actual = ahora_local.time()

    citasDisponibles = Cita.objects.filter(
        Q(dia__gt=hoy) |
        Q(dia=hoy, hora__gte=hora_actual)
    ).order_by('dia', 'hora')    

    citaAsignada = Cita.objects.filter(
        Q(expedientes=expediente),
    ).order_by('dia', 'hora').last()    
   
    if request.method == "POST":
        post = request.POST
        datos_agrupados = {}
        
        es_solo_credito = "guardar_credito" in post

        for key, value in post.items():
            if not key.startswith("registro-"):
                continue
           
            parts = key.split('-', 4)
            if len(parts) != 5:
                continue
           
            _, seccion_id_s, apartado_id_s, secuencial_s, field = parts
           
            try:
                ids_tuple = (int(seccion_id_s), int(apartado_id_s), int(secuencial_s))
            except ValueError:
                continue

            if ids_tuple not in datos_agrupados:
                datos_agrupados[ids_tuple] = {}

            datos_agrupados[ids_tuple][field] = value.strip()

        for (seccion_id, apartado_id, secuencial), campos in datos_agrupados.items():
            registro = RegistroSeccion.objects.filter(
                seccion__id=seccion_id,
                seccion__expediente=expediente,
                apartado__id=apartado_id,
                secuencial=secuencial
            ).first()
           
            if not registro:
                continue
            
            if es_solo_credito:
                if 'comentarioCredito' in campos:
                    registro.comentarioCredito = campos['comentarioCredito']
                    registro.save()
            else:
                if registro.seccion.tipoDeSeccion == 'VII' and 'descripcion_libre' in campos:
                    registro.comentario = campos['descripcion_libre']
                elif 'comentario' in campos:
                    registro.comentario = campos['comentario']

                if 'estatus' in campos:
                    registro.estatus = campos['estatus']

                if 'comentarioCredito' in campos:
                    registro.comentarioCredito = campos['comentarioCredito']
               
                if 'es_fecha' in campos:
                    registro.es_fecha = campos['es_fecha'].lower() == 'true'

                if registro.es_fecha:
                    registro.numero = None
                    if 'fecha_date' in campos:
                        val_fecha = campos['fecha_date']
                        if val_fecha:
                            try:
                                registro.fecha = datetime.strptime(val_fecha, "%Y-%m-%d").date()
                            except ValueError:
                                registro.fecha = None
                        else:
                            registro.fecha = None
                    else:
                        registro.fecha = None
                else:
                    registro.fecha = None
                    if 'fecha_num' in campos:
                        val_numero = campos['fecha_num']
                        if val_numero:
                            try:
                                registro.numero = val_numero
                            except ValueError:
                                registro.numero = None
                        else:
                            registro.numero = None
               
                registro.save()

        messages.success(request, 'Datos guardados con éxito.')
        return redirect(reverse('Index:editarExpediente', args=[expediente.pk]))

    num_kepler = expediente.socio.numeroKepler
    if num_kepler is None or str(num_kepler).strip() == "" or str(num_kepler).strip() == "0000" or str(num_kepler).strip() == "0":
        stringSocio = f"0000 {expediente.socio.nombre}"
    else:
        stringSocio = str(num_kepler).strip()

    archivos_encontrados = checarRuta(stringSocio, secciones)    
    print(stringSocio)

    registrosConComentarios = []
    for seccion in secciones:
        apartados = ApartadoCatalogo.objects.filter(tipoDeSeccion=seccion.tipoDeSeccion).order_by('clave')
        for apartado in apartados:
            reg = RegistroSeccion.objects.filter(seccion=seccion, apartado=apartado).first()
            if reg is not None and reg.comentarioCredito:
                registrosConComentarios.append({
                    'nombreSeccion': str(seccion.tituloSeccion),
                    'claveApartado': str(apartado.clave),
                    'comentarioCredito': str(reg.comentarioCredito)
                })

    context = {
        'estados': estados,
        'usuarios': usuarios,
        'expediente': expediente,
        'lineasLista': lineasLista,
        'secciones': [],
        'citasDisponibles': citasDisponibles,
        'citaAsignada': citaAsignada,
        'usuariosCreditos': usuariosCreditos,
        'usuariosNegocios': usuariosNegocios,
        'registrosConComentarios': registrosConComentarios,
    }
   
    totalRegistros = 0
    totalRegistrosLlenos = 0
    totalRegistrosNA = 0
    totalRegistrosVacios = 0
    es_credito = request.user.roles in ['Credito', 'Gerente de Credito']
    estatus_recepcion = expediente.estatus.nombre == "Completo"

    for seccion in secciones:
        registros_existentes = RegistroSeccion.objects.filter(seccion=seccion).select_related('apartado').order_by('apartado__clave', 'secuencial')

        filas = []
        for registro in registros_existentes:
            totalRegistros += 1

            if registro.estatus == "N/A":
                totalRegistrosNA += 1
            elif registro.numero or registro.fecha:
                totalRegistrosLlenos += 1
            else:
                #print(registro)
                totalRegistrosVacios += 1

            fecha_html = ""
            if registro.es_fecha:
                if registro.fecha:
                    fecha_html = registro.fecha.strftime("%Y-%m-%d")
            else:
                if registro.numero is not None:
                    fecha_html = str(registro.numero)

            info_archivo = archivos_encontrados.get(registro.id)

            filas.append({
                'apartado': registro.apartado,
                'registro': registro,
                'fecha_html': fecha_html,
                'archivo_url': info_archivo['ruta'] if info_archivo else None,
            })

        context['secciones'].append({
            'seccion': seccion,
            'filas': filas,
        })

    if totalRegistros != (totalRegistrosLlenos + totalRegistrosVacios + totalRegistrosNA):
        context['mensajeInfo'] = "Los registros no coinciden con los status"

    context['totalRegistros'] = totalRegistros
    context['totalRegistrosLlenos'] = totalRegistrosLlenos
    context['totalRegistrosNA'] = totalRegistrosNA
    context['totalRegistrosVacios'] = totalRegistrosVacios



    total_util = totalRegistrosLlenos + totalRegistrosVacios
    
    if total_util > 0:
        porcentaje = (totalRegistrosLlenos / total_util) * 100
    else:
        porcentaje = 0
    
    context['porcentajeLlenado'] = round(porcentaje, 2)

    context['rep_form'] = rep_form
    context["obl_form"] = obl_form
    context["lin_form"] = lin_form
    context['cita_form'] = cita_form
    lista_reps = RepresentanteLegal.objects.filter(expedientes=expediente)
    lista_obls = ObligadoSolidario.objects.filter(expedientes=expediente)
    context['lista_reps'] = lista_reps
    context["lista_obls"] = lista_obls
    return render(request, 'Index/editarExpediente.html', context)

@login_required(login_url='/login/')
def lineaCrear(request, id):
    print(f"[DEBUG] Inicio de lineaCrear. Request method: {request.method}, ID expediente: {id}")
    expedienteInstance = get_object_or_404(Expediente, pk=id)
    print(f"[DEBUG] Expediente encontrado: {expedienteInstance}")

    if request.method == "POST":
        lineasData = request.POST.get('lineas', '')
        print(f"[DEBUG] lineasData recibida: '{lineasData}'")

        if lineasData:
            listaSegmentada = lineasData.split('||')
            print(f"[DEBUG] Bloques segmentados ({len(listaSegmentada)}): {listaSegmentada}")

            tipo_persona_map = {'F': 'Fisicas', 'M': 'Morales'}
            tipo_persona_raw = getattr(expedienteInstance.socio, 'tipoPersona', None)
            area_socio = tipo_persona_map.get(tipo_persona_raw)
            print(f"[DEBUG] Tipo persona socio raw: '{tipo_persona_raw}', area_socio mapeada: '{area_socio}'")

            secciones_restantes = ['III', 'IV', 'V', 'VI','VII']

            try:
                with transaction.atomic():
                    for idx, bloque in enumerate(listaSegmentada):
                        print(f"[DEBUG] --- Procesando bloque [{idx}]: '{bloque}' ---")
                        if not bloque.strip():
                            print(f"[DEBUG] Bloque [{idx}] vacio, omitiendo.")
                            continue
                        
                        partes = bloque.split('::')
                        print(f"[DEBUG] Partes en bloque [{idx}] ({len(partes)}): {partes}")
                        if len(partes) < 4:
                            print(f"[DEBUG] Bloque [{idx}] invalido (menos de 4 partes), omitiendo.")
                            continue

                        numero = partes[0].strip()
                        monto = partes[1].strip()
                        tipoLineaId = partes[2].strip()
                        vigente = partes[3] == 'true'

                        print(f"[DEBUG] Creando Linea con: numero='{numero}', monto='{monto}', tipoLinea='{tipoLineaId}', vigente={vigente}")
                        nueva_linea = Linea.objects.create(
                            expediente=expedienteInstance,
                            numero=numero,
                            monto=monto,
                            tipoLinea=tipoLineaId,
                            vigente=True
                        )
                        print(f"[DEBUG] Linea creada con exito ID: {nueva_linea.pk}")

                        for tipo_sec in secciones_restantes:
                            print(f"[DEBUG] Creando seccion '{tipo_sec}' para linea ID: {nueva_linea.pk}")
                            nueva_seccion = SeccionesExpediente.objects.create(
                                expediente=expedienteInstance,
                                linea=nueva_linea,
                                tipoDeSeccion=tipo_sec
                            )
                            print(f"[DEBUG] Seccion creada ID: {nueva_seccion.pk}. Ejecutando _generar_con_debug_extremo...")

                            _generar_con_debug_extremo(nueva_seccion, area_socio)
                            print(f"[DEBUG] _generar_con_debug_extremo finalizado para seccion ID: {nueva_seccion.pk}")

                print("[DEBUG] Proceso completado exitosamente.")
                return JsonResponse({'status': 'success'}, status=200)

            except Exception as e:
                print(f"[ERROR EXCEPCION] Error en la transaccion: {str(e)}")
                import traceback
                print(f"[ERROR TRACEBACK]\n{traceback.format_exc()}")
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

        print("[WARNING] lineasData estaba vacio o no venia en request.POST.")
        return JsonResponse({'status': 'error', 'message': 'No data'}, status=400)

    print(f"[WARNING] Metodo de peticion no permitido: {request.method}")
    return JsonResponse({'status': 'error'}, status=405)
@login_required(login_url='/login/')
def servirArchivo(request):
    ruta_archivo = request.GET.get('ruta')
    if not ruta_archivo:
        raise Http404("El archivo no existe")

    def obtener_ruta_larga_windows(ruta):
        try:
            if not ruta.startswith("\\\\"):
                return ruta
            ruta_preparada = "\\\\?\\UNC" + ruta[1:] if not ruta.startswith("\\\\?\\UNC\\") else ruta
            buf = ctypes.create_unicode_buffer(2048)
            get_long_path_name = ctypes.windll.kernel32.GetLongPathNameW
            resultado = get_long_path_name(ruta_preparada, buf, 2048)
            if resultado > 0:
                ruta_larga = buf.value
                if ruta_larga.startswith("\\\\?\\UNC\\"):
                    return "\\\\" + ruta_larga[8:]
                return ruta_larga
        except Exception:
            pass
        return ruta

    ruta_real = obtener_ruta_larga_windows(ruta_archivo)
    chk_ruta = "\\\\?\\UNC" + ruta_real[1:] if ruta_real.startswith("\\\\") and not ruta_real.startswith("\\\\?\\UNC\\") else ruta_real

    if not os.path.exists(chk_ruta) or os.path.isdir(chk_ruta):
        ruta_real = obtener_ruta_larga_windows(ruta_archivo.upper())
        chk_ruta = "\\\\?\\UNC" + ruta_real[1:] if ruta_real.startswith("\\\\") and not ruta_real.startswith("\\\\?\\UNC\\") else ruta_real
        
        if not os.path.exists(chk_ruta) or os.path.isdir(chk_ruta):
            raise Http404("El archivo no existe")

    nombre_archivo = os.path.basename(ruta_real)
    mime_type, _ = mimetypes.guess_type(chk_ruta)
    
    response = FileResponse(open(chk_ruta, 'rb'), content_type=mime_type)
    response['Content-Disposition'] = f'inline; filename="{nombre_archivo}"'
    return response
    
@login_required(login_url='/login/')
def expediente_cambiar_usuario(request, id):
    expediente = get_object_or_404(Expediente, pk=id)

    if request.method == "POST":
        nuevo_usuarios_id = request.POST.get("usuario")

        if nuevo_usuarios_id:
            expediente.usuario_id = nuevo_usuarios_id
            expediente.save()


    return redirect('Index:editarExpediente', id=expediente.id)
        
@login_required(login_url='/login/')
def cambiarUsuarioCredito(request, id):
    expediente = get_object_or_404(Expediente, pk=id)

    if request.method == "POST":
        nuevo_usuarios_id = request.POST.get("usuario")

        if nuevo_usuarios_id:
            expediente.usuarioCredito_id = nuevo_usuarios_id
            expediente.save()


    return redirect('Index:editarExpediente', id=expediente.id)

@login_required(login_url='/login/')
def expediente_llenar(request, id):
    expediente = get_object_or_404(Expediente, pk=id)
    secciones = SeccionesExpediente.objects.filter(expediente=expediente).order_by('tipoDeSeccion', 'pk')
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
    return redirect('Index:editarExpediente', id=expediente.id)

@login_required(login_url='/login/')
def crearExpediente(request):
    if request.method == "POST":
        exp_form = ExpedienteCrearForm(request.POST)
        rep_form = CrearRepresentante(request.POST)
        obl_form = CrearObligado(request.POST)

        if exp_form.is_valid() and rep_form.is_valid() and obl_form.is_valid():
            try:
                with transaction.atomic():
                    socio_existente = exp_form.cleaned_data.get('socio')
                    nombre_manual = exp_form.cleaned_data.get('socio_manual_nombre')
                    tipo_manual = exp_form.cleaned_data.get('socio_manual_tipo')
                    numeroK = exp_form.cleaned_data.get('socio_manual_numero')

                    socio_a_asignar = None
                    if socio_existente:
                        socio_a_asignar = socio_existente
                    elif nombre_manual and tipo_manual:
                        socio_a_asignar = Socio.objects.create(
                            nombre=nombre_manual, 
                            tipoPersona=tipo_manual, 
                            numeroKepler=numeroK
                        )
                    
                    if not socio_a_asignar:
                        raise ValueError("Debe seleccionar un socio existente o completar los datos manuales.")

                    tipo_persona = socio_a_asignar.tipoPersona
                    tipo_persona_map = {'F': 'Fisicas', 'M': 'Morales'}
                    area_socio = tipo_persona_map.get(tipo_persona)

                    reps_raw = rep_form.cleaned_data.get('representantes', '').strip().strip("|")
                    nombres_reps = [x.strip() for x in reps_raw.split("||") if x.strip()]
                    
                    obls_raw = obl_form.cleaned_data.get('obligados', '').strip().strip("|")
                    raw_items = [x.strip() for x in obls_raw.split("||") if x.strip()]

                    import json
                    listado_obligados_procesados = []

                    for item in raw_items:
                        try:
                            data_obl = json.loads(item)
                            listado_obligados_procesados.append(data_obl)
                        except json.JSONDecodeError:
                            listado_obligados_procesados.append({
                                "id": "",
                                "nombre": item,
                                "tipo_persona": "F",
                                "tipo_persona_texto": "Persona Física",
                                "representante": "",
                                "representante_texto": ""
                            })

                    if tipo_persona == 'M' and not nombres_reps:
                        raise ValueError("Las Personas Morales requieren representantes.")

                    expediente = exp_form.save(commit=False)
                    expediente.socio = socio_a_asignar
                    expediente.estatus_id = 1
                    #expediente.usuario = request.user
                    expediente.save()
                    
                    EstadosFechas.objects.create(
                        expediente=expediente,
                        estado=Estado.objects.get(nombre="Nuevo"),
                        fecha=datetime.now(),
                        usuario=request.user
                    )
                    
                    for rep_nombre in nombres_reps:
                        representante, created = RepresentanteLegal.objects.get_or_create(nombre=rep_nombre)
                        representante.expedientes.add(expediente)

                    for o_data in listado_obligados_procesados:
                        if o_data.get("id"):
                            obligado = ObligadoSolidario.objects.filter(id=o_data["id"]).first()
                        else:
                            obligado = ObligadoSolidario.objects.filter(nombre=o_data["nombre"]).first()
                            if not obligado:
                                t_persona = o_data.get("tipo_persona") if o_data.get("tipo_persona") else "F"
                                obligado = ObligadoSolidario.objects.create(
                                    nombre=o_data["nombre"], 
                                    tipoPersona=t_persona
                                )
                        
                        if obligado:
                            obligado.expedientes.add(expediente)
                            
                            if obligado.tipoPersona == 'M' and o_data.get("representante_texto"):
                                rep_nom = o_data["representante_texto"]
                                r_legal, _ = RepresentanteLegal.objects.get_or_create(nombre=rep_nom)
                                obligado.representante = r_legal
                                integrado = r_legal
                                integrado.expedientes.add(expediente)
                                obligado.save()

                    secciones_permitidas = ['A', 'B', 'C', 'I', 'II']
                    SECCIONES = SeccionesExpediente.SECCIONES
                    
                    for tipo_sec, titulo_sec in SECCIONES:
                        if tipo_sec not in secciones_permitidas:
                            continue
                            
                        if tipo_sec == 'B':
                            for nombre in nombres_reps:
                                nueva = SeccionesExpediente.objects.create(
                                    expediente=expediente, 
                                    tipoDeSeccion=tipo_sec, 
                                    tituloSeccion=f"{titulo_sec} - {nombre}"
                                )
                                _generar_con_debug_extremo(nueva, area_socio)
                        elif tipo_sec == 'C':
                            for o_data in listado_obligados_procesados:
                                nombre_obl = o_data["nombre"]
                                nueva = SeccionesExpediente.objects.create(
                                    expediente=expediente, 
                                    tipoDeSeccion=tipo_sec, 
                                    tituloSeccion=f"{titulo_sec} - {nombre_obl}"
                                )
                                _generar_con_debug_extremo(nueva, area_socio)
                                
                                if o_data.get("id"):
                                    obl_obj = ObligadoSolidario.objects.filter(id=o_data["id"]).first()
                                else:
                                    obl_obj = ObligadoSolidario.objects.filter(nombre=nombre_obl).first()
                                    
                                if obl_obj and obl_obj.tipoPersona == 'M' and obl_obj.representante:
                                    nueva_rep = SeccionesExpediente.objects.create(
                                        expediente=expediente,
                                        tipoDeSeccion='B',
                                        tituloSeccion=f"Rep. Legal Obligado - {obl_obj.representante.nombre}"
                                    )
                                    _generar_con_debug_extremo(nueva_rep, area_socio)
                        else:
                            nueva = SeccionesExpediente.objects.create(
                                    expediente=expediente, 
                                    tipoDeSeccion=tipo_sec
                                )
                            _generar_con_debug_extremo(nueva, area_socio)

                return JsonResponse({
                    'success': True, 
                    'redirect_url': reverse('Index:expedientesLayout')
                })

            except ValueError as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=400)
            except Exception as e:
                return JsonResponse({
                    'success': False, 
                    'error': f"Ocurrió un error inesperado: {str(e)}"
                }, status=500)
        else:
            print(exp_form.errors.as_data())
            error_msg = f"Errores: {exp_form.errors.as_text()} {rep_form.errors.as_text()} {obl_form.errors.as_text()}"
            return JsonResponse({'success': False, 'error': error_msg}, status=400)

    exp_form = ExpedienteCrearForm()
    rep_form = CrearRepresentante()
    obl_form = CrearObligado()
    return render(request, 'Index/crearExpediente.html', {
        'exp_form': exp_form, 
        'rep_form': rep_form, 
        'obl_form': obl_form
    })

def _generar_con_debug_extremo(seccion_obj, area_socio, linea_instance=None):
    filtro_permitido = [area_socio, 'Ambas']
    
    todos_los_apartados = ApartadoCatalogo.objects.filter(
        tipoDeSeccion=seccion_obj.tipoDeSeccion
    ).annotate(
        clave_numerica=Cast('clave', FloatField())
    ).order_by('clave_numerica')

    for ap in todos_los_apartados:
        area_en_db = str(ap.areaDondeAplica).strip()
        condicion = area_en_db in filtro_permitido
        
        if condicion:
            RegistroSeccion.objects.create(
                seccion=seccion_obj, 
                apartado=ap
            )

@login_required(login_url='/login/')    
def expediente_eliminar(request,id):
    expediente = Expediente.objects.get(id=id)
    #expediente.delete()
    expediente.eliminado = True
    expediente.save()
    return redirect('Index:expedientesLayout')

def correoParaRevision(expediente,reenviado):
    destinatario = ["portiz@ucg.com.mx","dCorrea@ucg.com.mx", "mrubio@ucg.com.mx",]#"daudiffred@ucg.com.mx"
    dominio = "http://192.168.0.29:8000/expedientes/editarExpediente/"
    urlFinal = f"{dominio}{expediente.id}/"
    
    usuarioNombre = expediente.usuario.username 
    if reenviado =='True':

        asunto = "Expediente corregido para revisión"
        cuerpoHtml = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
                <h2 style="color: #2c3e50;">Actualización de estatus del expediente</h2>
                <p>Estimado usuario,</p>
                <p>Le informamos que el expediente <strong>{expediente.id}</strong> del socio <strong>{expediente.socio.nombre}</strong> ha sido corregido y está listo para su revisión.</p>
                <div style="margin: 30px 0; text-align: center;">
                    <a href="{urlFinal}" 
                       style="background-color: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Revisar Expediente
                    </a>
                </div>
                <p style="font-size: 0.9em; color: #555;">
                    Atentamente,<br>
                    <strong>{usuarioNombre}</strong>
                </p>
                <hr style="border: 0; border-top: 1px solid #eee;">
                <p style="font-size: 0.8em; color: #999; text-align: center;">
                    Este es un mensaje automático, por favor no responda a este correo.
                </p>
            </div>
        </body>
    </html>
    """
    else:    
        asunto = "Expediente listo para revisión"
        cuerpoHtml = f"""

   <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
                <h2 style="color: #2c3e50;">Actualización de estatus del expediente</h2>
                <p>Estimado usuario,</p>
                <p>Le informamos que el expediente <strong>{expediente.id}</strong> del socio <strong>{expediente.socio.nombre}</strong> está listo para su revisión.</p>
                <div style="margin: 30px 0; text-align: center;">
                    <a href="{urlFinal}" 
                       style="background-color: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Revisar Expediente
                    </a>
                </div>
                <p style="font-size: 0.9em; color: #555;">
                    Atentamente,<br>
                    <strong>{usuarioNombre}</strong>
                </p>
                <hr style="border: 0; border-top: 1px solid #eee;">
                <p style="font-size: 0.8em; color: #999; text-align: center;">
                    Este es un mensaje automático, por favor no responda a este correo.
                </p>
            </div>
        </body>
    </html>
    """
    SMTP_HOST = "ucg.com.mx"
    SMTP_PORT = 587
    USUARIO = "informacion@ucg.com.mx"
    CONTRASENA = "UcG911_@!#"

    mensaje = email.message.EmailMessage()
    mensaje["From"] = USUARIO
    mensaje["To"] = ", ".join(destinatario) if isinstance(destinatario, list) else destinatario
    mensaje["Subject"] = asunto
    
    mensaje.add_alternative(cuerpoHtml, subtype="html")

    try:
        servidor = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        servidor.starttls()
        servidor.login(USUARIO, CONTRASENA)
        servidor.send_message(mensaje)
        servidor.quit()
        print("Correo enviado correctamente")
    except Exception as e:
        print("Error al enviar correo:", e)
    #return redirect('Index:editarExpediente', expediente.id)

@login_required(login_url='/login/')    
def rechazarExpediente(request,expedienteID):
    from email.message import EmailMessage
    expediente = get_object_or_404(Expediente, pk=expedienteID)
    getEstado = Estado.objects.get(nombre='Rechazado')
    expediente.estatus = getEstado
    expediente.usuarioCredito = request.user
    expediente.save()
    darAlta(expediente,getEstado.nombre,request.user)

    seccionesConComentarios = []
    secciones = SeccionesExpediente.objects.filter(expediente=expediente).order_by('tipoDeSeccion', 'pk')
    
    for seccion in secciones:
        apartados = ApartadoCatalogo.objects.filter(tipoDeSeccion=seccion.tipoDeSeccion).order_by('clave')
        for apartado in apartados:
            registro = RegistroSeccion.objects.filter(seccion=seccion, apartado=apartado).first()
            
            if registro is not None:
                if registro.comentarioCredito:
                    seccionesConComentarios.append({
                        'nombreSeccion': str(seccion.tituloSeccion),
                        'claveApartado': str(apartado.clave),
                        'comentario': str(registro.comentarioCredito)
                    })
                    
    destinatario = [expediente.usuario.email] #expediente.usuarioCredito.email
    #destinatario = ["daudiffred@ucg.com.mx"]    
    dominio = "http://192.168.0.29:8000/expedientes/editarExpediente/"
    url_final = f"{dominio}{expediente.id}/"
    asunto = f"RECHAZO: Expediente {expediente.id} - {expediente.socio.nombre}"
    
    comentarios_texto = ""
    for item in seccionesConComentarios:
        comentarios_texto += f"\n- [{item['nombreSeccion']} - {item['claveApartado']}]: {item['comentario']}"


    cuerpo_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
                <h2 style="color: #2c3e50;">Actualización de estatus del expediente</h2>
                <p>Estimado usuario,</p>
                <p>Le informamos que el expediente {expediente.id} del socio {expediente.socio.nombre} - {expediente.socio.numeroKepler} ha sido rechazado.</p>
                <p>Atte {expediente.usuarioCredito.username}.</p>
                <div style="margin: 30px 0; text-align: center;">
                    <a href="{url_final}" 
                       style="background-color: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Revisar Expediente
                    </a>
                </div>
                <div style="background-color: #fdf2f2; border-left: 4px solid #f5c6cb; padding: 15px; margin: 20px 0; border-radius: 4px;">
                    <h4 style="margin-top: 0; color: #a94442;">Detalle de observaciones por sección:</h4>
                    <ul style="margin-bottom: 0; padding-left: 20px;">
    """

    for item in seccionesConComentarios:
        cuerpo_html += f"""
                        <li style="margin-bottom: 10px;">
                            <strong>{item['nombreSeccion']} (Clave: {item['claveApartado']}):</strong> {item['comentario']}
                        </li>
        """

    cuerpo_html += f"""
                    </ul>
                </div>
          
                <hr style="border: 0; border-top: 1px solid #eee;">
                <p style="font-size: 0.8em; color: #999; text-align: center;">
                    Este es un mensaje automático, por favor no responda a este correo.
                </p>
            </div>
        </body>
    </html>
    """
    SMTP_HOST = "ucg.com.mx"
    SMTP_PORT = 587
    USUARIO = "informacion@ucg.com.mx"
    CONTRASENA = "UcG911_@!#"
    
    mensaje = EmailMessage()
    mensaje["From"] = USUARIO
    mensaje["To"] = ", ".join(destinatario) if isinstance(destinatario, list) else destinatario
    mensaje["Subject"] = asunto
    
    mensaje.add_alternative(cuerpo_html, subtype="html")

    try:
        servidor = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        servidor.starttls()
        servidor.login(USUARIO, CONTRASENA)
        servidor.send_message(mensaje)
        servidor.quit()
        print("Correo enviado correctamente")
    except Exception as e:
        print("Error al enviar correo:", e)
    return redirect('Index:editarExpediente', expediente.id)

def darAlta(expediente, nuevo_estatus_nombre, usuario):
    #estadoActual = EstadosFechas.objects.filter(
    #    expediente=expediente, 
    #    estado__nombre=nuevo_estatus_nombre
    #).first()
    #
    #if estadoActual:
    #    estadoActual.fecha = datetime.now()
    #    estadoActual.save()
    #else:    
    EstadosFechas.objects.create(
            expediente=expediente,
            estado=Estado.objects.get(nombre=nuevo_estatus_nombre),
            fecha=datetime.now(),
            usuario=usuario
        )

@login_required(login_url='/login/')
def cambiarEstado(request, id):
    expediente = get_object_or_404(Expediente, pk=id)

    if request.method == "POST":
        nuevo_estatus_nombre = request.POST.get("estatus")
        if nuevo_estatus_nombre and nuevo_estatus_nombre != str(expediente.estatus.nombre):
            #darAlta(expediente, nuevo_estatus_nombre, request.user)
            #if nuevo_estatus_nombre == "Completo":
            #    correoParaRevision(expediente)
            #if nuevo_estatus_nombre == 'Rechazado':
            #    mandarCorreoRechazo(expediente.id)
            
            getEstado = Estado.objects.get(nombre=nuevo_estatus_nombre)
            expediente.estatus = getEstado
            expediente.save()
            
    return redirect('Index:editarExpediente', id=expediente.id)

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
        'nombreArchivo': apartado.nombreArchivo,
        'areaDondeAplica': apartado.areaDondeAplica,
    }
    return JsonResponse(data)


def obtener_obligado_data(request, obligado_id):
    obligado = get_object_or_404(ObligadoSolidario, id=obligado_id)
    
    rep_id = ""
    rep_nombre = ""
    
    if preparado := obligado.representante:
        rep_id = preparado.id
        rep_nombre = preparado.nombre
            
    return JsonResponse({
        'tipoPersona': obligado.tipoPersona,
        'representante_id': rep_id,
        'representante_nombre': rep_nombre
    })
def obtener_socio_data(request, socio_id):
    try:
        socio = Socio.objects.get(pk=socio_id)
        data = {
            'nombre': socio.nombre,
            'tipoPersona': socio.tipoPersona, 
            'numeroKepler': socio.numeroKepler, 

        }
        return JsonResponse(data)
    except Socio.DoesNotExist:
        return JsonResponse({'error': 'Socio no encontrado'}, status=404)

def obtener_lineas_socio(request, socio_id):
    socio = Socio.objects.get(pk=socio_id)
    socio_id = request.GET.get('socio_id')
    lineas = Linea.objects.filter(socio_id=socio).values('id', 'numero', 'monto')
    return JsonResponse(list(lineas), safe=False)

@login_required(login_url='/login/')
def exportarExcel(request, id):
    expediente = get_object_or_404(Expediente, pk=id)
    
    ruta_directorio = fr"C:\Users\Diego Audiffred\Downloads\Lista de proyectos\PlataformaExpedientes\drAlejandro\static"
    ruta_plantilla = os.path.join(ruta_directorio, "FormatoParaExpedientes.xlsx")
    
    try:
        wb = load_workbook(ruta_plantilla)
        ws = wb['Template1'] if 'Template1' in wb.sheetnames else wb.active

        ws['A2'] = f" {expediente.socio.nombre} -# {expediente.id}"

        fila_actual = 4
        
        secciones = SeccionesExpediente.objects.filter(expediente=expediente).order_by('tipoDeSeccion', 'pk')

        from openpyxl.styles import Alignment, Font, PatternFill, Border, Side

        thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        alignment_center = Alignment(horizontal='center', wrap_text=True, vertical='center')

        for item in secciones:
            registros = RegistroSeccion.objects.filter(seccion=item).select_related('apartado').order_by('apartado__clave')
            
            if not registros.exists():
                continue

            ws.merge_cells(start_row=fila_actual, start_column=1, end_row=fila_actual, end_column=5)
            
            for col in range(1, 6):
                celda_borde = ws.cell(row=fila_actual, column=col)
                celda_borde.border = thin_border
                if col == 1:
                    celda_borde.value = str(item.tituloSeccion).upper()
                    celda_borde.alignment = alignment_center
                    celda_borde.font = Font(bold=True)
                    celda_borde.fill = PatternFill(start_color="9BC2E6", end_color="9BC2E6", fill_type="solid")
                else:
                    celda_borde.fill = PatternFill(start_color="9BC2E6", end_color="9BC2E6", fill_type="solid")

            fila_actual += 1

            for reg in registros:
                datos = [
                    reg.apartado.clave,
                    reg.apartado.descripcion,
                    reg.fecha.strftime("%d/%m/%Y") if reg.fecha else "",
                    reg.estatus,
                    reg.comentario
                ]

                for col_idx, valor in enumerate(datos, start=1):
                    cell = ws.cell(row=fila_actual, column=col_idx, value=valor)
                    cell.border = thin_border
                    cell.alignment = alignment_center
                
                fila_actual += 1

        nombre_socio = "".join([c for c in str(expediente.socio.nombre) if c.isalnum() or c==' ']).replace(' ', '_')
        nombre_salida = f"Expediente_{expediente.id}_{nombre_socio}.xlsx"
        ruta_salida = os.path.join(ruta_directorio, nombre_salida)
        
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        with open(ruta_salida, "wb") as f:
            f.write(buffer.getbuffer())

        buffer.seek(0)
        response = FileResponse(buffer, as_attachment=True, filename=nombre_salida)
        response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        return response

    except Exception as e:
        return HttpResponse(f"Error critico al generar archivo: {str(e)}", status=500)
    
@login_required(login_url='/login/')
def exportarPDF(request, id):
    expediente = get_object_or_404(Expediente, pk=id)
    

    
    try:
        secciones_data = []
        secciones = SeccionesExpediente.objects.filter(expediente=expediente).order_by('tipoDeSeccion', 'pk')

        for item in secciones:
            registros = RegistroSeccion.objects.filter(seccion=item).select_related('apartado').order_by('apartado__clave')
            
            if registros.exists():
                secciones_data.append({
                    'titulo': str(item.tituloSeccion).upper(),
                    'registros': registros
                })

        context = {
            'expediente': expediente,
            'secciones': secciones_data,
            'socio_info': f"{expediente.socio.nombre} - #{expediente.id}"
        }

        ruta_logo = r"C:/Users/Diego Audiffred/Downloads/Lista de proyectos/PlataformaExpedientes/drAlejandro/static/img/Logo.png"

        html_string = f"""
        <html>
        <head>
            <style>
                @page {{ size: letter; margin: 1cm; }}
                body {{ font-family: Arial, sans-serif; font-size: 10px; }}
.header {{ 
    text-align: center; 
    font-weight: bold; 
    font-size: 24px; 
    background-color: #d6dce4; 
    border: 1px solid black; 
    padding: 15px 5px; /* El primer valor (30px) centra verticalmente */
}}                table {{ width: 100%; border-collapse: collapse; margin-bottom: 0px; table-layout: fixed; }}
                th, td {{ border: 1px solid black; padding: 4px; word-wrap: break-word; }}
                .titulo-seccion {{ background-color: #9BC2E6; font-weight: bold; text-align: center; }}
                .col-clave {{ width: 10%; text-align: center; }}
                .col-desc {{ width: 40%; }}
                .col-fecha {{ width: 12%; text-align: center;}}
                .col-status {{ width: 12%; text-align: center; }}
                .col-com {{ width: 26%; }}
            </style>
        </head>
        <body>
            <div style="background-color:#3eb1c8; border: 1px solid black; padding: 5px;">
                <table style="width: 100%; border: none; margin: 0;background-color:#3eb1c8; border: 1px solid black;">
                    <tr>
                        <td style="width: 20%; border: none; vertical-align: middle; text-align: left;">
                            <img src="{ruta_logo}" style="height: 40px;width:120px">
                        </td>
                        <td style="width: 80%; border: none; vertical-align: middle; text-align: right; font-weight: bold; font-size: 18px;color:#ffffff">
                            INTEGRACION DE EXPEDIENTE UNICO DE CRÉDITO
                        </td>
                    </tr>
                </table>
            </div>
            
            <div class="header">{context['socio_info']}</div>

            <table>
                <thead>
                    <tr>
                        <th colspan="2" style="width: 50%; text-align: center; font-size: 15px; background-color:#d6dce4;">I. Identificación del Socio</th>
                        <th class="col-fecha" style="font-size: 15px; background-color:#d6dce4; padding: 5px 5px;">Fecha</th>
                        <th class="col-status" style="font-size: 15px; background-color:#d6dce4; padding: 5px 5px;">Status</th>
                        <th class="col-com" style="font-size: 15px; background-color:#d6dce4; padding: 5px 5px;">Comentarios</th>
                    </tr>
                </thead>
                <tbody>
        """

        for sec in secciones_data:
            html_string += f'<tr><td colspan="5" class="titulo-seccion">{sec["titulo"]}</td></tr>'
            for reg in sec['registros']:
                if reg.fecha:
                                    fecha = reg.fecha.strftime("%d/%m/%Y") if reg.fecha else ""

                elif reg.numero:
                    fecha = reg.numero    
                else:
                    fecha=""
                html_string += f"""
                    <tr>
                        <td class="col-clave" style="text-align: center;">{reg.apartado.clave}</td>
                        <td class="col-desc">{reg.apartado.descripcion}</td>
                        <td class="col-fecha" style="text-align: center;">{fecha}</td>
                        <td class="col-status" style="text-align: center;">{reg.estatus or ''}</td>
                        <td class="col-com">{reg.comentario or ''}</td>
                    </tr>
                """

        html_string += "</tbody></table></body></html>"

        buffer = BytesIO()
        pisa_status = pisa.CreatePDF(html_string, dest=buffer)

        if pisa_status.err:
            return HttpResponse("Error al renderizar PDF", status=500)

        buffer.seek(0)
        nombre_socio = "".join([c for c in str(expediente.socio.nombre) if c.isalnum() or c==' ']).replace(' ', '_')
        return FileResponse(buffer, as_attachment=True, filename=f"Expediente_{expediente.id}_{nombre_socio}.pdf")

    except Exception as e:
        return HttpResponse(f"Error critico al generar PDF: {str(e)}", status=500)





@login_required(login_url='/login/')
def avances(request):
    fecha_actual = datetime.now()
    mes_actual = fecha_actual.month
    ano_actual = fecha_actual.year
    semana_actual = fecha_actual.isocalendar()[1]

    mes_seleccionado = int(request.GET.get('mes', mes_actual))
    ano_seleccionado = int(request.GET.get('ano', ano_actual))
    semana_seleccionada = request.GET.get('semana', '')
    tipo_reporte = request.GET.get('tipo_reporte', 'actual')
    filtro_contemplado = request.GET.get('filtro_contemplado', 'solamente')

    fecha_inicio_semana = None
    fecha_fin_semana = None
    rango_semana_texto = ""

    if semana_seleccionada:
        semana_int = int(semana_seleccionada)
        fecha_inicio_semana = datetime.strptime(f'{ano_seleccionado}-W{semana_int}-1', "%Y-W%W-%w").date()
        fecha_fin_semana = fecha_inicio_semana + timedelta(days=6)
        rango_semana_texto = f"Del {fecha_inicio_semana.strftime('%d/%m/%Y')} al {fecha_fin_semana.strftime('%d/%m/%Y')}"

    if request.user.roles == 'Gerente Centro de Negocios':
        usuarios = User.objects.filter(roles__in=['Ejecutivo de Servicios', 'Gerente Centro de Negocios']).distinct()
        estados = Estado.objects.all().order_by('id')
    elif request.user.roles == 'Gerente de Credito':
        usuarios = User.objects.filter(roles__in=['Credito', 'Crédito', 'Gerente de Credito', 'Gerente de Crédito']).distinct()
        estados = Estado.objects.exclude(nombre='Nuevo').order_by('id')
    elif request.user.roles == 'Administrador':
        usuarios = User.objects.all()
        estados = Estado.objects.all().order_by('id')
    else:
        usuarios = User.objects.none()
        estados = Estado.objects.none()

    data_por_usuario = {}

    lista_usuarios = list(usuarios)
    lista_usuarios.append(None)

    for us in lista_usuarios:
        rol_limpio = request.user.roles
        es_credito = rol_limpio in ['Credito', 'Crédito', 'Gerente de Credito', 'Gerente de Crédito']

        filtros_base = {'eliminado': False}
        if filtro_contemplado == 'solamente':
            filtros_base['contemplado'] = True

        if us is None:
            username_key = "Sin Asignar"
            grafica_barras = es_credito
            if es_credito:
                expedientes_totales = Expediente.objects.filter(usuarioCredito__isnull=True, **filtros_base)
            else:
                expedientes_totales = Expediente.objects.filter(usuario__isnull=True, **filtros_base)
        else:
            username_key = us.username
            rol_usuario = us.roles.strip() if us.roles else ""
            grafica_barras = rol_usuario in ['Credito', 'Crédito', 'Gerente de Credito', 'Gerente de Crédito', 'Ejecutivo de Servicios', 'Gerente Centro de Negocios']
            if rol_usuario in ['Credito', 'Crédito', 'Gerente de Credito', 'Gerente de Crédito']:
                expedientes_totales = Expediente.objects.filter(usuarioCredito=us, **filtros_base)
            else:
                expedientes_totales = Expediente.objects.filter(usuario=us, **filtros_base)

        numExpedientes = expedientes_totales.count()

        conteo_por_estado = {}
        historico_cambios = {}
        estado_cierre_mes = {}

        for estado in estados:
            conteo_por_estado[estado.nombre] = {
                'count': 0,
                'color': estado.color,
                'id': estado.id
            }
            historico_cambios[estado.nombre] = 0
            estado_cierre_mes[estado.nombre] = 0

        if tipo_reporte == 'actual':
            for exp in expedientes_totales:
                if exp.estatus and exp.estatus.nombre in conteo_por_estado:
                    conteo_por_estado[exp.estatus.nombre]['count'] += 1
        else:
            expedientes_ids = expedientes_totales.values_list('id', flat=True)
            for exp_id in expedientes_ids:
                filtros_fechas = {'expediente_id': exp_id}
                if semana_seleccionada and fecha_inicio_semana and fecha_fin_semana:
                    filtros_fechas['fecha__range'] = (fecha_inicio_semana, fecha_fin_semana)
                else:
                    filtros_fechas['fecha__month'] = mes_seleccionado
                    filtros_fechas['fecha__year'] = ano_seleccionado

                ultimo_cambio = EstadosFechas.objects.filter(**filtros_fechas).order_by('-fecha', '-hora').first()

                if ultimo_cambio:
                    if ultimo_cambio.estado.nombre in conteo_por_estado:
                        conteo_por_estado[ultimo_cambio.estado.nombre]['count'] += 1
                else:
                    limite_fecha = fecha_inicio_semana if semana_seleccionada else datetime(ano_seleccionado, mes_seleccionado, 1).date()
                    ultimo_cambio_historico = EstadosFechas.objects.filter(
                        expediente_id=exp_id,
                        fecha__lt=limite_fecha
                    ).order_by('-fecha', '-hora').first()

                    if ultimo_cambio_historico and ultimo_cambio_historico.estado.nombre in conteo_por_estado:
                        conteo_por_estado[ultimo_cambio_historico.estado.nombre]['count'] += 1

        filtros_historial = {'expediente__in': expedientes_totales}
        if semana_seleccionada and fecha_inicio_semana and fecha_fin_semana:
            filtros_historial['fecha__range'] = (fecha_inicio_semana, fecha_fin_semana)
        else:
            filtros_historial['fecha__month'] = mes_seleccionado
            filtros_historial['fecha__year'] = ano_seleccionado

        historial_periodo = EstadosFechas.objects.filter(**filtros_historial)

        for registro in historial_periodo:
            if registro.estado.nombre in historico_cambios:
                historico_cambios[registro.estado.nombre] += 1

        expedientes_ids = expedientes_totales.values_list('id', flat=True)
        for exp_id in expedientes_ids:
            filtros_cierre = {'expediente_id': exp_id}
            if semana_seleccionada and fecha_inicio_semana and fecha_fin_semana:
                filtros_cierre['fecha__range'] = (fecha_inicio_semana, fecha_fin_semana)
            else:
                filtros_cierre['fecha__month'] = mes_seleccionado
                filtros_cierre['fecha__year'] = ano_seleccionado

            ultimo_cambio = EstadosFechas.objects.filter(**filtros_cierre).order_by('-fecha', '-hora').first()

            if ultimo_cambio and ultimo_cambio.estado.nombre in estado_cierre_mes:
                estado_cierre_mes[ultimo_cambio.estado.nombre] += 1

        if tipo_reporte == 'actual':
            expedientes_completados = expedientes_totales.filter(estatus__id=2).count()
        else:
            expedientes_completados = 0
            for exp_id in expedientes_ids:
                filtros_comp = {'expediente_id': exp_id}
                if semana_seleccionada and fecha_inicio_semana and fecha_fin_semana:
                    filtros_comp['fecha__range'] = (fecha_inicio_semana, fecha_fin_semana)
                else:
                    filtros_comp['fecha__month'] = mes_seleccionado
                    filtros_comp['fecha__year'] = ano_seleccionado

                uc = EstadosFechas.objects.filter(**filtros_comp).order_by('-fecha', '-hora').first()
                if uc and uc.estado.id == 2:
                    expedientes_completados += 1

        if numExpedientes > 0:
            porcentaje_completado = (expedientes_completados / numExpedientes) * 100
        else:
            porcentaje_completado = 0

        if numExpedientes > 0 or us is not None:
            data_por_usuario[username_key] = {
                'total': numExpedientes,
                'porcentaje': round(porcentaje_completado, 2),
                'estados': conteo_por_estado,
                'grafica_barras': grafica_barras,
                'historico_cambios': historico_cambios,
                'estado_cierre_mes': estado_cierre_mes
            }

    filtros_negocios_base = {'eliminado': False}
    if filtro_contemplado == 'solamente':
        filtros_negocios_base['contemplado'] = True

    if tipo_reporte == 'actual':
        expedientes_negocios_qs = Expediente.objects.filter(**filtros_negocios_base)
    else:
        filtros_negocios_fechas = {}
        if semana_seleccionada and fecha_inicio_semana and fecha_fin_semana:
            filtros_negocios_fechas['fecha__range'] = (fecha_inicio_semana, fecha_fin_semana)
        else:
            filtros_negocios_fechas['fecha__month'] = mes_seleccionado
            filtros_negocios_fechas['fecha__year'] = ano_seleccionado

        ids_periodo = EstadosFechas.objects.filter(**filtros_negocios_fechas).values_list('expediente_id', flat=True).distinct()
        expedientes_negocios_qs = Expediente.objects.filter(id__in=ids_periodo, **filtros_negocios_base)

    agrupado_negocios = (
        expedientes_negocios_qs
        .values('usuarioNegocios__first_name', 'usuarioNegocios__last_name', 'usuarioNegocios__username')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    labels_negocios = []
    data_negocios = []

    for item in agrupado_negocios:
        nombre_completo = f"{item['usuarioNegocios__first_name'] or ''} {item['usuarioNegocios__last_name'] or ''}".strip()
        if not nombre_completo:
            nombre_completo = item['usuarioNegocios__username'] or 'Sin Asignar'
        labels_negocios.append(nombre_completo)
        data_negocios.append(item['total'])

    semanas_rango = []
    for num_semana in range(1, 54):
        try:
            inicio = datetime.strptime(f'{ano_seleccionado}-W{num_semana}-1', "%Y-W%W-%w").date()
            fin = inicio + timedelta(days=6)
            etiqueta = f"Semana {num_semana} {inicio.strftime('%d/%m/%Y')} al {fin.strftime('%d/%m/%Y')}"
            semanas_rango.append({'numero': num_semana, 'texto': etiqueta})
        except ValueError:
            pass

    context = {
        'data_por_usuario': data_por_usuario,
        'estados_list': estados,
        'mes_seleccionado': mes_seleccionado,
        'ano_seleccionado': ano_seleccionado,
        'semana_seleccionada': semana_seleccionada,
        'rango_semana_texto': rango_semana_texto,
        'tipo_reporte': tipo_reporte,
        'filtro_contemplado': filtro_contemplado,
        'meses_rango': range(1, 13),
        'semanas_rango': semanas_rango,
        'anos_rango': range(datetime.now().year - 3, datetime.now().year + 1),
        'labels_negocios': labels_negocios,
        'data_negocios': data_negocios,
    }

    return render(request, 'Index/avancesLayout.html', context)

@login_required(login_url='/login/')
def exportarEjecutivos(request):
    wb = openpyxl.Workbook()
    
    headers = [
        "FECHA DE ELABORACION DEL ESTUDIO",
        "NUMERO DE SOCIO",
        "SOCIO",
        "FECHA ENTREGA",
        "EJECUTIVO SERVICIOS",
        "TIPO DE CREDITO",
        "MONTO",
        "STATUS DEL CREDITO",
        "STATUS VIGENTE/VENCIDO",
        "DOCUMENTACIÓN REQUERIDA",
        "COMENTARIOS",
        "EJECUTIVO",
        "OBSERVACIONES EN CREDITO",
        "ESTATUS DEL EXPEDIENTE"
    ]

    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Calibri", size=10)
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left_align = Alignment(horizontal="left", vertical="center", wrap_text=True)
    right_align = Alignment(horizontal="right", vertical="center")
    
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )

    ws_total = wb.active
    ws_total.title = "Total"
    ws_total.append(headers)

    for col_num in range(1, len(headers) + 1):
        cell = ws_total.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align

    expedientes = Expediente.objects.filter(
        contemplado=True, 
        eliminado=False
    ).select_related(
        'socio', 'estatus', 'usuario', 'usuarioCredito', 'usuarioNegocios'
    ).prefetch_related('linea_set')

    dict_por_ejecutivo = {}

    for exp in expedientes:
        ejecutivo_obj = exp.usuarioNegocios
        if ejecutivo_obj:
            nombre_ejecutivo = f"{ejecutivo_obj.nombreCompleto}".strip()
            if not nombre_ejecutivo:
                nombre_ejecutivo = ejecutivo_obj.username
        else:
            nombre_ejecutivo = "Sin Asignar"

        lineas = exp.linea_set.all()
        if not lineas.exists():
            lineas = [None]

        ejecutivo_servicios = f"{exp.usuario.nombreCompleto}".strip() if exp.usuario else (exp.usuario.username if exp.usuario else "")
        ejecutivo_credito = f"{exp.usuarioCredito.nombreCompleto}".strip() if exp.usuarioCredito else (exp.usuarioCredito.username if exp.usuarioCredito else "")

        for lin in lineas:
            fecha_estudio = lin.fecha.strftime('%d/%m/%Y') if (lin and lin.fecha) else ""
            num_socio = exp.socio.numeroKepler if exp.socio and exp.socio.numeroKepler else "0000"
            nombre_socio = exp.socio.nombre if exp.socio else ""
            fecha_entrega = exp.fechaCreacion.strftime('%d/%m/%Y') if exp.fechaCreacion else ""
            
            tipo_credito = lin.tipoLinea if lin else "Sin linea registrada"
            monto = float(lin.monto) if lin else 0.0
            
            status_credito = "Activo"
            status_vigente = "Vigente" if (lin and lin.vigente) else ("Vencido" if lin else "")
            
            doc_requerida = ""
            comentarios = ""
            observaciones_credito = ""
            
            estatus_expediente = exp.estatus.nombre if exp.estatus else ""

            fila_datos = [
                fecha_estudio,
                num_socio,
                nombre_socio,
                fecha_entrega,
                ejecutivo_servicios,
                tipo_credito,
                monto,
                status_credito,
                status_vigente,
                doc_requerida,
                comentarios,
                ejecutivo_credito,
                observaciones_credito,
                estatus_expediente
            ]

            ws_total.append(fila_datos)

            if nombre_ejecutivo not in dict_por_ejecutivo:
                dict_por_ejecutivo[nombre_ejecutivo] = []
            dict_por_ejecutivo[nombre_ejecutivo].append(fila_datos)

    for ejecutivo, filas in dict_por_ejecutivo.items():
        sheet_title = (ejecutivo[:28] + '..') if len(ejecutivo) > 30 else ejecutivo
        sheet_title = sheet_title.replace(':', '').replace('*', '').replace('?', '').replace('/', '').replace('\\', '')
        
        ws = wb.create_sheet(title=sheet_title)
        ws.append(headers)

        for col_num in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = center_align

        for fila in filas:
            ws.append(fila)

    for ws in wb.worksheets:
        ws.views.sheetView[0].showGridLines = True
        
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=len(headers)):
            for cell in row:
                cell.font = data_font
                cell.border = thin_border
                
                if cell.column == 7:  # MONTO
                    cell.number_format = '$#,##0.00'
                    cell.alignment = right_align
                elif cell.column in [1, 2, 4, 8, 9, 14]:  # Fechas, Números y Estatus
                    cell.alignment = center_align
                else:
                    cell.alignment = left_align

        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val = str(cell.value or '')
                if len(val) > max_len:
                    max_len = len(val)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="Reporte_Expedientes_Ejecutivos.xlsx"'
    wb.save(response)
    return response

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
#@user_passes_test(is_admin)
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

@login_required(login_url='/login/')
#@user_passes_test(is_admin)
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

@login_required(login_url='/login/')
#@user_passes_test(is_admin)
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
            form_datos = UserAdminForm(instance=usuario)
            context = {
                'form': form_datos,
                'usuario': usuario,
                'formpassowrd':form
            }
            return render(request, "Index/editar_usuario.html", context)

""" 


Todo este apartado es para lineas


"""
#Templeate donde se ven todas las lineas
@login_required(login_url='/login/')    
def lineasLayout(request):
    lineas = Linea.objects.all().order_by('-id')

    usuarios = User.objects.all()
    
    contexto = {
        'lineas': lineas,
        'usuarios': usuarios,
    }
    return render(request, 'Index/lineasLayout.html',contexto)

#Metodo para filtrar las lineas
def filtrar_lineas_ajax(request):
    socio_query = request.GET.get('socio', '').strip()
    page_number = request.GET.get('page', 1)

    lineas = Linea.objects.all()

    if socio_query:

        filtro = Q(expediente__socio__nombre__icontains=socio_query)
        
        if socio_query.isdigit():
            filtro |= Q(expediente__socio__id=int(socio_query))
        
        lineas = lineas.filter(filtro).distinct()
    lineas = lineas.order_by('-id')

    paginator = Paginator(lineas, 10)
    page_obj = paginator.get_page(page_number)

    context = {
        'lineas': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator
    }

    return render(request, 'Index/tablasLineas.html', context)

def filtrar_obligados_ajax(request):
    socio_query = request.GET.get('socio', '').strip()
    page_number = request.GET.get('page', 1)

    lineas = Linea.objects.all()

    if socio_query:

        filtro = Q(expediente__socio__nombre__icontains=socio_query)
        
        if socio_query.isdigit():
            filtro |= Q(expediente__socio__id=int(socio_query))
        
        lineas = lineas.filter(filtro).distinct()
    lineas = lineas.order_by('-id')

    paginator = Paginator(lineas, 10)
    page_obj = paginator.get_page(page_number)

    context = {
        'lineas': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator
    }

    return render(request, 'Index/tablasLineas.html', context)

def filtrar_representantes_ajax(request):
    socio_query = request.GET.get('socio', '').strip()
    page_number = request.GET.get('page', 1)

    lineas = Linea.objects.all()

    if socio_query:

        filtro = Q(expediente__socio__nombre__icontains=socio_query)
        
        if socio_query.isdigit():
            filtro |= Q(expediente__socio__id=int(socio_query))
        
        lineas = lineas.filter(filtro).distinct()
    lineas = lineas.order_by('-id')

    paginator = Paginator(lineas, 10)
    page_obj = paginator.get_page(page_number)

    context = {
        'lineas': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator
    }

    return render(request, 'Index/tablasLineas.html', context)


#Metodo para editar una linea
@login_required(login_url='/login/')
def editarLinea(request, id):
    linea = get_object_or_404(Linea, pk=id)
    exito = False
    if request.method == "POST":
        form = LineaCrearForm(request.POST, instance=linea)
        if form.is_valid():
            instancia = form.save(commit=False)
            instancia.expediente = linea.expediente # Mantiene el expediente original
            instancia.save()
            messages.success(request, f"Línea de {linea.expediente.socio.nombre} actualizada.")
            exito = True
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = LineaCrearForm(instance=linea)
    
    context = {'form': form, 'exito': exito ,'linea':linea}
    return render(request, 'Index/editarLinea.html', context)


def cargaInicial(request):
    if request.method == 'POST':
        try:
            archivo = request.FILES['archivo_excel']
            
            contenido_texto = archivo.read().decode('utf-8').splitlines()
            lector_csv = csv.reader(contenido_texto)
            
            next(lector_csv, None)
            
            for index, row in enumerate(lector_csv, start=2):
                print(f"Fila {index} leída: {row}")
                
                if not row or not any(field.strip() for field in row):
                    print(f"Fila {index} está vacía, saltando...")
                    continue
                    
                print(f"Intentando guardar: Kepler={row[0]}, Nombre={row[1]}, Tipo={row[2]}")
                Socio.objects.create(
                    numeroKepler=row[0],
                    nombre=row[1],
                    tipoPersona=row[2]
                )
                print(f"Fila {index} guardada con éxito.")
                
        except Exception as e:
            print("Se produjo un error durante la carga:", str(e))
            
    return redirect('Index:administrador')




@login_required(login_url='/login/')

def juntasIndex(request):
    juntas = Cita.objects.all().prefetch_related('expedientes').order_by('-dia')
    cita_form = CitaForm()

    juntas_con_forms = []
    for junta in juntas:
        juntas_con_forms.append({
            'cita': junta,
            'form_editar': CitaForm(instance=junta)
        })

    context = {
        'juntas_con_forms': juntas_con_forms,
        'cita_form': cita_form,
    }
    return render(request, 'Index/juntasLayout.html', context)
@login_required(login_url='/login/')

def crearJunta(request):
    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('Index:juntasIndex')
@login_required(login_url='/login/')

def editarJunta(request, cita):
    instancia_cita = get_object_or_404(Cita, pk=cita)
    if request.method == 'POST':
        form = CitaForm(request.POST, instance=instancia_cita)
        if form.is_valid():
            form.save()
            return redirect('Index:juntasIndex')
@login_required(login_url='/login/')

def eliminarJunta(request, cita):
    if request.method == 'POST':
        Cita.objects.filter(id=cita).delete()
        return redirect('Index:juntasIndex')
    
@login_required(login_url='/login/')

def enviarExpediente(request, expedienteID,reenviado):
    expediente = get_object_or_404(Expediente, pk=expedienteID)
    if reenviado == 'True':
        correoParaRevision(expediente,reenviado)
        getEstado = Estado.objects.get(nombre='Recepción')
        expediente.estatus = getEstado
        expediente.save()
    elif reenviado == 'False':
        correoParaRevision(expediente,reenviado)
        getEstado = Estado.objects.get(nombre='Completo')
        expediente.estatus = getEstado
        expediente.save()

    darAlta(expediente,getEstado.nombre,request.user)
    print("Alta dada")
    return redirect('Index:editarExpediente', expediente.id)


@login_required(login_url='/login/')
def cambiarUsuarioNegocios(request, id):
    expediente = get_object_or_404(Expediente, pk=id)

    if request.method == "POST":
        nuevo_usuarios_id = request.POST.get("usuario")

        if nuevo_usuarios_id:
            expediente.usuarioNegocios_id = nuevo_usuarios_id
            expediente.save()


    return redirect('Index:editarExpediente', id=expediente.id)

@login_required(login_url='/login/')

def recepcionExpediente(request, expedienteID,observaciones):
    expediente = get_object_or_404(Expediente, pk=expedienteID)
    
  
    if observaciones == "S":
        asunto = "Entrega de Expedientes"
        getEstado = Estado.objects.get(nombre='Recepción')
        expediente.estatus = getEstado
        expediente.usuarioCredito = request.user
        expediente.save()
        usuarioNombre = expediente.usuarioCredito.nombreCompleto 

        darAlta(expediente,getEstado.nombre,request.user)
        cuerpo_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
                <h2 style="color: #2c3e50;">Entrega de Expedientes</h2>
                <p>Buenas tardes, {expediente.usuario.nombreCompleto}</p>
                <p>Confirmamos por este medio de haber recibido el expediente {expediente.id} del socio {expediente.socio.nombre} </p>
                <p> Quedando pendiente la revisión de los expedientes para su resguardo o el correo de faltantes. </p>
                <p> Quedo en espera de cualquier duda o comentario. </p>
 
                <p style="font-size: 0.9em; color: #555;">
                    Atentamente,<br>
                    <strong>{usuarioNombre}</strong>
                </p>
                <hr style="border: 0; border-top: 1px solid #eee;">
                <p style="font-size: 0.8em; color: #999; text-align: center;">
                    Este es un mensaje automático, por favor no responda a este correo.
                </p>
            </div>
        </body>
    </html>
    """

    elif observaciones == "N":
        getEstado = Estado.objects.get(nombre='Recepción con observaciones')
        expediente.estatus = getEstado
        expediente.usuarioCredito = request.user
        expediente.save()
        usuarioNombre = expediente.usuarioCredito.nombreCompleto 

        darAlta(expediente,getEstado.nombre,request.user)
        dominio = "http://192.168.0.29:8000/expedientes/editarExpediente/"
        url_final = f"{dominio}{expediente.id}/"
        asunto = f"RECHAZO: Expediente {expediente.id} - {expediente.socio.nombre}"
        seccionesConComentarios = []
        secciones = SeccionesExpediente.objects.filter(expediente=expediente).order_by('tipoDeSeccion', 'pk')

        for seccion in secciones:
            apartados = ApartadoCatalogo.objects.filter(tipoDeSeccion=seccion.tipoDeSeccion).order_by('clave')
            for apartado in apartados:
                registro = RegistroSeccion.objects.filter(seccion=seccion, apartado=apartado).first()

                if registro is not None:
                    if registro.comentarioCredito:
                        seccionesConComentarios.append({
                            'nombreSeccion': str(seccion.tituloSeccion),
                            'claveApartado': str(apartado.clave),
                            'comentario': str(registro.comentarioCredito)
                        })
                        registro.estatus = 'rechazado'
                        registro.save()

        
        comentarios_texto = ""
        for item in seccionesConComentarios:
            comentarios_texto += f"\n- [{item['nombreSeccion']} - {item['claveApartado']}]: {item['comentario']}"



        cuerpo_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
                    <h2 style="color: #2c3e50;">Actualización de estatus del expediente</h2>
                    <p>Estimado usuario,</p>
                    <p>Le informamos que el expediente {expediente.id} del socio {expediente.socio.nombre} - {expediente.socio.numeroKepler} ha sido recepcionado con observaciones.</p>
                    <p>Atte {usuarioNombre}.</p>
                    <div style="margin: 30px 0; text-align: center;">
                        <a href="{url_final}" 
                           style="background-color: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                            Revisar Expediente
                        </a>
                    </div>
                    <div style="background-color: #fdf2f2; border-left: 4px solid #f5c6cb; padding: 15px; margin: 20px 0; border-radius: 4px;">
                        <h4 style="margin-top: 0; color: #a94442;">Detalle de observaciones por sección:</h4>
                        <ul style="margin-bottom: 0; padding-left: 20px;">
        """

        for item in seccionesConComentarios:
            cuerpo_html += f"""
                            <li style="margin-bottom: 10px;">
                                <strong>{item['nombreSeccion']} (Clave: {item['claveApartado']}):</strong> {item['comentario']}
                            </li>
            """

        cuerpo_html += f"""
                        </ul>
                    </div>

                    <hr style="border: 0; border-top: 1px solid #eee;">
                    <p style="font-size: 0.8em; color: #999; text-align: center;">
                        Este es un mensaje automático, por favor no responda a este correo.
                    </p>
                </div>
            </body>
        </html>
        """


    else:
        print("Error")
        
 

    destinatario = [expediente.usuario.email] #,expediente.usuario.email 'daudiffred@ucg.com.mx'  expediente.usuarioCredito.email,
    
    
    
    SMTP_HOST = "ucg.com.mx"
    SMTP_PORT = 587
    USUARIO = "informacion@ucg.com.mx"
    CONTRASENA = "UcG911_@!#"

    mensaje = email.message.EmailMessage()
    mensaje["From"] = USUARIO
    mensaje["To"] = ", ".join(destinatario) if isinstance(destinatario, list) else destinatario
    mensaje["Subject"] = asunto
    
    mensaje.add_alternative(cuerpo_html, subtype="html")

    try:
        servidor = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        servidor.starttls()
        servidor.login(USUARIO, CONTRASENA)
        servidor.send_message(mensaje)
        servidor.quit()
        print("Correo enviado correctamente")
    except Exception as e:
        print("Error al enviar correo:", e)
    return redirect('Index:editarExpediente', expedienteID)

def enviarInvitacionCita(cita, expediente, usuario_accion=None, esCancelacion=False, esSugerencia=False):
    fechaInicio = datetime.combine(cita.dia, cita.hora)
    fechaFin = fechaInicio + timedelta(hours=1)

    cal = Calendar()
    cal.add('prodid', '-//Plataforma de Expedientes//mx//')
    cal.add('version', '2.0')
    
    metodo = 'CANCEL' if esCancelacion else 'REQUEST'
    cal.add('method', metodo)
    
    evento = Event()
    evento.add('dtstart', fechaInicio)
    evento.add('dtend', fechaFin)
    evento.add('dtstamp', datetime.now())
    evento.add('uid', f"cita-{cita.id}-{expediente.id}@plataformaexpedientes.com")
    
    rol_creador = getattr(usuario_accion, 'roles', None) if usuario_accion else None

    if esCancelacion:
        evento.add('status', 'CANCELLED')
        evento.add('summary', f"CANCELACIÓN: CITA PARA ENTREGAR EXPEDIENTE DEL SOCIO: {expediente.socio.numeroKepler} {expediente.socio.nombre.upper()}")
        evento.add('description', "Hola, se ha cancelado la cita que estaba programada para este expediente.")
        asunto = f"CANCELACIÓN: CITA PARA ENTREGAR EXPEDIENTE DEL SOCIO: {expediente.socio.numeroKepler} {expediente.socio.nombre.upper()} -- {cita.dia}"
    else:
        evento.add('status', 'CONFIRMED')
        evento.add('summary', f"CITA PARA ENTREGAR EXPEDIENTE DEL SOCIO: {expediente.socio.numeroKepler} {expediente.socio.nombre.upper()}")
        evento.add('description', "Cita programada para el expediente del socio.")
        
        if esSugerencia:
            asunto = f"Nueva Sugerencia de Cita: {cita.dia} a las {cita.hora} hrs"
            titulo_seccion = "Nueva Propuesta de Horario"
            texto_explicativo = f"Hola, se ha sugerido un cambio de horario para la entrega del expediente del socio <strong>{expediente.socio.numeroKepler} - {expediente.socio.nombre.upper()}</strong> debido a que el horario anterior fue rechazado."
        else:
            asunto = f"Confirmación de Cita: {cita.dia} a las {cita.hora} hrs"
            titulo_seccion = "Confirmación de Cita Programada"
            texto_explicativo = f"Hola, se ha agendado una cita para la entrega del expediente del socio <strong>{expediente.socio.numeroKepler} - {expediente.socio.nombre.upper()}</strong>."

    cal.add_component(evento)
    
    SMTP_HOST = "ucg.com.mx"
    SMTP_PORT = 465
    USUARIO = "informacion@ucg.com.mx"
    CONTRASENA = "UcG911_@!#"
    
    destinatariosCredito = ['portiz@ucg.com.mx', 'dcorrea@ucg.com.mx', 'mrubio@ucg.com.mx'] 
    destinatariosRaw = [
        getattr(getattr(expediente, 'usuarioCredito', None), 'email', None),
        getattr(getattr(expediente, 'usuario', None), 'email', None),
    ]

    destinatarios = list(set([correo for correo in destinatariosRaw + destinatariosCredito if correo]))
    
    # Lista de pruebas
    # destinatarios = ['daudiffred@ucg.com.mx']
    
    if not destinatarios:
        return

    try:
        conexion = get_connection(
            host=SMTP_HOST,
            port=SMTP_PORT,
            username=USUARIO,
            password=CONTRASENA,
            use_tls=False,
            use_ssl=True,
            timeout=10
        )
        
        urlConfirmar = "http://192.168.0.29:8000/expedientes/editarExpediente/Aceptar/"
        urlRechazar = "http://192.168.0.29:8000/expedientes/editarExpediente/Rechazar/"
        url_finalurlConfirmar = f"{urlConfirmar}{expediente.id}"
        url_finalurlurlRechazar = f"{urlRechazar}{expediente.id}"

        for correoDestino in destinatarios:
            if esCancelacion:
                cuerpo = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 5px;">
                    <h2 style="color: #dc3545;">Cancelación de Cita</h2>
                    <p style="color: #555555; font-size: 16px; line-height: 1.5;">
                        Hola, se ha cancelado la cita que estaba programada para la entrega del expediente del socio 
                        <strong>{expediente.socio.numeroKepler} - {expediente.socio.nombre.upper()}</strong>.
                    </p>
                    <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="margin: 5px 0; color: #333333;"><strong>Fecha Cancelada:</strong> {cita.dia}</p>
                        <p style="margin: 5px 0; color: #333333;"><strong>Hora Cancelada:</strong> {cita.hora} hrs</p>
                    </div>
                    <p style="color: #888888; font-size: 12px; margin-top: 30px; text-align: center; border-top: 1px solid #eeeeee; padding-top: 15px;">
                        Este es un correo automático generado por la Plataforma de Expedientes.
                    </p>
                </div>
                """
            else:
                mostrar_botones = True
                if rol_creador in ['Credito', 'Gerente de Credito', 'Gerente de Crédito']:
                    if correoDestino in destinatariosCredito or correoDestino == getattr(getattr(expediente, 'usuarioCredito', None), 'email', None):
                        mostrar_botones = False
                elif rol_creador in ['Ejecutivo de Servicios', 'Gerente Centro de Negocios']:
                    if correoDestino == getattr(getattr(expediente, 'usuario', None), 'email', None) or correoDestino not in destinatariosCredito:
                        if correoDestino != getattr(getattr(expediente, 'usuarioCredito', None), 'email', None):
                            mostrar_botones = False

                if mostrar_botones:
                    bloque_interaccion = f"""
                    <p style="color: #555555; font-size: 15px;">Por favor, responde a esta propuesta interactuando con los siguientes botones:</p>
                    <div style="margin-top: 25px; text-align: center;">
                        <a href="{url_finalurlConfirmar}" style="background-color: #28a745; color: white; padding: 12px 25px; text-decoration: none; font-weight: bold; border-radius: 4px; margin-right: 15px; display: inline-block;">Confirmar Cita</a>
                        <a href="{url_finalurlurlRechazar}" style="background-color: #dc3545; color: white; padding: 12px 25px; text-decoration: none; font-weight: bold; border-radius: 4px; display: inline-block;">Rechazar / Sugerir Cambio</a>
                    </div>
                    """
                else:
                    bloque_interaccion = f"""
                    <p style="color: #666666; font-size: 14px; font-style: italic; background-color: #f0f0f0; padding: 10px; border-radius: 4px; border-left: 4px solid #a0a0a0;">
                        Esperando respuesta de confirmación o cambio por parte de la contraparte del departamento correspondiente.
                    </p>
                    """

                cuerpo = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 5px;">
                    <h2 style="color: #333333;">{titulo_seccion}</h2>
                    <p style="color: #555555; font-size: 16px; line-height: 1.5;">
                        {texto_explicativo}
                    </p>
                    <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="margin: 5px 0; color: #333333;"><strong>Fecha Propuesta:</strong> {cita.dia}</p>
                        <p style="margin: 5px 0; color: #333333;"><strong>Hora Propuesta:</strong> {cita.hora} hrs</p>
                    </div>
                    {bloque_interaccion}
                    <p style="color: #888888; font-size: 12px; margin-top: 30px; text-align: center; border-top: 1px solid #eeeeee; padding-top: 15px;">
                        Este es un correo automático generado por la Plataforma de Expedientes.
                    </p>
                </div>
                """

            email = EmailMessage(
                subject=asunto,
                body=cuerpo,
                from_email=USUARIO,
                to=[correoDestino],
                connection=conexion
            )
            email.content_subtype = "html"
            
            ics_contenido = cal.to_ical().decode('utf-8')
            parte_calendario = SafeMIMEText(ics_contenido, 'calendar', 'utf-8')
            parte_calendario.set_param('method', metodo)
            parte_calendario.set_param('charset', 'UTF-8')
            
            email.attach(parte_calendario)
            email.attach(
                'invitacion-cita.ics',
                cal.to_ical(),
                f'text/calendar; charset=UTF-8; method={metodo}'
            )
            
            email.send()
        
        print("Correos enviados de forma individual correctamente")
        
    except Exception as e:
        print("Error al enviar correo:", e)
@login_required(login_url='/login/')
def asociarCitaExistente(request, expedienteId, citaId):
    if request.method == "POST":
        expediente = get_object_or_404(Expediente, pk=expedienteId)
        cita = get_object_or_404(Cita, pk=citaId)
        cita.expedientes.add(expediente)
        
        enviarInvitacionCita(cita, expediente, usuario_accion=request.user, esCancelacion=False, esSugerencia=False)
        messages.success(request, 'El expediente fue vinculado y se envió la invitación a Outlook.')
        
    return redirect('Index:editarExpediente', expedienteId)


@login_required(login_url='/login/')
def desasociarCitaExistente(request, expedienteId, citaId):
    if request.method == "POST":
        expediente = get_object_or_404(Expediente, pk=expedienteId)
        cita = get_object_or_404(Cita, pk=citaId)
        
        enviarInvitacionCita(cita, expediente, usuario_accion=request.user, esCancelacion=True, esSugerencia=False)
        
        cita.expedientes.remove(expediente)
        
        if not cita.expedientes.exists():
            cita.estatusCN = 'Pendiente'
            cita.estatusCR = 'Pendiente'
            cita.dia = None
            cita.hora = None
            cita.save()
            
        messages.success(request, 'La cita fue desasignada y se envió la notificación de cancelación.')
        
    return redirect('Index:editarExpediente', expedienteId)


@login_required(login_url='/login/')
def rechazarCita(request, id):
    expediente = get_object_or_404(Expediente, pk=id)
    cita = Cita.objects.filter(
        Q(expedientes=expediente),
    ).order_by('dia', 'hora').last()      
    
    if request.method == 'POST':
        form = CitaForm(request.POST, instance=cita, user=request.user)
        if form.is_valid():
            cita_modificada = form.save(commit=False)
            rol_usuario = getattr(request.user, 'roles', None)
            
            if rol_usuario in ['Ejecutivo de Servicios', 'Gerente Centro de Negocios']:
                cita_modificada.estatusCN = 'Aceptada'
                cita_modificada.estatusCR = 'Pendiente'
            elif rol_usuario in ['Credito', 'Gerente de Credito', 'Gerente de Crédito']:
                cita_modificada.estatusCR = 'Aceptada'
                cita_modificada.estatusCN = 'Pendiente'
            
            cita_modificada.save()
            form.save_m2m()
            
            enviarInvitacionCita(cita_modificada, expediente, usuario_accion=request.user, esCancelacion=False, esSugerencia=True)
            return redirect(reverse('Index:editarExpediente', args=[expediente.pk]))
    else:
        form = CitaForm(instance=cita, user=request.user)
        form.fields['expedientes'].widget = forms.MultipleHiddenInput()
        
    context = { 
        'expediente': expediente,
        'cita': cita,
        'form': form,
    }
    return render(request, 'Index/citaRechazada.html', context)


def crearCita(request, id):
    if request.method == "POST":
        cita_form = CitaForm(request.POST)
        if cita_form.is_valid():
            expediente = get_object_or_404(Expediente, pk=id)
            cita = cita_form.save(commit=False)
            cita.usuario = request.user
            
            rol_usuario = getattr(request.user, 'roles', None)
            if rol_usuario in ['Ejecutivo de Servicios', 'Gerente Centro de Negocios']:
                cita.estatusCN = 'Aceptada'
                cita.estatusCR = 'Pendiente'
            elif rol_usuario in ['Credito', 'Gerente de Credito', 'Gerente de Crédito']:
                cita.estatusCR = 'Aceptada'
                cita.estatusCN = 'Pendiente'
                
            cita.save()
            cita_form.save_m2m()
            cita.expedientes.add(expediente)
            
            enviarInvitacionCita(cita, expediente, usuario_accion=request.user, esCancelacion=False, esSugerencia=False)
            
    return redirect('Index:editarExpediente', id)
@login_required(login_url='/login/')

def aceptarCita(request, id):
    expediente = get_object_or_404(Expediente, pk=id)
    usuario = request.user
    cita = Cita.objects.filter(
        Q(expedientes=expediente),
    ).order_by('dia', 'hora').last()  
    
    if usuario.roles in ['Gerente de Credito', 'Credito']:
        cita.estatusCR = 'Aceptada'
    elif usuario.roles in ['Gerente Centro de Negocios', 'Ejecutivo de Servicios']:
        cita.estatusCN = 'Aceptada'
   
    cita.save()
    
    if cita.estatusCR == 'Aceptada' and cita.estatusCN == 'Aceptada':
        enviarCorreoCitaAceptada(cita, expediente)
        
    context = { 
        'expediente': expediente,
        'cita': cita,
    }
    return render(request, 'Index/citaAceptada.html', context)

def enviarCorreoCitaAceptada(cita, expediente):
    asunto = f"Cita Confirmada : {cita.dia} a las {cita.hora} hrs"
    
    cuerpo = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 5px;">
        <h2 style="color: #28a745;">Cita Confirmada</h2>
        <p style="color: #555555; font-size: 16px; line-height: 1.5;">
            Notificamos que ambos departamentos (Crédito y Centro de Negocios) están de acuerdo con el horario para la entrega y revisión del expediente del socio 
            <strong>{expediente.socio.numeroKepler} - {expediente.socio.nombre.upper()}</strong>.
        </p>
        <div style="background-color: #f1fcf4; padding: 15px; border: 1px solid #c3e6cb; border-radius: 5px; margin: 20px 0;">
            <p style="margin: 5px 0; color: #155724;"><strong>Fecha de la Cita:</strong> {cita.dia}</p>
            <p style="margin: 5px 0; color: #155724;"><strong>Hora de la Cita:</strong> {cita.hora} hrs</p>
            <p style="margin: 5px 0; color: #155724;"><strong>Estatus Crédito:</strong> Aceptada</p>
            <p style="margin: 5px 0; color: #155724;"><strong>Estatus Centro de Negocios:</strong> Aceptada</p>
        </div>
        <p style="color: #555555; font-size: 15px;">Este correo sirve como confirmación de que el horario ha quedado formalmente agendado en el sistema.</p>
        <p style="color: #888888; font-size: 12px; margin-top: 30px; text-align: center; border-top: 1px solid #eeeeee; padding-top: 15px;">
            Este es un correo automático generado por la Plataforma de Expedientes.
        </p>
    </div>
    """
    
    SMTP_HOST = "ucg.com.mx"
    SMTP_PORT = 465
    USUARIO = "informacion@ucg.com.mx"
    CONTRASENA = "UcG911_@!#"
    
    destinatariosCredito = ['portiz@ucg.com.mx','dcorrea@ucg.com.mx','mrubio@ucg.com.mx'] 
    destinatariosRaw = [
        getattr(getattr(expediente, 'usuarioCredito', None), 'email', None),
        getattr(getattr(expediente, 'usuario', None), 'email', None),
    ]

    destinatarios = list(set([correo for correo in destinatariosRaw + destinatariosCredito if correo]))
    #destinatarios = ['daudiffred@ucg.com.mx']
    try:
        conexion = get_connection(
            host=SMTP_HOST,
            port=SMTP_PORT,
            username=USUARIO,
            password=CONTRASENA,
            use_tls=False,
            use_ssl=True,
            timeout=10
        )
        
        for correoDestino in destinatarios:
            email = EmailMessage(
                subject=asunto,
                body=cuerpo,
                from_email=USUARIO,
                to=[correoDestino],
                connection=conexion
            )
            email.content_subtype = "html"
            email.send()
        
        print("Correo informativo de confirmación enviado con éxito")
        
    except Exception as e:
        print("Error al enviar correo de aceptación:", e)
         
@login_required(login_url='/login/')
def agregarRenglonExpediente(request, expedienteID, seccionID, apartadoID):
    expediente = get_object_or_404(Expediente, pk=expedienteID)
    seccion_actual = get_object_or_404(SeccionesExpediente, pk=seccionID, expediente=expediente)
    apartado_origen = get_object_or_404(ApartadoCatalogo, pk=apartadoID)

    registros_existentes = RegistroSeccion.objects.filter(
        seccion=seccion_actual,
        apartado=apartado_origen
    )

    registro_origen = registros_existentes.first()
    if not registro_origen:
        return JsonResponse({'ok': False, 'error': 'No hay un renglón base para este apartado.'}, status=400)

    max_secuencial = registros_existentes.aggregate(models.Max('secuencial'))['secuencial__max'] or 0

    nuevo_registro = RegistroSeccion.objects.create(
        seccion=seccion_actual,
        apartado=apartado_origen,
        estatus=registro_origen.estatus,
        comentario=registro_origen.comentario,
        comentarioCredito=registro_origen.comentarioCredito,
        es_fecha=registro_origen.es_fecha,
        secuencial=max_secuencial + 1
    )

    fila = {
        'apartado': apartado_origen,
        'registro': nuevo_registro,
        'fecha_html': '',
        'archivo_url': None,
    }
    html = render_to_string(
        'Index/_fila_expediente.html',
        {
            'fila': fila,
            'item': {'seccion': seccion_actual},
            'expediente': expediente,
        },
        request=request
    )
    return JsonResponse({'ok': True, 'html': html})


@login_required(login_url='/login/')
def eliminarRenglonExpediente(request, expedienteID, seccionID, apartadoID):
    expediente = get_object_or_404(Expediente, pk=expedienteID)
    seccion_actual = get_object_or_404(SeccionesExpediente, pk=seccionID, expediente=expediente)
    apartado_origen = get_object_or_404(ApartadoCatalogo, pk=apartadoID)

    ultimo_registro = RegistroSeccion.objects.filter(
        seccion=seccion_actual,
        apartado=apartado_origen
    ).order_by('-secuencial').first()

    if ultimo_registro and ultimo_registro.secuencial > 1:
        ultimo_registro.delete()
        return JsonResponse({'ok': True})

    return JsonResponse(
        {'ok': False, 'error': 'No es posible eliminar el renglón principal del apartado.'},
        status=400
    )
@login_required(login_url='/login/')
def revisionExpediente(request, expedienteID,observaciones):
    expediente = get_object_or_404(Expediente, pk=expedienteID)
    
  
    if observaciones == "S":
        getEstado = Estado.objects.get(nombre='En revisión')
        expediente.estatus = getEstado
        expediente.save()

        darAlta(expediente,getEstado.nombre,request.user)

    elif observaciones == "N":
        getEstado = Estado.objects.get(nombre='En revisión con observaciones')
        expediente.estatus = getEstado
        expediente.save()
        darAlta(expediente,getEstado.nombre,request.user)
        asunto = f"Expediente en recepción con obersavciones: Expediente {expediente.id} - {expediente.socio.nombre}"
        cuerpo_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
                    <h2 style="color: #2c3e50;">Actualización de estatus del expediente</h2>
                    <p>Estimado usuario,</p>
                    <p>Le informamos que el expediente {expediente.id} del socio {expediente.socio.nombre} - {expediente.socio.numeroKepler} ha sido recepcionado con comentarios.</p>
                    <p>Atte {expediente.usuarioCredito.username}.</p>
                    <div style="margin: 30px 0; text-align: center;">
                        <a href="{url_final}" 
                           style="background-color: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                            Revisar Expediente
                        </a>
                    </div>
                    <div style="background-color: #fdf2f2; border-left: 4px solid #f5c6cb; padding: 15px; margin: 20px 0; border-radius: 4px;">
                        <h4 style="margin-top: 0; color: #a94442;">Detalle de observaciones por sección:</h4>
                        <ul style="margin-bottom: 0; padding-left: 20px;">
        """
    elif observaciones == "R":
        from email.message import EmailMessage

        getEstado = Estado.objects.get(nombre='Recepción con observaciones')
        expediente.estatus = getEstado
        expediente.save()

        darAlta(expediente,getEstado.nombre,request.user)
        asunto = f"RECHAZO EN RECEPCIÓN: Expediente {expediente.id} - {expediente.socio.nombre}"
        cuerpo_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
                    <h2 style="color: #2c3e50;">Actualización de estatus del expediente</h2>
                    <p>Estimado usuario,</p>
                    <p>Le informamos que el expediente {expediente.id} del socio {expediente.socio.nombre} - {expediente.socio.numeroKepler} ha sido rechazado durante su recepción.</p>
                    <p>Atte {expediente.usuarioCredito.username}.</p>
                    <div style="margin: 30px 0; text-align: center;">
                        <a href="{url_final}" 
                           style="background-color: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                            Revisar Expediente
                        </a>
                    </div>
                    <div style="background-color: #fdf2f2; border-left: 4px solid #f5c6cb; padding: 15px; margin: 20px 0; border-radius: 4px;">
                        <h4 style="margin-top: 0; color: #a94442;">Detalle de observaciones por sección:</h4>
                        <ul style="margin-bottom: 0; padding-left: 20px;">
        """
    if observaciones == "R" or observaciones == "N":
        seccionesConComentarios = []
        secciones = SeccionesExpediente.objects.filter(expediente=expediente).order_by('tipoDeSeccion', 'pk')

        for seccion in secciones:
            apartados = ApartadoCatalogo.objects.filter(tipoDeSeccion=seccion.tipoDeSeccion).order_by('clave')
            for apartado in apartados:
                registro = RegistroSeccion.objects.filter(seccion=seccion, apartado=apartado).first()

                if registro is not None:
                    if registro.comentarioCredito:
                        seccionesConComentarios.append({
                            'nombreSeccion': str(seccion.tituloSeccion),
                            'claveApartado': str(apartado.clave),
                            'comentario': str(registro.comentarioCredito)
                        })

        destinatario = [expediente.usuario.email] #expediente.usuarioCredito.email
        #destinatario = ["daudiffred@ucg.com.mx"]    
        dominio = "http://192.168.0.29:8000/expedientes/editarExpediente/"
        url_final = f"{dominio}{expediente.id}/"
        #asunto = f"RECHAZO EN RECEPCIÓN: Expediente {expediente.id} - {expediente.socio.nombre}"

        comentarios_texto = ""
        for item in seccionesConComentarios:
            comentarios_texto += f"\n- [{item['nombreSeccion']} - {item['claveApartado']}]: {item['comentario']}"


        #cuerpo_html = f"""
        #<html>
        #    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        #        <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
        #            <h2 style="color: #2c3e50;">Actualización de estatus del expediente</h2>
        #            <p>Estimado usuario,</p>
        #            <p>Le informamos que el expediente {expediente.id} del socio {expediente.socio.nombre} - {expediente.socio.numeroKepler} ha sido rechazado durante su recepción.</p>
        #            <p>Atte {expediente.usuarioCredito.username}.</p>
        #            <div style="margin: 30px 0; text-align: center;">
        #                <a href="{url_final}" 
        #                   style="background-color: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">
        #                    Revisar Expediente
        #                </a>
        #            </div>
        #            <div style="background-color: #fdf2f2; border-left: 4px solid #f5c6cb; padding: 15px; margin: 20px 0; border-radius: 4px;">
        #                <h4 style="margin-top: 0; color: #a94442;">Detalle de observaciones por sección:</h4>
        #                <ul style="margin-bottom: 0; padding-left: 20px;">
        #"""

        for item in seccionesConComentarios:
            cuerpo_html += f"""
                            <li style="margin-bottom: 10px;">
                                <strong>{item['nombreSeccion']} (Clave: {item['claveApartado']}):</strong> {item['comentario']}
                            </li>
            """

        cuerpo_html += f"""
                        </ul>
                    </div>

                    <hr style="border: 0; border-top: 1px solid #eee;">
                    <p style="font-size: 0.8em; color: #999; text-align: center;">
                        Este es un mensaje automático, por favor no responda a este correo.
                    </p>
                </div>
            </body>
        </html>
        """
        SMTP_HOST = "ucg.com.mx"
        SMTP_PORT = 587
        USUARIO = "informacion@ucg.com.mx"
        CONTRASENA = "UcG911_@!#"

        mensaje = EmailMessage()
        mensaje["From"] = USUARIO
        mensaje["To"] = ", ".join(destinatario) if isinstance(destinatario, list) else destinatario
        mensaje["Subject"] = asunto

        mensaje.add_alternative(cuerpo_html, subtype="html")

        try:
            servidor = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            servidor.starttls()
            servidor.login(USUARIO, CONTRASENA)
            servidor.send_message(mensaje)
            servidor.quit()
            print("Correo enviado correctamente")
        except Exception as e:
            print("Error al enviar correo:", e)
    else:
            print("Error")
        
        
    return redirect('Index:editarExpediente', expedienteID)
@login_required(login_url='/login/')
def lineaEliminar(request, expediente_id, linea_id):
    if request.method == "POST":
        linea = get_object_or_404(Linea, pk=linea_id, expediente_id=expediente_id)
        
        try:
            with transaction.atomic():
                secciones_linea = SeccionesExpediente.objects.filter(linea=linea, expediente_id=expediente_id)
                RegistroSeccion.objects.filter(seccion__in=secciones_linea).delete()
                secciones_linea.delete()
                linea.delete()
                
            messages.success(request, 'Línea de crédito y todos sus apartados asociados fueron eliminados con éxito.')
        except Exception as e:
            messages.error(request, f'Error al eliminar la línea: {str(e)}')
            
        return redirect(reverse('Index:editarExpediente', args=[expediente_id]))
        
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)


def eliminarRepresentante(request,rep,exp):
    try:
        expediente = Expediente.objects.get(id=exp)
        obligado = RepresentanteLegal.objects.get(id=rep)
        
        try:
            seccion_obl = SeccionesExpediente.objects.get(
                expediente=expediente,
                tipoDeSeccion='B',
                tituloSeccion=f"Representante legal - {obligado.nombre}"
            )
            seccion_obl.delete()
        except SeccionesExpediente.DoesNotExist:
            pass

        obligado.expedientes.remove(expediente)

    except (Expediente.DoesNotExist, RepresentanteLegal.DoesNotExist):
        raise Http404

    return redirect(reverse('Index:editarExpediente', args=[expediente.id]))

def eliminarObligado(request, obl, exp):
    try:
        expediente = Expediente.objects.get(id=exp)
        obligado = ObligadoSolidario.objects.get(id=obl)
        
        try:
            seccion_obl = SeccionesExpediente.objects.get(
                expediente=expediente,
                tipoDeSeccion='C',
                tituloSeccion=f"Obligado solidario y garantes - {obligado.nombre}"
            )
            seccion_obl.delete()
        except SeccionesExpediente.DoesNotExist:
            pass

        obligado.expedientes.remove(expediente)

    except (Expediente.DoesNotExist, ObligadoSolidario.DoesNotExist):
        raise Http404

    return redirect(reverse('Index:editarExpediente', args=[expediente.id]))

def checkBoxChange(request, seccion, apartado, secuencial):
    registro = get_object_or_404(
        RegistroSeccion, 
        seccion_id=seccion, 
        apartado_id=apartado, 
        secuencial=secuencial
    )
    registro.enviar = not registro.enviar
    registro.save()
    return JsonResponse({'success': True, 'enviar': registro.enviar})

def notificarFaltantes(request, expedienteID):
    expediente = get_object_or_404(Expediente, pk=expedienteID)

    seccionesConCheckBox = []
    registros_marcados = (
        RegistroSeccion.objects
        .filter(seccion__expediente=expediente, enviar=True)
        .select_related('seccion', 'apartado')
        .order_by('seccion__tipoDeSeccion', 'seccion__pk', 'apartado__clave', 'secuencial')
    )
    for registro in registros_marcados:
        seccionesConCheckBox.append({
            'nombreSeccion': str(registro.seccion.tituloSeccion),
            'claveApartado': str(registro.apartado.clave),
            'secuencial': registro.secuencial,
            'comentario': registro.comentario or '',
        })
    destinatario = [expediente.usuario.email, expediente.usuarioNegocios.email]    
    dominio = "http://192.168.0.29:8000/expedientes/editarExpediente/"
    url_final = f"{dominio}{expediente.id}/"
    asunto = f"Documentos faltantes: Expediente {expediente.socio.numeroKepler} {expediente.socio.nombre}"
    
    cuerpo_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
                <h2 style="color: #2c3e50;">Actualización de estatus del expediente</h2>
                <p>Estimado usuario,</p>
                <p>Le informamos que el expediente del socio {expediente.socio.nombre} {expediente.socio.numeroKepler} requiere ciertos documentos.</p>
                <p>Atte {expediente.usuario.username}.</p>
                <div style="margin: 30px 0; text-align: center;">
                    <a href="{url_final}" 
                       style="background-color: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Revisar Expediente
                    </a>
                </div>
                <div style="background-color: #fdf2f2; border-left: 4px solid #f5c6cb; padding: 15px; margin: 20px 0; border-radius: 4px;">
                    <h4 style="margin-top: 0; color: #a94442;">Detalle de observaciones por sección:</h4>
                    <ul style="margin-bottom: 0; padding-left: 20px;">
    """

    for item in seccionesConCheckBox:
        cuerpo_html += f"""
                        <li style="margin-bottom: 10px;">
                            <strong>{item['nombreSeccion']} (Clave: {item['claveApartado']}):</strong> {item['comentario']}
                        </li>
        """

    cuerpo_html += f"""
                    </ul>
                </div>
            
                <hr style="border: 0; border-top: 1px solid #eee;">
                <p style="font-size: 0.8em; color: #999; text-align: center;">
                    Este es un mensaje automático, por favor no responda a este correo.
                </p>
            </div>
        </body>
    </html>
    """
    SMTP_HOST = "ucg.com.mx"
    SMTP_PORT = 587
    USUARIO = "informacion@ucg.com.mx"
    CONTRASENA = "UcG911_@!#"
    
    mensaje = email.message.EmailMessage()
    mensaje["From"] = USUARIO
    mensaje["To"] = ", ".join(destinatario) if isinstance(destinatario, list) else destinatario
    mensaje["Subject"] = asunto
    
    mensaje.set_content(cuerpo_html, subtype="html")

    # --- ENVÍO DESHABILITADO MIENTRAS SE DEPURA: solo se imprime en la terminal ---
    print("=== CORREO (NO ENVIADO) ===")
    print("Para:", mensaje["To"])
    print("Asunto:", asunto)
    print(f"Registros marcados: {len(seccionesConCheckBox)}")
    for item in seccionesConCheckBox:
        print(f"  - {item['nombreSeccion']} (clave {item['claveApartado']}, renglón {item['secuencial']}): {item['comentario']}")

    try:
         servidor = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
         servidor.starttls()
         servidor.login(USUARIO, CONTRASENA)
         servidor.send_message(mensaje)
         servidor.quit()
         print("Correo enviado correctamente")
    except Exception as e:
         print("Error al enviar correo:", e)
    return redirect('Index:editarExpediente', expediente.id)

@login_required(login_url='/login/')
def procesarArchivos(request, id):
    if request.method != "POST":
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    expediente = get_object_or_404(Expediente, pk=id)
    secciones = SeccionesExpediente.objects.filter(expediente=expediente)
    
    kepler = str(expediente.socio.numeroKepler).strip() if expediente.socio.numeroKepler else "0000"
    nombre_socio = str(expediente.socio.nombre).strip().upper()
    rutaServidor = fr"\\192.168.0.96\intranetucg$$\Evidencias\652 Digitalización de expedientes de crédito"

    def obtener_ruta_larga_windows(ruta):
        try:
            if not ruta.startswith("\\\\"):
                return ruta
            ruta_preparada = "\\\\?\\UNC" + ruta[1:] if not ruta.startswith("\\\\?\\UNC\\") else ruta
            buf = ctypes.create_unicode_buffer(2048)
            get_long_path_name = ctypes.windll.kernel32.GetLongPathNameW
            resultado = get_long_path_name(ruta_preparada, buf, 2048)
            if resultado > 0:
                ruta_larga = buf.value
                if ruta_larga.startswith("\\\\?\\UNC\\"):
                    return "\\\\" + ruta_larga[8:]
                return ruta_larga
        except Exception:
            pass
        return ruta

    carpeta_socio = None
    try:
        ruta_scan = "\\\\?\\UNC" + rutaServidor[1:] if rutaServidor.startswith("\\\\") and not rutaServidor.startswith("\\\\?\\UNC\\") else rutaServidor
        if os.path.exists(ruta_scan):
            for nombre_dir in os.listdir(ruta_scan):
                if kepler != "0000" and kepler in nombre_dir:
                    carpeta_socio = os.path.join(rutaServidor, nombre_dir)
                    break
                elif kepler == "0000" and nombre_socio in nombre_dir.upper():
                    carpeta_socio = os.path.join(rutaServidor, nombre_dir)
                    break
        
        if not carpeta_socio:
            nombre_nueva_carpeta = f"{kepler} {nombre_socio}".strip()
            carpeta_socio = os.path.join(rutaServidor, nombre_nueva_carpeta)
            os.makedirs("\\\\?\\UNC" + carpeta_socio[1:] if carpeta_socio.startswith("\\\\") and not carpeta_socio.startswith("\\\\?\\UNC\\") else carpeta_socio, exist_ok=True)
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error de acceso o creación de carpeta raíz: {str(e)}'}, status=500)

    carpeta_socio = obtener_ruta_larga_windows(carpeta_socio)
    rutaMaestra = os.path.join(carpeta_socio, "Maestra")
    rutaOperativa = os.path.join(carpeta_socio, "Operativa")

    mapeo_secciones = {
        "1": os.path.join(rutaMaestra, "I. Identificación del Socio"),
        "2": os.path.join(rutaMaestra, "II. Información Financiera"),
        "3": os.path.join(rutaOperativa, "III. Estudio de Crédito"),
        "4": os.path.join(rutaOperativa, "IV. Información de garantias"),
        "5": os.path.join(rutaOperativa, "V. Contratos"),
        "6": os.path.join(rutaOperativa, "VI. Seguimiento"),
        "7": os.path.join(rutaOperativa, "VII. Correspondencia")
    }
    
    meses_map = {
        "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
        "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12
    }
    
    meses_inv_map = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }

    archivos = request.FILES.getlist('archivos_pdf')
    resultados_proceso = []

    registros_validos = RegistroSeccion.objects.filter(seccion__in=secciones).select_related('apartado')
    mapeo_claves_registro = {}
    for r in registros_validos:
        clave_limpia = str(r.apartado.clave).strip()
        mapeo_claves_registro[clave_limpia] = r

    for f in archivos:
        nombre_archivo = f.name
        nombre_sin_ext, ext = os.path.splitext(nombre_archivo)
        
        partes_nombre = nombre_sin_ext.strip().split(' ')
        if not partes_nombre or partes_nombre[0] == "":
            resultados_proceso.append({'archivo': nombre_archivo, 'success': False, 'mensaje': 'Nombre inválido'})
            continue
            
        linea_detectada_num = None
        clave_detectada = None

        if '.' not in partes_nombre[0]:
            linea_detectada_num = partes_nombre[0].strip()
            if len(partes_nombre) > 1 and '.' in partes_nombre[1]:
                clave_detectada = partes_nombre[1].strip().rstrip('.')
            else:
                resultados_proceso.append({'archivo': nombre_archivo, 'success': False, 'mensaje': 'Estructura de clave x.xx no encontrada tras número de línea'})
                continue
        else:
            clave_detectada = partes_nombre[0].strip().rstrip('.')

        partes_c = clave_detectada.split('.')
        if len(partes_c) == 2 and len(partes_c[1]) >= 3:
            clave_destino_carpeta = f"{partes_c[0]}.{partes_c[1][:2]}"
        else:
            clave_destino_carpeta = clave_detectada

        prefijo = clave_destino_carpeta.split('.')[0]
        
        ruta_destino_base = mapeo_secciones.get(prefijo)
        if not ruta_destino_base:
            resultados_proceso.append({'archivo': nombre_archivo, 'success': False, 'mensaje': f'Clave "{clave_detectada}" no mapea a Maestra/Operativa'})
            continue

        ruta_destino_base = obtener_ruta_larga_windows(ruta_destino_base)

        if prefijo in ["3", "4", "5", "6", "7"]:
            if linea_detectada_num:
                lineas_asociadas = Linea.objects.filter(expediente=expediente, numero=linea_detectada_num)
            else:
                lineas_asociadas = Linea.objects.filter(expediente=expediente)

            if lineas_asociadas.exists():
                rutaOperativa_larga = obtener_ruta_larga_windows(rutaOperativa)
                chk_operativa = "\\\\?\\UNC" + rutaOperativa_larga[1:] if rutaOperativa_larga.startswith("\\\\") and not rutaOperativa_larga.startswith("\\\\?\\UNC\\") else rutaOperativa_larga
                os.makedirs(chk_operativa, exist_ok=True)
                try:
                    subdirs_operativa = os.listdir(chk_operativa)
                    encontrado = False
                    
                    for linea in lineas_asociadas:
                        num_kepler = str(expediente.socio.numeroKepler).strip()
                        if num_kepler == "" or num_kepler == "0000" or num_kepler == "0" or expediente.socio.numeroKepler is None:
                            prefijo_linea = f"{linea.numero} CS"
                        else:
                            prefijo_linea = f"{linea.numero} {num_kepler} CS"
                        
                        for subdir in subdirs_operativa:
                            if subdir.strip().startswith(prefijo_linea):
                                ruta_subdir_completa = os.path.join(rutaOperativa_larga, subdir)
                                ruta_subdir_completa = obtener_ruta_larga_windows(ruta_subdir_completa)
                                chk_subdir = "\\\\?\\UNC" + ruta_subdir_completa[1:] if ruta_subdir_completa.startswith("\\\\") and not ruta_subdir_completa.startswith("\\\\?\\UNC\\") else ruta_subdir_completa
                                if os.path.isdir(chk_subdir):
                                    nombre_carpeta_seccion = os.path.basename(ruta_destino_base)
                                    ruta_destino_base = os.path.join(ruta_subdir_completa, nombre_carpeta_seccion)
                                    encontrado = True
                                    break
                        if encontrado:
                            break
                    
                    if not encontrado:
                        linea_primera = lineas_asociadas.first()
                        num_l = str(linea_primera.numero).strip()
                        abrev_l = str(linea_primera.abreviacion).strip() if linea_primera.abreviacion else ""
                        monto_l = f"{linea_primera.monto:,}"
                        
                        fecha_str = ""
                        if linea_primera.fecha:
                            m_str = meses_inv_map.get(linea_primera.fecha.month, "")
                            y_str = linea_primera.fecha.strftime("%Y")
                            fecha_str = f"{m_str} {y_str}".strip()
                        
                        num_kepler = str(expediente.socio.numeroKepler).strip()
                        if num_kepler == "" or num_kepler == "0000" or num_kepler == "0" or expediente.socio.numeroKepler is None:
                            nombre_nueva_linea_dir = f"{num_l} {abrev_l} ${monto_l} {fecha_str}".strip()
                        else:
                            nombre_nueva_linea_dir = f"{num_l} {num_kepler} {abrev_l} ${monto_l} {fecha_str}".strip()
                            
                        ruta_nueva_linea_completa = os.path.join(rutaOperativa_larga, nombre_nueva_linea_dir)
                        ruta_nueva_linea_completa = obtener_ruta_larga_windows(ruta_nueva_linea_completa)
                        chk_nueva_linea = "\\\\?\\UNC" + ruta_nueva_linea_completa[1:] if ruta_nueva_linea_completa.startswith("\\\\") and not ruta_nueva_linea_completa.startswith("\\\\?\\UNC\\") else ruta_nueva_linea_completa
                        os.makedirs(chk_nueva_linea, exist_ok=True)
                        
                        nombre_carpeta_seccion = os.path.basename(mapeo_secciones.get(prefijo))
                        ruta_destino_base = os.path.join(ruta_nueva_linea_completa, nombre_carpeta_seccion)
                        
                except Exception:
                    pass

        registro_asociado = mapeo_claves_registro.get(clave_detectada)
        if not registro_asociado and len(partes_c) == 2 and len(partes_c[1]) >= 2:
            clave_truncada = f"{partes_c[0]}.{partes_c[1][:2]}"
            registro_asociado = mapeo_claves_registro.get(clave_truncada)

        if not registro_asociado:
            resultados_proceso.append({'archivo': nombre_archivo, 'success': False, 'mensaje': f'No hay renglón en base de datos para la clave {clave_detectada}'})
            continue

        if registro_asociado.estatus and registro_asociado.estatus != "":
            ultimo_secuencial = RegistroSeccion.objects.filter(
                seccion=registro_asociado.seccion,
                apartado=registro_asociado.apartado
            ).aggregate(max_sec=models.Max('secuencial'))['max_sec'] or 1
            
            registro_asociado = RegistroSeccion.objects.create(
                seccion=registro_asociado.seccion,
                apartado=registro_asociado.apartado,
                es_fecha=registro_asociado.es_fecha,
                secuencial=ultimo_secuencial + 1,
                comentario=registro_asociado.comentario,
                comentarioCredito=registro_asociado.comentarioCredito,
                enviar=registro_asociado.enviar
            )

        fecha_procesada = None
        ultimo_string_num = partes_nombre[-1].strip()

        if len(partes_nombre) >= 2:
            posible_fecha_str = f"{partes_nombre[-2]} {partes_nombre[-1]}".strip().lower()
            match_fecha = re.search(r'([a-z]{3})\s+(\d{2})$', posible_fecha_str)
            if match_fecha:
                mes_texto = match_fecha.group(1)
                anio_texto = match_fecha.group(2)
                if mes_texto in meses_map:
                    try:
                        fecha_procesada = datetime(int(f"20{anio_texto}"), meses_map[mes_texto], 1).date()
                    except ValueError:
                        pass

        if not fecha_procesada:
            ultimo_bloque = partes_nombre[-1].strip().lower()
            match_fecha_unico = re.search(r'([a-z]{3})\s+(\d{2})$', ultimo_bloque)
            if match_fecha_unico:
                mes_texto = match_fecha_unico.group(1)
                anio_texto = match_fecha_unico.group(2)
                if mes_texto in meses_map:
                    try:
                        fecha_procesada = datetime(int(f"20{anio_texto}"), meses_map[mes_texto], 1).date()
                    except ValueError:
                        pass

        try:
            ruta_destino_base = obtener_ruta_larga_windows(ruta_destino_base)
            chk_destino_base = "\\\\?\\UNC" + ruta_destino_base[1:] if ruta_destino_base.startswith("\\\\") and not ruta_destino_base.startswith("\\\\?\\UNC\\") else ruta_destino_base
            os.makedirs(chk_destino_base, exist_ok=True)
            
            carpeta_destino_final = None
            for item in os.listdir(chk_destino_base):
                ruta_item = os.path.join(ruta_destino_base, item)
                ruta_item = obtener_ruta_larga_windows(ruta_item)
                chk_item = "\\\\?\\UNC" + ruta_item[1:] if ruta_item.startswith("\\\\") and not ruta_item.startswith("\\\\?\\UNC\\") else ruta_item
                if os.path.isdir(chk_item):
                    item_clean = item.strip()
                    if item_clean.startswith(clave_destino_carpeta + " ") or item_clean.startswith(clave_destino_carpeta + ".") or item_clean == clave_destino_carpeta:
                        carpeta_destino_final = ruta_item
                        break
            
            if not carpeta_destino_final:
                nombre_personalizado_cat = registro_asociado.apartado.nombreArchivo
                if nombre_personalizado_cat and nombre_personalizado_cat.strip():
                    nombre_carpeta = f"{clave_destino_carpeta} {nombre_personalizado_cat.strip()}"
                else:
                    nombre_carpeta = clave_destino_carpeta
                    
                carpeta_destino_final = os.path.join(ruta_destino_base, nombre_carpeta)
                carpeta_destino_final = obtener_ruta_larga_windows(carpeta_destino_final)
                chk_destino_final = "\\\\?\\UNC" + carpeta_destino_final[1:] if carpeta_destino_final.startswith("\\\\") and not carpeta_destino_final.startswith("\\\\?\\UNC\\") else carpeta_destino_final
                os.makedirs(chk_destino_final, exist_ok=True)
            
            nombre_sin_ext_limpio = nombre_sin_ext
            if linea_detectada_num and nombre_sin_ext_limpio.startswith(linea_detectada_num + " "):
                nombre_sin_ext_limpio = nombre_sin_ext_limpio[len(linea_detectada_num):].strip()

            nombre_final_archivo = f"{nombre_sin_ext_limpio}{ext}"
            if prefijo in ["3", "4", "5", "6", "7"] and registro_asociado.numero:
                str_numero = str(registro_asociado.numero).strip()
                if str_numero in nombre_sin_ext_limpio:
                    nombre_sin_ext_limpio = nombre_sin_ext_limpio.replace(str_numero, "").replace("  ", " ").strip()
                    nombre_final_archivo = f"{nombre_sin_ext_limpio}{ext}"

            ruta_completa_archivo = os.path.join(carpeta_destino_final, nombre_final_archivo)
            ruta_completa_archivo = obtener_ruta_larga_windows(ruta_completa_archivo)
            chk_completa_archivo = "\\\\?\\UNC" + ruta_completa_archivo[1:] if ruta_completa_archivo.startswith("\\\\") and not ruta_completa_archivo.startswith("\\\\?\\UNC\\") else ruta_completa_archivo
            
            with open(chk_completa_archivo, 'wb+') as destination:
                for chunk in f.chunks():
                    destination.write(chunk)
            
            if fecha_procesada:
                registro_asociado.es_fecha = True
                registro_asociado.fecha = fecha_procesada
                registro_asociado.numero = None
                msg_exito = f'Copiado y enlazado con fecha {fecha_procesada.strftime("%b %y")}'
            else:
                registro_asociado.es_fecha = False
                registro_asociado.fecha = None
                registro_asociado.numero = str(ultimo_string_num)
                msg_exito = f'Copiado y enlazado con parámetro numérico: {ultimo_string_num}'

            if not registro_asociado.estatus or registro_asociado.estatus == "":
                registro_asociado.estatus = "ok"
            registro_asociado.save()
                    
            resultados_proceso.append({'archivo': nombre_final_archivo, 'success': True, 'mensaje': msg_exito})
        except Exception as e:
            resultados_proceso.append({'archivo': nombre_archivo, 'success': False, 'mensaje': f'Error en escritura: {str(e)}'})

    return JsonResponse({
        'global_success': any(r['success'] for r in resultados_proceso),
        'resultados': resultados_proceso
    })


def _to_unc(ruta):
    """Convierte una ruta \\\\servidor\\... a formato largo \\\\?\\UNC\\servidor\\...
    (necesario en Windows para rutas largas)."""
    if ruta.startswith("\\\\") and not ruta.startswith("\\\\?\\UNC\\"):
        return "\\\\?\\UNC" + ruta[1:]
    return ruta


def _match_fecha(registro, arch_norm, meses_es, indent="      "):
    """
    Determina si un archivo coincide con la FECHA del registro.

    Regla estricta: solo aplica si registro.es_fecha == True y registro.fecha
    existe y se puede parsear. El patrón buscado es "<mes_texto><año 2 dígitos>"
    (ej. "may26") permitiendo espacios entre ambos, tal como en
    "1.01 conoce a tu socio may 26".

    NOTA: si tus archivos usan formato numérico tipo "15/05/2026" en vez de
    "may 26", agrega ese patrón aquí (ver comentario más abajo).
    """
    if not (registro.es_fecha and registro.fecha):
        #print(f"{indent}[FECHA] registro.es_fecha=False o sin fecha asignada -> no aplica")
        return False

    fecha_obj = registro.fecha
    if isinstance(fecha_obj, str):
        parsed = False
        for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d"):
            try:
                fecha_obj = datetime.strptime(fecha_obj.strip(), fmt)
                parsed = True
                break
            except ValueError:
                continue
        if not parsed:
            #print(f"{indent}[FECHA] No se pudo parsear '{registro.fecha}' -> no aplica")
            return False

    mes_texto = meses_es.get(fecha_obj.month, "").lower()
    anio_dos_digitos = fecha_obj.strftime("%y")

    # Patrón 1: "may26" / "may 26" (mes en texto + año 2 dígitos)
    patron_texto = rf"{mes_texto}\s*{anio_dos_digitos}\b"

    # Patrón 2 (opcional): fecha numérica tipo dd/mm/aaaa o dd-mm-aaaa,
    # útil si algunos archivos usan "15/05/2026" en vez de "may 26".
    dia = fecha_obj.strftime("%d")
    mes_num = fecha_obj.strftime("%m")
    anio_completo = fecha_obj.strftime("%Y")
    patron_numerico = rf"{dia}[\/\-\s]{mes_num}[\/\-\s]{anio_completo}"

    #print(f"{indent}[FECHA] Buscando '{mes_texto} {anio_dos_digitos}' (regex texto: {patron_texto}) "          f"o '{dia}/{mes_num}/{anio_completo}' (regex numérico: {patron_numerico}) en '{arch_norm}'")

    if re.search(patron_texto, arch_norm):
        #print(f"{indent}[FECHA] \u2714 Coincidencia por patrón de texto (mes+año)")
        return True

    if re.search(patron_numerico, arch_norm):
        #print(f"{indent}[FECHA] \u2714 Coincidencia por patrón numérico (dd/mm/aaaa)")
        return True

    #print(f"{indent}[FECHA] \u2718 Sin coincidencia de fecha")
    return False


def _match_identificador(registro, arch_norm, indent="      "):
    """
    Determina si un archivo coincide con el NÚMERO/IDENTIFICADOR del registro.

    Regla estricta: solo aplica si registro.es_fecha == False. El valor de
    registro.numero (o registro.identificador si existiera) debe aparecer
    literalmente en el nombre del archivo, ej. "ggpt" en
    "1.01 conoce a tu socio ggpt".
    """
    if registro.es_fecha:
        #print(f"{indent}[ID] registro.es_fecha=True -> este registro se valida por fecha, no por identificador")
        return False

    criterio_val = None
    if registro.numero:
        criterio_val = re.sub(r'\s+', ' ', str(registro.numero).strip()).lower()
    elif hasattr(registro, 'identificador') and registro.identificador:
        criterio_val = re.sub(r'\s+', ' ', str(registro.identificador).strip()).lower()

    if not criterio_val:
        #print(f"{indent}[ID] Registro sin numero/identificador asignado -> no aplica")
        return False

    #print(f"{indent}[ID] Buscando identificador '{criterio_val}' en '{arch_norm}'")
    if criterio_val in arch_norm:
        #print(f"{indent}[ID] \u2714 Coincidencia por identificador")
        return True

    #print(f"{indent}[ID] \u2718 Sin coincidencia de identificador")
    return False


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def checarRuta(identificador_socio, secciones):

    rutaServidor = fr"\\192.168.0.96\intranetucg$$\Evidencias\652 Digitalización de expedientes de crédito"

    #print(f"\n{'='*80}\n[INICIO] checarRuta(identificador_socio='{identificador_socio}', secciones={secciones})\n{'='*80}")

    carpeta_socio = None
    try:
        ruta_scan = _to_unc(rutaServidor)
        #print(f"[1] Escaneando servidor raíz: {ruta_scan}")
        dirs_servidor = os.listdir(ruta_scan)
        for nombre_dir in dirs_servidor:
            if identificador_socio in nombre_dir:
                carpeta_socio = os.path.join(rutaServidor, nombre_dir)
                #print(f"[1] \u2714 Carpeta de socio encontrada: {carpeta_socio}")
                break
        if not carpeta_socio:
            #print(f"[1] \u2718 Ningún directorio contiene '{identificador_socio}' en el servidor")
            pass
    except Exception as e:
        #print(f"[1] \u2718 ERROR al listar el servidor: {e}")
        return {}

    if not carpeta_socio:
        #print("[FIN] No se encontró carpeta de socio -> se retorna {}")
        return {}

    rutaMaestra = os.path.join(carpeta_socio, "Maestra")
    rutaOperativa = os.path.join(carpeta_socio, "Operativa")

    mapeo_secciones = {
        "1": os.path.join(rutaMaestra, "I. Identificación del Socio"),
        "2": os.path.join(rutaMaestra, "II. Información Financiera"),
        "3": os.path.join(rutaOperativa, "III. Estudio de Crédito"),
        "4": os.path.join(rutaOperativa, "IV. Información de garantias"),
        "5": os.path.join(rutaOperativa, "V. Contratos"),
        "6": os.path.join(rutaOperativa, "VI. Seguimiento"),
        "7": os.path.join(rutaOperativa, "VII. Correspondencia")
    }

    meses_es = {
        1: "ene", 2: "feb", 3: "mar", 4: "abr", 5: "may", 6: "jun",
        7: "jul", 8: "ago", 9: "sep", 10: "oct", 11: "nov", 12: "dic"
    }

    resultados = {}

    for seccion in secciones:
        #print(f"\n[2] --- Procesando sección: {seccion} ---")
        registros_existentes = RegistroSeccion.objects.filter(seccion=seccion).select_related(
            'apartado', 'seccion__expediente'
        )
        #print(f"[2] {registros_existentes.count()} registro(s) encontrados en BD para esta sección")

        for registro in registros_existentes:
            #print(f"\n  [3] Registro id={registro.id} | clave={registro.apartado.clave} | "                  f"es_fecha={registro.es_fecha} | fecha={registro.fecha} | numero={registro.numero}")

            clave = str(registro.apartado.clave).strip()
            partes_c = clave.split('.')
            if len(partes_c) == 2 and len(partes_c[1]) == 3:
                clave_busqueda = f"{partes_c[0]}.{partes_c[1][:2]}"
            else:
                clave_busqueda = clave
            #print(f"  [3] clave_busqueda normalizada: '{clave_busqueda}'")

            prefijo = clave_busqueda.split('.')[0]
            ruta_base_seccion = mapeo_secciones.get(prefijo)

            if not ruta_base_seccion:
                #print(f"  [3] \u2718 Prefijo '{prefijo}' no está en mapeo_secciones -> se omite registro")
                continue

            #print(f"  [4] Ruta base de la sección: {ruta_base_seccion}")

            # ---- Construir TODAS las rutas candidatas (una por cada línea del expediente) ----
            rutas_candidatas = [ruta_base_seccion]

            if prefijo in ["3", "4", "5", "6", "7"]:
                rutas_candidatas = []
                try:
                    expediente_actual = registro.seccion.expediente
                    lineas_asociadas = Linea.objects.filter(expediente=expediente_actual)
                    #print(f"  [4] Líneas asociadas al expediente: {[l.numero for l in lineas_asociadas]}")

                    chk_operativa = _to_unc(rutaOperativa)
                    if os.path.exists(chk_operativa):
                        subdirs_operativa = os.listdir(chk_operativa)
                        nombre_carpeta_seccion = os.path.basename(ruta_base_seccion)

                        for linea in lineas_asociadas:
                            prefijo_linea_solo = f"{str(linea.numero).strip()} "
                            for subdir in subdirs_operativa:
                                if subdir.strip().startswith(prefijo_linea_solo):
                                    posible_ruta = os.path.join(rutaOperativa, subdir, nombre_carpeta_seccion)
                                    if posible_ruta not in rutas_candidatas:
                                        rutas_candidatas.append(posible_ruta)
                                        #print(f"  [4] \u2714 Línea '{linea.numero}' -> carpeta '{subdir}' -> " f"candidata: {posible_ruta}")
                    else:
                        #print(f"  [4] \u2718 Ruta Operativa no existe en disco: {chk_operativa}")
                        pass
                    if not rutas_candidatas:
                        #print(f"  [4] \u2718 Ninguna carpeta de línea coincide; se usará la ruta base de la sección")
                        rutas_candidatas = [ruta_base_seccion]
                except Exception as e_enrutamiento:
                    #print(f"  [4] \u2718 EXCEPCIÓN durante enrutamiento por línea: {e_enrutamiento}")
                    rutas_candidatas = [ruta_base_seccion]

            archivo_mas_reciente = None
            mtime_maximo = 0
            clave_normalizada = clave_busqueda.lower()

            # ---- Escanear cada ruta candidata y quedarse con el archivo más reciente ----
            for ruta_final_busqueda in rutas_candidatas:
                chk_busqueda = _to_unc(ruta_final_busqueda)
                #print(f"  [5] Ruta a escanear: {chk_busqueda}")

                if not os.path.exists(chk_busqueda):
                    #print(f"  [5] \u2718 La ruta no existe en disco -> se omite esta candidata")
                    continue

                try:
                    items_directorio = os.listdir(chk_busqueda)
                    #print(f"  [6] {len(items_directorio)} elemento(s) en el directorio")

                    # ¿Existe una subcarpeta que empiece con la clave? (ej. "3.02 Cat res")
                    for item in items_directorio:
                        if item.lower().strip().startswith(clave_normalizada):
                            posible_sub_carpeta = os.path.join(ruta_final_busqueda, item)
                            chk_sub_carpeta = _to_unc(posible_sub_carpeta)
                            if os.path.isdir(chk_sub_carpeta):
                                #print(f"  [6] La clave corresponde a una subcarpeta: {item} -> se entra a ella")
                                ruta_final_busqueda = posible_sub_carpeta
                                chk_busqueda = chk_sub_carpeta
                                items_directorio = os.listdir(chk_busqueda)
                                break

                    for nombre_item in items_directorio:
                        ruta_item = os.path.join(ruta_final_busqueda, nombre_item)
                        nombre_item_clean = nombre_item.strip()
                        item_normalizado = re.sub(r'\s+', ' ', nombre_item_clean).lower()

                        if not item_normalizado.startswith(clave_normalizada):
                            continue

                        #print(f"  [7] Elemento con la clave correcta: '{nombre_item}'")

                        archivos_a_evaluar = []
                        chk_item = _to_unc(ruta_item)

                        if os.path.isdir(chk_item):
                            try:
                                sub_items = os.listdir(chk_item)
                                for sub_item in sub_items:
                                    archivos_a_evaluar.append((sub_item, os.path.join(ruta_item, sub_item)))
                                #print(f"  [7] Es carpeta, contiene {len(sub_items)} archivo(s) a evaluar")
                            except Exception as e:
                                #print(f"  [7] \u2718 No se pudo listar subcarpeta: {e}")
                                pass
                        else:
                            archivos_a_evaluar.append((nombre_item, ruta_item))

                        for nombre_arch, ruta_arch in archivos_a_evaluar:
                            arch_norm = re.sub(r'\s+', ' ', nombre_arch.strip()).lower()

                            if not arch_norm.startswith(clave_normalizada):
                                continue

                            #print(f"    -> Evaluando archivo: '{nombre_arch}'")

                            # --- REGLA ESTRICTA: solo fecha O solo identificador, según es_fecha ---
                            if registro.es_fecha:
                                coincide = _match_fecha(registro, arch_norm, meses_es)
                            else:
                                coincide = _match_identificador(registro, arch_norm)

                            if not coincide:
                                #print(f"    -> \u2718 Archivo descartado (sin fecha/identificador válido)")
                                continue

                            try:
                                chk_arch = _to_unc(ruta_arch)
                                mtime = os.path.getmtime(chk_arch)
                                #print(f"    -> \u2714 Archivo válido, mtime={datetime.fromtimestamp(mtime)}")
                                if mtime > mtime_maximo:
                                    mtime_maximo = mtime
                                    archivo_mas_reciente = ruta_arch
                            except Exception as e:
                                #print(f"    -> \u2718 No se pudo obtener mtime: {e}")
                                pass
                except Exception as e:
                   # print(f"  [6] \u2718 EXCEPCIÓN escaneando {chk_busqueda}: {e}")
                    
                    continue

            if archivo_mas_reciente:
                #print(f"  [8] \u2714 RESULTADO: archivo más reciente = {archivo_mas_reciente}")
                resultados[registro.id] = {
                    'clave': clave,
                    'ruta': archivo_mas_reciente,
                    'fecha_modificacion': datetime.fromtimestamp(mtime_maximo)
                }
            else:
                #print(f"  [8] \u2718 RESULTADO: ningún archivo cumplió fecha/identificador estricto "                      f"-> registro {registro.id} sin ruta")
                pass
    #print(f"\n[FIN] Total de registros con archivo encontrado: {len(resultados)} de " f"{sum(RegistroSeccion.objects.filter(seccion=s).count() for s in secciones)}")
    return resultados


@login_required(login_url='/login/')
def avancesMovimientos(request):
    expedientes = Expediente.objects.select_related('socio', 'estatus').prefetch_related(
        Prefetch(
            'estadosfechas_set',
            queryset=EstadosFechas.objects.select_related('estado').order_by('fecha'),
            to_attr='lista_estados'
        )
    ).order_by('socio__nombre')

    for exp in expedientes:
        estados = exp.lista_estados
        total = len(estados)
        for i in range(total):
            if i < total - 1:
                estados[i].dias_siguiente = (estados[i+1].fecha - estados[i].fecha).days
            else:
                estados[i].dias_siguiente = None

    context = {
        'expedientes': expedientes,
    }

    return render(request, 'Index/avancesMovimientos.html', context)

def correoArchivado(expediente, porcentajeLlenado):
    porcentajeLlenado = float(porcentajeLlenado)

    if porcentajeLlenado < 50:
        color_porcentaje = "#dc3545"
    elif porcentajeLlenado < 100:
        color_porcentaje = "#ffc107"
    else:
        color_porcentaje = "#198754"
    seccionesConComentarios = []
    secciones = SeccionesExpediente.objects.filter(expediente=expediente).order_by('tipoDeSeccion', 'pk')
        
    for seccion in secciones:
            apartados = ApartadoCatalogo.objects.filter(tipoDeSeccion=seccion.tipoDeSeccion).order_by('clave')
            for apartado in apartados:
                registro = RegistroSeccion.objects.filter(seccion=seccion, apartado=apartado).first()
                
                if registro is not None:
                    if registro.comentarioCredito:
                        registro.estatus = 'pendiente'
                        registro.save()
                        seccionesConComentarios.append({
                                'nombreSeccion': str(seccion.tituloSeccion),
                                'claveApartado': str(apartado.clave),
                                'comentarioCredito' : str(registro.comentarioCredito),
                        })
    
    tiene_pendientes = len(seccionesConComentarios) > 0
    
    comentarios_html = ""
    if tiene_pendientes:
        for item in seccionesConComentarios:
            comentarios_html += f"""
                            <li style="margin-bottom: 10px;">
                                <strong>{item['nombreSeccion']} (Clave: {item['claveApartado']}):</strong> {item['comentarioCredito']}
                            </li>
            """

    destinatario = {
        email for email in [
            "bvillanueva@ucg.com.mx",
            expediente.usuario.email,
            expediente.usuarioNegocios.email,
            "pOrtiz@ucg.com.mx",
            "dCorrea@ucg.com.mx",
            "mRubio@ucg.com.mx",
            "dAudiffred@ucg.com.mx"
        ] if email
    }
    dominio = "http://192.168.0.29:8000/expedientes/editarExpediente/"
    urlFinal = f"{dominio}{expediente.id}/"
    
    usuarioNombre = expediente.usuarioCredito.username 
    if tiene_pendientes:
        asunto = "Expediente Archivado con Observaciones"
    else:
        asunto = "Expediente Archivado"
    
    bloque_pendientes = ""
    if tiene_pendientes:
        bloque_pendientes = f"""
                <div style="margin: 20px 0; padding: 15px; background-color: #fff3cd; border: 1px solid #ffeeba; border-radius: 8px;">
                    <h3 style="color: #856404; margin-top: 0;">Registros Pendientes / Informativos:</h3>
                    <ul style="padding-left: 20px; color: #856404;">
                        {comentarios_html}
                    </ul>
                </div>
        """

    cuerpoHtml = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
                <h2 style="color: #2c3e50;">Expediente Archivado</h2>
                <p>Estimado usuario,</p>
                <p>Le informamos que el expediente <strong>{expediente.numeroKepler}</strong> correspondiente al socio <strong>{expediente.socio.nombre}</strong> ha sido archivado exitosamente.</p>
                
                <div style="margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-radius: 8px; text-align: center;">
                    <span style="font-size: 0.9em; color: #6c757d; font-weight: bold; display: block;">PORCENTAJE DE COMPLETADO</span>
                    <span style="font-size: 1.8em; font-weight: bold; color: {color_porcentaje};">{porcentajeLlenado}%</span>
                </div>

                {bloque_pendientes}

                <div style="margin: 30px 0; text-align: center;">
                    <a href="{urlFinal}" 
                       style="background-color: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Revisar Expediente
                    </a>
                </div>
                <p style="font-size: 0.9em; color: #555;">
                    Atentamente,<br>
                    <strong>{usuarioNombre}</strong>
                </p>
                <hr style="border: 0; border-top: 1px solid #eee;">
                <p style="font-size: 0.8em; color: #999; text-align: center;">
                    Este es un mensaje automático, por favor no responda a este correo.
                </p>
            </div>
        </body>
    </html>
    """
    SMTP_HOST = "ucg.com.mx"
    SMTP_PORT = 587
    USUARIO = "informacion@ucg.com.mx"
    CONTRASENA = "UcG911_@!#"

    mensaje = email.message.EmailMessage()
    mensaje["From"] = USUARIO
    mensaje["To"] = ", ".join(destinatario)
    mensaje["Subject"] = asunto
    
    mensaje.add_alternative(cuerpoHtml, subtype="html")

    try:
        servidor = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        servidor.starttls()
        servidor.login(USUARIO, CONTRASENA)
        servidor.send_message(mensaje)
        servidor.quit()
        print("Correo enviado correctamente")
    except Exception as e:
        print("Error al enviar correo:", e)

def archivarExpediente(request, id,porcentajeLlenado):
    expediente = get_object_or_404(Expediente, pk=id)
    correoArchivado(expediente,porcentajeLlenado)
    getEstado = get_object_or_404(Estado, nombre='Archivado')
    expediente.usuarioArchivo = request.user
    expediente.fechaArchivado = timezone.now()
    expediente.estatus = getEstado
    expediente.save()

    darAlta(expediente, getEstado.nombre, request.user)

    return redirect('Index:editarExpediente', expediente.id)

def generarLista(request):
    response = HttpResponse(content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="lista_expedientes.txt"'

    expedientes = Expediente.objects.all()

    lineas = []
    for e in expedientes:
        nombre_socio = getattr(e.socio, 'nombre', 'Sin Nombre')
        
        numero_kepler = getattr(e.socio, 'numeroKepler', None)
        if not numero_kepler:
            numero_kepler = '0000'

        linea = f"{nombre_socio}, {numero_kepler}\n"
        lineas.append(linea)

    response.writelines(lineas)
    return response

def cambiarAtrasado(request, id):
    exp = get_object_or_404(Expediente, id=id)
    exp.expedienteResagado = not exp.expedienteResagado
    exp.save()
    return JsonResponse({'status': 'ok', 'expedienteResagado': exp.expedienteResagado})

def cambiarAnalizar(request, id):
    exp = get_object_or_404(Expediente, id=id)
    exp.contemplado = not exp.contemplado
    exp.save()
    return JsonResponse({'status': 'ok', 'contemplado': exp.contemplado})
    
"""Temas a considerar:



2.-Crear copias cuando se suben mas de 1 con la misma clave 
3.-Formato para carpetas al cargar archivo
5.-Apartado para archivados


"""


# Asume que ya tienes en este módulo: Expediente, SeccionesExpediente,
# RegistroSeccion, Linea y la función _to_unc() que ya definiste.

RUTA_SERVIDOR = r"\\192.168.0.96\intranetucg$$\Evidencias\652 Digitalización de expedientes de crédito"

MESES_ES = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
}

# prefijo -> (carpeta padre, nombre de la carpeta de sección)
SECCIONES_FS = {
    "1": ("Maestra", "I. Identificación del Socio"),
    "2": ("Maestra", "II. Información Financiera"),
    "3": ("Operativa", "III. Estudio de Crédito"),
    "4": ("Operativa", "IV. Información de garantias"),
    "5": ("Operativa", "V. Contratos"),
    "6": ("Operativa", "VI. Seguimiento"),
    "7": ("Operativa", "VII. Correspondencia"),
}

# [opcional número de línea] + clave tipo 1.02 (o 1.025), seguida de espacio, punto o fin
REGEX_CLAVE = re.compile(r'^\s*(?:(\d+)\s+)?(\d{1,2}\.\d{1,3})(?=[\s.]|$)')

ARCHIVOS_IGNORADOS = {"thumbs.db", "desktop.ini", ".ds_store"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
import unicodedata

PARTICULAS = {"de", "del", "la", "las", "los", "y", "e"}


def _sin_acentos(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                   if unicodedata.category(c) != 'Mn')


def _iniciales_posibles(nombre):
    """'José Mario Hugo Juárez' -> {'JMHJ'}.
    Con partículas ('María de la Luz Pérez') acepta MDLP y MLP."""
    palabras = _sin_acentos(nombre).upper().split()
    todas = ''.join(p[0] for p in palabras)
    sin_particulas = ''.join(p[0] for p in palabras if p.lower() not in PARTICULAS)
    return {todas, sin_particulas}


def _mapa_iniciales(personas):
    mapa = {}
    for p in personas:
        for ini in _iniciales_posibles(p.nombre):
            if ini:
                mapa.setdefault(ini, []).append(p)
    return mapa


def _cargar_personas(expediente):
    """Claves 'C' = obligados solidarios, 'B' = representantes legales
    (igual que SeccionesExpediente.tipoDeSeccion)."""
    obligados = list(ObligadoSolidario.objects.filter(expedientes=expediente).distinct())
    representantes = list(RepresentanteLegal.objects.filter(expedientes=expediente).distinct())
    return {
        'C': {'lista': obligados, 'mapa': _mapa_iniciales(obligados)},
        'B': {'lista': representantes, 'mapa': _mapa_iniciales(representantes)},
    }


def _secciones_de_personas(secciones, personas):
    """{('B'|'C', persona_id): [seccion_id, ...]} usando el título de la sección
    ('Representante legal - Juan', 'Obligado solidario y garantes - Ana', ...)."""
    mapa = {}
    for s in secciones:
        if s.tipoDeSeccion not in ('B', 'C'):
            continue
        titulo = (s.tituloSeccion or '').strip().lower()
        for p in personas[s.tipoDeSeccion]['lista']:
            if titulo.endswith(f" - {p.nombre.strip().lower()}"):
                mapa.setdefault((s.tipoDeSeccion, p.id), []).append(s.id)
                break
    return mapa
def _normalizar_clave(clave):
    """'1.025' -> '1.02' ; '1.02.' -> '1.02'"""
    partes = str(clave).strip().rstrip('.').split('.')
    if len(partes) == 2 and len(partes[1]) >= 3:
        return f"{partes[0]}.{partes[1][:2]}"
    return '.'.join(partes)


def _parsear_nombre(nombre, es_archivo=True, personas=None, tipos_clave=None):
    stem = os.path.splitext(nombre)[0] if es_archivo else nombre
    stem = re.sub(r'\s+', ' ', stem.strip())

    m = REGEX_CLAVE.match(stem)
    if not m:
        return None

    clave = _normalizar_clave(m.group(2))
    resto = stem[m.end():].strip(' .')

    # --- Iniciales: solo si la clave es por persona, y solo entre su tipo ---
    tipo = (tipos_clave or {}).get(clave)          # 'B', 'C' o None
    persona, ambiguo = None, False
    if tipo and personas and resto:
        mapa = personas[tipo]['mapa']
        tokens = resto.split(' ')
        for i, tok in enumerate(tokens):
            # No confundir el mes ("may 26") con unas iniciales como MAY
            es_mes = (tok.lower() in MESES_ES and i + 1 < len(tokens)
                      and re.fullmatch(r'\d{2}', tokens[i + 1]))
            if es_mes:
                continue
            candidatos = mapa.get(_sin_acentos(tok).upper())
            if candidatos:
                if len(candidatos) > 1:
                    ambiguo = True
                else:
                    persona = candidatos[0]
                del tokens[i]                 # se quita para no contaminar fecha/número
                resto = ' '.join(tokens)
                break

    fecha = None
    mf = re.search(r'(?:^|\s)([a-z]{3})\s*(\d{2})$', resto.lower())
    if mf and mf.group(1) in MESES_ES:
        try:
            fecha = datetime(int(f"20{mf.group(2)}"), MESES_ES[mf.group(1)], 1).date()
        except ValueError:
            fecha = None

    numero = None
    if not fecha and resto:
        numero = resto.split(' ')[-1].strip()

    return {'clave': clave, 'fecha': fecha, 'numero': numero,
            'tipo_persona': tipo, 'persona': persona, 'ambiguo': ambiguo}

def _ya_registrado(registros, fecha, numero, obligado_id=None):
    esperado = (numero or '').strip().lower()
    for r in registros:
        if not r.estatus:
            continue
       
        if fecha:
            if r.es_fecha and hasattr(r.fecha, 'year') and \
                    (r.fecha.year, r.fecha.month) == (fecha.year, fecha.month):
                return True
        else:
            actual = re.sub(r'\s+', ' ', str(r.numero or '').strip()).lower()
            if not r.es_fecha and actual == esperado:
                return True
    return False

def _buscar_carpeta_socio(expediente):
    kepler = str(expediente.socio.numeroKepler).strip() if expediente.socio.numeroKepler else "0000"
    nombre_socio = str(expediente.socio.nombre).strip().upper()

    for nombre_dir in os.listdir(_to_unc(RUTA_SERVIDOR)):
        if kepler != "0000" and kepler in nombre_dir:
            return os.path.join(RUTA_SERVIDOR, nombre_dir)
        if kepler == "0000" and nombre_socio in nombre_dir.upper():
            return os.path.join(RUTA_SERVIDOR, nombre_dir)
    return None


def _es_dir(ruta):
    return os.path.isdir(_to_unc(ruta))


def _es_archivo(ruta):
    return os.path.isfile(_to_unc(ruta))


def _recolectar_items(carpeta_socio, expediente, personas=None, tipos_clave=None):
    """
    Recorre el servidor y devuelve la lista de elementos a evaluar:
    {'nombre', 'ruta', 'info' (dict o None), 'omitir' (motivo o None), 'linea_id'}
    """
    ruta_maestra = os.path.join(carpeta_socio, "Maestra")
    ruta_operativa = os.path.join(carpeta_socio, "Operativa")

    # (prefijo, ruta de la carpeta de sección, linea_id)
    secciones_ruta = []
    for prefijo in ("1", "2"):
        secciones_ruta.append((prefijo, os.path.join(ruta_maestra, SECCIONES_FS[prefijo][1]), None))

    if _es_dir(ruta_operativa):
        subdirs_op = os.listdir(_to_unc(ruta_operativa))
        lineas = Linea.objects.filter(expediente=expediente)
        carpetas_linea = []   # lista de (ruta, linea)
        for linea in lineas:
            pref = f"{str(linea.numero).strip()} "
            for sd in subdirs_op:
                ruta_sd = os.path.join(ruta_operativa, sd)
                if sd.strip().startswith(pref) and _es_dir(ruta_sd) \
                        and all(ruta_sd != r for r, _ in carpetas_linea):
                    carpetas_linea.append((ruta_sd, linea))

        for ruta_linea, linea in carpetas_linea:
            for prefijo in ("3", "4", "5", "6", "7"):
                secciones_ruta.append((prefijo, os.path.join(ruta_linea, SECCIONES_FS[prefijo][1]), linea.id))

    items = []

    def agregar_archivo(nombre, ruta, prefijo, linea_id):
        if nombre.lower() in ARCHIVOS_IGNORADOS or nombre.startswith("~$"):
            return
        info = _parsear_nombre(nombre, es_archivo=True, personas=personas, tipos_clave=tipos_clave)
        if not info:
            items.append({'nombre': nombre, 'ruta': ruta, 'info': None, 'linea_id': linea_id,
                          'omitir': 'Sin clave en el nombre, no aplica'})
        elif info['clave'].split('.')[0] != prefijo:
            items.append({'nombre': nombre, 'ruta': ruta, 'info': None, 'linea_id': linea_id,
                          'omitir': f"La clave {info['clave']} no corresponde a esta sección"})
        else:
            items.append({'nombre': nombre, 'ruta': ruta, 'info': info,
                          'omitir': None, 'linea_id': linea_id})

    for prefijo, ruta_seccion, linea_id in secciones_ruta:
        if not _es_dir(ruta_seccion):
            continue
        for item in sorted(os.listdir(_to_unc(ruta_seccion))):
            ruta_item = os.path.join(ruta_seccion, item)

            if _es_archivo(ruta_item):
                agregar_archivo(item, ruta_item, prefijo, linea_id)

            elif _es_dir(ruta_item):
                # Solo entramos a carpetas que empiecen con clave (ej. "1.02 Identificación Vigente")
                if _parsear_nombre(item, es_archivo=False):
                    for sub in sorted(os.listdir(_to_unc(ruta_item))):
                        ruta_sub = os.path.join(ruta_item, sub)
                        if _es_archivo(ruta_sub):
                            agregar_archivo(sub, ruta_sub, prefijo, linea_id)
                else:
                    items.append({'nombre': item, 'ruta': ruta_item, 'info': None, 'linea_id': linea_id,
                                  'omitir': 'Carpeta sin clave, no aplica'})
    return items

def _emit(**kw):
    return json.dumps(kw, ensure_ascii=False, default=str) + "\n"


# ---------------------------------------------------------------------------
# Vista principal (streaming NDJSON: una línea JSON por evento)
# ---------------------------------------------------------------------------

@login_required(login_url='/login/')
def detectarArchivos(request, id):
    if request.method != "POST":
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    expediente = get_object_or_404(Expediente, pk=id)
    secciones = SeccionesExpediente.objects.filter(expediente=expediente)

    def generador():
        resumen = {'creado': 0, 'duplicado': 0, 'omitido': 0, 'error': 0}

        try:
            yield _emit(tipo='estado', mensaje='Buscando la carpeta del socio en el servidor...')
            carpeta_socio = _buscar_carpeta_socio(expediente)
            if not carpeta_socio:
                yield _emit(tipo='error_fatal', mensaje='No se encontró la carpeta del socio en el servidor.')
                return

            yield _emit(tipo='estado', mensaje=f'Carpeta encontrada: {os.path.basename(carpeta_socio)}. Escaneando archivos...')

            personas = _cargar_personas(expediente)
            secciones_persona = _secciones_de_personas(secciones, personas)

            # Registros existentes agrupados por (línea, clave) y tipo de sección de cada clave
            mapeo = {}
            tipos_por_clave = {}
            for r in RegistroSeccion.objects.filter(seccion__in=secciones).select_related('apartado', 'seccion'):
                clave_r = _normalizar_clave(r.apartado.clave)
                mapeo.setdefault((r.seccion.linea_id, clave_r), []).append(r)
                tipos_por_clave.setdefault(clave_r, set()).add(r.seccion.tipoDeSeccion)

            # Clave "por persona": existe únicamente en secciones B (representante) o C (obligado)
            tipos_clave = {c: next(iter(t)) for c, t in tipos_por_clave.items()
                           if len(t) == 1 and next(iter(t)) in ('B', 'C')}

            items = _recolectar_items(carpeta_socio, expediente, personas, tipos_clave)
            total = len(items)
            yield _emit(tipo='inicio', total=total)

            if total == 0:
                yield _emit(tipo='fin', resumen=resumen, mensaje='No se encontraron archivos.')
                return

            for i, it in enumerate(items, 1):
                estado, mensaje = 'omitido', it['omitir'] or ''
                try:
                    if not it['omitir']:
                        info = it['info']
                        clave = info['clave']
                        tipo = info['tipo_persona']                  # 'B', 'C' o None
                        persona = info['persona']
                        lista_clave = mapeo.get((it['linea_id'], clave), [])
                        lista_personas = personas[tipo]['lista'] if tipo else []
                        etiqueta = 'representante legal' if tipo == 'B' else 'obligado solidario'

                        # Sin iniciales pero único de su tipo en el expediente: se asigna solo
                        if tipo and not persona and len(lista_personas) == 1:
                            persona = lista_personas[0]

                        # Renglones que le corresponden: los de la sección de esa persona
                        if tipo:
                            ids_secc = secciones_persona.get((tipo, persona.id), []) if persona else []
                            registros = [r for r in lista_clave if r.seccion_id in ids_secc]
                        else:
                            registros = [r for r in lista_clave if r.seccion.tipoDeSeccion not in ('B', 'C')]

                        if info['ambiguo']:
                            estado, mensaje = 'error', 'Las iniciales coinciden con más de una persona'
                        elif tipo and not persona and len(lista_personas) > 1:
                            estado, mensaje = 'error', (f"La clave {clave} es por {etiqueta} y hay "
                                                        f"{len(lista_personas)} en el expediente: agrega las iniciales")
                        elif tipo and not persona:
                            estado, mensaje = 'omitido', f"No hay {etiqueta} registrado en el expediente"
                        elif not registros:
                            estado, mensaje = 'omitido', (f"No hay renglón en BD para la clave {clave}"
                                                          + (f" de {persona.nombre}" if persona else ""))
                        elif _ya_registrado(registros, info['fecha'], info['numero']):
                            estado, mensaje = 'duplicado', 'Ya estaba registrado'
                        else:
                            with transaction.atomic():
                                vacio = next((r for r in registros if not r.estatus), None)
                                if vacio:
                                    reg = vacio
                                else:
                                    base = registros[0]
                                    ultimo = max((r.secuencial or 1) for r in registros
                                                 if r.seccion_id == base.seccion_id)
                                    reg = RegistroSeccion(
                                        seccion=base.seccion, apartado=base.apartado,
                                        secuencial=ultimo + 1, comentario=base.comentario,
                                        comentarioCredito=base.comentarioCredito, enviar=base.enviar,
                                    )
                                    lista_clave.append(reg)   # para que los siguientes archivos lo vean

                                if info['fecha']:
                                    reg.es_fecha, reg.fecha, reg.numero = True, info['fecha'], None
                                    detalle = f"fecha {info['fecha'].strftime('%m/%Y')}"
                                else:
                                    reg.es_fecha, reg.fecha, reg.numero = False, None, info['numero']
                                    detalle = f"identificador '{info['numero']}'" if info['numero'] else 'sin identificador'
                                if persona:
                                    detalle += f" · {persona.nombre}"
                                reg.estatus = "ok"
                                reg.save()
                            estado, mensaje = 'creado', f"Registro creado ({detalle})"

                except Exception as e:
                    estado, mensaje = 'error', str(e)

                resumen[estado] += 1
                yield _emit(tipo='progreso', actual=i, total=total, archivo=it['nombre'],
                            estado=estado, mensaje=mensaje, resumen=resumen)

            yield _emit(tipo='fin', resumen=resumen, mensaje='Detección finalizada.')

        except Exception as e:
            yield _emit(tipo='error_fatal', mensaje=f'Error inesperado: {e}')

    respuesta = StreamingHttpResponse(generador(), content_type='application/x-ndjson; charset=utf-8')
    respuesta['Cache-Control'] = 'no-cache'
    respuesta['X-Accel-Buffering'] = 'no'  # evita buffering si hay nginx delante
    return respuesta

# urls.py:
# 










