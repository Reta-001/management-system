console.log('Compras.js limpio cargado');

// Función para mostrar notificaciones push modernas
function mostrarMensajeEnPagina(mensaje, tipo) {
  // Detectar si es un mensaje especial de carrito
  const esCarritoSuccess = tipo === 'success' && /agregado al carrito/i.test(mensaje);
  const esCarritoEliminado = tipo === 'danger' && /eliminado del carrito/i.test(mensaje);
  // Detectar mensaje de compra creada exitosamente
  const esCompraCreada = tipo === 'success' && /compra #\d+ creada exitosamente\.?/i.test(mensaje);

  if ((esCarritoSuccess || esCarritoEliminado) && !esCompraCreada) {
    // Mostrar como alerta dentro de <main class="content">
    let mainContent = document.querySelector('main.content');
    if (!mainContent) mainContent = document.body;
    // Eliminar alertas previas del mismo tipo (solo JS, no las de Django)
    const prevAlerts = mainContent.querySelectorAll('.alert[data-js-alert]');
    prevAlerts.forEach(alert => alert.remove());
    // Crear la alerta tipo Bootstrap
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${tipo} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.setAttribute('data-js-alert', 'true');
    alertDiv.style.cssText = `
      margin-bottom: 18px;
      font-size: 1.1rem;
      box-shadow: 0 4px 16px rgba(0,0,0,0.07);
      display: flex;
      align-items: center;
      gap: 12px;
    `;
    // Icono
    let iconHtml = '';
    if (tipo === 'success') {
      iconHtml = '<i class="bi bi-check-circle me-2" style="font-size:1.3em;"></i>';
    } else if (tipo === 'danger') {
      iconHtml = '<i class="bi bi-x-circle me-2" style="font-size:1.3em;"></i>';
    }
    alertDiv.innerHTML = `
      ${iconHtml}
      <span style="flex:1;">${mensaje}</span>
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar" style="pointer-events:auto;"></button>
    `;
    alertDiv.querySelector('.btn-close').onclick = function() {
      alertDiv.classList.remove('show');
      setTimeout(() => {
        if (alertDiv.parentNode) alertDiv.parentNode.removeChild(alertDiv);
      }, 200);
    };
    if (mainContent.firstChild) {
      mainContent.insertBefore(alertDiv, mainContent.firstChild);
    } else {
      mainContent.appendChild(alertDiv);
    }
    setTimeout(() => {
      alertDiv.classList.remove('show');
      setTimeout(() => {
        if (alertDiv.parentNode) alertDiv.parentNode.removeChild(alertDiv);
      }, 200);
    }, 3000);
    return;
  }

  // --- DISEÑO MODERNO FLOTANTE PARA OTROS MENSAJES ---
  let notificationContainer = document.getElementById('notification-container');
  if (!notificationContainer) {
    notificationContainer = document.createElement('div');
    notificationContainer.id = 'notification-container';
    notificationContainer.style.cssText = `
      position: fixed;
      top: 24px;
      right: 24px;
      left: auto;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      pointer-events: none;
    `;
    document.body.appendChild(notificationContainer);
  }
  // Crear la notificación flotante
  const notification = document.createElement('div');
  notification.className = 'notification';
  notification.style.cssText = `
    background: ${tipo === 'danger' ? '#dc3545' : tipo === 'success' ? '#198754' : tipo === 'warning' ? '#ffc107' : '#0d6efd'};
    color: white;
    padding: 16px 20px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    margin-bottom: 10px;
    position: relative;
    overflow: hidden;
    font-family: 'Poppins', sans-serif;
    font-weight: 500;
    min-width: 350px;
    max-width: 600px;
    display: flex;
    align-items: center;
    gap: 12px;
    pointer-events: auto;
  `;
  // Icono
  let icon = 'bi-info-circle';
  if (tipo === 'success') icon = 'bi-check-circle';
  else if (tipo === 'danger') icon = 'bi-x-circle';
  else if (tipo === 'warning') icon = 'bi-exclamation-triangle';
  notification.innerHTML = `
    <i class="bi ${icon}" style="font-size: 1.2em;"></i>
    <span style="flex:1;">${mensaje}</span>
    <button type="button" class="btn-close" aria-label="Cerrar" style="pointer-events:auto;"></button>
  `;
  notification.querySelector('.btn-close').onclick = function() {
    notification.classList.remove('show');
    setTimeout(() => {
      if (notification.parentNode) notification.parentNode.removeChild(notification);
    }, 200);
  };
  notificationContainer.appendChild(notification);
  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => {
      if (notification.parentNode) notification.parentNode.removeChild(notification);
    }, 200);
  }, 3000);
}

