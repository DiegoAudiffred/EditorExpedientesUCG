from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import ApartadoCatalogo, Estado


@receiver(post_migrate)
def cargar_apartados_default(sender, **kwargs):
    defaults = {
        "A": {
            "1.01": {"descripcion": "FORMATO CONOCE A TU SOCIO", "area_aplicacion": "Ambas"},
            "1.02": {"descripcion": "IDENTIFICACIÓN VIGENTE (INE, pasaporte o cédula profesional no mayor a 10 años). ACTA DE NACIMIENTO Y ACTA DE MATRIMONIO EN SU CASO. Requieren ser cotejadas.", "area_aplicacion": "Fisicas"},
            "1.03": {"descripcion": "CURP. Requiere ser cotejado.", "area_aplicacion": "Fisicas"},
            "1.04": {"descripcion": "DICTAMEN JURIDICO ACTUALIZADO Y/O CARTA DE NO MODIFICACIÓN DE PODERES", "area_aplicacion": "Morales"},
            "1.05": {"descripcion": "VERIFICACIÓN DE SOCIEDAD. Vigencia máxima: 12 meses", "area_aplicacion": "Morales"},
            "1.06": {"descripcion": "ACTA CONSTITUTIVA, SUS MODIFICACIONES Y PODERES (Copias legibles cuando se trate de aumentos de capital, cambio de apoderados, modificación de objeto y/o denominación social, etc). Requiere ser cotejado.", "area_aplicacion": "Morales"},
            "1.07": {"descripcion": "COMPROBANTE DE DOMICILIO FISCAL, no mayor a 3 meses de antigüedad. (Luz, teléfono, predial, agua, gas y estados de cuenta). Requiere ser cotejado. (actualizar anualmente)", "area_aplicacion": "Ambas"},
            "1.08": {"descripcion": "CONSTANCIA DE SITUACIÓN FISCAL del Solicitante (Cédula de identificación fiscal y Alta de Hacienda).(No mayor a 1 año). Requiere ser Cotejado", "area_aplicacion": "Ambas"},
            "1.09": {"descripcion": "CONSTANCIA/IMPRESIÓN PANTALLA DE SERIE DE FIEL (Firma Electrónica) y/o CARTA explicativa en caso de no contar con ella.", "area_aplicacion": "Morales"},
            "1.10": {"descripcion": "ORGANIGRAMA (Cuando cuente con el)", "area_aplicacion": "Ambas"},
            "1.11": {"descripcion": "CUESTIONARIO DE IDENTIFICACIÓN DE INFORMACIÓN ADICIONAL (En su caso)", "area_aplicacion": "Ambas"},
        },
        "B": {
            "1.12": {"descripcion": "IDENTIFICACIÓN VIGENTE (INE, pasaporte o cédula profesional no mayor a 10 años). ACTA DE NACIMIENTO Y ACTA DE MATRIMONIO EN SU CASO. Requieren ser cotejadas.", "area_aplicacion": "Ambas"},
            "1.13": {"descripcion": "CURP. Requiere ser cotejado.", "area_aplicacion": "Ambas"},
            "1.141": {"descripcion": "COMPROBANTE DE DOMICILIO FISCAL, no mayor a 3 meses. Requiere cotejo.", "area_aplicacion": "Ambas"},
            "1.142": {"descripcion": "COMPROBANTE DE DOMICILIO PERSONAL, no mayor a 3 meses. Requiere cotejo.", "area_aplicacion": "Ambas"},
            "1.15": {"descripcion": "CONSTANCIA DE SITUACIÓN FISCAL del Representante Legal. Requiere cotejo.", "area_aplicacion": "Moral"},
        },
        "C": {
            "1.16":{"descripcion": "FORMATO DE IDENTIFICACION DE COACREDITADOS Y OBLIGADOS SOLIDARIOS (Solo en caso de no ser socio)", "area_aplicacion": "Ambas"}, 
            "1.17": {"descripcion": "IDENTIFICACIÓN VIGENTE DEL OBLIGADO SOLIDARIO / GARANTE (INE, pasaporte o cédula profesional no mayor a 10 años). Requiere ser cotejado.", "area_aplicacion": "Ambas"},
            "1.18": {"descripcion": "CURP. Requiere ser cotejado", "area_aplicacion": "Ambas"},
            "1.19": {"descripcion": "ACTA DE NACIMIENTO Y ACTA DE MATRIMONIO ( En su caso) (Requieren ser cotejados)", "area_aplicacion": "Fisicas"},
            "1.20": {"descripcion": "DICTAMEN JURIDICO ACTUALIZADO Y/O CARTA DE NO MODIFICACIÓN DE PODERES", "area_aplicacion": "Ambas"},
            "1.21": {"descripcion": "VERIFICACIÓN DE SOCIEDAD. Vigencia máxima: 12 meses", "area_aplicacion": "Ambas"},
            "1.22": {"descripcion": "ACTA CONSTITUTIVA, SUS MODIFICACIONES Y PODERES (Copias legibles cuando se trate de aumentos de capital, cambio de apoderados, modificación de objeto y/o denominación social, etc). Requiere ser cotejado.", "area_aplicacion": "Ambas"},
            "1.231": {"descripcion": "COMPROBANTE DE DOMICILIO FISCAL , no mayor a 3 meses de antigüedad. (Luz, teléfono, predial o agua). Requiere ser cotejado.", "area_aplicacion": "Ambas"},
            "1.232": {"descripcion": "COMPROBANTE DE DOMICILIO PERSONAL, no mayor a 3 meses de antigüedad. (Luz, teléfono, predial o agua). Requiere ser cotejado.", "area_aplicacion": "Ambas"},
            "1.24": {"descripcion": "CONSTANCIA DE SITUACIÓN FISCAL del Obligado Solidario / Garante (No mayor a 1 año). Requiere ser Cotejado", "area_aplicacion": "Ambas"},
            "1.251": {"descripcion": "CONSTANCIA/IMPRESIÓN PANTALLA DE SERIE DE FIEL (Firma Electrónica) solo en caso de contar con ella.", "area_aplicacion": "Ambas"},
            "1.252": {"descripcion": "En caso de que el Obligado o Garante sea Persona Moral archivar los documentos del apartado b)", "area_aplicacion": "Ambas"},
        },
        "I": {
            "1.26": {"descripcion": "PRESENTACIÓN INSTITUCIONAL", "area_aplicacion": "Ambas"},
            "1.27": {"descripcion": "CONSTANCIA DE RENOVACION DE DICTAMEN TÉCNICO(SOLO SOFOM,CENTRO CAMBIARIO,TRANSMISORES DE DINERO)", "area_aplicacion": "Ambas"},
            "1.28": {"descripcion": "OTROS INTERMEDIARIOS; EVIDENCIA DEL CUMPLIMIENTO ANTE CONDUSEF (SIPRES,RECO,RECA,REUNE,REDECO,BURO DE ENTIDADES FINANCIERAS)", "area_aplicacion": "Ambas"},
            "1.29": {"descripcion": "OFICIO DE ENTREGA DE CLAVE PARA EL SISTEMA INTERINSTITUCIONAL DE TRANFERENCIA DE LA INFORMACION PLD/FT (SITI)", "area_aplicacion": "Ambas"},
            "1.30": {"descripcion": "ACUSE DE RECIBO DE ENVIO DEL INFORME DE AUDITORIA ENVIADO A TRAVES DEL SITI", "area_aplicacion": "Ambas"},
            "1.31": {"descripcion": "AUDITORIA CNBV (en su caso)", "area_aplicacion": "Ambas"},
            "1.32": {"descripcion": "OTROS PERMISOS EN GENERAL", "area_aplicacion": "Ambas"},
            "1.33": {"descripcion": "CONSTANCIA DE REGISTRO ANTE EL SAT COMO ACTIVIDAD VULNERABLE (en su caso)", "area_aplicacion": "Ambas"},
            "1.34": {"descripcion": "CONSTANCIA DE REGISTRO DE RESPONSABLE DE CUMPLIMIENTO (en su caso)", "area_aplicacion": "Ambas"},
        },
        "II": {
            "2.01": {"descripcion": "ESTADOS FINANCIEROS: 2 ÚLTIMOS EJERCICIOS Y PARCIAL RECIENTE CON ANTIGÜEDAD PREFERENTEMENTE NO MAYOR A 3 MESES, PUDIENDO SER HASTA 6 MESES, Y CON RELACIONES ANALÍTICAS DE LAS PRINCIPALES CUENTAS (Auditados en su caso, y firmados por el representante y contador que los elabora, con la siguiente leyenda: Bajo protesta de decir verdad, manifiesto que las cifras contenidas en este Estado Financiero son veraces y contienen toda la información referente a la situación financiera y/o los resultados de la empresa y afirmo que somos legalmente responsables de la autenticidad y veracidad de las mismas, asumiendo asimismo, todo tipo de responsabilidad derivada de cualquier declaración en falso sobre las mismas", "area_aplicacion": "Ambas"},
            "2.02": {"descripcion": "ESTADOS DE CUENTA DE CHEQUES (Carátula de los últimos 3 meses, a partir de la información financiera mas reciente) de todas las Instituciones de Crédito en donde el Socio tiene cuenta.", "area_aplicacion": "Ambas"},
            "2.03": {"descripcion": "DECLARACIÓN ANUAL DE I.S.R. QUE CONTENGA EL ACUSE DE RECIBO CON EL SELLO DIGITAL (2 últimos ejercicios). Si se optó por DICTAMINAR, los estados financieros deberán ser los DICTAMINADOS. (actualizar anualmente).", "area_aplicacion": "Ambas"},
        },
        "III": {
            "3.01": {"descripcion": "CARTA DE TERMINOS Y CONDICIONES, firmada por el Socio.", "area_aplicacion": "Ambas"},
            "3.02": {"descripcion": "CARATULA DE RESOLUCION DE CREDITO FIRMADA", "area_aplicacion": "Ambas"},
            "3.03": {"descripcion": "ESTUDIO DE CRÉDITO", "area_aplicacion": "Ambas"},
            "3.04": {"descripcion": "FORMATO DE REPORTE DE VISITA OCULAR CON FOTOGRAFÍAS (Solo en caso de socio nuevo o inactivo por más de 12 meses).", "area_aplicacion": "Ambas"},
            "3.05": {"descripcion": "REPORTE DE BURO DE CRÉDITO DE LOS PARTICIPANTES EN EL CRÉDITO. EN CASO DE SOCIOS NUEVOS REPORTE DE BURO DE CRÉDITO ESPECIAL (Solo en el caso de socios que cuenten con saldo en el reporte de Buro de Crédito Normal) Y REPORTE DE LOS ACCIONISTAS CON PARTICIPACIÓN ACCIONARIA MAYOR A 25%, Y EN SU CASO AGREGAR LA DETERMINACIÓN DEL GRADO DE RIESGO INTERNO Y PROVISIÓN INICIAL.", "area_aplicacion": "Ambas"},
            "3.06": {"descripcion": "OPINIÓN DE CUMPLIMIENTO ANTE EL SAT (No mayor a 3 meses)", "area_aplicacion": "Ambas"},
            "3.07": {"descripcion": "FLUJO DE EFECTIVO PROYECTADO CITANDO PREMISAS DE ELABORACION. Por la vigencia del crédito, mensualizado el primer año. (Solo para créditos mayores a 5 mdp y plazo mayor a 36 meses y en cualquier solicitud de una IFNB) (excepto garantía liquida)", "area_aplicacion": "Ambas"},
            "3.08": {"descripcion": "COTIZACIONES DE LOS CONCEPTOS A FINANCIAR/ARRENDAR. (En su caso) En caso de construcción o remodelación, se requiere copia de proyecto y avance de obra", "area_aplicacion": "Ambas"},
            "3.09": {"descripcion": "CARTA SOLICITUD MEMBRETADA Y FIRMADA(INDICAR MONTO,PLAZO,GARANTIA Y DETALLAR EL DESTINO DEL CREDITO)", "area_aplicacion": "Ambas"},

        },
        "IV": {
            "4.01": {"descripcion": "GARANTIA LIQUIDA: CARTA MANDATO Y PAGARÉ DE INVERSION DEBIDAMENTE ENDOSADO (Copia)", "area_aplicacion": "Ambas"},
            "4.02": {"descripcion": "GARANTIA HIPOTECARIA: ESCRITURA INMUEBLE PROPUESTO EN GARANTÍA (Copia legible con datos de inscripción en el Registro Publico de la Propiedad) Y DICTAMEN JURIDICO ( Se actualizará solo en caso de cambios en la verificación). GARANTIA FIDUCIARIA: PAGO DE AGUA", "area_aplicacion": "Ambas"},
            "4.03": {"descripcion": "VERIFICACION DE ANTECEDENTES REGISTRALES DE LA PROPIEDAD. Vigencia Máxima: 12 Meses", "area_aplicacion": "Ambas"},
            "4.04": {"descripcion": "AVALUO Y BOLETA PREDIAL DEL INMUEBLE PROPUESTO EN GARANTÍA. (Año en curso)", "area_aplicacion": "Ambas"},
            "4.05": {"descripcion": "GARANTIA PRENDARIA: (Documentos que la acrediten: Facturas, cuentas por cobrar, titulos accionarios, etc).", "area_aplicacion": "Ambas"},
            "4.06": {"descripcion": "RELACION PATRIMONIAL DE LOS OBLIGADOS SOLIDARIOS (actualizar anualmente).", "area_aplicacion": "Ambas"},
        },
        "V": {
            "5.01": {"descripcion": "CONTRATO CELEBRADO CON LA UNIÓN DE CRÉDITO GENERAL, DEBE INCLUIR LOS FORMATOS SOLICITADOS POR CONDUSEF (copia).", "area_aplicacion": "Ambas"},
            "5.02": {"descripcion": "DISPOSICION DEL CRÉDITO: PAGARE Y TABLA DE AMORTIZACION. (Copia)", "area_aplicacion": "Ambas"},
            "5.03": {"descripcion": "CONTRATOS DE CRÉDITO QUE TENGA CON OTRAS INSTITUCIONES FINANCIERAS (copia simple) / Formato de Pasivos Bancarios", "area_aplicacion": "Ambas"},
            "5.04": {"descripcion": "CONTRATO DE ARRENDAMIENTO/COMODATO (copia) (en caso de que la empresa no sea propietaria del inmueble que ocupa).", "area_aplicacion": "Ambas"},
        },
        "VI": {
            "6.01": {"descripcion": "PÓLIZA DE SEGURO DE LA GARANTÍA, CON EL ENDOSO A FAVOR DE LA UNIÓN, PAGO ANUAL DE LA PRIMA, DEL AGUA Y BOLETA PREDIAL. (actualizar anualmente).", "area_aplicacion": "Ambas"},
            "6.02": {"descripcion": "COMPROBACION DEL CRÉDITO (indicando en qué se utilizaron los recursos)", "area_aplicacion": "Ambas"},
            "6.03": {"descripcion": "REPORTE ANUAL DE SEGUIMIENTO DE CONDICIONES DE HACER Y NO HACER, ESTATUS DE LAS GARANTÍAS DURANTE LA VIGENCIA DEL CRÉDITO.", "area_aplicacion": "Ambas"},
            "6.04": {"descripcion": "ACTUALIZACION ANUAL DEL REPORTE DE BURO DE ACREDITADOS Y OBLIGADOS SOLIDARIOS, AVALISTA O FIADOR", "area_aplicacion": "Ambas"},
            "6.05": {"descripcion": "REPORTE ANUAL DE DISPOSICIONES, PAGOS REALIZADOS, RENOVACIONES O REESTRUCTURAS, QUITAS, ADJUDICACIONES O DACIONES EN PAGO QUE SOPORTE LA CALIFICACION OTORGADA AL CREDITO", "area_aplicacion": "Ambas"},
            "6.06": {"descripcion": "CEDULA DE CALIFICACION DE CARTERA DE LOS ULTIMOS 4 TRIMESTRES", "area_aplicacion": "Ambas"},
            "6.07": {"descripcion": "INFORMACIÓN FONDEO", "area_aplicacion": "Ambas"},
        },
    }

    for tipo, items in defaults.items():
            for clave_str, data in items.items():
                ApartadoCatalogo.objects.get_or_create(
                    tipoDeSeccion=tipo,
                    clave=str(clave_str),
                    defaults={
                        'descripcion': data['descripcion'],
                        'areaDondeAplica': data['area_aplicacion']
                    }
                )
    #Estado.objects.get_or_create(nombre="Nuevo", color="#FFFFFF")