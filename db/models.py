from django.db import models

# Create your models here.
from datetime import datetime, timezone
import decimal
import math
import urllib
import json
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models.deletion import CASCADE
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q
from django.utils import timezone
from colorfield.fields import ColorField



from django.contrib.auth.models import BaseUserManager

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self,  password, **extra_fields):
        """Create and save a User with the given email and password."""

        user = self.model( **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user( password, **extra_fields)

    def create_superuser(self, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(password, **extra_fields)

TipoPersona = (
        ("F","F"),
        ("M","M")
    )

class User(AbstractUser):
    ROLES = (
        ('Ejecutivo de Negocios', 'Ejecutivo de Negocios'), #Sonia,Omar etc
        ('Ejecutivo de Servicios', 'Ejecutivo de Servicios'), #Andres,Maru
        ('Administrador', 'Administrador'), #Servilleta 
        ('Credito', 'Credito'), #Pao,etc
        ('Gerente de Credito', 'Gerente de Credito'),
        ('Gerente Centro de Negocios', 'Gerente Centro de Negocios')
    )


    username = models.CharField('Usuario',max_length=20, unique=True, blank=False, null=False,default="Nuevo")
    nombreCompleto = models.CharField('NombreCompleto',max_length=100, blank=True, null=True)
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = [] 
    roles = models.CharField(max_length=30, choices = ROLES, null=True,default='Administrador')
    #canEdit = models.BooleanField('Habilitar Usuario',default=False) #Sedara solo permisos a ejecutivos como Pao,Brisa
    objects = UserManager()
    is_active= models.BooleanField('Habilitar Usuario',default=True)

    def __str__(self):
        return self.username
    
class Socio(models.Model):
    #id por default
    nombre = models.CharField("Nombre", max_length=50, unique=True, null=True)
    #apellidoP
    #apellidoM
    tipoPersona = models.CharField("Tipo",max_length=1,null=True,choices=TipoPersona)
    is_socio = models.BooleanField("Socio",default=True)
    #is_obligado = models.BooleanField("Obligado Solidario",default=False)
    #is_representante = models.BooleanField("Representante Legal",default=False)
    numeroKepler = models.CharField("Numero en Kepler",default="",null=True,blank=True)
    def __str__(self):
        return self.nombre


  
    
class Estado(models.Model):
    nombre = models.CharField("Nombre", max_length=30,  null=True)
    
    color = ColorField(
        default='#FFFFFF', 
        verbose_name="Color de Identificación" 
    )

    def __str__(self):
        return self.nombre


class Expediente(models.Model):
    socio = models.ForeignKey(Socio, on_delete=models.CASCADE, null=False, blank=False)
    estatus = models.ForeignKey(Estado, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, related_name='centroNegocios', blank=True, null=True, on_delete=models.CASCADE)
    usuarioCredito = models.ForeignKey(User, related_name='credito', blank=True, null=True, on_delete=models.CASCADE)
    usuarioArchivo = models.ForeignKey(User, related_name='Archivado', blank=True, null=True, on_delete=models.CASCADE)
    fechaCreacion = models.DateField(auto_now_add=True, blank=True)
    usuarioNegocios = models.ForeignKey(User, related_name='negocios', blank=True, null=True, on_delete=models.CASCADE)

    eliminado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.socio}"
class EstadosFechas(models.Model):
    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE)
    fecha = models.DateField(null=True, blank=True)
    hora = models.TimeField(auto_now_add=True, blank=True,null=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, blank=True,null=True)


class Cita(models.Model):
    listaEstatus = (('Aceptada','Aceptada'),('Rechazada','Rechazada'),('Pendiente','Pendiente'))
    dia = models.DateField(null=True, blank=True)
    hora = models.TimeField(null=True, blank=True)
    expedientes = models.ManyToManyField(Expediente,related_name="Expedientes_Citas")
    usuario = models.ForeignKey(User, related_name='usuario', blank=True, null=True, on_delete=models.CASCADE)
    estatusCR = models.CharField(choices=listaEstatus,default='Pendiente')
    estatusCN = models.CharField(choices=listaEstatus,default='Pendiente')
       
class RepresentanteLegal(models.Model):
    nombre = models.CharField("Nombre", max_length=50, unique=True, null=True)
    expedientes = models.ManyToManyField(Expediente,related_name="Expedientes_Representantes")
    def __str__(self):
        return self.nombre