// Función para mostrar mensaje con botón deshacer
function mostrarMensajeConDeshacer(mensaje, compraId) {
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
                  onclick="restaurarCompra(${compraId}, this)" 
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

// Función para restaurar compra
function restaurarCompra(compraId, button) {
  console.log('Iniciando restauración de compra:', compraId);
  
  // Deshabilitar botón
  button.disabled = true;
  button.textContent = 'Restaurando...';
  button.style.opacity = '0.7';
  
  // Enviar petición para restaurar
  fetch(`/compras/restaurar/${compraId}/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
      'X-Requested-With': 'XMLHttpRequest'
    }
  })
  .then(response => {
    console.log('Respuesta recibida:', response);
    console.log('Status:', response.status);
    console.log('Headers:', response.headers);
    
    // Verificar si la respuesta es JSON
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      // Si no es JSON, obtener el texto para debug
      return response.text().then(text => {
        console.error('Respuesta no es JSON:', text);
        throw new Error(`El servidor devolvió HTML en lugar de JSON. Status: ${response.status}`);
      });
    }
    
    return response.json();
  })
  .then(data => {
    console.log('Datos recibidos:', data);
    if (data.success) {
      // Mostrar mensaje de éxito
      mostrarMensajeEnPagina(data.message, 'success');
      
      // Actualizar tabla
      actualizarTablaCompras();
      
      // Remover la notificación de eliminación
      const notification = button.closest('.notification');
      if (notification) {
        notification.remove();
      }
    } else {
      // Mostrar error
      mostrarMensajeEnPagina(data.message || 'Error al restaurar la compra', 'danger');
      
      // Restaurar botón
      button.disabled = false;
      button.textContent = 'Deshacer';
      button.style.opacity = '1';
    }
  })
  .catch(error => {
    console.error('Error al restaurar compra:', error);
    mostrarMensajeEnPagina(`Error al restaurar la compra: ${error.message}`, 'danger');
    
    // Restaurar botón
    button.disabled = false;
    button.textContent = 'Deshacer';
    button.style.opacity = '1';
  });
}

// Función para actualizar la tabla de compras dinámicamente
function actualizarTablaCompras(compraEliminadaId = null) {
  // Si se pasa un ID, eliminar solo ese acordeón
  if (compraEliminadaId) {
    const acordeon = document.querySelector(`.accordion-item [data-id="${compraEliminadaId}"]`);
    if (acordeon) {
      const item = acordeon.closest('.accordion-item');
      if (item) item.remove();
    }
    // Si no quedan compras, mostrar mensaje
    if (!document.querySelector('.accordion-item')) {
      const accordion = document.querySelector('.accordion');
      if (accordion) {
        accordion.innerHTML = '<div class="alert alert-info mb-0">No hay compras registradas.</div>';
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
      
      // Buscar específicamente el card-body del historial de compras (el segundo card-body)
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
      console.error('Error al actualizar tabla de compras:', error);
      // Si hay error, recargar la página como fallback
      window.location.reload();
    });
}

// Función para actualizar el estado de entrega
function actualizarEstadoEntrega(compraId) {
  // Obtener datos actualizados del servidor
  fetch(window.location.href)
    .then(response => response.text())
    .then(html => {
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');
      
      // Buscar el acordeón actualizado en el HTML del servidor
      const nuevoAcordeon = doc.querySelector(`[data-bs-target="#collapse${compraId}"]`);
      if (nuevoAcordeon) {
        const nuevoAcordeonContainer = nuevoAcordeon.closest('.accordion-item');
        const acordeonActual = document.querySelector(`[data-bs-target="#collapse${compraId}"]`);
        
        if (nuevoAcordeonContainer && acordeonActual) {
          const acordeonActualContainer = acordeonActual.closest('.accordion-item');
          
          // Reemplazar el acordeón actual con el actualizado
          acordeonActualContainer.outerHTML = nuevoAcordeonContainer.outerHTML;
        }
      }
    })
    .catch(error => {
      console.error('Error al actualizar estado de entrega:', error);
      // Si hay error, recargar la página como fallback
      window.location.reload();
    });
}

// Función para mostrar mensajes en modales
function mostrarMensajeEnModal(modalId, mensaje, tipo) {
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
  
  // Auto-ocultar mensajes de error después de 5 segundos
  if (tipo === 'danger' || tipo === 'warning') {
    setTimeout(() => {
      alertDiv.style.display = 'none';
    }, 5000);
  }
}

// Modal de confirmar entrega
const confirmarEntregaModal = document.getElementById('confirmarEntregaModal');

confirmarEntregaModal.addEventListener('show.bs.modal', function (event) {
  const button = event.relatedTarget;
  const id = button.getAttribute('data-id');
  
  document.getElementById('entrega-id').value = id;
  document.getElementById('entrega-compra-id').textContent = id;
});

// Manejar formulario de confirmar entrega con AJAX
const confirmarEntregaForm = document.getElementById('confirmarEntregaForm');
if (confirmarEntregaForm) {
  confirmarEntregaForm.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const submitButton = this.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;
    
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Confirmando...';
    
    fetch(`/compras/confirmar-entrega/${formData.get('id')}/`, {
      method: 'POST',
      body: formData,
      headers: {
        'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Cerrar el modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('confirmarEntregaModal'));
        modal.hide();
        
        mostrarMensajeEnPagina(data.message, 'success');
        
        // Actualizar el estado de entrega en la tabla
        actualizarEstadoEntrega(formData.get('id'));
      } else {
        mostrarMensajeEnModal('confirmarEntregaModal', data.message, 'danger');
      }
      
      submitButton.disabled = false;
      submitButton.innerHTML = originalText;
    })
    .catch(error => {
      console.error('Error al confirmar entrega:', error);
      mostrarMensajeEnModal('confirmarEntregaModal', 'Error al confirmar la entrega', 'danger');
      submitButton.disabled = false;
      submitButton.innerHTML = originalText;
    });
  });
}

// Modales edición y eliminación 
const deleteCompraModal = document.getElementById('deleteCompraModal');

deleteCompraModal.addEventListener('show.bs.modal', function (event) {
  const button = event.relatedTarget;
  const id = button.getAttribute('data-id');
  
  document.getElementById('delete-id').value = id;
  
  // Buscar el número de compra en el DOM
  const compraElement = document.querySelector(`[data-bs-target="#collapse${id}"]`);
  if (compraElement) {
    const compraText = compraElement.querySelector('.fw-bold').textContent;
    const numeroCompra = compraText.match(/Compra #(\d+)/);
    if (numeroCompra) {
      document.getElementById('delete-producto').textContent = `#${numeroCompra[1]}`;
    } else {
      document.getElementById('delete-producto').textContent = `#${id}`;
    }
  } else {
    document.getElementById('delete-producto').textContent = `#${id}`;
  }
  
  document.getElementById('deleteCompraForm').action = `/compras/eliminar/${id}/`;
});

