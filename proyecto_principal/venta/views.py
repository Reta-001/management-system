from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, FileResponse
from home.models import Venta, Producto, Codigo, DetalleVenta, Categoria, Reembolso, ReembolsoDetalle, ConfiguracionBoleta
from .forms import VentaForm, DetalleVentaForm
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
from django.utils.dateparse import parse_date

# --- Utilidades de carrito en sesión ---
def get_cart(request):
    carrito = request.session.get('carrito_venta', [])
    
    # Si el carrito no existe en la sesión, inicializarlo
    if 'carrito_venta' not in request.session:
        request.session['carrito_venta'] = []
        request.session.modified = True
        carrito = []
    
    return carrito

def save_cart(request, cart):
    request.session['carrito_venta'] = cart
    request.session.modified = True

def clear_cart(request):
    if 'carrito_venta' in request.session:
        del request.session['carrito_venta']
        request.session.modified = True
    # Asegurar que el carrito esté inicializado como lista vacía
    if 'carrito_venta' not in request.session:
        request.session['carrito_venta'] = []
        request.session.modified = True

def get_producto_or_none(producto_id):
    try:
        return Producto.objects.get(id_producto=producto_id)
    except Producto.DoesNotExist:
        return None

# --- Vistas de Carrito ---
def ventas(request):
    mostrar = int(request.GET.get('mostrar', 5))
    orden = request.GET.get('orden', 'desc')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    # Debug: imprimir parámetros recibidos
    print(f"DEBUG VENTAS - Parámetros recibidos: fecha_inicio={fecha_inicio}, fecha_fin={fecha_fin}")

    ventas_qs = Venta.objects.filter(eliminado=False)
    if fecha_inicio:
        print(f"DEBUG VENTAS - Aplicando filtro fecha_inicio: {fecha_inicio}")
        ventas_qs = ventas_qs.filter(fecha__date__gte=parse_date(fecha_inicio))
    if fecha_fin:
        print(f"DEBUG VENTAS - Aplicando filtro fecha_fin: {fecha_fin}")
        ventas_qs = ventas_qs.filter(fecha__date__lte=parse_date(fecha_fin))
    
    print(f"DEBUG VENTAS - Total de ventas después de filtros: {ventas_qs.count()}")

    if orden == 'asc':
        lista_ventas = ventas_qs.order_by('fecha', 'id_venta')
    else:
        lista_ventas = ventas_qs.order_by('-fecha', '-id_venta')
    nombre_usuario = request.session.get('usuario_nombre', 'Invitado')

    # Inicializar carrito explícitamente
    if 'carrito_venta' not in request.session:
        request.session['carrito_venta'] = []
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
            subtotal = producto.precio_unitario * item['cantidad']
            productos_carrito.append({
                'producto': producto,
                'cantidad': item['cantidad'],
                'subtotal': subtotal
            })
            total_carrito += subtotal
        except Producto.DoesNotExist:
            continue

    # Obtener todos los productos disponibles para el formulario
    productos = Producto.objects.all()
    categorias = Categoria.objects.all()

    # Obtener detalles de cada venta (agrupados)
    ventas_con_detalles = []
    for venta in lista_ventas:
        detalles = []
        total_venta = 0
        # Solo incluir detalles con cantidad > 0
        for d in venta.detalles.select_related('producto').all():
            if d.cantidad > 0:
                subtotal = d.cantidad * d.precio_unitario
                detalles.append({
                    'producto': d.producto,
                    'cantidad': d.cantidad,
                    'precio_unitario': d.precio_unitario,
                    'subtotal': subtotal,
                })
                total_venta += subtotal
        ventas_con_detalles.append({
            'venta': venta,
            'detalles': detalles,
            'total_venta': total_venta,
        })

    # Paginación: ventas por página según 'mostrar'
    page_number = request.GET.get('page', 1)
    paginator = Paginator(ventas_con_detalles, mostrar)
    page_obj = paginator.get_page(page_number)

    context = {
        'ventas': lista_ventas,
        'ventas_con_detalles': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'nombre_usuario': nombre_usuario,
        'carrito': productos_carrito,
        'total_carrito': total_carrito,
        'productos': productos,
        'categorias': categorias,
        'mostrar': mostrar,
        'orden': orden,
    }
    
    return render(request, 'venta/ventas.html', context)

@require_POST
def agregar_a_carrito(request):
    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        if not producto_id or not producto_id.isdigit():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Debes seleccionar un producto válido.'
                })
            messages.error(request, 'Debes seleccionar un producto válido.')
            return redirect('ventas')
        try:
            cantidad = int(request.POST.get('cantidad', 1))
        except (TypeError, ValueError):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Cantidad inválida.'
                })
            messages.error(request, 'Cantidad inválida.')
            return redirect('ventas')
        if cantidad <= 0:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'La cantidad debe ser mayor a cero.'
                })
            messages.error(request, 'La cantidad debe ser mayor a cero.')
            return redirect('ventas')
        producto = get_producto_or_none(producto_id)
        if not producto:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Producto no encontrado.'
                })
            messages.error(request, 'Producto no encontrado.')
            return redirect('ventas')
        if producto.stock_actual < cantidad:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Stock insuficiente para el producto.'
                })
            messages.error(request, 'Stock insuficiente para el producto.')
            return redirect('ventas')
        carrito = get_cart(request)
        # Buscar si el producto ya está en el carrito
        producto_en_carrito = False
        for item in carrito:
            if item['producto_id'] == producto.id_producto:
                # Si ya existe, reemplazar la cantidad (no sumar)
                item['cantidad'] = cantidad
                producto_en_carrito = True
                break
        
        # Si no existe, agregarlo
        if not producto_en_carrito:
            carrito.append({'producto_id': producto.id_producto, 'cantidad': cantidad})
        
        save_cart(request, carrito)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'{producto.nombre} agregado al carrito.'
            })
        messages.success(request, f'{producto.nombre} agregado al carrito.')
        return redirect('ventas')
    return redirect('ventas')

