function cargarLineas() {
    const socioId = document.getElementById('id_socio').value;
    const lineaSelect = document.getElementById('id_socio_linea');
    const montoInput = document.getElementById('id_monto');

    lineaSelect.innerHTML = '<option value="">--- Seleccione Linea ---</option>';
    montoInput.value = '';

    if (!socioId) return;

    fetch(`/obtener-lineas-socio/${socioId}/`)

        .then(response => response.json())
        .then(data => {
            data.forEach(linea => {
                const option = document.createElement('option');
                option.value = linea.id;
                option.textContent = linea.numero;
                option.setAttribute('data-monto', linea.monto);
                lineaSelect.appendChild(option);

            });
        });
}

function actualizarMonto() {



    const selectedOption = lineaSelect.options[lineaSelect.selectedIndex];

    if (selectedOption && selectedOption.getAttribute('data-monto')) {
        montoInput.value = selectedOption.getAttribute('data-monto');
        aplicarEstiloDeshabilitado(montoInput, true);
        montoInput.disabled = true;
        aplicarEstiloDeshabilitado(spanInput, true);



    } else {
        montoInput.value = '';
        aplicarEstiloDeshabilitado(montoInput, false);
        montoInput.disabled = false;
        aplicarEstiloDeshabilitado(spanInput, false);
    }
}
socio_linea = forms.ModelChoiceField(
    label = "Linea del expediente",
    queryset = Linea.objects.none(),
    required = False,
    widget = forms.Select(attrs = { 'class': 'form-control', 'id': 'id_socio_linea', 'onchange': 'actualizarMonto()' }),
)

monto = forms.IntegerField(
    label = "Monto del expediente",
    required = False,
    widget = forms.NumberInput(attrs = { 'class': 'form-control border-start-0 ps-0', 'id': 'id_monto' }),
)
