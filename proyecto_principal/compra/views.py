from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, FileResponse
from home.models import Compra, Producto, Codigo, DetalleCompra, Categoria, Proveedore, ProductoProveedore
from .forms import CompraForm, DetalleCompraForm
from decimal import Decimal
from django.db import transaction
from django.forms import modelformset_factory
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.db.models import Q
from io import BytesIO
import xlsxwriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
from django.db import models
from usuario.models import Usuario
from reportlab.lib.units import mm
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date

# --- Utilidades de carrito en sesión ---
def get_cart(request):
    carrito = request.session.get('carrito_compra', [])
    
    # Si el carrito no existe en la sesión, inicializarlo
    if 'carrito_compra' not in request.session:
        request.session['carrito_compra'] = []
        request.session.modified = True
        carrito = []
    
    return carrito

def save_cart(request, cart):
    request.session['carrito_compra'] = cart
    request.session.modified = True

def clear_cart(request):
    if 'carrito_compra' in request.session:
        del request.session['carrito_compra']
        request.session.modified = True
    # Asegurar que el carrito esté inicializado como lista vacía
    if 'carrito_compra' not in request.session:
        request.session['carrito_compra'] = []
        request.session.modified = True

def get_producto_or_none(producto_id):
    try:
        return Producto.objects.get(id_producto=producto_id)
    except Producto.DoesNotExist:
        return None

# --- Vistas de Carrito ---
def compras(request):
    mostrar = int(request.GET.get('mostrar', 5))
    orden = request.GET.get('orden', 'desc')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    # Debug: imprimir parámetros recibidos
    print(f"DEBUG - Parámetros recibidos: fecha_inicio={fecha_inicio}, fecha_fin={fecha_fin}")

    compras_qs = Compra.objects.filter(eliminado=False)
    if fecha_inicio:
        print(f"DEBUG - Aplicando filtro fecha_inicio: {fecha_inicio}")
        compras_qs = compras_qs.filter(fecha__date__gte=parse_date(fecha_inicio))
    if fecha_fin:
        print(f"DEBUG - Aplicando filtro fecha_fin: {fecha_fin}")
        compras_qs = compras_qs.filter(fecha__date__lte=parse_date(fecha_fin))
    
    print(f"DEBUG - Total de compras después de filtros: {compras_qs.count()}")

    if orden == 'asc':
        lista_compras = compras_qs.order_by('fecha', 'id_compra')
    else:
        lista_compras = compras_qs.order_by('-fecha', '-id_compra')
    nombre_usuario = request.session.get('usuario_nombre', 'Invitado')

    # Inicializar carrito explícitamente
    if 'carrito_compra' not in request.session:
        request.session['carrito_compra'] = []
        request.session.modified = True

    # Carrito actual en sesión
    carrito = get_cart(request)
    
    # Asegurar que el carrito sea una lista válida
    if carrito is None or not isinstance(carrito, list):
        carrito = []
        save_cart(request, carrito)
    
    productos_carrito = []
    total_carrito = Decimal('0.00')
    
    for item in carrito:
        try:
            producto = Producto.objects.get(id_producto=item['producto_id'])
            # Obtener precio del proveedor si está disponible
            precio_compra = item.get('precio_compra', producto.precio_unitario)
            # Convertir a Decimal para cálculos precisos
            precio_compra_decimal = Decimal(str(precio_compra))
            subtotal = precio_compra_decimal * item['cantidad']
            subtotal_float = float(subtotal)
            
            # Obtener el proveedor del carrito
            proveedor = None
            if 'proveedor_id' in item:
                try:
                    proveedor = Proveedore.objects.get(id_proveedor=item['proveedor_id'])
                except Proveedore.DoesNotExist:
                    pass
            
            productos_carrito.append({
                'producto': producto,
                'proveedor': proveedor,
                'cantidad': item['cantidad'],
                'precio_compra': float(precio_compra),
                'subtotal': subtotal_float
            })
            total_carrito += subtotal  # subtotal es Decimal, compatible con total_carrito
        except Producto.DoesNotExist:
            continue

    # Obtener todos los productos disponibles para el formulario
    productos = Producto.objects.all()
    categorias = Categoria.objects.all()
    proveedores = Proveedore.objects.all()

    # Obtener detalles de cada compra (agrupados)
    compras_con_detalles = []
    for compra in lista_compras:
        detalles = []
        total_compra = Decimal('0.00')
        # Solo incluir detalles con cantidad > 0
        for d in compra.detalles.select_related('producto').all():
            if d.cantidad > 0:
                subtotal = d.cantidad * d.precio_compra
                subtotal_float = float(subtotal)
                
                # Usar el proveedor de la compra directamente
                detalles.append({
                    'producto': d.producto,
                    'proveedor': compra.proveedor,
                    'cantidad': d.cantidad,
                    'precio_compra': float(d.precio_compra),
                    'subtotal': subtotal_float,
                })
                total_compra += subtotal  # subtotal es Decimal, compatible con total_compra
        compras_con_detalles.append({
            'compra': compra,
            'detalles': detalles,
            'total_compra': float(total_compra),
        })

    # Paginación: compras por página según 'mostrar'
    page_number = request.GET.get('page', 1)
    paginator = Paginator(compras_con_detalles, mostrar)
    page_obj = paginator.get_page(page_number)

    context = {
        'compras': lista_compras,
        'compras_con_detalles': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'nombre_usuario': nombre_usuario,
        'carrito': productos_carrito,
        'total_carrito': float(total_carrito),
        'productos': productos,
        'categorias': categorias,
        'proveedores': proveedores,
        'mostrar': mostrar,
        'orden': orden,
    }
    
    return render(request, 'compra/compras.html', context)