// Manejar el envío del formulario de eliminación con AJAX
const deleteCompraForm = document.getElementById('deleteCompraForm');
if (deleteCompraForm) {
  deleteCompraForm.addEventListener('submit', function (event) {
    event.preventDefault();
    event.stopPropagation();
    
    const formData = new FormData(this);
    const modal = document.getElementById('deleteCompraModal');
    const submitButton = modal.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;
    
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Eliminando...';
    
    fetch('/compras/eliminar/' + formData.get('id') + '/', {
      method: 'POST',
      body: formData,
      headers: {
        'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
    .then(response => {
      return response.json();
    })
    .then(data => {
      if (data) {
        if (data.success) {
          // Eliminación exitosa, cerrar el modal
          const modal = bootstrap.Modal.getInstance(document.getElementById('deleteCompraModal'));
          modal.hide();
          
          // Mostrar mensaje con botón deshacer
          mostrarMensajeConDeshacer(data.message, data.compra_id);
          
          // Eliminar acordeón de la compra eliminada
          actualizarTablaCompras(data.compra_id);
        } else {
          // Error
          mostrarMensajeEnPagina(data.message || 'Error al eliminar la compra', 'danger');
        }
        // Restaurar botón
        submitButton.disabled = false;
        submitButton.innerHTML = originalText;
      }
    })
    .catch(error => {
      console.error('Error en eliminación:', error);
      mostrarMensajeEnPagina('Error al eliminar la compra', 'danger');
      submitButton.disabled = false;
      submitButton.innerHTML = originalText;
    });
    return false;
  });
} else {
  console.log('Formulario de eliminación NO encontrado');
}

// El formulario de finalizar compra ahora se maneja en inicializarEventListenersCarrito()

// Autocomplete y validación en modal de agregar producto
(function() {
  const proveedorInput = document.getElementById('proveedor_autocomplete');
  const proveedorSuggestions = document.getElementById('proveedor_suggestions');
  const proveedorHidden = document.getElementById('proveedor_id_hidden');
  const productoInput = document.getElementById('producto_autocomplete');
  const productoSuggestions = document.getElementById('autocomplete_suggestions');
  const productoHidden = document.getElementById('producto_id_hidden');
  const errorMsg = document.getElementById('addManualErrorMsg');
  const form = document.querySelector('#addManualModal form');
  let currentFocus = -1;
  let proveedores = [];
  let productos = [];

  if (!proveedorInput || !proveedorSuggestions || !proveedorHidden || 
      !productoInput || !productoSuggestions || !productoHidden || 
      !errorMsg || !form) {
    return;
  }

  function closeProveedorSuggestions() {
    proveedorSuggestions.innerHTML = '';
    proveedorSuggestions.style.display = 'none';
    currentFocus = -1;
  }

  function closeProductoSuggestions() {
    productoSuggestions.innerHTML = '';
    productoSuggestions.style.display = 'none';
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

  function renderProveedorSuggestions(items) {
    proveedorSuggestions.innerHTML = '';
    if (!items.length) {
      proveedorSuggestions.style.display = 'none';
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
            <small class="text-muted">${item.telefono} | ${item.correo}</small>
          </div>
        </div>
      `;
      div.onclick = function() {
        proveedorInput.value = item.nombre;
        proveedorHidden.value = item.id;
        closeProveedorSuggestions();
        clearError();
        
        // Si ya hay un producto seleccionado, verificar que sea compatible
        if (productoHidden.value) {
          verificarCompatibilidadProductoProveedor();
        } else {
          // Si no hay producto, habilitar búsqueda de productos para este proveedor
          productoInput.disabled = false;
          productoInput.focus();
        }
      };
      proveedorSuggestions.appendChild(div);
    });
    proveedorSuggestions.style.display = 'block';
  }

  function renderProductoSuggestions(items) {
    productoSuggestions.innerHTML = '';
    if (!items.length) {
      productoSuggestions.style.display = 'none';
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
            <small class="text-muted">Código: ${item.codigo} | Stock: ${item.stock}</small>
          </div>
          <span class="badge bg-primary rounded-pill">$${item.precio_venta}</span>
        </div>
      `;
      div.onclick = function() {
        productoInput.value = item.nombre;
        productoHidden.value = item.id;
        closeProductoSuggestions();
        clearError();
        
        // Si ya hay un proveedor seleccionado, verificar que sea compatible
        if (proveedorHidden.value) {
          verificarCompatibilidadProductoProveedor();
        } else {
          // Si no hay proveedor, habilitar búsqueda de proveedores para este producto
          proveedorInput.disabled = false;
          proveedorInput.focus();
        }
      };
      productoSuggestions.appendChild(div);
    });
    productoSuggestions.style.display = 'block';
  }

  function fetchProveedores() {
    const q = proveedorInput.value.trim();
    const productoId = productoHidden.value;
    
    if (q.length === 0) {
      closeProveedorSuggestions();
      proveedorHidden.value = '';
      return;
    }

    // Si hay un producto seleccionado, buscar solo proveedores de ese producto
    const url = productoId ? 
      `/compras/autocomplete_proveedores/?q=${encodeURIComponent(q)}&producto=${productoId}` :
      `/compras/autocomplete_proveedores/?q=${encodeURIComponent(q)}`;

    fetch(url)
      .then(res => res.json())
      .then(data => {
        proveedores = data.results || [];
        renderProveedorSuggestions(proveedores);
        
        if (proveedores.length === 1) {
          proveedorHidden.value = proveedores[0].id;
        } else {
          proveedorHidden.value = '';
        }
      });
  }

  function fetchProductos() {
    const q = productoInput.value.trim();
    const proveedorId = proveedorHidden.value;
    
    if (q.length === 0) {
      closeProductoSuggestions();
      productoHidden.value = '';
      return;
    }

    // Si hay un proveedor seleccionado, buscar solo productos de ese proveedor
    const url = proveedorId ? 
      `/compras/autocomplete_productos/?q=${encodeURIComponent(q)}&proveedor=${proveedorId}` :
      `/compras/autocomplete_productos/?q=${encodeURIComponent(q)}`;

    fetch(url)
      .then(res => res.json())
      .then(data => {
        productos = data.results || [];
        renderProductoSuggestions(productos);
        
        if (productos.length === 1) {
          productoHidden.value = productos[0].id;
        } else {
          productoHidden.value = '';
        }
      });
  }

  function verificarCompatibilidadProductoProveedor() {
    const productoId = productoHidden.value;
    const proveedorId = proveedorHidden.value;
    
    if (!productoId || !proveedorId) return;
    
    // Verificar que el producto y proveedor sean compatibles
    fetch(`/compras/verificar_compatibilidad/?producto=${productoId}&proveedor=${proveedorId}`)
      .then(res => res.json())
      .then(data => {
        if (!data.compatible) {
          showError('⚠️ Este producto no está disponible con el proveedor seleccionado.');
          // Limpiar el campo que se seleccionó último
          if (proveedorInput.value && !productoInput.value) {
            productoHidden.value = '';
            productoInput.value = '';
          } else if (productoInput.value && !proveedorInput.value) {
            proveedorHidden.value = '';
            proveedorInput.value = '';
          }
        } else {
          clearError();
        }
      });
  }

  // Event listeners para proveedores
  proveedorInput.addEventListener('input', fetchProveedores);
  proveedorInput.addEventListener('focus', fetchProveedores);

  proveedorInput.addEventListener('keydown', function(e) {
    const items = proveedorSuggestions.querySelectorAll('.list-group-item');
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
      else if (proveedores.length === 1) {
        e.preventDefault();
        proveedorInput.value = proveedores[0].nombre;
        proveedorHidden.value = proveedores[0].id;
        closeProveedorSuggestions();
      }
    }
  });

  // Event listeners para productos
  productoInput.addEventListener('input', fetchProductos);
  productoInput.addEventListener('focus', fetchProductos);

  productoInput.addEventListener('keydown', function(e) {
    const items = productoSuggestions.querySelectorAll('.list-group-item');
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
        productoInput.value = productos[0].nombre;
        productoHidden.value = productos[0].id;
        closeProductoSuggestions();
      }
    }
  });

  // Cerrar sugerencias al hacer clic fuera
  document.addEventListener('click', function(e) {
    if (!proveedorInput.contains(e.target) && !proveedorSuggestions.contains(e.target)) {
      closeProveedorSuggestions();
    }
    if (!productoInput.contains(e.target) && !productoSuggestions.contains(e.target)) {
      closeProductoSuggestions();
    }
  });

  // Validar formulario antes de enviar
  form.addEventListener('submit', function(e) {
    e.preventDefault();
    const proveedorInput = document.getElementById('proveedor_autocomplete').value.trim();
    const productoInput = document.getElementById('producto_autocomplete').value.trim();
    const cantidadInput = document.getElementById('cantidad').value.trim();
    const cantidad = parseInt(cantidadInput);

    if (!proveedorInput) {
      showError('⚠️ Por favor, ingrese un proveedor.');
      return;
    }

    if (!proveedorHidden.value) {
      showError(`⚠️ No se encontró el proveedor "<strong>${proveedorInput}</strong>".`);
      return;
    }

    if (!productoInput) {
      showError('⚠️ Por favor, ingrese un producto.');
      return;
    }

    if (!productoHidden.value) {
      showError(`⚠️ No se encontró el producto "<strong>${productoInput}</strong>".`);
      return;
    }

    if (isNaN(cantidad) || cantidad <= 0) {
      showError('⚠️ Por favor, ingrese una cantidad válida.');
      return;
    }

    // Si todo está bien, el envío lo maneja el otro event listener con AJAX
  });

  // Limpiar al abrir el modal
  const addManualModal = document.getElementById('addManualModal');
  addManualModal.addEventListener('show.bs.modal', function() {
    clearError();
    proveedorInput.value = '';
    proveedorHidden.value = '';
    productoInput.value = '';
    productoHidden.value = '';
    // Ambos campos habilitados desde el inicio
    proveedorInput.disabled = false;
    productoInput.disabled = false;
    closeProveedorSuggestions();
    closeProductoSuggestions();
  });
})();

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
        fetch('/compras/validar_codigo/?codigo=' + encodeURIComponent(codigo))
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

