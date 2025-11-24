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
    
    # CAMBIO CLAVE AQUÍ: Lista vacía.
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = [] 

    objects = UserManager()
    is_active= models.BooleanField(default=True)

    def __str__(self):
        return self.username
    
class Socio(models.Model):
    #id por default
    nombre = models.CharField("Nombre", max_length=50, unique=True, null=True)
    #numRegistro = models.IntegerField("Num Registros":default=1)
    def __str__(self):
        return self.nombre
    
class Estado(models.Model):
    nombre = models.CharField("Nombre", max_length=30, unique=True, null=True)
    
    color = ColorField(
        default='#FFFFFF', 
        verbose_name="Color de Identificación" # Nombre amigable en el Admin
    )

    def __str__(self):
        return self.nombre


    def __str__(self):
        return self.nombre    
    
class Expediente(models.Model):
    socio = models.ForeignKey(
        Socio,
        on_delete=models.CASCADE, 
        null=False, 
        blank=False,
  
    )
    estatus = models.ForeignKey(Estado,on_delete=models.CASCADE)
    usuario = models.ForeignKey(User,blank=True,null=True,on_delete=CASCADE)
    fecha = models.DateField(auto_now_add=True, blank=True)
class ApartadoA(models.Model):
    expediente = models.OneToOneField(
        Expediente, 
        on_delete=models.CASCADE, 
        primary_key=True 
    )
    respuesta_a1 = models.CharField(max_length=255)
    respuesta_a2 = models.IntegerField()

    def __str__(self):
        return f"Apartado A de Expediente #{self.expediente.pk}"
    
class ApartadoB(models.Model):
    expediente = models.ForeignKey(
        Expediente, 
        on_delete=models.CASCADE,

        related_name='apartados_b_set' 
    )
    tipo = models.CharField(max_length=50)
    detalle = models.TextField()

    def __str__(self):
        return f"Apartado B ({self.tipo}) de Expediente #{self.expediente.pk}"

class ApartadoC(models.Model):
    expediente = models.ForeignKey(
        Expediente, 
        on_delete=models.CASCADE,
        related_name='apartados_c_set'
    )
    fecha = models.DateField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"Apartado C (Monto: {self.monto}) de Expediente #{self.expediente.pk}"

class ApartadoD(models.Model):
    expediente = models.OneToOneField(
        Expediente, 
        on_delete=models.CASCADE, 
        primary_key=True
    )
    respuesta_d1 = models.TextField()

    def __str__(self):
        return f"Apartado D de Expediente #{self.expediente.pk}"
    