@require_POST
def agregar_a_carrito(request):
    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        proveedor_id = request.POST.get('proveedor_id')
        
        if not producto_id or not producto_id.isdigit():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Debes seleccionar un producto válido.'
                })
            messages.error(request, 'Debes seleccionar un producto válido.')
            return redirect('compras')
            
        if not proveedor_id or not proveedor_id.isdigit():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Debes seleccionar un proveedor.'
                })
            messages.error(request, 'Debes seleccionar un proveedor.')
            return redirect('compras')
            
        try:
            cantidad = int(request.POST.get('cantidad', 1))
        except (TypeError, ValueError):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Cantidad inválida.'
                })
            messages.error(request, 'Cantidad inválida.')
            return redirect('compras')
            
        if cantidad <= 0:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'La cantidad debe ser mayor a cero.'
                })
            messages.error(request, 'La cantidad debe ser mayor a cero.')
            return redirect('compras')
            
        producto = get_producto_or_none(producto_id)
        if not producto:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Producto no encontrado.'
                })
            messages.error(request, 'Producto no encontrado.')
            return redirect('compras')
            
        proveedor = get_object_or_404(Proveedore, id_proveedor=proveedor_id)
        
        # Obtener precio del proveedor si está disponible
        try:
            producto_proveedor = ProductoProveedore.objects.get(
                id_producto=producto, 
                id_proveedor=proveedor
            )
            precio_compra = producto_proveedor.precio_proveedor or producto.precio_unitario
        except ProductoProveedore.DoesNotExist:
            precio_compra = producto.precio_unitario
        
        # Convertir Decimal a float para JSON
        precio_compra_float = float(precio_compra)
        
        carrito = get_cart(request)
        
        # Verificar si el producto ya está en el carrito
        producto_existente = None
        for item in carrito:
            if item['producto_id'] == producto_id and item['proveedor_id'] == proveedor_id:
                producto_existente = item
                break
        
        if producto_existente:
            # Actualizar cantidad existente
            producto_existente['cantidad'] += cantidad
            producto_existente['precio_compra'] = precio_compra_float
        else:
            # Agregar nuevo producto al carrito
            carrito.append({
                'producto_id': producto_id,
                'proveedor_id': proveedor_id,
                'cantidad': cantidad,
                'precio_compra': precio_compra_float
            })
        
        save_cart(request, carrito)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'{producto.nombre} agregado al carrito.',
                'carrito_count': len(carrito)
            })
        
        messages.success(request, f'{producto.nombre} agregado al carrito.')
        return redirect('compras')

