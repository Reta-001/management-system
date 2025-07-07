// Modales edición y eliminación 
const deleteVentaModal = document.getElementById('deleteVentaModal');

deleteVentaModal.addEventListener('show.bs.modal', function (event) {
  const button = event.relatedTarget;
  const id = button.getAttribute('data-id');
  
  document.getElementById('delete-id').value = id;
  
  // Buscar el número de venta en el DOM
  const ventaElement = document.querySelector(`[data-bs-target="#collapse${id}"]`);
  if (ventaElement) {
    const ventaText = ventaElement.querySelector('.fw-bold').textContent;
    const numeroVenta = ventaText.match(/Venta #(\d+)/);
    if (numeroVenta) {
      document.getElementById('delete-producto').textContent = `#${numeroVenta[1]}`;
    } else {
      document.getElementById('delete-producto').textContent = `#${id}`;
    }
  } else {
    document.getElementById('delete-producto').textContent = `#${id}`;
  }
  
  document.getElementById('deleteVentaForm').action = `/ventas/eliminar/${id}/`;
});

// Manejar todos los formularios con AJAX
document.addEventListener('DOMContentLoaded', function() {
  console.log('DOMContentLoaded iniciado');
  
  // Manejar el envío del formulario de eliminación con AJAX
  const deleteVentaForm = document.getElementById('deleteVentaForm');
  if (deleteVentaForm) {
    console.log('Formulario de eliminación encontrado');
    
    deleteVentaForm.addEventListener('submit', function (event) {
      console.log('Formulario de eliminación enviado, previniendo envío normal');
      event.preventDefault();
      event.stopPropagation();
      
      const formData = new FormData(this);
      const modal = document.getElementById('deleteVentaModal');
      const submitButton = modal.querySelector('button[type="submit"]');
      const originalText = submitButton.innerHTML;
      
      console.log('ID de la venta a eliminar:', formData.get('id'));
      
      // Deshabilitar botón y mostrar loading
      submitButton.disabled = true;
      submitButton.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Eliminando...';
      
      fetch('/ventas/eliminar/' + formData.get('id') + '/', {
        method: 'POST',
        body: formData,
        headers: {
          'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        }
      })
      .then(response => {
        console.log('Respuesta de eliminación recibida:', response);
        // Intentar parsear como JSON
        return response.json();
      })
      .then(data => {
        if (data) {
          console.log('Datos de eliminación recibidos:', data);
          
          if (data.success) {
            // Eliminación exitosa, cerrar el modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('deleteVentaModal'));
            modal.hide();
            
            // Mostrar mensaje con botón deshacer
            mostrarMensajeConDeshacer(data.message, data.venta_id);
            
            // Eliminar acordeón de la venta eliminada
            actualizarTablaVentas(data.venta_id);
          } else {
            // Error
            mostrarMensajeEnModal('deleteVentaModal', data.message, 'danger');
          }
          
          // Restaurar botón
          submitButton.disabled = false;
          submitButton.innerHTML = originalText;
        }
      })
      .catch(error => {
        console.error('Error en eliminación:', error);
        // Si hay error, recargar la página para mostrar los mensajes de Django
        window.location.reload();
      });
      
      return false;
    });
  } else {
    console.log('Formulario de eliminación NO encontrado');
  }
});

// Función para mostrar mensajes en modales
function mostrarMensajeEnModal(modalId, mensaje, tipo) {
  console.log('Mostrando mensaje en modal:', modalId, mensaje, tipo);
  
  const modal = document.getElementById(modalId);
  let alertDiv = modal.querySelector('.modal-alert');
  
  // Crear div de alerta si no existe
  if (!alertDiv) {
    alertDiv = document.createElement('div');
    alertDiv.className = 'modal-alert alert mt-3';
    alertDiv.style.display = 'none';
    
    // Insertar al inicio del modal-footer (arriba de los botones)
    const modalFooter = modal.querySelector('.modal-footer');
    modalFooter.insertBefore(alertDiv, modalFooter.firstChild);
  }
  
  // Configurar el mensaje
  alertDiv.className = `modal-alert alert alert-${tipo} mt-3`;
  
  // Icono según el tipo
  let icon = 'bi-exclamation-triangle';
  if (tipo === 'success') {
    icon = 'bi-check-circle';
  } else if (tipo === 'info') {
    icon = 'bi-info-circle';
  }
  
  alertDiv.innerHTML = `
    <i class="bi ${icon} me-2"></i>
    ${mensaje}
  `;
  alertDiv.style.display = 'block';
  
  console.log('Mensaje mostrado en modal');
  
  // Auto-ocultar mensajes de error después de 5 segundos
  if (tipo === 'danger' || tipo === 'warning') {
    setTimeout(() => {
      alertDiv.style.display = 'none';
    }, 5000);
  }
}

// Función para mostrar notificaciones push modernas
function mostrarMensajeEnPagina(mensaje, tipo) {
  console.log('Mostrando notificación push:', mensaje, tipo);
  
  // Crear el contenedor de notificaciones si no existe
  let notificationContainer = document.getElementById('notification-container');
  if (!notificationContainer) {
    notificationContainer = document.createElement('div');
    notificationContainer.id = 'notification-container';
    notificationContainer.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      gap: 10px;
      max-width: 350px;
    `;
    document.body.appendChild(notificationContainer);
  }
  
  // Crear la notificación
  const notification = document.createElement('div');
  notification.className = 'notification';
  notification.style.cssText = `
    background: ${tipo === 'danger' ? '#dc3545' : '#198754'};
    color: white;
    padding: 16px 20px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    transform: translateX(400px);
    transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
    position: relative;
    overflow: hidden;
    font-family: 'Poppins', sans-serif;
    font-weight: 500;
  `;
  
  // Agregar barra de progreso
  const progressBar = document.createElement('div');
  progressBar.style.cssText = `
    position: absolute;
    bottom: 0;
    left: 0;
    height: 3px;
    background: rgba(255,255,255,0.3);
    width: 100%;
    transform: scaleX(1);
    transform-origin: left;
    transition: transform 3s linear;
  `;
  
  notification.appendChild(progressBar);
  
  // Contenido de la notificación
  notification.innerHTML += `
    <div style="display: flex; align-items: center; justify-content: space-between;">
      <div style="flex: 1;">
        <div style="font-size: 16px; font-weight: 600; text-align: center;">
          ${mensaje}
        </div>
      </div>
      <button onclick="this.parentElement.parentElement.remove()" 
              style="background: none; border: none; color: white; font-size: 18px; cursor: pointer; padding: 0; margin-left: 12px; opacity: 0.7; transition: opacity 0.2s;">
        ×
      </button>
    </div>
  `;
  
  // Agregar la notificación al contenedor
  notificationContainer.appendChild(notification);
  
  // Animar entrada
  setTimeout(() => {
    notification.style.transform = 'translateX(0)';
  }, 10);
  
  // Animar barra de progreso
  setTimeout(() => {
    progressBar.style.transform = 'scaleX(0)';
  }, 100);
  
  // Auto-remover después de 3 segundos
  setTimeout(() => {
    if (notification.parentElement) {
      notification.style.transform = 'translateX(400px)';
      setTimeout(() => {
        if (notification.parentElement) {
          notification.remove();
        }
      }, 300);
    }
  }, 3000);
  
  // Efecto hover
  notification.addEventListener('mouseenter', () => {
    notification.style.transform = 'translateX(0) scale(1.02)';
    progressBar.style.transition = 'none';
  });
  
  notification.addEventListener('mouseleave', () => {
    notification.style.transform = 'translateX(0) scale(1)';
    progressBar.style.transition = 'transform 3s linear';
  });
}

// Función para mostrar mensaje con botón deshacer
function mostrarMensajeConDeshacer(mensaje, ventaId) {
  console.log('Mostrando mensaje con deshacer:', mensaje, ventaId);
  
  // Crear el contenedor de notificaciones si no existe
  let notificationContainer = document.getElementById('notification-container');
  if (!notificationContainer) {
    notificationContainer = document.createElement('div');
    notificationContainer.id = 'notification-container';
    notificationContainer.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      gap: 10px;
      max-width: 350px;
    `;
    document.body.appendChild(notificationContainer);
  }
  
  // Crear la notificación con botón deshacer
  const notification = document.createElement('div');
  notification.className = 'notification';
  notification.style.cssText = `
    background: #dc3545;
    color: white;
    padding: 16px 20px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    transform: translateX(400px);
    transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
    position: relative;
    overflow: hidden;
    font-family: 'Poppins', sans-serif;
    font-weight: 500;
  `;
  
  // Agregar barra de progreso
  const progressBar = document.createElement('div');
  progressBar.style.cssText = `
    position: absolute;
    bottom: 0;
    left: 0;
    height: 3px;
    background: rgba(255,255,255,0.3);
    width: 100%;
    transform: scaleX(1);
    transform-origin: left;
    transition: transform 10s linear;
  `;
  
  notification.appendChild(progressBar);
  
  // Contenido de la notificación con botón deshacer
  notification.innerHTML += `
    <div style="display: flex; align-items: center; justify-content: space-between;">
      <div style="flex: 1;">
        <div style="font-size: 16px; font-weight: 600; margin-bottom: 8px; text-align: center;">
          ${mensaje}
        </div>
        <div style="text-align: center;">
          <button id="btnDeshacerEliminacion" 
                  onclick="restaurarVenta(${ventaId}, this)" 
                  style="background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); color: white; padding: 6px 12px; border-radius: 4px; font-size: 12px; cursor: pointer; transition: all 0.2s; font-weight: 500;">
            Deshacer
          </button>
        </div>
      </div>
      <button onclick="this.parentElement.parentElement.remove()" 
              style="background: none; border: none; color: white; font-size: 18px; cursor: pointer; padding: 0; margin-left: 12px; opacity: 0.7; transition: opacity 0.2s;">
        ×
      </button>
    </div>
  `;
  
  // Agregar la notificación al contenedor
  notificationContainer.appendChild(notification);
  
  // Animar entrada
  setTimeout(() => {
    notification.style.transform = 'translateX(0)';
  }, 10);
  
  // Animar barra de progreso
  setTimeout(() => {
    progressBar.style.transform = 'scaleX(0)';
  }, 100);
  
  // Auto-remover después de 10 segundos
  setTimeout(() => {
    if (notification.parentElement) {
      notification.style.transform = 'translateX(400px)';
      setTimeout(() => {
        if (notification.parentElement) {
          notification.remove();
        }
      }, 300);
    }
  }, 10000);
  
  // Efecto hover
  notification.addEventListener('mouseenter', () => {
    notification.style.transform = 'translateX(0) scale(1.02)';
    progressBar.style.transition = 'none';
  });
  
  notification.addEventListener('mouseleave', () => {
    notification.style.transform = 'translateX(0) scale(1)';
    progressBar.style.transition = 'transform 10s linear';
  });
}

// Función para restaurar venta
function restaurarVenta(ventaId, button) {
  console.log('Restaurando venta:', ventaId);
  
  // Deshabilitar botón
  button.disabled = true;
  button.textContent = 'Restaurando...';
  button.style.opacity = '0.7';
  
  // Enviar petición para restaurar
  fetch(`/ventas/restaurar/${ventaId}/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
    }
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      // Mostrar mensaje de éxito
      mostrarMensajeEnPagina(data.message, 'success');
      
      // Actualizar tabla
      actualizarTablaVentas();
      
      // Remover la notificación de eliminación
      const notification = button.closest('.notification');
      if (notification) {
        notification.remove();
      }
    } else {
      // Mostrar error
      alert('Error al restaurar la venta: ' + data.message);
      
      // Restaurar botón
      button.disabled = false;
      button.textContent = 'Deshacer';
      button.style.opacity = '1';
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('Error al restaurar la venta');
    
    // Restaurar botón
    button.disabled = false;
    button.textContent = 'Deshacer';
    button.style.opacity = '1';
  });
}

// Función para actualizar la tabla de ventas dinámicamente
function actualizarTablaVentas(ventaEliminadaId = null) {
  // Si se pasa un ID, eliminar solo ese acordeón
  if (ventaEliminadaId) {
    const acordeon = document.querySelector(`.accordion-item [data-id="${ventaEliminadaId}"]`);
    if (acordeon) {
      const item = acordeon.closest('.accordion-item');
      if (item) item.remove();
    }
    // Si no quedan ventas, mostrar mensaje
    if (!document.querySelector('.accordion-item')) {
      const accordion = document.querySelector('.accordion');
      if (accordion) {
        accordion.innerHTML = '<div class="alert alert-info mb-0">No hay ventas registradas.</div>';
      }
    }
    return;
  }
  
  // Si no, obtener datos actualizados del servidor
  fetch(window.location.href)
    .then(response => response.text())
    .then(html => {
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');
      
      // Buscar específicamente el card-body del historial de ventas (el segundo card-body)
      const cardBodies = doc.querySelectorAll('.card-body');
      if (cardBodies.length >= 2) {
        const nuevaSeccionHistorial = cardBodies[1]; // El segundo card-body es el del historial
        const seccionHistorialActual = document.querySelectorAll('.card-body')[1]; // El segundo card-body actual
        
        if (nuevaSeccionHistorial && seccionHistorialActual) {
          // Actualizar solo el contenido del card-body del historial, NO el del carrito
          seccionHistorialActual.innerHTML = nuevaSeccionHistorial.innerHTML;
        } else {
          // Si no se encuentra, recargar la página como fallback
          window.location.reload();
        }
      } else {
        // Si no hay suficientes card-bodies, recargar la página
        window.location.reload();
      }
    })
    .catch(error => {
      console.error('Error al actualizar tabla:', error);
      // Si hay error, recargar la página como fallback
      window.location.reload();
    });
}

// Interceptar formulario de agregar al carrito
(function() {
  const addManualForm = document.querySelector('#addManualModal form');
  if (addManualForm) {
    addManualForm.addEventListener('submit', function(e) {
      // NO prevenir el envío por defecto - dejar que Django maneje todo
      const submitBtn = this.querySelector('button[type="submit"]');
      const originalText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Agregando...';
      
      // El formulario se enviará normalmente y Django mostrará el mensaje
    });
  }
})();

// Interceptar formulario de finalizar venta
(function() {
  const finalizarForm = document.querySelector('form[action$="finalizar/"]');
  if (finalizarForm) {
    finalizarForm.addEventListener('submit', function(e) {
      e.preventDefault();
      const formData = new FormData(this);
      const submitBtn = this.querySelector('button[type="submit"]');
      const originalText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Procesando...';
      fetch(this.action, {
        method: 'POST',
        body: formData,
        headers: {
          'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      .then(res => res.redirected ? window.location.href = res.url : res.json())
      .then(data => {
        if (data && data.success) {
          mostrarMensajeEnPagina('Venta agregada correctamente', 'success');
          
          // Vaciar el carrito en la interfaz
          const carritoCardBody = document.querySelector('.card-body');
          if (carritoCardBody) {
            // Buscar si hay una tabla en el carrito
            const carritoTable = carritoCardBody.querySelector('.table-responsive');
            if (carritoTable) {
              // Si hay tabla, reemplazar todo el contenido del card-body
              carritoCardBody.innerHTML = '<div class="alert alert-info mb-0">El carrito está vacío. Añade productos para iniciar una venta.</div>';
            } else {
              // Si no hay tabla, verificar si ya está vacío
              const alertaVacio = carritoCardBody.querySelector('.alert-info');
              if (!alertaVacio) {
                carritoCardBody.innerHTML = '<div class="alert alert-info mb-0">El carrito está vacío. Añade productos para iniciar una venta.</div>';
              }
            }
          }
          
          // Actualizar tabla de ventas para mostrar la nueva venta
          actualizarTablaVentas();
        } else if (data && data.message) {
          mostrarMensajeEnPagina(data.message, 'danger');
        }
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
      })
      .catch(() => {
        mostrarMensajeEnPagina('Error al finalizar venta', 'danger');
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
      });
    });
  }
})();

// Animación de ícono acordeón
window.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.accordion-button').forEach(function(btn) {
    btn.addEventListener('click', function() {
      setTimeout(() => {
        btn.blur();
      }, 300);
    });
  });
});

// Script para el escaneo de códigos
(function() {
  const scanCodeModalEl = document.getElementById('scanCodeModal');
  const scanCodeInput = document.getElementById('scanCodeInput');
  const scanMessage = document.getElementById('scanMessage');
  let scanTimeout = null;

  function showError(message) {
    scanMessage.innerHTML = message;
    scanMessage.style.display = 'block';
  }

  function clearError() {
    scanMessage.innerHTML = '';
    scanMessage.style.display = 'none';
  }

  if (scanCodeModalEl && scanCodeInput && scanMessage) {
    scanCodeModalEl.addEventListener('shown.bs.modal', () => {
      scanCodeInput.value = '';
      clearError();
      scanCodeInput.focus();
    });

    scanCodeInput.addEventListener('keydown', function(event) {
      if(event.key === 'Enter') {
        event.preventDefault();
        const codigo = this.value.trim();
        if(codigo === '') return;

        // Limpiar timeout anterior si existe
        if (scanTimeout) {
          clearTimeout(scanTimeout);
        }

        // Validar el código
        fetch(scanCodeModalEl.getAttribute('data-validar-url') || '/ventas/validar_codigo/?codigo=' + encodeURIComponent(codigo))
          .then(response => response.json())
          .then(data => {
            if(!data.existe) {
              showError(`⚠️ No se encontró el código "<strong>${codigo}</strong>".`);
              scanCodeInput.value = '';
              scanCodeInput.focus();
            } else {
              // Código existe, cerrar modal escaneo y abrir modal agregar producto
              const scanModalInstance = bootstrap.Modal.getInstance(scanCodeModalEl);
              scanModalInstance.hide();

              // Abrir modal de agregar producto
              const addManualModal = new bootstrap.Modal(document.getElementById('addManualModal'));
              addManualModal.show();

              // Poner código en el input de producto y poner foco
              const productoInput = document.getElementById('producto_autocomplete');
              if(productoInput) {
                productoInput.value = codigo;
                productoInput.focus();
                // Disparar el evento input para activar la búsqueda
                productoInput.dispatchEvent(new Event('input'));
              }
            }
          })
          .catch(() => {
            showError('⚠️ Error al validar el código. Intente nuevamente.');
            scanCodeInput.value = '';
            scanCodeInput.focus();
          });
      }
    });

    // Limpiar el input después de un tiempo si no se completó el escaneo
    scanCodeInput.addEventListener('input', function() {
      if (scanTimeout) {
        clearTimeout(scanTimeout);
      }
      scanTimeout = setTimeout(() => {
        this.value = '';
      }, 1000);
    });

    // Limpiar error al cerrar el modal
    scanCodeModalEl.addEventListener('hidden.bs.modal', () => {
      clearError();
      scanCodeInput.value = '';
    });
  }
})();

// Abrir modal de agregar manual desde botón (si existe)
const btnAgregarManual = document.getElementById('btnAgregarManual');
if (btnAgregarManual) {
  btnAgregarManual.addEventListener('click', () => {
    // Ocultar modal de escaneo
    const scanModalEl = document.getElementById('scanCodeModal');
    const scanModal = bootstrap.Modal.getInstance(scanModalEl);
    scanModal.hide();

    // Abrir modal de añadir venta
    const addVentaModalEl = document.getElementById('addVentaModal');
    const addVentaModal = new bootstrap.Modal(addVentaModalEl);
    addVentaModal.show();
  });
}

// Autocomplete y validación en modal de agregar producto
(function() {
  const input = document.getElementById('producto_autocomplete');
  const suggestions = document.getElementById('autocomplete_suggestions');
  const hiddenId = document.getElementById('producto_id_hidden');
  const categoriaFiltro = document.getElementById('categoria_filtro');
  const errorMsg = document.getElementById('addManualErrorMsg');
  const form = document.querySelector('#addManualModal form');
  let currentFocus = -1;
  let productos = [];

  if (!input || !suggestions || !hiddenId || !categoriaFiltro || !errorMsg || !form) return;

  function closeSuggestions() {
    suggestions.innerHTML = '';
    suggestions.style.display = 'none';
    currentFocus = -1;
  }

  function showError(message) {
    errorMsg.innerHTML = message;
    errorMsg.classList.remove('d-none');
  }

  function clearError() {
    errorMsg.innerHTML = '';
    errorMsg.classList.add('d-none');
  }

  function renderSuggestions(items) {
    suggestions.innerHTML = '';
    if (!items.length) {
      suggestions.style.display = 'none';
      return;
    }
    items.forEach((item, idx) => {
      const div = document.createElement('button');
      div.type = 'button';
      div.className = 'list-group-item list-group-item-action';
      div.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
          <div>
            <strong>${item.nombre}</strong>
            <br>
            <small class="text-muted">Código: ${item.codigo}</small>
          </div>
          <span class="badge bg-primary rounded-pill">$${item.precio_venta}</span>
        </div>
      `;
      div.onclick = function() {
        input.value = item.nombre;
        hiddenId.value = item.id;
        closeSuggestions();
        clearError();
      };
      suggestions.appendChild(div);
    });
    suggestions.style.display = 'block';
  }

  function fetchProductos() {
    const q = input.value.trim();
    const categoria = categoriaFiltro.value;
    if (q.length === 0) {
      closeSuggestions();
      hiddenId.value = '';
      return;
    }
    fetch(`/ventas/autocomplete_productos/?q=${encodeURIComponent(q)}${categoria ? '&categoria=' + encodeURIComponent(categoria) : ''}`)
      .then(res => res.json())
      .then(data => {
        productos = data.results || [];
        renderSuggestions(productos);
        
        if (productos.length === 1) {
          hiddenId.value = productos[0].id;
        } else {
          hiddenId.value = '';
        }
      });
  }

  input.addEventListener('input', fetchProductos);
  categoriaFiltro.addEventListener('change', fetchProductos);
  input.addEventListener('focus', fetchProductos);

  input.addEventListener('keydown', function(e) {
    const items = suggestions.querySelectorAll('.list-group-item');
    if (!items.length) return;
    if (e.key === 'ArrowDown') {
      currentFocus++;
      if (currentFocus >= items.length) currentFocus = 0;
      items.forEach((el, idx) => el.classList.toggle('active', idx === currentFocus));
      e.preventDefault();
    } else if (e.key === 'ArrowUp') {
      currentFocus--;
      if (currentFocus < 0) currentFocus = items.length - 1;
      items.forEach((el, idx) => el.classList.toggle('active', idx === currentFocus));
      e.preventDefault();
    } else if (e.key === 'Enter') {
      if (currentFocus > -1 && items[currentFocus]) {
        e.preventDefault();
        items[currentFocus].click();
      }
      else if (productos.length === 1) {
        e.preventDefault();
        input.value = productos[0].nombre;
        hiddenId.value = productos[0].id;
        closeSuggestions();
      }
    }
  });

  document.addEventListener('click', function(e) {
    if (!suggestions.contains(e.target) && e.target !== input) {
      closeSuggestions();
    }
  });

  // Validar al enviar el formulario
  form.addEventListener('submit', function(e) {
    e.preventDefault();
    const productoInput = input.value.trim();
    const cantidadInput = document.getElementById('cantidad').value.trim();
    const cantidad = parseInt(cantidadInput);

    if (!productoInput) {
      showError('⚠️ Por favor, ingrese un producto.');
      return;
    }

    if (!hiddenId.value) {
      showError(`⚠️ No se encontró el producto "<strong>${productoInput}</strong>".`);
      return;
    }

    if (isNaN(cantidad) || cantidad <= 0) {
      showError('⚠️ Por favor, ingrese una cantidad válida.');
      return;
    }

    // Si todo está bien, enviar el formulario
    this.submit();
  });

  // Limpiar error al abrir el modal
  const addManualModal = document.getElementById('addManualModal');
  addManualModal.addEventListener('show.bs.modal', function() {
    clearError();
    input.value = '';
    hiddenId.value = '';
    closeSuggestions();
  });
})();

// Abrir boleta en nueva pestaña y volver el foco
if (window.document.querySelectorAll('.boleta-link').length) {
  document.querySelectorAll('.boleta-link').forEach(function(link) {
    link.addEventListener('click', function(e) {
      setTimeout(function() {
        window.focus();
      }, 200);
    });
  });
} 