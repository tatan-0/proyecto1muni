document.getElementById('fecha').valueAsDate = new Date();

function switchTab(panelId, element) {

    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    

    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    document.getElementById(panelId).classList.add('active');
    element.classList.add('active');
}

let contadorRegistros = 2;

function registrarActividad(event) {
    event.preventDefault();

    contadorRegistros++;
    
    const fechaVal = document.getElementById('fecha').value;
    const actividadVal = document.getElementById('actividad').value;
    const contactoVal = document.getElementById('contacto').value || 'Sin contacto';
    const itemVal = document.getElementById('itemSelect').value;

    const codigoGen = 'RUR' + Math.floor(100 + Math.random() * 900);

    const tbody = document.querySelector('#tablaHistorial tbody');
    const row = document.createElement('tr');

    row.innerHTML = `
        <td>${contadorRegistros}</td>
        <td>${fechaVal}</td>
        <td>${actividadVal}</td>
        <td>${contactoVal}</td>
        <td>${itemVal}</td>
        <td><code>${codigoGen}</code></td>
        <td><span class="badge badge-verde">SÍ</span></td>
        <td><span class="badge badge-ambar">Pendiente</span></td>
    `;

    tbody.prepend(row);
    
    alert('¡Actividad registrada exitosamente!\nCódigo de Evidencia Asignado: ' + codigoGen);
    
    document.getElementById('actividadForm').reset();
    document.getElementById('fecha').valueAsDate = new Date();
}