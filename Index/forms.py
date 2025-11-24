from django import forms
from db.models import *

class ExpedienteCrearForm(forms.ModelForm):
    class Meta:
        model = Expediente
        fields = ['socio', 'usuario']

        widgets = {
            'socio': forms.Select(attrs={'class': 'form-select'}),
            'usuario': forms.Select(attrs={'class': 'form-select'}),
        }


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