@require_POST
def eliminar_de_carrito(request, producto_id):
    carrito = get_cart(request)
    carrito = [item for item in carrito if item['producto_id'] != int(producto_id)]
    save_cart(request, carrito)
    messages.error(request, 'Producto eliminado del carrito.')
    return redirect('ventas')

@require_POST
def editar_carrito(request, producto_id):
    if request.method == 'POST':
        try:
            nueva_cantidad = int(request.POST.get('cantidad', 1))
        except (TypeError, ValueError):
            messages.error(request, 'Cantidad inválida.')
            return redirect('ventas')
        if nueva_cantidad <= 0:
            messages.error(request, 'La cantidad debe ser mayor a cero.')
            return redirect('ventas')
        producto = get_producto_or_none(producto_id)
        if not producto:
            messages.error(request, 'Producto no encontrado.')
            return redirect('ventas')
        if producto.stock_actual < nueva_cantidad:
            messages.error(request, f'Stock insuficiente para {producto.nombre}.')
            return redirect('ventas')
        carrito = get_cart(request)
        for item in carrito:
            if item['producto_id'] == int(producto_id):
                item['cantidad'] = nueva_cantidad
                break
        save_cart(request, carrito)
        messages.success(request, 'Cantidad editada correctamente en el carrito.')
    return redirect('ventas')

@require_POST
def finalizar_venta(request):
    try:
        carrito = get_cart(request)
        if not carrito or not isinstance(carrito, list) or not any(item.get('cantidad', 0) > 0 for item in carrito):
            clear_cart(request)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'El carrito está vacío.'
                })
            messages.error(request, 'El carrito está vacío.')
            return redirect('ventas')
        
        # Validación anticipada de stock
        productos_faltantes = []
        total_venta = Decimal('0.00')
        productos_validos = []
        for item in carrito:
            try:
                producto = get_producto_or_none(int(item['producto_id']))
            except Exception:
                producto = None
            if not producto:
                productos_faltantes.append(f"ID {item['producto_id']}")
            elif producto.stock_actual < item['cantidad']:
                productos_faltantes.append(producto.nombre)
            else:
                total_venta += producto.precio_unitario * item['cantidad']
                productos_validos.append((producto, item['cantidad']))
        
        if productos_faltantes or not productos_validos:
            clear_cart(request)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f"Stock insuficiente o producto no encontrado para: {', '.join(productos_faltantes)}."
                })
            messages.error(request, f"Stock insuficiente o producto no encontrado para: {', '.join(productos_faltantes)}.")
            return redirect('ventas')
        
        observaciones = request.POST.get('observaciones', '').strip() or '---'
        
        with transaction.atomic():
            usuario_id = request.session.get('usuario_id')
            if usuario_id:
                from usuario.models import Usuario
                usuario = Usuario.objects.get(id_usuario=usuario_id)
                venta = Venta.objects.create(
                    observaciones=observaciones,
                    total_venta=total_venta,
                    estado='COMPLETADA',
                    usuario=usuario
                )
            else:
                venta = Venta.objects.create(
                    observaciones=observaciones,
                    total_venta=total_venta,
                    estado='COMPLETADA',
                    usuario=None
                )
            venta.asignar_numero_venta()
            for producto, cantidad in productos_validos:
                precio_unitario = producto.precio_unitario
                subtotal = precio_unitario * cantidad
                DetalleVenta.objects.create(
                    venta=venta,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    subtotal=subtotal,
                    estado='ACTIVO'
                )
                producto.stock_actual -= cantidad
                producto.save()
        clear_cart(request)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Venta agregada correctamente.'
            })
        messages.success(request, 'Venta agregada correctamente.')
        return redirect('ventas')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'Error inesperado al finalizar la venta: {str(e)}'
            })
        messages.error(request, f'Error inesperado al finalizar la venta: {str(e)}')
        return redirect('ventas')

def agregar_venta(request):
    if request.method == 'POST':
        form = VentaForm(request.POST)
        if form.is_valid():
            producto = form.cleaned_data['producto']
            cantidad = form.cleaned_data['cantidad']
            observaciones = form.cleaned_data.get('observaciones', '')

            if producto.stock_actual < cantidad:
                return redirect('ventas')

            Venta.objects.create(
                id_producto=producto,
                cantidad=cantidad,
                observaciones=observaciones,
            )
            producto.stock_actual -= cantidad
            producto.save()

            request.session['detalle_venta'] = {'producto_id': producto.id_producto, 'cantidad': cantidad}
            messages.success(request, "Venta agregada correctamente.")
        else:
            return redirect('ventas')

    return redirect('ventas')

