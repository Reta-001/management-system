// Modales edición y eliminación 
const editProveedorModal = document.getElementById('editProveedorModal');
const deleteProveedorModal = document.getElementById('deleteProveedorModal');

editProveedorModal.addEventListener('show.bs.modal', function (event) {
  const button = event.relatedTarget;
  const id = button.getAttribute('data-id');
  const nombre = button.getAttribute('data-nombre');
  const telefono = button.getAttribute('data-telefono');
  const correo = button.getAttribute('data-correo');
  const direccion = button.getAttribute('data-direccion');
  const pais = button.getAttribute('data-pais');
  const ciudad = button.getAttribute('data-ciudad');
  const comuna = button.getAttribute('data-comuna');

  document.getElementById('edit-id').value = id;
  document.getElementById('edit-nombre').value = nombre;
  document.getElementById('edit-telefono').value = telefono;
  document.getElementById('edit-correo').value = correo;
  document.getElementById('edit-direccion').value = direccion;
  document.getElementById('edit-pais').value = pais;
  document.getElementById('edit-ciudad').value = ciudad;
  document.getElementById('edit-comuna').value = comuna;

  document.getElementById('editProveedorForm').action = `/proveedor/editar/${id}/`;
});

deleteProveedorModal.addEventListener('show.bs.modal', function (event) {
  const button = event.relatedTarget;
  const id = button.getAttribute('data-id');
  const nombre = button.getAttribute('data-nombre');

  document.getElementById('delete-id').value = id;
  document.getElementById('delete-nombre').textContent = nombre;
  document.getElementById('deleteProveedorForm').action = `/proveedor/eliminar/${id}/`;
});

