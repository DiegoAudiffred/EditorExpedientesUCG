from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import ApartadoCatalogo


@receiver(post_migrate)
def cargar_apartados_default(sender, **kwargs):
    defaults = {
        "A": {
            "1.1": "FORMATO CONOCE A TU SOCIO",
            "1.4": "DICTAMEN JURIDICO ACTUALIZADO Y/O CARTA DE NO MODIFICACIÓN DE PODERES",
            "1.5": "VERIFICACIÓN DE SOCIEDAD. Vigencia máxima: 12 meses",
            "1.6": "ACTA CONSTITUTIVA, SUS MODIFICACIONES Y PODERES (Copias legibles cuando se trate de aumentos de capital, cambio de apoderados, modificación de objeto y/o denominación social, etc).  Requiere ser cotejado.",
            "1.7": "COMPROBANTE DE DOMICILIO FISCAL, no mayor a 3 meses de antigüedad. (Luz, teléfono, predial, agua, gas y estados de cuenta).  Requiere ser cotejado. (actualizar anualmente)",
            "1.8": "CONSTANCIA DE SITUACIÓN FISCAL del Solicitante (Cédula de identificación fiscal y Alta de Hacienda).(No mayor a 1 año). Requiere ser Cotejado",
            "1.9": "CONSTANCIA/IMPRESIÓN PANTALLA DE SERIE DE FIEL (Firma Electrónica) y/o CARTA explicativa en caso de no contar con ella.	",
            "1.10": "ORGANIGRAMA (Cuando cuente con el)	",
            "1.11": "CUESTIONARIO DE IDENTIFICACIÓN DE INFORMACIÓN ADICIONAL (En su caso)",

        },
        "B": {
            "1.12": "IDENTIFICACIÓN VIGENTE (INE, pasaporte o cédula profesional no mayor a 10 años). ACTA DE NACIMIENTO Y ACTA DE MATRIMONIO EN SU CASO. Requieren ser cotejadas.",
            "1.13": "CURP. Requiere ser cotejado.",
            "1.14": "COMPROBANTE DE DOMICILIO FISCAL, no mayor a 3 meses. Requiere cotejo.",
            "1.14": "COMPROBANTE DE DOMICILIO PERSONAL, no mayor a 3 meses. Requiere cotejo.",
            "1.15": "CONSTANCIA DE SITUACIÓN FISCAL del Representante Legal. Requiere cotejo.",
            "1.25": "CONSTANCIA/IMPRESIÓN PANTALLA DE SERIE DE FIEL o carta explicativa.",
        },
        "C": {
            "1.16":"FORMATO DE IDENTIFICACION DE COACREDITADOS Y OBLIGADOS SOLIDARIOS  (Solo en caso de no ser socio)",	
            "1.17":	"IDENTIFICACIÓN VIGENTE DEL OBLIGADO SOLIDARIO / GARANTE (INE, pasaporte o cédula profesional no mayor a 10 años). Requiere ser cotejado.",
            "1.18":	"CURP. Requiere ser cotejado",
            "1.19":	"ACTA DE NACIMIENTO Y ACTA DE MATRIMONIO ( En su caso)   (Requieren ser cotejados)",
            "1.20":	"DICTAMEN JURIDICO ACTUALIZADO Y/O CARTA DE NO MODIFICACIÓN DE PODERES",
            "1.21":	"VERIFICACIÓN DE SOCIEDAD. Vigencia máxima: 12 meses",
            "1.22":	"ACTA CONSTITUTIVA, SUS MODIFICACIONES Y PODERES (Copias legibles cuando se trate de aumentos de capital, cambio de apoderados, modificación de objeto y/o denominación social, etc).  Requiere ser cotejado.",
            "1.23":	"COMPROBANTE DE DOMICILIO FISCAL , no mayor a 3 meses de antigüedad. (Luz, teléfono, predial o agua).  Requiere ser cotejado.",
            "1.23":	"COMPROBANTE DE DOMICILIO PERSONAL, no mayor a 3 meses de antigüedad. (Luz, teléfono, predial o agua).  Requiere ser cotejado.",
            "1.24":	"CONSTANCIA DE SITUACIÓN FISCAL del Obligado Solidario / Garante (No mayor a 1 año). Requiere ser Cotejado",
            "1.25":	"CONSTANCIA/IMPRESIÓN PANTALLA DE SERIE DE FIEL (Firma Electrónica) solo en caso de  contar con ella.",
            "1.25":	"En caso de que el Obligado o Garante sea Persona Moral archivar los documentos del apartado b)",
            },
        "I": {
            "1.26":	"PRESENTACIÓN INSTITUCIONAL",
            "1.33":	"CONSTANCIA DE REGISTRO ANTE EL SAT COMO ACTIVIDAD VULNERABLE (en su caso)",
            "1.34":	"CONSTANCIA DE REGISTRO DE RESPONSABLE DE CUMPLIMIENTO (en su caso)",

        },
        "II": {
            "2.1":	"ESTADOS FINANCIEROS: 2 ÚLTIMOS EJERCICIOS Y PARCIAL RECIENTE CON ANTIGÜEDAD PREFERENTEMENTE NO MAYOR A 3 MESES, PUDIENDO SER HASTA 6 MESES, Y CON RELACIONES ANALÍTICAS DE LAS PRINCIPALES CUENTAS (Auditados en su caso, y firmados por el representante y contador que los elabora, con la siguiente leyenda: Bajo protesta de decir verdad, manifiesto que las cifras contenidas en este Estado Financiero son veraces y contienen toda la información referente a la situación financiera y/o los resultados de la empresa y afirmo que somos legalmente responsables de la autenticidad y veracidad de las mismas, asumiendo asimismo, todo tipo de responsabilidad derivada de cualquier declaración en falso sobre las mismas",
            "2.2":	"ESTADOS DE CUENTA DE CHEQUES (Carátula de los últimos 3 meses, a partir de la información financiera mas reciente) de todas las Instituciones de Crédito en donde el Socio tiene cuenta.",
            "2.3":	"DECLARACIÓN ANUAL DE I.S.R. QUE CONTENGA EL ACUSE DE RECIBO CON EL SELLO DIGITAL (2 últimos ejercicios). Si se optó por DICTAMINAR, los estados financieros deberán ser los DICTAMINADOS. (actualizar anualmente).",

        },
        "III": {
            "3.1":	"CARTA DE TERMINOS Y CONDICIONES, firmada por el Socio.",
            "3.2":	"CARATULA DE RESOLUCION DE CREDITO FIRMADA ",
            "3.3":	"ESTUDIO DE CRÉDITO",
            "3.4":	"FORMATO DE REPORTE DE VISITA OCULAR CON FOTOGRAFÍAS  (Solo en caso de socio nuevo o inactivo por más de 12 meses).",
            "3.5":	"REPORTE DE BURO DE CRÉDITO DE LOS PARTICIPANTES EN EL CRÉDITO. EN CASO DE SOCIOS NUEVOS REPORTE DE BURO DE CRÉDITO ESPECIAL (Solo en el caso de socios que cuenten con saldo en el reporte de Buro de Crédito Normal) Y REPORTE DE LOS ACCIONISTAS CON PARTICIPACIÓN ACCIONARIA MAYOR A 25%, Y EN SU CASO AGREGAR LA DETERMINACIÓN DEL GRADO DE RIESGO INTERNO Y PROVISIÓN INICIAL. 			",
            "3.6":	"OPINIÓN DE CUMPLIMIENTO ANTE EL SAT  (No mayor a 3 meses)",
            "3.7":	"FLUJO DE EFECTIVO PROYECTADO CITANDO PREMISAS DE ELABORACION. Por la vigencia del crédito, mensualizado el primer año. (Solo para créditos mayores a 5 mdp y plazo mayor a 36 meses y en cualquier solicitud de una IFNB) (excepto garantía liquida)",
            "3.8":	"COTIZACIONES DE LOS CONCEPTOS A FINANCIAR/ARRENDAR. (En su caso)   En caso de construcción o remodelación, se requiere copia de proyecto y avance de obra",


        },
        "IV": {
            "4.1":	"GARANTIA LIQUIDA: CARTA MANDATO Y PAGARÉ DE INVERSION DEBIDAMENTE ENDOSADO (Copia)",
            "4.2":	"GARANTIA HIPOTECARIA: ESCRITURA INMUEBLE PROPUESTO EN GARANTÍA  (Copia legible con datos de inscripción en el Registro Publico de la Propiedad)  Y DICTAMEN JURIDICO ( Se actualizará solo en caso de cambios en la verificación). GARANTIA FIDUCIARIA: PAGO DE AGUA",
            "4.3":	"VERIFICACION DE ANTECEDENTES REGISTRALES DE LA PROPIEDAD. Vigencia Máxima: 12 Meses",
            "4.4":	"AVALUO Y BOLETA PREDIAL DEL INMUEBLE PROPUESTO EN GARANTÍA. (Año en curso)",
            "4.5":	"GARANTIA PRENDARIA: (Documentos que la acrediten: Facturas, cuentas por cobrar, titulos accionarios, etc).",
            "4.6":	"RELACION PATRIMONIAL DE LOS OBLIGADOS SOLIDARIOS (actualizar anualmente).",

        },
        "V": {
            "5.1":	"CONTRATO CELEBRADO CON LA UNIÓN DE CRÉDITO GENERAL, DEBE INCLUIR LOS FORMATOS SOLICITADOS POR CONDUSEF (copia).",
            "5.2":	"DISPOSICION DEL CRÉDITO: PAGARE Y TABLA DE AMORTIZACION. (Copia)",
            "5.3":	"CONTRATOS DE CRÉDITO QUE TENGA CON OTRAS INSTITUCIONES FINANCIERAS (copia simple) / Formato de Pasivos Bancarios",
            "5.4":	"CONTRATO DE ARRENDAMIENTO/COMODATO (copia) (en caso de que la empresa no sea propietaria del inmueble que ocupa).",
        },
        "VI": {
            "6.1":	"PÓLIZA DE SEGURO DE LA GARANTÍA, CON EL ENDOSO A FAVOR DE LA UNIÓN, PAGO ANUAL DE LA PRIMA, DEL AGUA Y BOLETA PREDIAL. (actualizar anualmente).",
            "6.2":	"COMPROBACION DEL CRÉDITO (indicando en qué se utilizaron los recursos)",
            "6.3":	"REPORTE ANUAL DE SEGUIMIENTO DE CONDICIONES DE HACER Y NO HACER, ESTATUS DE LAS GARANTÍAS DURANTE LA VIGENCIA DEL CRÉDITO.",
            "6.4":	"ACTUALIZACION ANUAL DEL REPORTE DE BURO DE ACREDITADOS Y OBLIGADOS SOLIDARIOS, AVALISTA O FIADOR",
            "6.5":	"REPORTE ANUAL DE DISPOSICIONES, PAGOS REALIZADOS, RENOVACIONES O REESTRUCTURAS, QUITAS, ADJUDICACIONES O DACIONES EN PAGO QUE SOPORTE LA CALIFICACION OTORGADA AL CREDITO",
            "6.6":	"CEDULA DE CALIFICACION DE CARTERA DE LOS ULTIMOS 4 TRIMESTRES",
            "6.7":	"INFORMACIÓN FONDEO",
        },        
    }

    for tipo, items in defaults.items():
        for clave, descripcion in items.items():
            ApartadoCatalogo.objects.get_or_create(
                tipoDeSeccion=tipo,
                clave=clave,
                defaults={'descripcion': descripcion}
            )