def eliminar_venta(request, id):
    if request.method == 'POST':
        try:
            venta = get_object_or_404(Venta, id_venta=id)
            with transaction.atomic():
                # Devolver el stock de los productos antes de eliminar
                for detalle in venta.detalles.all():
                    producto = detalle.producto
                    producto.stock_actual += detalle.cantidad
                    producto.save()
                
                # Eliminar reembolsos asociados primero
                venta.reembolsos.all().delete()
                
                # NO eliminar los detalles de la venta físicamente
                # Los detalles se mantienen para poder restaurar la venta
                # Solo marcar la venta como eliminada
                
                # Usar soft delete en lugar de eliminación física
                venta.soft_delete()
                
                # Nota: No reorganizar números automáticamente para evitar conflictos
                # Los números se asignarán correctamente en la siguiente venta
            
            return JsonResponse({
                'success': True,
                'message': 'Venta eliminada correctamente.',
                'venta_id': id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al eliminar la venta: {str(e)}'
            })
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido.'
    })

def restaurar_venta(request, id):
    if request.method == 'POST':
        try:
            venta = get_object_or_404(Venta.all_objects, id_venta=id)
            with transaction.atomic():
                # Restaurar la venta
                venta.restore()
                
                # Restar el stock de los productos nuevamente
                for detalle in venta.detalles.all():
                    producto = detalle.producto
                    producto.stock_actual -= detalle.cantidad
                    producto.save()
                
            return JsonResponse({
                'success': True,
                'message': 'Venta restaurada correctamente.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al restaurar la venta: {str(e)}'
            })
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido.'
    })

def validar_producto(request):
    nombre_o_codigo = request.GET.get('producto', '').strip()
    producto = Producto.objects.filter(nombre__iexact=nombre_o_codigo).first()
    if not producto:
        codigo_obj = Codigo.objects.filter(codigo__iexact=nombre_o_codigo).first()
        if codigo_obj:
            producto = Producto.objects.filter(id_producto=codigo_obj.id_producto.id_producto).first()
    if producto:
        return JsonResponse({
            'existe': True, 
            'stock': producto.stock_actual,
            'stock_minimo': producto.stock_minimo if producto.stock_minimo is not None else None
        })
    return JsonResponse({'existe': False})

def editar_venta(request, id):
    venta = get_object_or_404(Venta, id_venta=id)
    
    # Actualizar el estado de la venta antes de mostrar la página
    venta.actualizar_estado()
    venta.refresh_from_db()
    
    # Obtener detalles y actualizar sus estados
    detalles = venta.detalles.select_related('producto').all()
    for detalle in detalles:
        detalle.actualizar_estado()
        detalle.refresh_from_db()
    
    if request.method == 'POST':
        with transaction.atomic():
            total_reembolso = Decimal('0.00')
            venta_modificada = False
            reembolso_items = []
            cambios_detallados = []
            
            print(f"DEBUG: Editando venta {id}")
            
            for detalle in detalles:
                nueva_cantidad_str = request.POST.get(f'cantidad_{detalle.id_detalle}', '0')
                nueva_cantidad = int(nueva_cantidad_str) if nueva_cantidad_str.isdigit() else 0
                cantidad_original = detalle.cantidad
                
                print(f"DEBUG: Detalle {detalle.id_detalle} - Original: {cantidad_original}, Nueva: {nueva_cantidad}")
                
                if nueva_cantidad < 0:
                    messages.error(request, 'La cantidad no puede ser negativa.')
                    return redirect('ventas')
                
                # Comparación más robusta
                if nueva_cantidad != cantidad_original:
                    print(f"DEBUG: Cambio detectado en detalle {detalle.id_detalle}")
                    venta_modificada = True
                    cantidad_reembolso = cantidad_original - nueva_cantidad
                    
                    if cantidad_reembolso > 0:  # Hay reembolso
                        print(f"DEBUG: Reembolso de {cantidad_reembolso} unidades")
                        # Actualizar stock
                        detalle.producto.stock_actual += cantidad_reembolso
                        detalle.producto.save()
                        # Calcular monto reembolsado
                        monto_reembolso = cantidad_reembolso * detalle.precio_unitario
                        total_reembolso += monto_reembolso
                        # Guardar para crear el registro de reembolso
                        reembolso_items.append({
                            'producto': detalle.producto,
                            'cantidad': cantidad_reembolso,
                            'monto': monto_reembolso
                        })
                        # Actualizar detalle
                        detalle.cantidad = nueva_cantidad
                        detalle.subtotal = nueva_cantidad * detalle.precio_unitario
                        detalle.estado = 'Parcialmente Reembolsado' if nueva_cantidad > 0 else 'Reembolsado'
                        detalle.save()
                        
                        cambios_detallados.append(f"Reembolso de {cantidad_reembolso} unidades de {detalle.producto.nombre}")
                        
                    elif nueva_cantidad > cantidad_original:  # Aumentar cantidad
                        diferencia_agregar = nueva_cantidad - cantidad_original
                        print(f"DEBUG: Aumento de {diferencia_agregar} unidades")
                        if detalle.producto.stock_actual < diferencia_agregar:
                            messages.error(request, f'Stock insuficiente para {detalle.producto.nombre}. Stock disponible: {detalle.producto.stock_actual}, necesitas: {diferencia_agregar}')
                            return redirect('ventas')
                        # Actualizar stock
                        detalle.producto.stock_actual -= diferencia_agregar
                        detalle.producto.save()
                        # Actualizar detalle
                        detalle.cantidad = nueva_cantidad
                        detalle.subtotal = nueva_cantidad * detalle.precio_unitario
                        detalle.estado = 'ACTIVO'
                        detalle.save()
                        
                        cambios_detallados.append(f"Agregadas {diferencia_agregar} unidades de {detalle.producto.nombre}")
            
            print(f"DEBUG: Venta modificada: {venta_modificada}")
            
            if venta_modificada:
                # Crear registro de reembolso si corresponde
                if reembolso_items:
                    usuario_id = request.session.get('usuario_id')
                    if usuario_id:
                        try:
                            usuario = Usuario.objects.get(id_usuario=usuario_id)
                        except Usuario.DoesNotExist:
                            usuario = None
                    else:
                        usuario = None
                        
                    reembolso = Reembolso.objects.create(
                        venta=venta,
                        usuario=usuario,
                        observaciones=request.POST.get('observaciones', ''),
                        total_devuelto=total_reembolso
                    )
                    
                    # Asignar automáticamente el número de reembolso
                    reembolso.asignar_numero_reembolso()
                    
                    for item in reembolso_items:
                        ReembolsoDetalle.objects.create(
                            reembolso=reembolso,
                            producto=item['producto'],
                            cantidad=item['cantidad'],
                            monto=item['monto']
                        )
                
                # Actualizar total de la venta
                venta.actualizar_total()
                
                # Actualizar estado de la venta usando el método del modelo
                venta.actualizar_estado()
                
                # Mensaje de éxito más detallado
                if total_reembolso > 0:
                    mensaje = f'Venta editada correctamente. Reembolso total: ${total_reembolso:.2f}'
                    if cambios_detallados:
                        mensaje += f' ({", ".join(cambios_detallados)})'
                    messages.success(request, mensaje)
                else:
                    mensaje = 'Venta editada correctamente.'
                    if cambios_detallados:
                        mensaje += f' ({", ".join(cambios_detallados)})'
                    messages.success(request, mensaje)
            else:
                messages.info(request, 'No se realizaron cambios en la venta.')
            return redirect('ventas')
    return render(request, 'venta/editar_venta.html', {
        'venta': venta,
        'detalles': detalles,
    })

