from django import forms
from db.models import *
from django import forms
from django.contrib.auth.forms import UserChangeForm
class UserAdminForm(UserChangeForm):

    password = None 

    class Meta:
        model = User
        # Define los campos que el administrador PUEDE modificar
        fields = ('username', 'roles', 'is_active')
        
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control border border-3 border-primary my-2'}), 
            'roles': forms.Select(attrs={'class': 'form-control border border-3 border-primary my-2'}), 
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input border border-3 border-primary my-1'}),

        }
        def __init__(self, *args, **kwargs):
            super(UserAdminForm, self).__init__(*args, **kwargs)
            self.fields['username'].required = True
            self.fields['roles'].required = True
            self.fields['is_active'].required = True

class UserAdminPassForm(forms.ModelForm):
    nueva_contrasena = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control border border-3 border-primary my-2'}
        ),
        label="Contraseña",
        required=True
    )
    confirmar_contrasena = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control border border-3 border-primary my-2'}
        ),
        label="Confirmar Contraseña",
        required=True
    )
    
    class Meta:
        model = User
        fields = ('username', 'roles', 'is_active') 
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control border border-3 border-primary my-2'}), 
            'roles': forms.Select(attrs={'class': 'form-control border border-3 border-primary my-2'}), 
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input border border-3 border-primary my-1'}),
        }

    def __init__(self, *args, **kwargs):
        super(UserAdminPassForm, self).__init__(*args, **kwargs)
        self.fields['username'].required = True
        self.fields['roles'].required = True
        self.fields['is_active'].required = True

    def clean(self):
        cleaned_data = super().clean()
        nueva_contrasena = cleaned_data.get("nueva_contrasena")
        confirmar_contrasena = cleaned_data.get("confirmar_contrasena")

        if nueva_contrasena and confirmar_contrasena:
            if nueva_contrasena != confirmar_contrasena:
                raise forms.ValidationError("Las contraseñas no coinciden.")
        else:
            raise forms.ValidationError("Ambos campos de contraseña son requeridos.")
             
        return cleaned_data
        
    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("nueva_contrasena")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user

class UserPasswordForm(forms.Form):
    nueva_contrasena = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control border border-3 border-primary my-2'}
        ),
        label="Nueva Contraseña"
    )
    confirmar_contrasena = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control border border-3 border-primary my-2'}
        ),
        label="Confirmar Contraseña"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        nueva_contrasena = cleaned_data.get("nueva_contrasena")
        confirmar_contrasena = cleaned_data.get("confirmar_contrasena")

        if nueva_contrasena and confirmar_contrasena and nueva_contrasena != confirmar_contrasena:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data    