@require_POST
def eliminar_de_carrito(request, producto_id):
    carrito = get_cart(request)
    carrito = [item for item in carrito if str(item['producto_id']) != str(producto_id)]
    save_cart(request, carrito)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Producto eliminado del carrito.'})
    messages.success(request, 'Producto eliminado del carrito.')
    return redirect('compras')

@require_POST
def editar_carrito(request, producto_id):
    if request.method == 'POST':
        try:
            nueva_cantidad = int(request.POST.get('cantidad', 1))
        except (TypeError, ValueError):
            messages.error(request, 'Cantidad inválida.')
            return redirect('compras')
        if nueva_cantidad <= 0:
            messages.error(request, 'La cantidad debe ser mayor a cero.')
            return redirect('compras')
        producto = get_producto_or_none(producto_id)
        if not producto:
            messages.error(request, 'Producto no encontrado.')
            return redirect('compras')
        carrito = get_cart(request)
        for item in carrito:
            if str(item['producto_id']) == str(producto_id):
                item['cantidad'] = nueva_cantidad
                break
        save_cart(request, carrito)
        messages.success(request, 'Cantidad editada correctamente en el carrito.')
    return redirect('compras')

@require_POST
def finalizar_compra(request):
    carrito = get_cart(request)
    
    if not carrito:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'El carrito está vacío.'
            })
        messages.error(request, 'El carrito está vacío.')
        return redirect('compras')
    
    try:
        with transaction.atomic():
            # Obtener el usuario personalizado desde la sesión
            usuario_id = request.session.get('usuario_id')
            usuario = None
            if usuario_id:
                from usuario.models import Usuario
                try:
                    usuario = Usuario.objects.get(id_usuario=usuario_id)
                except Usuario.DoesNotExist:
                    pass
            
            # Crear la compra
            compra = Compra.objects.create(
                usuario=usuario,
                observaciones=request.POST.get('observaciones', '')
            )
            
            total_compra = Decimal('0.00')
            
            # Crear detalles de compra
            for item in carrito:
                producto = Producto.objects.get(id_producto=item['producto_id'])
                proveedor = Proveedore.objects.get(id_proveedor=item['proveedor_id'])
                
                # Actualizar stock del producto
                producto.stock_actual += item['cantidad']
                producto.save()
                
                # Crear detalle de compra
                detalle = DetalleCompra.objects.create(
                    compra=compra,
                    producto=producto,
                    cantidad=item['cantidad'],
                    precio_compra=Decimal(str(item['precio_compra'])),
                    subtotal=Decimal(str(item['precio_compra'])) * item['cantidad']
                )
                
                total_compra += detalle.subtotal
            
            # Actualizar total de la compra
            compra.total_compra = total_compra
            # Usar el proveedor del primer item del carrito como proveedor principal de la compra
            compra.proveedor = Proveedore.objects.get(id_proveedor=carrito[0]['proveedor_id'])
            compra.save()
            
            # Limpiar carrito
            clear_cart(request)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Compra #{compra.id_compra} creada exitosamente.'
                })
            messages.success(request, f'Compra #{compra.id_compra} creada exitosamente.')
            return redirect('compras')
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'Error al crear la compra: {str(e)}'
            })
        messages.error(request, f'Error al crear la compra: {str(e)}')
        return redirect('compras')

def agregar_compra(request):
    if request.method == 'POST':
        form = CompraForm(request.POST)
        if form.is_valid():
            compra = form.save(commit=False)
            compra.usuario = request.user if request.user.is_authenticated else None
            compra.save()
            messages.success(request, 'Compra agregada exitosamente.')
            return redirect('compras')
    else:
        form = CompraForm()
    
    return render(request, 'compra/agregar_compra.html', {'form': form})

@require_POST
def eliminar_compra(request, id):
    try:
        compra = Compra.objects.get(id_compra=id)
        compra.soft_delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Compra #{compra.id_compra} eliminada exitosamente.',
                'compra_id': compra.id_compra
            })
        
        messages.success(request, f'Compra #{compra.id_compra} eliminada exitosamente.')
        return redirect('compras')
        
    except Compra.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Compra no encontrada.'
            })
        
        messages.error(request, 'Compra no encontrada.')
        return redirect('compras')