@csrf_exempt
@require_POST
def editar_venta_ajax(request, id):
    import json
    venta = get_object_or_404(Venta, id_venta=id)
    try:
        data = json.loads(request.body)
        cantidades = data.get('cantidades', [])
        observaciones = data.get('observaciones', '')
        fecha = data.get('fecha', None)
        detalles = list(venta.detalles.select_related('producto').all())
        if len(cantidades) != len(detalles):
            return JsonResponse({'success': False, 'error': 'Cantidad de productos no coincide.'})
        # Validar stock
        for idx, detalle in enumerate(detalles):
            nueva_cantidad = int(cantidades[idx])
            producto = detalle.producto
            stock_disponible = producto.stock_actual + detalle.cantidad
            if nueva_cantidad > stock_disponible:
                return JsonResponse({'success': False, 'error': f'Stock insuficiente para {producto.nombre}.'})
        # Actualizar detalles y stock
        for idx, detalle in enumerate(detalles):
            nueva_cantidad = int(cantidades[idx])
            producto = detalle.producto
            producto.stock_actual += detalle.cantidad  # devolver stock anterior
            producto.stock_actual -= nueva_cantidad    # restar nuevo
            producto.save()
            detalle.cantidad = nueva_cantidad
            detalle.save()
        venta.observaciones = observaciones
        if fecha:
            venta.fecha = fecha
        venta.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_GET
def autocomplete_productos(request):
    query = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria')
    
    if not query:
        return JsonResponse({'results': []})
    
    # Primero buscar coincidencia exacta por nombre o código
    producto_exacto = Producto.objects.filter(
        Q(nombre__iexact=query) | 
        Q(codigo__codigo__iexact=query)
    ).first()
    
    if producto_exacto:
        # Si hay coincidencia exacta, retornar solo ese producto
        codigo = producto_exacto.codigo_set.first()
        return JsonResponse({
            'results': [{
                'id': producto_exacto.id_producto,
                'nombre': producto_exacto.nombre,
                'codigo': codigo.codigo if codigo else '',
                'precio_venta': float(producto_exacto.precio_unitario),
                'stock': producto_exacto.stock_actual,
                'categoria': producto_exacto.id_categoria.nombre if producto_exacto.id_categoria else None
            }]
        })
    
    # Si no hay coincidencia exacta, buscar coincidencias parciales
    productos = Producto.objects.filter(
        Q(nombre__icontains=query) | 
        Q(codigo__codigo__icontains=query)
    ).distinct()
    
    if categoria_id:
        productos = productos.filter(id_categoria_id=categoria_id)
    
    # Limitar a 10 resultados y ordenar por nombre
    productos = productos.order_by('nombre')[:10]
    
    results = []
    for p in productos:
        codigo = p.codigo_set.first()
        results.append({
            'id': p.id_producto,
            'nombre': p.nombre,
            'codigo': codigo.codigo if codigo else '',
            'precio_venta': float(p.precio_unitario),
            'stock': p.stock_actual,
            'categoria': p.id_categoria.nombre if p.id_categoria else None
        })
    
    return JsonResponse({'results': results})