class ExpedienteCrearForm(forms.ModelForm):
    socio = forms.ModelChoiceField(
        queryset=Socio.objects.all(), 
        required=False,
        widget=forms.Select(attrs={'class': 'form-control',  'id': 'id_socio'}), #'onchange': 'cargarLineas()'
        empty_label="--- Seleccionar Socio Existente ---"
    )

    socio_manual_nombre = forms.CharField(
        label="Nombre del Nuevo Socio",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    TIPO_CHOICES = [
        ('F', 'Fisica'),
        ('M', 'Moral'),
    ]

    socio_manual_tipo = forms.ChoiceField(
        label="Tipo de Persona",
        choices=TIPO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    socio_manual_numero = forms.CharField(
        label="Numero Kepler",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Expediente
        fields = ['socio', 'usuario',] 
        widgets = {
            'usuario': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'socio' in self.data:
            try:
                socio_id = int(self.data.get('socio'))
                #self.fields['socio_linea'].queryset = Linea.objects.filter(socio_id=socio_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.socio:
            #self.fields['socio_linea'].queryset = self.instance.socio.linea_set.all()
            pass

    def clean(self):
        cleaned_data = super().clean()
        socio_existente = cleaned_data.get('socio')
        nombre_manual = cleaned_data.get('socio_manual_nombre')
        tipo_manual = cleaned_data.get('socio_manual_tipo')

        if socio_existente:
            cleaned_data['socio_manual_nombre'] = None
            cleaned_data['socio_manual_tipo'] = None
        elif nombre_manual:
            if not tipo_manual:
                self.add_error('socio_manual_tipo', 'Debe seleccionar si es Persona Física (F) o Moral (M) para un nuevo socio.')
            if not nombre_manual.strip():
                self.add_error('socio_manual_nombre', 'El nombre del nuevo socio no puede estar vacío.')

        return cleaned_data
    
class CrearObligado(forms.ModelForm):
    obligados = forms.CharField(widget=forms.HiddenInput(), required=False)
    obligado_selector = forms.ModelChoiceField(
        queryset=ObligadoSolidario.objects.all(),
        label="Obligado a Editar/Crear",
        empty_label="--- Nuevo Obligado ---",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select border border-3 border-primary my-2'})
    )

    class Meta:
        model = ObligadoSolidario
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].required = False

class CrearRepresentante(forms.ModelForm):
    representantes = forms.CharField(widget=forms.HiddenInput(), required=False)
    representante_selector = forms.ModelChoiceField(
        queryset=RepresentanteLegal.objects.all(),
        label="Representante a Editar/Crear",
        empty_label="--- Nuevo Representante ---",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select border border-3 border-primary my-2'})
    )

    class Meta:
        model = RepresentanteLegal
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].required = False
class LineaCrearForm(forms.ModelForm):
    class Meta:
        model = Linea
        fields = ['expediente', 'numero','monto','tipoLinea','vigente'] 
        widgets = {
            'expediente': forms.Select(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control'}),
            'tipoLinea': forms.Select(attrs={'class': 'form-control'}),


        }
    def __init__(self, *args, **kwargs):
            super(LineaCrearForm, self).__init__(*args, **kwargs)
            check_style = 'form-check-input fs-2 my-0'
            self.fields['vigente'].widget.attrs.update({'class': check_style})



class ModificarEstados(forms.ModelForm):
    class Meta:
        model = Estado
        fields = ['nombre', 'color'] 
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control border border-3 border-primary my-2 '}), 
            'color': forms.TextInput(attrs={'class': 'form-control border border-3 border-primary my-2 rounded-circle'}),
        }

class EditarSocio(forms.ModelForm):
    TIPO_CHOICES = [
        ('F', 'Fisica'),
        ('M', 'Moral'),
    ]
    
    socio_selector = forms.ModelChoiceField(
        queryset=Socio.objects.all(),
        label="Socio a Editar/Crear",
        empty_label="--- Nuevo Socio  ---",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select border border-3 border-primary my-2', 'onchange': 'cargarSocio(this.value)'})
    )

    tipoPersona = forms.ChoiceField(
        label="Tipo de Persona",
        choices=TIPO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select border border-3 border-primary my-2'})
    )
    
    class Meta:
        model = Socio
        fields = ['nombre', 'tipoPersona','numeroKepler'] 
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control border border-3 border-primary my-2'}), 
            'numeroKepler': forms.TextInput(attrs={'class': 'form-control border border-3 border-primary my-2'}), 
        }

class ModificarApartado(forms.ModelForm):
    class Meta:
        model = ApartadoCatalogo
        fields = ['tipoDeSeccion', 'clave', 'descripcion', 'areaDondeAplica']
        widgets = {
            'tipoDeSeccion': forms.Select(attrs={'class': 'form-select  border border-3 border-primary my-2'}),
            'clave': forms.TextInput(attrs={'class': 'form-control  border border-3 border-primary my-2'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control  border border-3 border-primary my-2', 'rows': 3}),
            'areaDondeAplica': forms.Select(attrs={'class': 'form-select  border border-3 border-primary my-2'}),
        }

class SelectorApartadoForm(forms.Form):
    apartado_selector = forms.ModelChoiceField(
        queryset=ApartadoCatalogo.objects.all(),
        label="Apartado a Editar",
        required=False,
        empty_label="--- Nuevo Apartado ---",
        widget=forms.Select(attrs={'class': 'form-select  border border-3 border-primary my-2', 'onchange': 'cargarApartado(this.value)'})
    )
#SociosoFormSet = forms.modelformset_factory(Socio, form=EditarSocio, extra=1, can_delete=True)

EstadoFormSet = forms.modelformset_factory(Estado, form=ModificarEstados, extra=1, can_delete=True)

