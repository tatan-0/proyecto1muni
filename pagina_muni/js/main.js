// 1. Poner la fecha de hoy automáticamente en el formulario
document.getElementById('fecha').valueAsDate = new Date();

// 2. Función para cambiar entre las pestañas del menú lateral
function switchTab(panelId, element) {
    // Oculta todos los paneles de contenido
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    
    // Quita la marca de selección de todos los botones del menú
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    // Muestra solo el panel seleccionado y marca su botón activo
    document.getElementById(panelId).classList.add('active');
    element.classList.add('active');
}

// 3. Función para simular el guardado de una actividad diaria
let contadorRegistros = 2;

function registrarActividad(event) {
    // Evita que la página se recargue al enviar el formulario
    event.preventDefault();

    contadorRegistros++;
    
    // Obtener los datos ingresados por el funcionario
    const fechaVal = document.getElementById('fecha').value;
    const actividadVal = document.getElementById('actividad').value;
    const contactoVal = document.getElementById('contacto').value || 'Sin contacto';
    const itemVal = document.getElementById('itemSelect').value;

    // Generar un código único e inmutable de evidencia (ej: RUR742)
    const codigoGen = 'RUR' + Math.floor(100 + Math.random() * 900);

    // Crear la nueva fila para la tabla del historial
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

    // Agregar la nueva fila al inicio de la tabla
    tbody.prepend(row);
    
    // Mostrar mensaje de confirmación con el código asignado
    alert('¡Actividad registrada exitosamente!\nCódigo de Evidencia Asignado: ' + codigoGen);
    
    // Limpiar el formulario y reestablecer la fecha de hoy
    document.getElementById('actividadForm').reset();
    document.getElementById('fecha').valueAsDate = new Date();
}