// Manejar formulario de agregar al carrito con AJAX
const addToCartForm = document.querySelector('#addManualModal form');
if (addToCartForm) {
  addToCartForm.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const submitButton = this.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;
    
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Agregando...';
    
    fetch(this.action, {
      method: 'POST',
      body: formData,
      headers: {
        'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Cerrar el modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('addManualModal'));
        modal.hide();
        
        mostrarMensajeEnPagina(data.message, 'success');
        
        // Actualizar solo la sección del carrito
        actualizarSeccionCarrito();
      } else {
        mostrarMensajeEnModal('addManualModal', data.message, 'danger');
      }
      
      submitButton.disabled = false;
      submitButton.innerHTML = originalText;
    })
    .catch(error => {
      console.error('Error al agregar al carrito:', error);
      mostrarMensajeEnModal('addManualModal', 'Error al agregar al carrito', 'danger');
      submitButton.disabled = false;
      submitButton.innerHTML = originalText;
    });
  });
}

// Función para actualizar solo la sección del carrito
function actualizarSeccionCarrito() {
  console.log('Iniciando actualización del carrito...');
  
  // Hacer la petición para obtener el HTML actualizado
  fetch(window.location.href)
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.text();
    })
    .then(html => {
      console.log('HTML recibido, procesando...');
      
      // Crear un parser para el HTML
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');
      
      // Buscar todos los cards en el HTML nuevo
      const cardsNuevos = doc.querySelectorAll('.card');
      console.log('Cards encontrados en HTML nuevo:', cardsNuevos.length);
      
      // Buscar todos los cards en el HTML actual
      const cardsActuales = document.querySelectorAll('.card');
      console.log('Cards encontrados en HTML actual:', cardsActuales.length);
      
      // Buscar el card del carrito en el HTML nuevo
      let carritoCardNuevo = null;
      for (let i = 0; i < cardsNuevos.length; i++) {
        const card = cardsNuevos[i];
        const header = card.querySelector('.card-header');
        if (header && header.textContent.includes('Carrito de Compra')) {
          carritoCardNuevo = card;
          console.log('Card del carrito encontrado en HTML nuevo (índice:', i, ')');
          break;
        }
      }
      
      // Buscar el card del carrito en el HTML actual
      let carritoCardActual = null;
      for (let i = 0; i < cardsActuales.length; i++) {
        const card = cardsActuales[i];
        const header = card.querySelector('.card-header');
        if (header && header.textContent.includes('Carrito de Compra')) {
          carritoCardActual = card;
          console.log('Card del carrito encontrado en HTML actual (índice:', i, ')');
          break;
        }
      }
      
      // Verificar que encontramos ambos cards
      if (!carritoCardNuevo) {
        console.error('No se encontró el card del carrito en el HTML nuevo');
        return;
      }
      
      if (!carritoCardActual) {
        console.error('No se encontró el card del carrito en el HTML actual');
        return;
      }
      
      // Obtener las secciones card-body
      const nuevaSeccionCarrito = carritoCardNuevo.querySelector('.card-body');
      const seccionCarritoActual = carritoCardActual.querySelector('.card-body');
      
      console.log('Secciones encontradas:', {
        nueva: !!nuevaSeccionCarrito,
        actual: !!seccionCarritoActual
      });
      
      // Verificar que encontramos ambas secciones
      if (!nuevaSeccionCarrito) {
        console.error('No se encontró la sección card-body en el HTML nuevo');
        return;
      }
      
      if (!seccionCarritoActual) {
        console.error('No se encontró la sección card-body en el HTML actual');
        return;
      }
      
      // Actualizar el contenido
      console.log('Actualizando contenido del carrito...');
      seccionCarritoActual.innerHTML = nuevaSeccionCarrito.innerHTML;
      
      // Re-inicializar los event listeners
      inicializarEventListenersCarrito();
      console.log('Carrito actualizado exitosamente');
    })
    .catch(error => {
      console.error('Error al actualizar carrito:', error);
    });
}

