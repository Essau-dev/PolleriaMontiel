
// app/static/js/main.js
console.log("Pollería Montiel JS Cargado!");

// Lógica de UI global puede ir aquí
// Ejemplo: Manejo de menú hamburguesa en móvil, etc.

document.addEventListener('DOMContentLoaded', function () {
    // Ejemplo: Cerrar mensajes flash después de un tiempo
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        // Si no es un error persistente, quitarlo después de 5 segundos
        if (!alert.classList.contains('alert--error')) {
            setTimeout(function() {
                // alert.style.display = 'none'; // O una animación de fade-out
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, 7000); // 7 segundos
        }
        // Añadir un botón de cierre manual si no existe
        if (!alert.querySelector('.close-alert')) {
            const closeButton = document.createElement('button');
            closeButton.innerHTML = '×'; // Símbolo de 'x'
            closeButton.className = 'close-alert'; // Para estilizarlo
            closeButton.style.cssText = `
                position: absolute;
                top: 5px;
                right: 10px;
                background: transparent;
                border: none;
                font-size: 1.5rem;
                font-weight: bold;
                color: inherit;
                opacity: 0.7;
                cursor: pointer;
            `;
            closeButton.onmouseover = () => closeButton.style.opacity = '1';
            closeButton.onmouseout = () => closeButton.style.opacity = '0.7';
            closeButton.onclick = function() {
                // alert.style.display = 'none';
                 if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            };
            alert.appendChild(closeButton);
        }
    });

    // Más listeners de eventos o inicializaciones aquí
});

// Funciones helper de JS (ejemplos)
function mostrarSpinner(elementoPadre) {
    // Lógica para mostrar un indicador de carga
    const spinner = document.createElement('div');
    spinner.className = 'spinner'; // Estilizar .spinner en CSS
    spinner.textContent = 'Cargando...';
    if (elementoPadre) {
        elementoPadre.appendChild(spinner);
    }
    return spinner;
}

function ocultarSpinner(spinnerElement) {
    if (spinnerElement && spinnerElement.parentNode) {
        spinnerElement.parentNode.removeChild(spinnerElement);
    }
}

// Para peticiones Fetch (AJAX)
async function fetchData(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content'), // Si usas CSRF token en meta
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                ...options.headers,
            },
            ...options,
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ message: response.statusText }));
            throw new Error(errorData.message || `Error HTTP: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error en fetchData:', error);
        // Mostrar un mensaje de error al usuario, ej. con un mensaje flash dinámico
        mostrarMensajeFlash(`Error: ${error.message}`, 'error');
        throw error;
    }
}

function mostrarMensajeFlash(mensaje, categoria = 'info', contenedorId = 'flash-container') {
    // Esta función necesitaría un div con id="flash-container" en base.html
    // o podrías crear dinámicamente el contenedor de alertas.
    // Por simplicidad, aquí solo logueamos y asumimos que los mensajes flash del backend son suficientes por ahora.
    console.log(`FLASH [${categoria}]: ${mensaje}`);
    const flashContainer = document.getElementById(contenedorId) || document.querySelector('main.container');
    if(flashContainer){
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert--${categoria}`;
        alertDiv.setAttribute('role', 'alert');
        alertDiv.textContent = mensaje;
        // Añadir botón de cierre
        const closeButton = document.createElement('button');
        closeButton.innerHTML = '×';
        closeButton.className = 'close-alert';
        closeButton.style.cssText = `position: absolute; top: 5px; right: 10px; background: transparent; border: none; font-size: 1.5rem; cursor: pointer;`;
        closeButton.onclick = () => alertDiv.remove();
        alertDiv.appendChild(closeButton);

        flashContainer.insertBefore(alertDiv, flashContainer.firstChild);
        setTimeout(() => alertDiv.remove(), 7000);
    }
}