class ObligadoSolidario(models.Model):
    nombre = models.CharField("Nombre", max_length=50, unique=True, null=True)
    expedientes = models.ManyToManyField(Expediente,related_name="Expedientes_Obligados")

    tipoPersona = models.CharField("Tipo",choices=TipoPersona,max_length=1,null=True)
    def __str__(self):
        return self.nombre
class Garantia(models.Model):
    garantias = (
        ("Hipotecaria","Hipotecaria"),
        ("Prendaria","Prendaria"),
        ("Colateral","Colateral"),
        ("Avales","Avales"),
        ("Fiduciaria","Fiduciaria"),
        ("Sin garantia","Sin garantia")
    )
    nombre = models.CharField(choices=garantias,blank=False,default="Cuenta Corriente", max_length=50,unique=True, null=False)

    def __str__(self):
        return self.nombre


class Linea(models.Model):
    tipoLinea = (
        ("Cuenta Corriente","Cuenta Corriente"),
        ("Simple","Simple"),
        ("Habilitacion","Habilitacion"),
        ("Refaccionario","Refaccionario"),
        ("Factoraje", "Factoraje"),
        ("Quirografario","Quirografario"),
        ("Linea de descuento","Linea de descuento")
    )    
    


    expediente = models.ForeignKey(Expediente,on_delete=models.CASCADE,null=False,blank=False)
    numero = models.CharField("Numero", max_length=10, blank=False,null=False,unique=True)
    monto = models.IntegerField(default=0,blank=False,null=False)  
    vigente = models.BooleanField(default=True)
    tipoLinea = models.CharField(choices=tipoLinea,blank=False,default="Cuenta Corriente", max_length=50)
    tipoGarantia = models.ManyToManyField(Garantia, blank=True, related_name="lineas")
    
    def __str__(self):
        return self.numero
    
class SeccionesExpediente(models.Model):#ENCABEZADO DE LA SECCION Y SU NOMBRE
    SECCIONES = [
        ('A', 'Solicitante'),
        ('B', 'Representante legal'),
        ('C', 'Obligado solidario y garantes'),
        ('I', 'Actividades vulnerables'),
        ('II','Informacion Financiera'),
        ('III','Estudio de Crédito'),
        ('IV','Información de garantias'),
        ('V','Contratos'),
        ('VI','Seguimiento')
    ]

    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE)
    tipoDeSeccion = models.CharField(max_length=3, choices=SECCIONES)
    tituloSeccion = models.CharField(max_length=100, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.tituloSeccion:
            self.tituloSeccion = dict(self.SECCIONES).get(self.tipoDeSeccion, '')
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.expediente.socio} - {self.tipoDeSeccion} - {self.tituloSeccion} - {self.expediente}"
class ApartadoCatalogo(models.Model):#Los Apartados que existen la info del renglon
    SECCIONES = [
        ('A', 'A'), ('B', 'B'), ('C', 'C'), ('I', 'I'),
        ('II','II'), ('III','III'), ('IV','IV'), ('V','V'), ('VI','VI')
    ]
    AREAS = [('Fisicas','Fisicas'),('Ambas','Ambas'),('Morales','Morales')] 
    
    tipoDeSeccion = models.CharField(max_length=7, choices=SECCIONES)
    clave = models.CharField(max_length=10)
    descripcion = models.TextField()
    areaDondeAplica = models.CharField(max_length=8, choices=AREAS, null=True, blank=True) 

    class Meta:
        unique_together = ('tipoDeSeccion', 'clave')
        ordering = ['tipoDeSeccion', 'clave']

    def __str__(self):
        return f"{self.tipoDeSeccion} - {self.clave}"
class RegistroSeccion(models.Model): #El renglon
    seccion = models.ForeignKey(SeccionesExpediente, on_delete=models.CASCADE)
    apartado = models.ForeignKey(ApartadoCatalogo, on_delete=models.PROTECT)
    fecha = models.DateField(null=True, blank=True)
    numero = models.IntegerField(max_length=10, null=True, blank=True)
    estatus = models.CharField(max_length=20, null=True, blank=True)
    comentario = models.TextField(null=True, blank=True)
    comentarioCredito = models.TextField(null=True, blank=True)
    es_fecha = models.BooleanField(default=True)


    class Meta:
        # ESTO EVITA DUPLICADOS Y ERRORES DE LÓGICA
        unique_together = ('seccion', 'apartado') 

    def __str__(self):
        return f"{self.seccion.tipoDeSeccion} - {self.apartado.clave} {self.seccion.expediente.socio}"