def listar_reembolsos(request):
    reembolsos = Reembolso.objects.select_related('venta', 'usuario').prefetch_related('detalles__producto').order_by('-fecha_hora')
    # Filtros opcionales
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    venta_numero = request.GET.get('venta')
    
    if fecha_inicio:
        reembolsos = reembolsos.filter(fecha_hora__date__gte=fecha_inicio)
    if fecha_fin:
        reembolsos = reembolsos.filter(fecha_hora__date__lte=fecha_fin)
    if venta_numero and venta_numero not in ('', None, 'None'):
        try:
            venta_numero_int = int(venta_numero)
            reembolsos = reembolsos.filter(venta__numero_venta=venta_numero_int)
        except ValueError:
            pass
    
    total_reembolsado = reembolsos.aggregate(total=models.Sum('total_devuelto'))['total'] or 0
    
    return render(request, 'venta/lista_reembolsos.html', {
        'reembolsos': reembolsos,
        'total_reembolsado': total_reembolsado,
        'filtros': {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'venta_id': venta_numero,
        }
    })

def exportar_reembolsos_excel(request):
    # Obtener los mismos filtros que en listar_reembolsos
    reembolsos = Reembolso.objects.select_related('venta', 'usuario').prefetch_related('detalles__producto').order_by('-fecha_hora')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    venta_numero = request.GET.get('venta')
    
    if fecha_inicio:
        reembolsos = reembolsos.filter(fecha_hora__date__gte=fecha_inicio)
    if fecha_fin:
        reembolsos = reembolsos.filter(fecha_hora__date__lte=fecha_fin)
    if venta_numero and venta_numero not in ('', None, 'None'):
        try:
            venta_numero_int = int(venta_numero)
            reembolsos = reembolsos.filter(venta__numero_venta=venta_numero_int)
        except ValueError:
            pass

    # Crear el archivo Excel
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    # Formatos
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#D9E1F2',
        'border': 1
    })
    money_format = workbook.add_format({
        'num_format': '$#,##0',
        'border': 1
    })
    date_format = workbook.add_format({
        'num_format': 'yyyy-mm-dd hh:mm',
        'border': 1
    })
    border_format = workbook.add_format({'border': 1})

    # Escribir encabezados
    headers = ['Fecha', 'ID Venta', 'ID Reembolso', 'Productos', 'Cantidad', 'Total Devuelto', 'Usuario', 'Observaciones']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)

    # Escribir datos
    row = 1
    for reembolso in reembolsos:
        for detalle in reembolso.detalles.all():
            worksheet.write(row, 0, reembolso.fecha_hora, date_format)
            numero_venta = reembolso.venta.numero_venta if reembolso.venta.numero_venta else reembolso.venta.id_venta
            numero_reembolso = reembolso.numero_reembolso if reembolso.numero_reembolso else reembolso.id_reembolso
            worksheet.write(row, 1, numero_venta, border_format)
            worksheet.write(row, 2, numero_reembolso, border_format)
            worksheet.write(row, 3, detalle.producto.nombre, border_format)
            worksheet.write(row, 4, detalle.cantidad, border_format)
            worksheet.write(row, 5, float(detalle.monto), money_format)
            worksheet.write(row, 6, reembolso.usuario.username if reembolso.usuario else '', border_format)
            worksheet.write(row, 7, reembolso.observaciones or '', border_format)
            row += 1

    # Ajustar ancho de columnas
    worksheet.set_column('A:A', 20)
    worksheet.set_column('B:B', 10)
    worksheet.set_column('C:C', 12)
    worksheet.set_column('D:D', 30)
    worksheet.set_column('E:E', 10)
    worksheet.set_column('F:F', 15)
    worksheet.set_column('G:G', 15)
    worksheet.set_column('H:H', 40)

    # Escribir total
    total = reembolsos.aggregate(total=models.Sum('total_devuelto'))['total'] or 0
    worksheet.write(row, 4, 'Total:', header_format)
    worksheet.write(row, 5, float(total), money_format)

    workbook.close()
    output.seek(0)

    # Preparar la respuesta
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=reembolsos_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
    return response

