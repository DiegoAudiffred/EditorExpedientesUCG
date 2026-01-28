let reps = [];
let obls = [];

const socioSelect = document.getElementById('id_socio');
const nombreManualInput = document.getElementById('id_socio_manual_nombre');
const tipoManualSelect = document.getElementById('id_socio_manual_tipo');
const lineaSelect = document.getElementById('id_socio_linea')
const montoInput = document.getElementById('id_monto');
const spanInput = document.getElementById('span');

function syncHidden() {
    document.getElementsByName("representantes")[0].value = reps.join("||");
    document.getElementsByName("obligados")[0].value = obls.join("||");
}

function aplicarEstiloDeshabilitado(element, deshabilitar) {
    if (deshabilitar) {
        element.classList.add('bg-grayBorder');
    } else {
        element.classList.remove('bg-grayBorder');
    }
}

function cargarSocio(socioId) {
    if (!socioId) {
        tipoManualSelect.value = '';
        tipoManualSelect.disabled = false;
        aplicarEstiloDeshabilitado(tipoManualSelect, false);
        nombreManualInput.disabled = false;
        aplicarEstiloDeshabilitado(nombreManualInput, false);
        return;
    }

    fetch(`/obtener-socio-data/${socioId}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('No se pudo obtener el socio');
            }
            return response.json();
        })
        .then(data => {
            tipoManualSelect.value = data.tipoPersona;
            tipoManualSelect.disabled = true;
            aplicarEstiloDeshabilitado(tipoManualSelect, true);
        })
        .catch(error => console.error('Error al cargar datos del socio:', error));
}

function handleSocioSelectChange() {
    const selectedValue = socioSelect.value;
    if (selectedValue && selectedValue !== '') {
        nombreManualInput.value = '';
        tipoManualSelect.disabled = true;
        aplicarEstiloDeshabilitado(tipoManualSelect, true);
        nombreManualInput.disabled = true;
        aplicarEstiloDeshabilitado(nombreManualInput, true);
        cargarSocio(selectedValue);
    } else {
        tipoManualSelect.disabled = false;
        aplicarEstiloDeshabilitado(tipoManualSelect, false);
        nombreManualInput.disabled = false;
        aplicarEstiloDeshabilitado(nombreManualInput, false);
        tipoManualSelect.value = '';

        aplicarEstiloDeshabilitado(montoInput, false);
        montoInput.disabled = false;
        aplicarEstiloDeshabilitado(spanInput, false);
        montoInput.value = '';
        lineaSelect.value = '';
    }
}

function handleManualInputChange() {
    const manualName = nombreManualInput.value.trim();
    if (manualName !== '') {
        socioSelect.value = '';
        tipoManualSelect.disabled = false;
        aplicarEstiloDeshabilitado(tipoManualSelect, false);
    }
    handleSocioSelectChange();
}

socioSelect.addEventListener('change', handleSocioSelectChange);
nombreManualInput.addEventListener('input', handleManualInputChange);

handleSocioSelectChange();

function render() {
    const repList = document.getElementById("rep-list");
    repList.innerHTML = reps.map((x, i) => `
<div class="input-group m-3">
    <input type="text" class="form-control" value="${x}" oninput="reps[${i}]=this.value; syncHidden();">
    <button class="btn btn-danger" onclick="reps.splice(${i},1); render();">X</button>
</div>
`).join("");

    const oblList = document.getElementById("obl-list");
    oblList.innerHTML = obls.map((x, i) => `
<div class="input-group m-3">
    <input type="text" class="form-control" value="${x}" oninput="obls[${i}]=this.value; syncHidden();">
    <button class="btn btn-danger" onclick="obls.splice(${i},1); render();">X</button>
</div>
`).join("");

    syncHidden();
}

function agregarRep() {
    reps.push("");
    render();
}

function agregarObl() {
    obls.push("");
    render();
}

render();



document.querySelector('form').addEventListener('submit', function (e) {
    e.preventDefault();

    Swal.fire({
        title: 'Procesando...',
        text: 'Estamos creando el expediente',
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading() }
    });

    const formData = new FormData(this);

    fetch(window.location.href, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                Swal.fire({
                    icon: 'success',
                    title: '¡Creado!',
                    text: 'El expediente se ha generado correctamente',
                    timer: 2000,
                    showConfirmButton: false
                }).then(() => {
                    window.location.href = data.redirect_url;
                });
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Atención',
                    html: data.error,
                    confirmButtonColor: '#3085d6'
                });
            }
        })
        .catch(error => {
            Swal.fire({
                icon: 'error',
                title: 'Error de servidor',
                text: 'No se pudo completar la solicitud.'
            });
        });
});

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