// Función para inicializar los event listeners del carrito
function inicializarEventListenersCarrito() {
  console.log('Inicializando event listeners del carrito...');
  
  // Event listeners para eliminar del carrito
  const deleteFromCartForms = document.querySelectorAll('form[action*="carrito/eliminar"]');
  console.log('Formularios de eliminar encontrados:', deleteFromCartForms.length);
  
  deleteFromCartForms.forEach((form, index) => {
    console.log(`Formulario ${index + 1}:`, form.action);
    // Remover event listeners existentes para evitar duplicados
    form.removeEventListener('submit', handleDeleteFromCart);
    // Agregar el nuevo event listener
    form.addEventListener('submit', handleDeleteFromCart);
    console.log(`Event listener agregado al formulario ${index + 1}`);
  });
  
  // Event listener para finalizar compra
  const finalizarCompraForm = document.querySelector('form[action*="carrito/finalizar"]');
  if (finalizarCompraForm) {
    console.log('Formulario de finalizar compra encontrado:', finalizarCompraForm.action);
    // Remover event listeners existentes para evitar duplicados
    finalizarCompraForm.removeEventListener('submit', handleFinalizarCompra);
    // Agregar el nuevo event listener
    finalizarCompraForm.addEventListener('submit', handleFinalizarCompra);
    console.log('Event listener agregado al formulario de finalizar compra');
  } else {
    console.log('No se encontró el formulario de finalizar compra');
  }
}