def exportar_reembolsos_pdf(request):
    # Obtener los mismos filtros que en listar_reembolsos
    reembolsos = Reembolso.objects.select_related('venta', 'usuario').prefetch_related('detalles__producto').order_by('-fecha_hora')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    venta_numero = request.GET.get('venta')
    
    if fecha_inicio:
        reembolsos = reembolsos.filter(fecha_hora__date__gte=fecha_inicio)
    if fecha_fin:
        reembolsos = reembolsos.filter(fecha_hora__date__lte=fecha_fin)
    if venta_numero and venta_numero not in ('', None, 'None'):
        try:
            venta_numero_int = int(venta_numero)
            reembolsos = reembolsos.filter(venta__numero_venta=venta_numero_int)
        except ValueError:
            pass

    # Crear el PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Título
    elements.append(Paragraph("Reporte de Reembolsos", styles['Title']))
    elements.append(Paragraph(f"Generado el {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Paragraph("<br/><br/>", styles['Normal']))

    # Datos de la tabla
    data = [['Fecha', 'ID Venta', 'ID Reembolso', 'Producto', 'Cantidad', 'Total', 'Usuario', 'Observaciones']]
    for reembolso in reembolsos:
        for detalle in reembolso.detalles.all():
            data.append([
                reembolso.fecha_hora.strftime('%Y-%m-%d %H:%M'),
                str(reembolso.venta.numero_venta if reembolso.venta.numero_venta else reembolso.venta.id_venta),
                str(reembolso.numero_reembolso if reembolso.numero_reembolso else reembolso.id_reembolso),
                detalle.producto.nombre,
                str(detalle.cantidad),
                f"${detalle.monto:,.0f}",
                reembolso.usuario.username if reembolso.usuario else '',
                reembolso.observaciones or ''
            ])

    # Crear la tabla
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (3, 1), (4, -1), 'RIGHT'),
    ]))
    elements.append(table)

    # Total
    total = reembolsos.aggregate(total=models.Sum('total_devuelto'))['total'] or 0
    elements.append(Paragraph(f"<br/>Total Reembolsado: ${total:,.0f}", styles['Heading2']))

    # Generar PDF
    doc.build(elements)
    buffer.seek(0)

    # Preparar la respuesta
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=reembolsos_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
    return response

@require_POST
def eliminar_reembolso(request, id_reembolso):
    try:
        reembolso = get_object_or_404(Reembolso, id_reembolso=id_reembolso)
        
        with transaction.atomic():
            # Obtener la venta asociada
            venta = reembolso.venta
            
            # Asegurar que la venta tenga un número de venta asignado
            if not venta.numero_venta:
                venta.asignar_numero_venta()
            
            # Guardar datos del reembolso antes de eliminar para poder restaurarlo
            reembolso_data = {
                'id_reembolso': reembolso.id_reembolso,
                'numero_reembolso': reembolso.numero_reembolso,
                'fecha_hora': reembolso.fecha_hora.isoformat(),
                'total_devuelto': float(reembolso.total_devuelto),
                'observaciones': reembolso.observaciones,
                'venta_id': venta.id_venta,
                'usuario_id': reembolso.usuario.id_usuario if reembolso.usuario else None,
                'detalles': []
            }
            
            # Guardar detalles del reembolso
            for detalle_reembolso in reembolso.detalles.all():
                reembolso_data['detalles'].append({
                    'producto_id': detalle_reembolso.producto.id_producto,
                    'cantidad': detalle_reembolso.cantidad,
                    'monto': float(detalle_reembolso.monto)
                })
            
            # Devolver las cantidades reembolsadas a la venta original
            for detalle_reembolso in reembolso.detalles.all():
                producto = detalle_reembolso.producto
                cantidad_reembolsada = detalle_reembolso.cantidad
                
                # Buscar el detalle de venta correspondiente
                try:
                    detalle_venta = venta.detalles.get(producto=producto)
                    # Aumentar la cantidad en la venta original
                    detalle_venta.cantidad += cantidad_reembolsada
                    detalle_venta.subtotal = detalle_venta.cantidad * detalle_venta.precio_unitario
                    detalle_venta.save()
                    
                    # Actualizar el estado del detalle de venta
                    detalle_venta.actualizar_estado()
                    
                    # Reducir el stock (porque se devuelve a la venta)
                    producto.stock_actual -= cantidad_reembolsada
                    producto.save()
                    
                except DetalleVenta.DoesNotExist:
                    # Si no existe el detalle de venta, crear uno nuevo
                    DetalleVenta.objects.create(
                        venta=venta,
                        producto=producto,
                        cantidad=cantidad_reembolsada,
                        precio_unitario=producto.precio_unitario,
                        subtotal=cantidad_reembolsada * producto.precio_unitario
                    )
                    
                    # Reducir el stock
                    producto.stock_actual -= cantidad_reembolsada
                    producto.save()
            
            # Guardar el número de reembolso antes de eliminar
            numero_reembolso_mostrar = reembolso.numero_reembolso if reembolso.numero_reembolso else reembolso.id_reembolso
            
            # Eliminar el reembolso
            reembolso.delete()
            
            # Actualizar el total de la venta
            venta.actualizar_total()
            
            # Forzar la actualización del estado de la venta
            venta.actualizar_estado()
            
            # Recargar la venta para obtener el estado actualizado
            venta.refresh_from_db()
            
            # Guardar datos en sessionStorage para poder restaurar
            request.session['reembolso_eliminado'] = reembolso_data
            
            # Usar el número de venta actual en el mensaje
            numero_venta_mostrar = venta.numero_venta if venta.numero_venta else venta.id_venta
            
            return JsonResponse({
                'success': True,
                'message': f'Reembolso #{numero_reembolso_mostrar} cancelado correctamente. Las cantidades han sido devueltas a la venta #{numero_venta_mostrar}.',
                'reembolso_id': id_reembolso,
                'venta_estado': venta.estado,
                'venta_id': venta.id_venta
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al cancelar el reembolso: {str(e)}'
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido.'
    })

