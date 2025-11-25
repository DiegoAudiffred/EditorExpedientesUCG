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




"""Formatodevariables 
1.-camelCase
2.-singular
3.-espanol
"""


class User(AbstractUser):

    username = models.CharField('Usuario',max_length=20, unique=True, blank=True, null=True)
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = [] 

    objects = UserManager()
    is_active= models.BooleanField(default=True)

    def __str__(self):
        return self.username
    
class Socio(models.Model):
    #id por default
    idKepler = models.CharField("KeplerID",max_length=4,null=True)
    nombre = models.CharField("Nombre", max_length=50, unique=True, null=True)
    tipoPersona = models.CharField("Tipo",max_length=1,null=True)
    def __str__(self):
        return self.nombre
    
class Estado(models.Model):
    nombre = models.CharField("Nombre", max_length=30, unique=True, null=True)
    
    color = ColorField(
        default='#FFFFFF', 
        verbose_name="Color de Identificación" 
    )

    def __str__(self):
        return self.nombre


class Expediente(models.Model):
    socio = models.ForeignKey(Socio,on_delete=models.CASCADE,null=False,blank=False)
    estatus = models.ForeignKey(Estado,on_delete=models.CASCADE)
    usuario = models.ForeignKey(User,blank=True,null=True,on_delete=CASCADE)
    fecha = models.DateField(auto_now_add=True, blank=True)
    eliminado = models.BooleanField(default=False)
class SeccionesExpediente(models.Model):
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
class ApartadoCatalogo(models.Model):
    SECCIONES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('I', 'I'),
        ('II','II'),
        ('III','III'),
        ('IV','IV'),
        ('V','V'),
        ('VI','VI')
    ]

    tipoDeSeccion = models.CharField(max_length=3, choices=SECCIONES)
    clave = models.CharField(max_length=10)
    descripcion = models.TextField()

    class Meta:
        unique_together = ('tipoDeSeccion', 'clave')

    def __str__(self):
        return f"{self.tipoDeSeccion} - {self.clave}"

class RegistroSeccion(models.Model):
    seccion = models.ForeignKey(SeccionesExpediente, on_delete=models.CASCADE)
    apartado = models.ForeignKey(ApartadoCatalogo, on_delete=models.PROTECT)
    fecha = models.DateField(null=True, blank=True)
    estatus = models.CharField(max_length=20, null=True, blank=True)
    comentario = models.TextField(null=True, blank=True)

    class Meta:
        # ESTO EVITA DUPLICADOS Y ERRORES DE LÓGICA
        unique_together = ('seccion', 'apartado') 

    def __str__(self):
        return f"{self.seccion.tipoDeSeccion} - {self.apartado.clave}"