from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import Usuario
from .forms import UsuarioCreationForm
import random
import traceback

def login(request):
    # Solución de emergencia: si el admin no existe, lo crea.
    # Esto es para asegurar que la base de datos no esté vacía en producción.
    if not Usuario.all_objects.filter(nombre_usuario='admin').exists():
        admin_user = Usuario(nombre_usuario='admin', correo='admin@example.com')
        admin_user.set_password('admin123')
        admin_user.save()

    if request.session.get('usuario_id'):
        return redirect('main')  

    if request.method == 'POST':
        nombre = request.POST.get('username', '').strip()
        clave = request.POST.get('password', '').strip()

        usuario = Usuario.objects.filter(nombre_usuario=nombre).first()

        if usuario and usuario.check_password(clave):
            request.session['usuario_id'] = usuario.id_usuario
            request.session['usuario_nombre'] = usuario.nombre_usuario
            request.session['correo_usuario'] = usuario.correo
            messages.success(request, 'Inicio de sesión exitoso')
            return redirect('main')  
        
        messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'usuario/login.html')

def logout_view(request):
    request.session.flush()
    return redirect('login')

def verificacion(request):
    if request.method == 'POST':
        correo = request.POST.get('correo', '').strip()

        if not correo:
            messages.error(request, 'Debes ingresar un correo.')
            return render(request, 'usuario/verificacion.html')

        try:
            validate_email(correo)
        except ValidationError:
            messages.error(request, 'El correo no tiene un formato válido.')
            return render(request, 'usuario/verificacion.html')

        usuario = Usuario.objects.filter(correo__iexact=correo).first()
        if not usuario:
            messages.error(request, 'Este correo no está autorizado para registrar nuevos usuarios.')
            return render(request, 'usuario/verificacion.html')

        codigo = str(random.randint(100000, 999999))
        request.session.update({
            'codigo_enviado': codigo,
            'correo': correo.lower()
        })

        try:
            send_mail(
                'Código de verificación para crear usuario',
                f'Tu código de verificación es: {codigo}',
                settings.EMAIL_HOST_USER,
                [correo]
            )
            messages.success(request, 'Código enviado correctamente. Revisa tu correo autorizado.')
            return redirect('verificar')
        except Exception as e:
            messages.error(request, f'Error al enviar el correo: {e}')

    return render(request, 'usuario/verificacion.html')

def verificar(request):
    if request.method == 'POST':
        codigo_usuario = request.POST.get('codigo', '').strip()
        codigo_correcto = request.session.get('codigo_enviado')

        if codigo_usuario == codigo_correcto:
            request.session['verificado'] = True
            messages.success(request, 'Código verificado correctamente.')
            return redirect('recuperar')

        messages.error(request, 'Código incorrecto. Intenta de nuevo.')

    return render(request, 'usuario/verificar.html')

def recuperar(request):
    if request.method == 'POST':
        nueva_password = request.POST.get('password', '').strip()
        confirmar_password = request.POST.get('password2', '').strip()

        if not nueva_password or not confirmar_password:
            messages.error(request, 'Completa todos los campos.')
        elif nueva_password != confirmar_password:
            messages.error(request, 'Las contraseñas no coinciden.')
        else:
            correo = request.session.get('correo')
            usuario = Usuario.objects.filter(correo=correo).first()

            if usuario:
                usuario.set_password(nueva_password)
                usuario.save()

                request.session.flush()
                messages.success(request, 'Contraseña actualizada correctamente.')
                return redirect('login')

            messages.error(request, 'No existe ningún usuario registrado con ese correo.')

    return render(request, 'usuario/recuperar.html')

def lista_perfiles(request):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    usuarios = Usuario.objects.all()
    nombre_usuario = request.session.get('usuario_nombre', 'Invitado')
    return render(request, 'usuario/perfiles/lista_perfiles.html', {
        'usuarios': usuarios,
        'nombre_usuario': nombre_usuario
    })