@require_POST
def restaurar_reembolso(request, id_reembolso):
    try:
        # Obtener datos del reembolso eliminado de la sesión
        reembolso_data = request.session.get('reembolso_eliminado')
        if not reembolso_data:
            return JsonResponse({
                'success': False,
                'message': 'No se encontraron datos del reembolso para restaurar.'
            })
        
        with transaction.atomic():
            # Obtener la venta
            venta = get_object_or_404(Venta, id_venta=reembolso_data['venta_id'])
            
            # Obtener el usuario
            usuario = None
            if reembolso_data['usuario_id']:
                usuario = get_object_or_404(Usuario, id_usuario=reembolso_data['usuario_id'])
            
            # Crear el reembolso
            reembolso = Reembolso.objects.create(
                numero_reembolso=reembolso_data['numero_reembolso'],
                fecha_hora=reembolso_data['fecha_hora'],
                total_devuelto=reembolso_data['total_devuelto'],
                observaciones=reembolso_data['observaciones'],
                venta=venta,
                usuario=usuario
            )
            
            # Crear los detalles del reembolso
            for detalle_data in reembolso_data['detalles']:
                producto = get_object_or_404(Producto, id_producto=detalle_data['producto_id'])
                ReembolsoDetalle.objects.create(
                    reembolso=reembolso,
                    producto=producto,
                    cantidad=detalle_data['cantidad'],
                    monto=detalle_data['monto']
                )
                
                # Buscar el detalle de venta correspondiente
                try:
                    detalle_venta = venta.detalles.get(producto=producto)
                    # Reducir la cantidad en la venta original
                    detalle_venta.cantidad -= detalle_data['cantidad']
                    detalle_venta.subtotal = detalle_venta.cantidad * detalle_venta.precio_unitario
                    detalle_venta.save()
                    
                    # Actualizar el estado del detalle de venta
                    detalle_venta.actualizar_estado()
                    
                    # Aumentar el stock (porque se quita de la venta)
                    producto.stock_actual += detalle_data['cantidad']
                    producto.save()
                    
                except DetalleVenta.DoesNotExist:
                    # Si no existe el detalle de venta, no hacer nada
                    pass
            
            # Actualizar el total de la venta
            venta.actualizar_total()
            
            # Forzar la actualización del estado de la venta
            venta.actualizar_estado()
            
            # Recargar la venta para obtener el estado actualizado
            venta.refresh_from_db()
            
            # Limpiar datos de la sesión
            del request.session['reembolso_eliminado']
            
            numero_reembolso_mostrar = reembolso.numero_reembolso if reembolso.numero_reembolso else reembolso.id_reembolso
            
            # Obtener datos del reembolso restaurado para actualizar la tabla
            reembolso_data = {
                'id_reembolso': reembolso.id_reembolso,
                'numero_reembolso': numero_reembolso_mostrar,
                'fecha_hora': reembolso.fecha_hora.strftime('%d/%m/%Y %H:%M'),
                'total_devuelto': float(reembolso.total_devuelto),
                'observaciones': reembolso.observaciones or '',
                'usuario_nombre': reembolso.usuario.nombre_usuario if reembolso.usuario else 'Sin usuario',
                'venta_id': venta.id_venta,
                'venta_numero': venta.numero_venta if venta.numero_venta else venta.id_venta,
                'detalles': []
            }
            
            # Obtener detalles del reembolso
            for detalle in reembolso.detalles.all():
                reembolso_data['detalles'].append({
                    'producto_nombre': detalle.producto.nombre,
                    'cantidad': detalle.cantidad,
                    'precio_unitario': float(detalle.producto.precio_unitario),
                    'monto': float(detalle.monto)
                })
            
            return JsonResponse({
                'success': True,
                'message': f'Reembolso #{numero_reembolso_mostrar} restaurado correctamente.',
                'reembolso_data': reembolso_data,
                'venta_estado': venta.estado
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al restaurar el reembolso: {str(e)}'
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido.'
    })

@require_GET
def obtener_estado_venta(request, id_venta):
    """Vista AJAX para obtener el estado actualizado de una venta y sus detalles"""
    try:
        venta = get_object_or_404(Venta, id_venta=id_venta)
        
        # Actualizar el estado de la venta
        venta.actualizar_estado()
        venta.refresh_from_db()
        
        # Obtener el estado actualizado de los detalles
        detalles_estado = []
        for detalle in venta.detalles.all():
            detalle.actualizar_estado()
            detalle.refresh_from_db()
            detalles_estado.append({
                'id_detalle': detalle.id_detalle,
                'estado': detalle.estado,
                'cantidad': detalle.cantidad,
                'subtotal': float(detalle.subtotal)
            })
        
        return JsonResponse({
            'success': True,
            'venta_estado': venta.estado,
            'total_venta': float(venta.total_venta),
            'detalles': detalles_estado
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener el estado de la venta: {str(e)}'
        })

