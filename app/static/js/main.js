// app/static/js/main.js
console.log("Pollería Montiel JS Cargado!");

// Lógica de UI global puede ir aquí

document.addEventListener('DOMContentLoaded', function () {
    // Ejemplo: Cerrar mensajes flash después de un tiempo
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        // Si no es un error persistente, quitarlo después de 7 segundos
        if (!alert.classList.contains('alert--error')) {
            setTimeout(function() {
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
                 if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            };
            alert.appendChild(closeButton);
        }
    });

    // Lógica para el menú hamburguesa en móvil
    const menuToggle = document.querySelector('.menu-toggle');
    const navMenu = document.querySelector('.nav-menu');
    const dropdownToggles = document.querySelectorAll('.site-header__nav .dropdown-toggle');

    if (menuToggle && navMenu) {
        menuToggle.addEventListener('click', function() {
            navMenu.classList.toggle('is-open');
            // Cerrar dropdowns si el menú principal se cierra
            if (!navMenu.classList.contains('is-open')) {
                 dropdownToggles.forEach(toggle => {
                     const dropdown = toggle.closest('.dropdown');
                     if (dropdown) {
                         dropdown.classList.remove('is-open');
                     }
                 });
            }
        });
    }

    // Lógica para abrir/cerrar dropdowns en móvil (al hacer clic en el toggle)
    dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', function(event) {
            // Prevenir la navegación por defecto si el enlace es '#'
            if (toggle.getAttribute('href') === '#') {
                 event.preventDefault();
            }
            const dropdown = toggle.closest('.dropdown');
            if (dropdown) {
                // Cerrar otros dropdowns abiertos en el mismo nivel
                dropdowns.forEach(otherDropdown => {
                    if (otherDropdown !== dropdown) {
                        otherDropdown.classList.remove('is-open');
                    }
                });
                dropdown.classList.toggle('is-open');
            }
        });
    });

    // Opcional: Cerrar menú y dropdowns si se hace clic fuera (en móvil)
    document.addEventListener('click', function(event) {
        const header = document.querySelector('.site-header');
        if (header && !header.contains(event.target)) {
            if (navMenu && navMenu.classList.contains('is-open')) {
                 navMenu.classList.remove('is-open');
                 // Cerrar dropdowns si el menú principal se cierra
                 dropdownToggles.forEach(toggle => {
                     const dropdown = toggle.closest('.dropdown');
                     if (dropdown) {
                         dropdown.classList.remove('is-open');
                     }
                 });
            }
        }
    });
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
                // 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content'), // Si usas CSRF token en meta
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

function mostrarMensajeFlash(mensaje, categoria = 'info', contenedorId = 'js-flash-container') {
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

        // Insertar al principio del contenedor
        flashContainer.insertBefore(alertDiv, flashContainer.firstChild);

        // Eliminar automáticamente después de 7 segundos, excepto errores
        if (categoria !== 'error') {
             setTimeout(() => alertDiv.remove(), 7000);
        }
    }
}