// Manejar todos los formularios con AJAX
document.addEventListener('DOMContentLoaded', function() {
  console.log('DOMContentLoaded iniciado');
  
  // Manejar el envío del formulario de eliminación con AJAX
  const deleteProveedorForm = document.getElementById('deleteProveedorForm');
  if (deleteProveedorForm) {
    console.log('Formulario de eliminación encontrado');
    
    deleteProveedorForm.addEventListener('submit', function (event) {
      console.log('Formulario de eliminación enviado, previniendo envío normal');
      event.preventDefault();
      event.stopPropagation();
      
      const formData = new FormData(this);
      const modal = document.getElementById('deleteProveedorModal');
      const submitButton = modal.querySelector('button[type="submit"]');
      const originalText = submitButton.innerHTML;
      
      console.log('ID del proveedor a eliminar:', formData.get('id'));
      
      // Deshabilitar botón y mostrar loading
      submitButton.disabled = true;
      submitButton.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Eliminando...';
      
      fetch('/proveedor/eliminar/' + formData.get('id') + '/', {
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
            const modal = bootstrap.Modal.getInstance(document.getElementById('deleteProveedorModal'));
            modal.hide();
            
            // Mostrar mensaje con botón deshacer
            mostrarMensajeConDeshacer(data.message, data.proveedor_id);
            
            // Actualizar la tabla dinámicamente
            actualizarTablaProveedores();
          } else {
            // Error
            mostrarMensajeEnModal('deleteProveedorModal', data.message, 'danger');
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
  
  // Manejar el envío del formulario de agregar proveedor con AJAX
  const addProveedorForm = document.getElementById('addProveedorModal').querySelector('form');
  console.log('Buscando formulario de agregar:', addProveedorForm);
  
  if (addProveedorForm) {
    console.log('Formulario de agregar encontrado, agregando event listener');
    
    addProveedorForm.addEventListener('submit', function (event) {
      console.log('Formulario de agregar enviado, previniendo envío normal');
      event.preventDefault();
      event.stopPropagation();
      
      const formData = new FormData(this);
      const modal = document.getElementById('addProveedorModal');
      const submitButton = modal.querySelector('button[type="submit"]');
      const originalText = submitButton.innerHTML;
      
      console.log('Datos del formulario de agregar:', {
        action: this.action,
        nombre: formData.get('nombre'),
        telefono: formData.get('telefono')
      });
      
      // Deshabilitar botón y mostrar loading
      submitButton.disabled = true;
      submitButton.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Guardando...';
      
      fetch(this.action, {
        method: 'POST',
        body: formData,
        headers: {
          'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        }
      })
      .then(response => {
        console.log('Respuesta de agregar recibida:', response);
        console.log('Status:', response.status);
        console.log('Status Text:', response.statusText);
        console.log('Headers:', response.headers);
        
        // Verificar si es redirección
        if (response.redirected || response.status === 302) {
          console.log('Redirección detectada, actualizando tabla');
          // Mostrar mensaje de éxito y actualizar tabla
          mostrarMensajeEnPagina("Operación completada exitosamente.", "success");
          actualizarTablaProveedores();
          return null;
        }
        
        // Intentar parsear como JSON
        console.log('Intentando parsear como JSON...');
        return response.json();
      })
      .then(data => {
        if (data) {
          console.log('Datos JSON de agregar recibidos:', data);
          
          if (data.success) {
            // Operación exitosa
            console.log('Operación exitosa:', data.message);
            
            // Cerrar el modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('addProveedorModal'));
            modal.hide();
            
            // Mostrar mensaje de éxito en la página principal
            mostrarMensajeEnPagina(data.message, 'success');
            
            // Actualizar la tabla dinámicamente
            actualizarTablaProveedores();
          } else {
            // Error
            const modal = document.getElementById('addProveedorModal');
            let alertDiv = modal.querySelector('.modal-alert');
            
            if (!alertDiv) {
              alertDiv = document.createElement('div');
              alertDiv.className = 'modal-alert alert alert-danger mt-3';
              const modalFooter = modal.querySelector('.modal-footer');
              modalFooter.insertBefore(alertDiv, modalFooter.firstChild);
            }
            
            alertDiv.innerHTML = `<i class="bi bi-exclamation-triangle me-2"></i>${data.message}`;
            alertDiv.style.display = 'block';
            
            // Mostrar errores específicos de campos si existen
            if (data.errors) {
              Object.keys(data.errors).forEach(field => {
                const input = this.querySelector(`[name="${field}"]`);
                if (input) {
                  input.classList.add('is-invalid');
                  const errorDiv = input.parentNode.querySelector('.invalid-feedback') || 
                                  input.parentNode.appendChild(document.createElement('div'));
                  errorDiv.className = 'invalid-feedback';
                  errorDiv.textContent = data.errors[field];
                }
              });
            }
          }
          
          // Restaurar botón
          submitButton.disabled = false;
          submitButton.innerHTML = originalText;
        } else {
          console.log('No hay datos JSON, probablemente fue exitoso');
        }
      })
      .catch(error => {
        console.error('Error en agregar:', error);
        console.log('Error completo:', error);
        
        // Si hay error, recargar la página para mostrar los mensajes de Django
        window.location.reload();
      });
      
      return false;
    });
  } else {
    console.log('Formulario de agregar NO encontrado');
  }
  
  // Manejar el envío del formulario de editar proveedor con AJAX
  const editProveedorForm = document.getElementById('editProveedorForm');
  console.log('Buscando formulario de editar:', editProveedorForm);
  
  if (editProveedorForm) {
    console.log('Formulario de editar encontrado, agregando event listener');
    
    editProveedorForm.addEventListener('submit', function (event) {
      console.log('Formulario de editar enviado, previniendo envío normal');
      event.preventDefault();
      event.stopPropagation();
      
      const formData = new FormData(this);
      const modal = document.getElementById('editProveedorModal');
      const submitButton = modal.querySelector('button[type="submit"]');
      const originalText = submitButton.innerHTML;
      
      console.log('Datos del formulario de editar:', {
        action: this.action,
        id: formData.get('id'),
        nombre: formData.get('nombre')
      });
      
      // Deshabilitar botón y mostrar loading
      submitButton.disabled = true;
      submitButton.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Guardando...';
      
      fetch(this.action, {
        method: 'POST',
        body: formData,
        headers: {
          'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        }
      })
      .then(response => {
        console.log('Respuesta de editar recibida:', response);
        console.log('Status:', response.status);
        console.log('Status Text:', response.statusText);
        console.log('Headers:', response.headers);
        
        // Verificar si es redirección
        if (response.redirected || response.status === 302) {
          console.log('Redirección detectada, actualizando tabla');
          // Mostrar mensaje de éxito y actualizar tabla
          mostrarMensajeEnPagina("Operación completada exitosamente.", "success");
          actualizarTablaProveedores();
          return null;
        }
        
        // Intentar parsear como JSON
        console.log('Intentando parsear como JSON...');
        return response.json();
      })
      .then(data => {
        if (data) {
          console.log('Datos JSON de editar recibidos:', data);
          
          if (data.success) {
            // Operación exitosa
            console.log('Operación exitosa:', data.message);
            
            // Cerrar el modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('editProveedorModal'));
            modal.hide();
            
            // Mostrar mensaje de éxito en la página principal
            mostrarMensajeEnPagina(data.message, 'success');
            
            // Actualizar la tabla dinámicamente
            actualizarTablaProveedores();
          } else {
            // Error
            const modal = document.getElementById('editProveedorModal');
            let alertDiv = modal.querySelector('.modal-alert');
            
            if (!alertDiv) {
              alertDiv = document.createElement('div');
              alertDiv.className = 'modal-alert alert alert-danger mt-3';
              const modalFooter = modal.querySelector('.modal-footer');
              modalFooter.insertBefore(alertDiv, modalFooter.firstChild);
            }
            
            alertDiv.innerHTML = `<i class="bi bi-exclamation-triangle me-2"></i>${data.message}`;
            alertDiv.style.display = 'block';
            
            // Mostrar errores específicos de campos si existen
            if (data.errors) {
              Object.keys(data.errors).forEach(field => {
                const input = this.querySelector(`[name="${field}"]`);
                if (input) {
                  input.classList.add('is-invalid');
                  const errorDiv = input.parentNode.querySelector('.invalid-feedback') || 
                                  input.parentNode.appendChild(document.createElement('div'));
                  errorDiv.className = 'invalid-feedback';
                  errorDiv.textContent = data.errors[field];
                }
              });
            }
          }
          
          // Restaurar botón
          submitButton.disabled = false;
          submitButton.innerHTML = originalText;
        } else {
          console.log('No hay datos JSON, probablemente fue exitoso');
        }
      })
      .catch(error => {
        console.error('Error en editar:', error);
        console.log('Error completo:', error);
        
        // Si hay error, recargar la página para mostrar los mensajes de Django
        window.location.reload();
      });
      
      return false;
    });
  } else {
    console.log('Formulario de editar NO encontrado');
  }
  
  // Limpiar errores de validación cuando se abren los modales
  const addModal = document.getElementById('addProveedorModal');
  if (addModal) {
    addModal.addEventListener('show.bs.modal', function () {
      // Limpiar errores de validación
      const invalidFields = this.querySelectorAll('.is-invalid');
      invalidFields.forEach(field => {
        field.classList.remove('is-invalid');
      });
      
      const errorMessages = this.querySelectorAll('.invalid-feedback');
      errorMessages.forEach(error => {
        error.remove();
      });
      
      // Limpiar mensajes de error en el modal
      const modalAlerts = this.querySelectorAll('.modal-alert');
      modalAlerts.forEach(alert => {
        alert.remove();
      });
    });
  }

  const editModal = document.getElementById('editProveedorModal');
  if (editModal) {
    editModal.addEventListener('show.bs.modal', function () {
      // Limpiar errores de validación
      const invalidFields = this.querySelectorAll('.is-invalid');
      invalidFields.forEach(field => {
        field.classList.remove('is-invalid');
      });
      
      const errorMessages = this.querySelectorAll('.invalid-feedback');
      errorMessages.forEach(error => {
        error.remove();
      });
      
      // Limpiar mensajes de error en el modal
      const modalAlerts = this.querySelectorAll('.modal-alert');
      modalAlerts.forEach(alert => {
        alert.remove();
      });
    });
  }
});

// Validaciones de teléfono para modales
document.addEventListener('DOMContentLoaded', function() {
  // Función para validar teléfono
  function validarTelefono(input) {
    // Remover cualquier carácter que no sea número
    let value = input.value.replace(/[^0-9]/g, '');
    
    // Limitar a máximo 9 dígitos
    if (value.length > 9) {
      value = value.substring(0, 9);
    }
    
    input.value = value;
    
    // Validar y mostrar mensaje de error
    const errorDiv = input.parentNode.querySelector('.telefono-error');
    if (errorDiv) {
      errorDiv.remove();
    }
    
    if (value.length > 0 && value.length !== 9) {
      const errorElement = document.createElement('div');
      errorElement.className = 'text-danger small telefono-error mt-1';
      errorElement.textContent = 'El teléfono debe tener exactamente 9 dígitos';
      input.parentNode.appendChild(errorElement);
    }
  }

  // Validar al enviar formulario
  function validarFormularioTelefono(form, telefonoInput) {
    const telefonoValue = telefonoInput.value.trim();
    
    // Remover mensajes de error anteriores
    const existingError = form.querySelector('.modal-error');
    if (existingError) {
      existingError.remove();
    }
    
    if (telefonoValue.length > 0 && telefonoValue.length !== 9) {
      // Crear mensaje de error en el modal
      const errorElement = document.createElement('div');
      errorElement.className = 'alert alert-danger modal-error mb-3 proveedor-modal-alert';
      errorElement.innerHTML = '<i class="bi bi-exclamation-triangle me-2"></i>El teléfono debe tener exactamente 9 dígitos numéricos';
      
      // Aplicar estilos inline para forzar el comportamiento
      errorElement.style.cssText = `
        max-width: 85% !important;
        width: auto !important;
        margin: 0 auto 15px auto !important;
        padding: 12px 20px !important;
        border-radius: 8px !important;
        font-size: 0.95rem !important;
        text-align: center !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
        display: block !important;
        float: none !important;
        clear: both !important;
      `;
      
      // Insertar el mensaje justo antes del modal-footer
      const modalFooter = form.querySelector('.modal-footer');
      modalFooter.parentNode.insertBefore(errorElement, modalFooter);
      
      telefonoInput.focus();
      return false;
    }
    
    if (telefonoValue.length > 0 && !/^[0-9]{9}$/.test(telefonoValue)) {
      // Crear mensaje de error en el modal
      const errorElement = document.createElement('div');
      errorElement.className = 'alert alert-danger modal-error mb-3 proveedor-modal-alert';
      errorElement.innerHTML = '<i class="bi bi-exclamation-triangle me-2"></i>El teléfono solo debe contener números';
      
      // Aplicar estilos inline para forzar el comportamiento
      errorElement.style.cssText = `
        max-width: 85% !important;
        width: auto !important;
        margin: 0 auto 15px auto !important;
        padding: 12px 20px !important;
        border-radius: 8px !important;
        font-size: 0.95rem !important;
        text-align: center !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
        display: block !important;
        float: none !important;
        clear: both !important;
      `;
      
      // Insertar el mensaje justo antes del modal-footer
      const modalFooter = form.querySelector('.modal-footer');
      modalFooter.parentNode.insertBefore(errorElement, modalFooter);
      
      telefonoInput.focus();
      return false;
    }
    
    return true;
  }

  // Aplicar validaciones a campos de teléfono en modales
  const addTelefonoField = document.getElementById('add-telefono');
  const editTelefonoField = document.getElementById('edit-telefono');

  if (addTelefonoField) {
    addTelefonoField.addEventListener('input', function() {
      validarTelefono(this);
    });

    const addForm = addTelefonoField.closest('form');
    if (addForm) {
      addForm.addEventListener('submit', function(e) {
        if (!validarFormularioTelefono(this, addTelefonoField)) {
          e.preventDefault();
        }
      });
    }
  }

  if (editTelefonoField) {
    editTelefonoField.addEventListener('input', function() {
      validarTelefono(this);
    });

    const editForm = editTelefonoField.closest('form');
    if (editForm) {
      editForm.addEventListener('submit', function(e) {
        if (!validarFormularioTelefono(this, editTelefonoField)) {
          e.preventDefault();
        }
      });
    }
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
function mostrarMensajeConDeshacer(mensaje, proveedorId) {
  console.log('Mostrando mensaje con deshacer:', mensaje, proveedorId);
  
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
                  onclick="restaurarProveedor(${proveedorId}, this)" 
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

// Función para restaurar proveedor
function restaurarProveedor(proveedorId, button) {
  console.log('Restaurando proveedor:', proveedorId);
  
  // Deshabilitar botón
  button.disabled = true;
  button.textContent = 'Restaurando...';
  button.style.opacity = '0.7';
  
  // Enviar petición para restaurar
  fetch(`/proveedor/restaurar/${proveedorId}/`, {
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
      actualizarTablaProveedores();
      
      // Remover la notificación de eliminación
      const notification = button.closest('.notification');
      if (notification) {
        notification.remove();
      }
    } else {
      // Mostrar error
      alert('Error al restaurar el proveedor: ' + data.message);
      
      // Restaurar botón
      button.disabled = false;
      button.textContent = 'Deshacer';
      button.style.opacity = '1';
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('Error al restaurar el proveedor');
    
    // Restaurar botón
    button.disabled = false;
    button.textContent = 'Deshacer';
    button.style.opacity = '1';
  });
}

// Función para actualizar la tabla de proveedores dinámicamente
function actualizarTablaProveedores() {
  console.log('Actualizando tabla de proveedores...');
  
  // Obtener los datos actualizados de la tabla
  fetch(window.location.href)
    .then(response => response.text())
    .then(html => {
      console.log('HTML recibido, longitud:', html.length);
      
      // Crear un elemento temporal para parsear el HTML
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');
      
      // Verificar si hay proveedores en la nueva respuesta
      const nuevaTabla = doc.querySelector('.table-responsive');
      const nuevoCardTabla = doc.querySelector('.card.shadow-lg.border-0.mb-4');
      const nuevoMensaje = doc.querySelector('.alert-info');
      const cardActual = document.querySelector('.card.shadow-lg.border-0.mb-4');
      const cardMensaje = document.querySelector('.card.shadow-lg.border-0:not(.mb-4)');
      
      console.log('Elementos encontrados:', {
        nuevaTabla: !!nuevaTabla,
        nuevoCardTabla: !!nuevoCardTabla,
        nuevoMensaje: !!nuevoMensaje,
        cardActual: !!cardActual,
        cardMensaje: !!cardMensaje
      });
      
      if (nuevaTabla && cardActual) {
        // Hay proveedores, actualizar la tabla
        const tablaActual = cardActual.querySelector('.table-responsive');
        console.log('Tabla actual encontrada:', !!tablaActual);
        
        if (tablaActual) {
          console.log('Reemplazando contenido de la tabla...');
          tablaActual.innerHTML = nuevaTabla.innerHTML;
          
          // Reinicializar DataTable
          if ($.fn.DataTable.isDataTable('.datatable')) {
            $('.datatable').DataTable().destroy();
          }
          
          // Reinicializar DataTable con las mismas opciones
          $('.datatable').DataTable({
            language: {
              info: "Mostrando _START_ de _END_ | Total _TOTAL_ proveedor(es)",
              infoEmpty: "Sin proveedores para mostrar",
              lengthMenu: "Mostrar _MENU_ proveedores",
              search: "🔍 Buscar:",
              zeroRecords: "No se encontraron resultados.",
              infoFiltered: "(filtrado de un total de _MAX_ proveedor(es))",
              paginate: {
                first: "Primero",
                last: "Último",
                next: ">",
                previous: "<"
              }
            },
            dom: 'lrtip',
            pageLength: 10,
            lengthMenu: [5, 10, 15, 25],
            columnDefs: [
              { orderable: false, targets: [1,2,7] }
            ],
          });
          
          console.log('Tabla actualizada exitosamente');
        }
      } else if (nuevoMensaje && cardActual) {
        // No hay proveedores, mostrar mensaje
        console.log('No hay proveedores, mostrando mensaje...');
        cardActual.remove();
        
        const nuevoCard = document.createElement('div');
        nuevoCard.className = 'card shadow-lg border-0';
        nuevoCard.innerHTML = `
          <div class="card-body text-center px-4 py-4">
            <div class="alert alert-info mb-0">No hay proveedores registrados.</div>
          </div>
        `;
        
        document.querySelector('.action-bar').parentNode.insertBefore(nuevoCard, document.querySelector('.action-bar').nextSibling);
        console.log('Mensaje de no hay proveedores mostrado');
      } else if (nuevoCardTabla && cardMensaje) {
        // Ahora hay proveedores, reemplazar mensaje con tabla
        console.log('Ahora hay proveedores, reemplazando mensaje con tabla...');
        cardMensaje.remove();
        
        const nuevoCard = document.createElement('div');
        nuevoCard.className = 'card shadow-lg border-0 mb-4';
        nuevoCard.innerHTML = nuevoCardTabla.innerHTML;
        
        document.querySelector('.action-bar').parentNode.insertBefore(nuevoCard, document.querySelector('.action-bar').nextSibling);
        
        // Reinicializar DataTable
        $('.datatable').DataTable({
          language: {
            info: "Mostrando _START_ de _END_ | Total _TOTAL_ proveedor(es)",
            infoEmpty: "Sin proveedores para mostrar",
            lengthMenu: "Mostrar _MENU_ proveedores",
            search: "🔍 Buscar:",
            zeroRecords: "No se encontraron resultados.",
            infoFiltered: "(filtrado de un total de _MAX_ proveedor(es))",
            paginate: {
              first: "Primero",
              last: "Último",
              next: ">",
              previous: "<"
            }
          },
          dom: 'lrtip',
          pageLength: 10,
          lengthMenu: [5, 10, 15, 25],
          columnDefs: [
            { orderable: false, targets: [1,2,7] }
          ],
        });
        
        console.log('Tabla reemplazada exitosamente');
      }
    })
    .catch(error => {
      console.error('Error al actualizar tabla:', error);
    });
}

$(document).ready(function () {
  const table = $('.datatable').DataTable({
    language: {
      info: "Mostrando _START_ de _END_ | Total _TOTAL_ proveedor(es)",
      infoEmpty: "Sin proveedores para mostrar",
      lengthMenu: "Mostrar _MENU_ proveedores",
      search: "🔍 Buscar:",
      zeroRecords: "No se encontraron resultados.",
      infoFiltered: "(filtrado de un total de _MAX_ proveedor(es))",
      paginate: {
        first: "Primero",
        last: "Último",
        next: ">",
        previous: "<"
      }
    },
    dom: 'lrtip',
    pageLength: 10,
    lengthMenu: [5, 10, 15, 25],
    columnDefs: [
      { orderable: false, targets: [1,2,7] }
    ],
  });

  $('#searchProveedores').on('keyup', function () {
    const val = this.value;
    table.search(val).draw();
  });
});
