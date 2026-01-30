from io import BytesIO
import os
from pyexpat.errors import messages
from urllib import request
from django.conf import settings
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from openpyxl import load_workbook
from Index.forms import *
from db.models import *
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import user_passes_test,login_required
from django.core.paginator import Paginator
from django.contrib import messages 
from django.shortcuts import render
from django.db.models import Q
from openpyxl.styles import *
from openpyxl.styles.borders import Border, Side
import smtplib
from email.message import EmailMessage
#LOS STATUS DEBEN SER 1="Nuevo" y 2="Completado" por temas de compatiblidad
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
    lineasLista = Linea.objects.filter(expediente=expediente)
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
        'lineasLista':lineasLista,
        'secciones': [],
    }
    
    totalRegistros = 0
    totalRegistrosLlenos = 0

    for seccion in secciones:
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

     
                reps_raw = rep_form.cleaned_data.get('representantes', '').strip().strip("|")
                nombres_reps = [x.strip() for x in reps_raw.split("||") if x.strip()]
                obls_raw = obl_form.cleaned_data.get('obligados', '').strip().strip("|")
                nombres_obls = [x.strip() for x in obls_raw.split("||") if x.strip()]

                for rep in nombres_reps:

                    RepresentanteLegal.objects.get_or_create(nombre=rep)  
                for obls in nombres_obls:

                    ObligadoSolidario.objects.get_or_create(nombre=obls,tipoPersona="F")  

                if tipo_persona == 'M' and (not nombres_reps or not nombres_obls):
                    return JsonResponse({'success': False, 'error': "Faltan representantes u obligados para Persona Moral."}, status=400)

                expediente = exp_form.save(commit=False)
                expediente.socio = socio_a_asignar
                expediente.estatus_id = 1
                expediente.save()
              

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

                return JsonResponse({'success': True, 'redirect_url': reverse('Index:expedientesLayout')})

            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
                
        return JsonResponse({'success': False, 'error': "Formulario no válido."}, status=400)

    return render(request, 'Index/crearExpediente.html', {'exp_form': ExpedienteCrearForm(), 'rep_form': RepresentantesForm(), 'obl_form': ObligadosForm()})

from django.db.models.functions import Cast
from django.db.models import FloatField
def _generar_con_debug_extremo(seccion_obj, area_socio):
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
    expediente.eliminado = True
    expediente.save()
    return redirect('Index:expedientesLayout')



def correroParaRevision(expediente):
    #scortes@ucg.com.mx 
    # "daudiffred@ucg.com.mx" 
    destinatario = "portiz@ucg.com.mx"
    dominio = "http://192.168.0.132:8000/expedientes/editarExpediente/"
    url_final = f"{dominio}{expediente.id}/"
    asunto = "Informe listo para revisión"
    
    cuerpo_texto = f"""
    Le informamos que el expediente {expediente.id} del socio {expediente.socio.nombre} esta listo para su revisión. 
    Atte {expediente.usuario.username}.
    Ingrese directamente: {url_final}
    """

    cuerpo_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
                <h2 style="color: #2c3e50;">Actualización de estatus del expediente</h2>
                <p>Estimado usuario,</p>
                <p>Le informamos que el expediente <strong>{expediente.id}</strong> del socio <strong>{expediente.socio.nombre}</strong> está listo para su revisión.</p>
                <div style="margin: 30px 0; text-align: center;">
                    <a href="{url_final}" 
                       style="background-color: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Revisar Expediente
                    </a>
                </div>
                <p style="font-size: 0.9em; color: #555;">
                    Atentamente,<br>
                    <strong>{expediente.usuario.username}</strong>
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

    mensaje = EmailMessage()
    mensaje["From"] = USUARIO
    mensaje["To"] = ", ".join(destinatario) if isinstance(destinatario, list) else destinatario
    mensaje["Subject"] = asunto
    
    mensaje.set_content(cuerpo_texto)

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

@login_required(login_url='/login/')
def expediente_cambiar_status(request, id):
    expediente = get_object_or_404(Expediente, pk=id)

    if request.method == "POST":
        nuevo_estatus_id = request.POST.get("estatus")
        print(nuevo_estatus_id)
        print(str(expediente.estatus.id))
        if nuevo_estatus_id and  nuevo_estatus_id != str(expediente.estatus.id)  :
            if nuevo_estatus_id == "2" :
                correroParaRevision(expediente)
            expediente.estatus_id = nuevo_estatus_id
            expediente.save()
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
            'numeroKepler': socio.numeroKepler, 

        }
        return JsonResponse(data)
    except Socio.DoesNotExist:
        return JsonResponse({'error': 'Socio no encontrado'}, status=404)

def obtener_lineas_socio(request, socio_id):
    socio = Socio.objects.get(pk=socio_id)
    print(socio)
    socio_id = request.GET.get('socio_id')
    lineas = Linea.objects.filter(socio_id=socio).values('id', 'numero', 'monto')
    print(lineas)
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
    
    from django.template.loader import render_to_string
    from xhtml2pdf import pisa
    
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
                fecha = reg.fecha.strftime("%d/%m/%Y") if reg.fecha else ""
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
    usuarios = User.objects.filter(roles__in=['Ejecutivo de Servicios', 'Ejecutivo de Negocios']).distinct()    
    estados = Estado.objects.all().order_by('id')
    data_por_usuario = {}
    
    for us in usuarios:
        expedientes_totales = Expediente.objects.filter(usuario=us, eliminado=False)
        numExpedientes = expedientes_totales.count()
        
        conteo_por_estado = {}
        for estado in estados:
            conteo_por_estado[estado.nombre] = {
                'count': 0,
                'color': estado.color,
                'id': estado.id
            }

        for exp in expedientes_totales:
            if exp.estatus and exp.estatus.nombre in conteo_por_estado:
                conteo_por_estado[exp.estatus.nombre]['count'] += 1
            
        expedientes_completados = expedientes_totales.filter(estatus__id=2).count()
        
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

#Metodo para crear una linea
@login_required(login_url='/login/')
def lineaCrear(request):
    exito=False


    if request.method == "POST":
        form = LineaCrearForm(request.POST)
        if form.is_valid():
            form.save(commit=True)
            messages.success(request, f"Línea creada con éxito.")
            exito = True
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    form = LineaCrearForm()
    context = {'form': form, 'exito': exito}
    return render(request, 'Index/crearLinea.html',context)

#Metodo para editar una linea
@login_required(login_url='/login/')
def editarLinea(request, id):
    linea = get_object_or_404(Linea, pk=id)
    exito = False

    if request.method == "POST":
        form = LineaCrearForm(request.POST, instance=linea)
        if form.is_valid():
            form.save()
            messages.success(request, f"Línea de {linea.expediente.socio.nombre} actualizada.")
            exito = True
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = LineaCrearForm(instance=linea)
    
    context = {'form': form, 'exito': exito}
    return render(request, 'Index/editarLinea.html', context)
