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


class UserAdminPassForm(UserChangeForm):

    nueva_contrasena = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control border border-3 border-primary my-2'}
        ),
        label="Contraseña",
        required=False 
    )
    confirmar_contrasena = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control border border-3 border-primary my-2'}
        ),
        label="Confirmar Contraseña",
        required=False
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
            self.fields['nueva_contrasena'].required = True
            self.fields['confirmar_contrasena'].required = True

    def clean(self):
        cleaned_data = super().clean()
        nueva_contrasena = cleaned_data.get("nueva_contrasena")
        confirmar_contrasena = cleaned_data.get("confirmar_contrasena")
        if nueva_contrasena == "" and confirmar_contrasena == "":
            raise forms.ValidationError("Las contraseñas no pueden quedar vacias.")

        if nueva_contrasena and nueva_contrasena != confirmar_contrasena:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        
        if (nueva_contrasena and not confirmar_contrasena) or (confirmar_contrasena and not nueva_contrasena):
             raise forms.ValidationError("Debes ingresar y confirmar la nueva contraseña.")
             
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
        widget=forms.Select(attrs={'class': 'form-control','onclick':'cargarSocio(this)'}),
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

    class Meta:
        model = Expediente
        fields = ['socio', 'usuario'] 

        widgets = {
            'usuario': forms.Select(attrs={'class': 'form-control'}),
        }

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
    
class RepresentantesForm(forms.Form):
    representantes = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

class ObligadosForm(forms.Form):
    obligados = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

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
        fields = ['nombre', 'tipoPersona'] 
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control border border-3 border-primary my-2'}), 
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
# La creación del formset debe funcionar correctamente con el cambio
#SociosoFormSet = forms.modelformset_factory(Socio, form=EditarSocio, extra=1, can_delete=True)

EstadoFormSet = forms.modelformset_factory(Estado, form=ModificarEstados, extra=1, can_delete=True)