def boleta_venta(request, id_venta):
    # Leer configuración desde la base de datos
    config = ConfiguracionBoleta.objects.first()
    FERRETERIA_NOMBRE = config.nombre if config else "Ferretería El Ingeniero"
    FERRETERIA_DIRECCION = config.direccion if config else "Av. Principal 123, Ciudad"
    FERRETERIA_FONO = config.fono if config else "Fono: +56 9 1234 5678"
    FERRETERIA_RUT = config.rut if config else "RUT: 12.345.678-9"
    LOGO_PATH = config.logo.path if config and config.logo else None

    venta = get_object_or_404(Venta, id_venta=id_venta)
    detalles = venta.detalles.select_related('producto').all()
    usuario = venta.usuario.nombre_usuario if venta.usuario else '—'
    observaciones = venta.observaciones or '—'
    fecha = venta.fecha.strftime('%d-%m-%Y') if hasattr(venta.fecha, 'strftime') else str(venta.fecha)
    numero_venta_mostrar = venta.numero_venta if venta.numero_venta else venta.id_venta
    nro_boleta = str(numero_venta_mostrar).zfill(6)

    correo = config.correo if config else ""
    sitio_web = config.sitio_web if config else ""
    mensaje_pie = config.mensaje_pie if config else "¡Gracias por su compra!"

    from io import BytesIO
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 40

    # Logo (si existe)
    if LOGO_PATH:
        try:
            from reportlab.lib.utils import ImageReader
            logo = ImageReader(LOGO_PATH)
            logo_width, logo_height = logo.getSize()
            max_logo_height = 50
            scale = max_logo_height / logo_height if logo_height > max_logo_height else 1
            display_width = logo_width * scale
            display_height = logo_height * scale
            x = (width - display_width) / 2
            p.drawImage(logo, x, y - display_height, width=display_width, height=display_height, mask='auto')
            y -= display_height + 25  # Más espacio después del logo
        except Exception as e:
            y -= 25

    # Encabezado
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width/2, y, FERRETERIA_NOMBRE)
    y -= 25
    p.setFont("Helvetica", 10)
    p.drawCentredString(width/2, y, FERRETERIA_DIRECCION)
    y -= 15
    p.drawCentredString(width/2, y, FERRETERIA_FONO)
    y -= 15
    p.drawCentredString(width/2, y, FERRETERIA_RUT)
    y -= 13
    if correo:
        p.drawCentredString(width/2, y, correo)
        y -= 13
    if sitio_web:
        p.drawCentredString(width/2, y, sitio_web)
        y -= 13
    y -= 10
    # Fecha y boleta
    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, y, f"Fecha: {fecha}")
    p.drawString(220, y, f"N° Boleta: {nro_boleta}")
    y -= 18
    # Vendedor solo si hay nombre
    if usuario and usuario != '—':
        p.setFont("Helvetica", 10)
        p.drawString(40, y, f"Vendedor: {usuario}")
        y -= 15
    # Tabla de productos
    p.setFont("Helvetica-Bold", 10)
    x_producto = 60
    x_cant = x_producto + 140
    x_unit = x_cant + 50
    x_subt = x_unit + 70
    p.drawString(x_producto, y, "Producto")
    p.drawString(x_cant, y, "Cant.")
    p.drawString(x_unit, y, "P.Unitario")
    p.drawString(x_subt, y, "Subtotal")
    y -= 12
    p.setFont("Helvetica", 10)
    p.line(40, y, 500, y)
    y -= 10
    total = 0
    for det in detalles:
        if det.cantidad == 0:
            continue
        if y < 80:
            p.showPage()
            y = height - 40
        p.drawString(x_producto, y, str(det.producto.nombre))
        p.drawRightString(x_cant + 40, y, str(det.cantidad))
        p.drawRightString(x_unit + 60, y, f"${det.precio_unitario:,.0f}")
        p.drawRightString(x_subt + 60, y, f"${det.subtotal:,.0f}")
        total += det.subtotal
        y -= 15
    y -= 10
    # Totales
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(width/2, y, "TOTAL A PAGAR")
    y -= 20
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width/2, y, f"${total:,.0f}")
    y -= 25
    p.setFont("Helvetica-Oblique", 9)
    p.setFillGray(0.4)
    p.drawCentredString(width/2, y, "IVA incluido en el precio")
    y -= 13
    p.drawCentredString(width/2, y, "Documento interno. No válido como boleta electrónica SII.")
    y -= 13
    if mensaje_pie:
        p.setFont("Helvetica", 10)
        p.setFillGray(0)
        p.drawCentredString(width/2, y, mensaje_pie)
    p.setFillGray(0)
    p.showPage()
    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=False, filename=f'boleta_venta_{numero_venta_mostrar}.pdf', content_type='application/pdf')




@require_http_methods(["GET", "POST"])
def configurar_boleta(request):
    config = ConfiguracionBoleta.objects.first()
    if request.method == "POST":
        nombre = request.POST.get("nombre", "Ferretería El Ingeniero")
        direccion = request.POST.get("direccion", "Av. Principal 123, Ciudad")
        fono = request.POST.get("fono", "Fono: +56 9 1234 5678")
        rut = request.POST.get("rut", "RUT: 12.345.678-9")
        correo = request.POST.get("correo", "")
        sitio_web = request.POST.get("sitio_web", "")
        mensaje_pie = request.POST.get("mensaje_pie", "¡Gracias por su compra!")
        logo = request.FILES.get("logo")
        if not config:
            config = ConfiguracionBoleta()
        config.nombre = nombre
        config.direccion = direccion
        config.fono = fono
        config.rut = rut
        config.correo = correo
        config.sitio_web = sitio_web
        config.mensaje_pie = mensaje_pie
        if logo:
            config.logo = logo
        config.save()
        return redirect(reverse('ventas'))
    nombre_usuario = request.session.get('usuario_nombre', 'Invitado')
    return render(request, 'venta/configurar_boleta.html', {
        "config": config,
        "nombre_usuario": nombre_usuario
    })

