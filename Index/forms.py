from django import forms
from db.models import *


class ExpedienteCrearForm(forms.ModelForm):
    socio = forms.ModelChoiceField(
        queryset=Socio.objects.all(), 
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="--- Seleccionar Socio Existente ---"
    )

    socio_manual_nombre = forms.CharField(
        label="Nombre del Nuevo Socio",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    TIPO_CHOICES = [
        ('F', 'Física'),
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
    
#class EditarSocio(forms.Form):
#    TIPO_CHOICES = [
#        ('F', 'Física'),
#        ('M', 'Moral'),
#    ]
#    tipo_Persona = forms.ChoiceField(
#        label="Tipo de Persona",
#        choices=TIPO_CHOICES,
#        required=False,
#        widget=forms.Select(attrs={'class': 'form-control'})
#    )
#    class Meta:
#        model = Socio
#        fields = ['nombre'] 
#
#        widgets = {
#            'usuario': forms.Select(attrs={'class': 'form-control'}),  
#
#        }

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
            'nombre': forms.TextInput(attrs={'class': 'form-control border border-3 border-primary my-2'}), 
            'color': forms.TextInput(attrs={'class': 'form-control border border-3 border-primary my-2 rounded-circle'}),
        }

EstadoFormSet = forms.modelformset_factory(Estado, form=ModificarEstados, extra=1, can_delete=True)