@require_POST
def restaurar_compra(request, id):
    try:
        compra = Compra.all_objects.get(id_compra=id)
        compra.restore()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Compra #{compra.id_compra} restaurada exitosamente.',
                'compra_id': compra.id_compra
            })
        
        messages.success(request, f'Compra #{compra.id_compra} restaurada exitosamente.')
        return redirect('compras')
        
    except Compra.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Compra no encontrada.'
            })
        
        messages.error(request, 'Compra no encontrada.')
        return redirect('compras')

@require_POST
def confirmar_entrega(request, id):
    try:
        compra = Compra.objects.get(id_compra=id)
        compra.fecha_entrega = timezone.now()
        compra.actualizar_estado()  # Esto cambiará el estado a 'ENTREGADO'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Entrega de compra #{compra.id_compra} confirmada.',
                'compra_id': compra.id_compra
            })
        
        messages.success(request, f'Entrega de compra #{compra.id_compra} confirmada.')
        return redirect('compras')
        
    except Compra.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Compra no encontrada.'
            })
        
        messages.error(request, 'Compra no encontrada.')
        return redirect('compras')

def validar_producto(request):
    producto_id = request.GET.get('producto_id')
    if producto_id:
        try:
            producto = Producto.objects.get(id_producto=producto_id)
            return JsonResponse({
                'existe': True,
                'nombre': producto.nombre,
                'precio': float(producto.precio_unitario)
            })
        except Producto.DoesNotExist:
            return JsonResponse({'existe': False})
    return JsonResponse({'existe': False})

def editar_compra(request, id):
    compra = get_object_or_404(Compra, id_compra=id)
    
    if request.method == 'POST':
        # Procesar cambios en las cantidades
        detalles = compra.detalles.all()
        total_compra = Decimal('0.00')
        
        for detalle in detalles:
            nueva_cantidad = int(request.POST.get(f'cantidad_{detalle.id_detalle}', 0))
            if nueva_cantidad >= 0:
                detalle.cantidad = nueva_cantidad
                detalle.subtotal = detalle.precio_compra * nueva_cantidad
                detalle.save()
                total_compra += detalle.subtotal
        
        # Actualizar total de la compra
        compra.total_compra = total_compra
        compra.observaciones = request.POST.get('observaciones', '')
        compra.save()
        
        messages.success(request, 'Compra actualizada exitosamente.')
        return redirect('compras')
    
    # Obtener detalles de la compra con proveedores
    detalles = compra.detalles.select_related('producto').all()
    
    # Agregar información del proveedor a cada detalle
    detalles_con_proveedor = []
    for detalle in detalles:
        detalles_con_proveedor.append({
            'detalle': detalle,
            'producto': detalle.producto,
            'proveedor': compra.proveedor,
            'cantidad': detalle.cantidad,
            'precio_compra': detalle.precio_compra,
            'subtotal': detalle.subtotal
        })
    
    # Debug: imprimir información de los detalles
    print(f"DEBUG: Compra {compra.id_compra} tiene {len(detalles_con_proveedor)} detalles")
    for detalle_info in detalles_con_proveedor:
        print(f"DEBUG: Detalle {detalle_info['detalle'].id_detalle} - Producto: {detalle_info['producto'].nombre}, Cantidad: {detalle_info['cantidad']}, Precio: {detalle_info['precio_compra']}, Subtotal: {detalle_info['subtotal']}")
    
    return render(request, 'compra/editar_compra.html', {
        'compra': compra,
        'detalles': detalles_con_proveedor
    })

@csrf_exempt
@require_POST
def editar_compra_ajax(request, id):
    try:
        compra = Compra.objects.get(id_compra=id)
        # Lógica de edición AJAX aquí
        return JsonResponse({'success': True, 'message': 'Compra actualizada exitosamente.'})
    except Compra.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Compra no encontrada.'})