// Función para manejar la eliminación del carrito
function handleDeleteFromCart(e) {
  console.log('Función handleDeleteFromCart ejecutada');
  e.preventDefault();
  
  const formData = new FormData(this);
  const submitButton = this.querySelector('button[type="submit"]');
  const originalText = submitButton.innerHTML;
  
  submitButton.disabled = true;
  submitButton.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Eliminando...';
  
  fetch(this.action, {
    method: 'POST',
    body: formData,
    headers: {
      'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
      'X-Requested-With': 'XMLHttpRequest'
    }
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      mostrarMensajeEnPagina(data.message, 'danger');
      
      // Actualizar solo la sección del carrito
      actualizarSeccionCarrito();
    } else {
      mostrarMensajeEnPagina(data.message, 'danger');
    }
    
    submitButton.disabled = false;
    submitButton.innerHTML = originalText;
  })
  .catch(error => {
    console.error('Error al eliminar del carrito:', error);
    mostrarMensajeEnPagina('Error al eliminar del carrito', 'danger');
    submitButton.disabled = false;
    submitButton.innerHTML = originalText;
  });
}

// Función para manejar la finalización de compra
function handleFinalizarCompra(e) {
  e.preventDefault();
  
  const formData = new FormData(this);
  const submitButton = this.querySelector('button[type="submit"]');
  const originalText = submitButton.innerHTML;
  
  submitButton.disabled = true;
  submitButton.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Finalizando...';
  
  fetch(this.action, {
    method: 'POST',
    body: formData,
    headers: {
      'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
      'X-Requested-With': 'XMLHttpRequest'
    }
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      mostrarMensajeEnPagina(data.message, 'success');
      
      // Actualizar tanto el carrito como el historial de compras
      actualizarSeccionCarrito();
      actualizarTablaCompras();
    } else {
      mostrarMensajeEnPagina(data.message, 'danger');
    }
    
    submitButton.disabled = false;
    submitButton.innerHTML = originalText;
  })
  .catch(error => {
    console.error('Error al finalizar compra:', error);
    mostrarMensajeEnPagina('Error al finalizar la compra', 'danger');
    submitButton.disabled = false;
    submitButton.innerHTML = originalText;
  });
}

// Abrir modal de agregar manual desde botón (si existe)
const btnAgregarManual = document.getElementById('btnAgregarManual');
if (btnAgregarManual) {
  btnAgregarManual.addEventListener('click', () => {
    // Ocultar modal de escaneo
    const scanModalEl = document.getElementById('scanCodeModal');
    const scanModal = bootstrap.Modal.getInstance(scanModalEl);
    scanModal.hide();

    // Abrir modal de añadir compra
    const addManualModal = new bootstrap.Modal(document.getElementById('addManualModal'));
    addManualModal.show();
  });
}

// Manejar formularios de eliminar del carrito con AJAX
document.addEventListener('DOMContentLoaded', function() {
  inicializarEventListenersCarrito();
});