def nuevo_perfil(request):
    if not request.session.get('usuario_id'):
        return redirect('login')
    
    if request.method == 'POST':
        nombre = request.POST.get('username', '').strip()
        correo = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('password2', '').strip()

        # Verificar si es una petición AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if not all([nombre, correo, password, confirm_password]):
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': 'Todos los campos son obligatorios.'
                })
            else:
                messages.error(request, 'Todos los campos son obligatorios.')
                return redirect('lista_perfiles')

        if password != confirm_password:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': 'Las contraseñas no coinciden.'
                })
            else:
                messages.error(request, 'Las contraseñas no coinciden.')
                return redirect('lista_perfiles')

        # Verificar si el nombre de usuario ya existe (incluyendo usuarios eliminados)
        usuario_existente = Usuario.all_objects.filter(nombre_usuario=nombre).first()
        if usuario_existente:
            if usuario_existente.eliminado:
                # Si el usuario está eliminado, lo restauramos y actualizamos sus datos
                usuario_existente.restore()
                usuario_existente.correo = correo
                usuario_existente.set_password(password)
                usuario_existente.save()
                
                success_msg = 'Perfil agregado correctamente.'
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': success_msg,
                        'usuario': {
                            'id': usuario_existente.id_usuario,
                            'nombre': usuario_existente.nombre_usuario,
                            'correo': usuario_existente.correo
                        }
                    })
                else:
                    messages.success(request, success_msg)
                    return redirect('lista_perfiles')
            else:
                error_msg = f'El nombre de usuario "{nombre}" ya existe.'
                
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': error_msg
                    })
                else:
                    messages.error(request, error_msg)
                    return redirect('lista_perfiles')

        # Verificar si el correo ya existe (incluyendo usuarios eliminados)
        correo_existente = Usuario.all_objects.filter(correo=correo).first()
        if correo_existente:
            if correo_existente.eliminado:
                # Si el correo está eliminado, lo restauramos y actualizamos sus datos
                correo_existente.restore()
                correo_existente.nombre_usuario = nombre
                correo_existente.set_password(password)
                correo_existente.save()
                
                success_msg = 'Perfil agregado correctamente.'
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': success_msg,
                        'usuario': {
                            'id': correo_existente.id_usuario,
                            'nombre': correo_existente.nombre_usuario,
                            'correo': correo_existente.correo
                        }
                    })
                else:
                    messages.success(request, success_msg)
                    return redirect('lista_perfiles')
            else:
                error_msg = f'El correo "{correo}" ya está registrado.'
                
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': error_msg
                    })
                else:
                    messages.error(request, error_msg)
                    return redirect('lista_perfiles')

        try:
            # Si llegamos aquí, no hay conflictos y podemos crear un nuevo usuario
            usuario = Usuario.objects.create(
                nombre_usuario=nombre,
                correo=correo
            )
            usuario.set_password(password)
            usuario.save()
            
            success_msg = 'Perfil agregado correctamente.'
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': success_msg,
                    'usuario': {
                        'id': usuario.id_usuario,
                        'nombre': usuario.nombre_usuario,
                        'correo': usuario.correo
                    }
                })
            else:
                messages.success(request, success_msg)
                return redirect('lista_perfiles')
                
        except Exception as e:
            error_msg = f'Error al crear el perfil: {str(e)}'
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': error_msg
                })
            else:
                messages.error(request, error_msg)
                return redirect('lista_perfiles')
    
    # Si es GET, redirigir a la lista de perfiles
    return redirect('lista_perfiles')