@require_GET
def autocomplete_productos(request):
    query = request.GET.get('q', '').strip()
    proveedor_id = request.GET.get('proveedor')
    
    if not query:
        return JsonResponse({'results': []})
    
    # Si hay proveedor seleccionado, buscar solo productos de ese proveedor
    if proveedor_id:
        productos_proveedor = ProductoProveedore.objects.filter(
            id_proveedor_id=proveedor_id
        ).select_related('id_producto', 'id_producto__id_categoria')
        
        # Filtrar por nombre o código del producto
        productos_filtrados = []
        for pp in productos_proveedor:
            producto = pp.id_producto
            # Buscar coincidencia en nombre o códigos
            if (query.lower() in producto.nombre.lower() or 
                any(query.lower() in codigo.codigo.lower() for codigo in producto.codigo_set.all())):
                productos_filtrados.append(pp)
    else:
        # Si no hay proveedor, buscar todos los productos
        productos = Producto.objects.filter(
            Q(nombre__icontains=query) |
            Q(codigo__codigo__icontains=query)
        ).distinct()
        
        productos_filtrados = []
        for producto in productos:
            # Crear un objeto similar a ProductoProveedore para mantener consistencia
            productos_filtrados.append(type('obj', (object,), {
                'id_producto': producto
            })())
    
    # Ordenar por nombre del producto y limitar a 10
    productos_filtrados.sort(key=lambda x: x.id_producto.nombre)
    productos_filtrados = productos_filtrados[:10]
    
    results = []
    for pp in productos_filtrados:
        producto = pp.id_producto
        codigo = producto.codigo_set.first()
        results.append({
            'id': producto.id_producto,
            'nombre': producto.nombre,
            'codigo': codigo.codigo if codigo else '',
            'precio_venta': float(producto.precio_unitario),
            'stock': producto.stock_actual,
            'categoria': producto.id_categoria.nombre if producto.id_categoria else None
        })
    
    return JsonResponse({'results': results})

@require_GET
def autocomplete_proveedores(request):
    query = request.GET.get('q', '').strip()
    producto_id = request.GET.get('producto')
    
    if not query:
        return JsonResponse({'results': []})
    
    # Si hay producto seleccionado, buscar solo proveedores de ese producto
    if producto_id:
        proveedores_producto = ProductoProveedore.objects.filter(
            id_producto_id=producto_id
        ).select_related('id_proveedor')
        
        # Filtrar por nombre del proveedor
        proveedores_filtrados = []
        for pp in proveedores_producto:
            proveedor = pp.id_proveedor
            if query.lower() in proveedor.nombre.lower():
                proveedores_filtrados.append(proveedor)
    else:
        # Si no hay producto, buscar todos los proveedores
        proveedores_filtrados = Proveedore.objects.filter(
            nombre__icontains=query
        )
    
    # Ordenar por nombre y limitar a 10
    proveedores_filtrados = sorted(proveedores_filtrados, key=lambda x: x.nombre)[:10]
    
    results = []
    for p in proveedores_filtrados:
        results.append({
            'id': p.id_proveedor,
            'nombre': p.nombre,
            'telefono': p.telefono or '',
            'correo': p.correo or ''
        })
    
    return JsonResponse({'results': results})

@require_GET
def obtener_estado_compra(request, id_compra):
    try:
        compra = Compra.objects.get(id_compra=id_compra)
        return JsonResponse({
            'estado': compra.estado,
            'fecha_entrega': compra.fecha_entrega.isoformat() if compra.fecha_entrega else None
        })
    except Compra.DoesNotExist:
        return JsonResponse({'error': 'Compra no encontrada'}, status=404)

@require_GET
def validar_codigo(request):
    codigo = request.GET.get('codigo', '').strip()
    if codigo:
        try:
            producto = Producto.objects.get(codigo__codigo=codigo)
            return JsonResponse({
                'existe': True,
                'nombre': producto.nombre,
                'precio': float(producto.precio_unitario)
            })
        except Producto.DoesNotExist:
            return JsonResponse({'existe': False})
    return JsonResponse({'existe': False})

@require_GET
def verificar_compatibilidad(request):
    producto_id = request.GET.get('producto')
    proveedor_id = request.GET.get('proveedor')
    
    if not producto_id or not proveedor_id:
        return JsonResponse({'compatible': False})
    
    try:
        # Verificar si existe la relación ProductoProveedore
        compatible = ProductoProveedore.objects.filter(
            id_producto_id=producto_id,
            id_proveedor_id=proveedor_id
        ).exists()
        
        return JsonResponse({'compatible': compatible})
    except Exception as e:
        return JsonResponse({'compatible': False})
