from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from home.models import Producto, Codigo
from .forms import ProductoForm
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse

def productos(request):
    lista_productos = Producto.objects.all()
    nombre_usuario = request.session.get('usuario_nombre', 'Invitado')
    return render(request, 'producto/productos.html', {
        'productos': lista_productos,
        'nombre_usuario': nombre_usuario,
    })

def agregar_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        codigo = request.POST.get('codigo', '').strip()
        
        # Validar si el código ya existe (solo productos no eliminados)
        if codigo and Codigo.objects.filter(codigo=codigo, id_producto__eliminado=False).exists():
            return JsonResponse({
                'success': False,
                'message': f"El código SKU '{codigo}' ya existe. Por favor, use un código diferente.",
                'field': 'codigo'
            })
        
        if form.is_valid():
            producto = form.save()
            if codigo:
                Codigo.objects.create(id_producto=producto, codigo=codigo)
            return JsonResponse({
                'success': True,
                'message': 'Producto agregado correctamente.'
            })
        else:
            # Devolver errores del formulario
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list[0]
            return JsonResponse({
                'success': False,
                'message': 'Error al agregar el producto.',
                'errors': errors
            })
    
    return redirect('productos')

def editar_producto(request, id):
    producto = get_object_or_404(Producto, id_producto=id)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        codigo = request.POST.get('codigo', '').strip()
        
        # Validar si el código ya existe (excluyendo el código actual del producto)
        codigo_actual = producto.codigo_set.first()
        if codigo:
            if codigo_actual and codigo == codigo_actual.codigo:
                # Es el mismo código, no hay problema
                pass
            elif Codigo.objects.filter(codigo=codigo, id_producto__eliminado=False).exists():
                return JsonResponse({
                    'success': False,
                    'message': f"El código SKU '{codigo}' ya existe. Por favor, use un código diferente.",
                    'field': 'codigo'
                })
        
        if form.is_valid():
            form.save()
            if codigo:
                Codigo.objects.filter(id_producto=producto).delete()
                Codigo.objects.create(id_producto=producto, codigo=codigo)
            return JsonResponse({
                'success': True,
                'message': 'Producto editado correctamente.'
            })
        else:
            # Devolver errores del formulario
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list[0]
            return JsonResponse({
                'success': False,
                'message': 'Error al actualizar el producto.',
                'errors': errors
            })
    
    return redirect('productos')

def eliminar_producto(request, id):
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id_producto=id)
        try:
            # Usar soft delete en lugar de eliminación permanente
            producto.soft_delete()
            return JsonResponse({
                'success': True,
                'message': 'Producto eliminado correctamente.',
                'producto_id': producto.id_producto
            })
        except ValueError as e:
            # Capturar el error específico de dependencias
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Error al eliminar el producto.'
            })
    
    return redirect('productos')

def restaurar_producto(request, id):
    if request.method == 'POST':
        producto = get_object_or_404(Producto.all_objects, id_producto=id, eliminado=True)
        try:
            producto.restore()
            return JsonResponse({
                'success': True,
                'message': 'Producto restaurado correctamente.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Error al restaurar el producto.'
            })
    
    return redirect('productos')

def validar_codigo(request):
    codigo = request.GET.get('codigo', '').strip()
    existe = Codigo.objects.filter(codigo=codigo, id_producto__eliminado=False).exists()
    return JsonResponse({'existe': existe})