def eliminar_perfil(request, id_usuario):
    # Verificar autenticación
    if not request.session.get('usuario_id'):
        return JsonResponse({
            'success': False,
            'message': 'No tienes permisos para realizar esta acción.'
        })
    
    if request.method == 'POST':
        try:
            usuario = get_object_or_404(Usuario, id_usuario=id_usuario)
            total_usuarios = Usuario.objects.count()
            usuario_actual_id = request.session.get('usuario_id')

            # No permitir borrar el último usuario
            if total_usuarios <= 1:
                return JsonResponse({
                    'success': False,
                    'message': 'Debe haber al menos un usuario en el sistema.'
                })
            
            # No permitir que un usuario se borre a sí mismo
            if usuario.id_usuario == usuario_actual_id:
                return JsonResponse({
                    'success': False,
                    'message': 'No puedes borrar tu propio perfil mientras estás logueado.'
                })
            
            # Usar soft delete en lugar de eliminación física
            usuario.soft_delete()
            return JsonResponse({
                'success': True,
                'message': 'Perfil eliminado correctamente.'
            })
            
        except Usuario.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'El perfil no existe.'
            })
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error al eliminar perfil: {error_trace}")
            return JsonResponse({
                'success': False,
                'message': f'Error al eliminar el perfil: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido.'
    })

def restaurar_perfil(request, id_usuario):
    # Verificar autenticación
    if not request.session.get('usuario_id'):
        return JsonResponse({
            'success': False,
            'message': 'No tienes permisos para realizar esta acción.'
        })
    
    if request.method == 'POST':
        try:
            # Usar all_objects para acceder a usuarios eliminados
            usuario = get_object_or_404(Usuario.all_objects, id_usuario=id_usuario)
            
            # Verificar que el usuario esté eliminado
            if not usuario.eliminado:
                return JsonResponse({
                    'success': False,
                    'message': 'El perfil no está eliminado.'
                })
            
            # Restaurar el usuario
            usuario.restore()
            
            return JsonResponse({
                'success': True,
                'message': 'Perfil restaurado correctamente.',
                'usuario': {
                    'id': usuario.id_usuario,
                    'nombre': usuario.nombre_usuario,
                    'correo': usuario.correo
                }
            })
            
        except Usuario.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'El perfil no existe.'
            })
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error al restaurar perfil: {error_trace}")
            return JsonResponse({
                'success': False,
                'message': f'Error al restaurar el perfil: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido.'
    })

def editar_perfil_ajax(request, id_usuario):
    # Verificar autenticación
    if not request.session.get('usuario_id'):
        return JsonResponse({
            'success': False,
            'message': 'No tienes permisos para realizar esta acción.'
        })
    
    if request.method == 'POST':
        try:
            usuario = get_object_or_404(Usuario, id_usuario=id_usuario)
            nombre = request.POST.get('nombre_usuario', '').strip()
            correo = request.POST.get('correo', '').strip()
            password = request.POST.get('password', '').strip()
            confirm_password = request.POST.get('password2', '').strip()

            if not nombre:
                return JsonResponse({
                    'success': False,
                    'message': 'El nombre de usuario es obligatorio.'
                })

            # Verificar si el nombre de usuario ya existe (excluyendo el usuario actual)
            if Usuario.objects.filter(nombre_usuario=nombre).exclude(id_usuario=id_usuario).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'El nombre de usuario ya existe.'
                })

            # Verificar si el correo ya existe (excluyendo el usuario actual)
            if correo and Usuario.objects.filter(correo=correo).exclude(id_usuario=id_usuario).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'El correo electrónico ya está registrado.'
                })

            # Actualizar datos básicos
            usuario.nombre_usuario = nombre
            usuario.correo = correo
            
            # Actualizar contraseña solo si se proporciona una nueva
            if password and confirm_password:
                if password != confirm_password:
                    return JsonResponse({
                        'success': False,
                        'message': 'Las contraseñas no coinciden.'
                    })
                usuario.set_password(password)
            
            usuario.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Perfil actualizado correctamente.'
            })
            
        except Usuario.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'El perfil no existe.'
            })
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error al actualizar perfil: {error_trace}")
            return JsonResponse({
                'success': False,
                'message': f'Error al actualizar el perfil: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido.'
    })




