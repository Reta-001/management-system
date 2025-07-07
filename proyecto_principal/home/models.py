from django.db import models
from django.utils import timezone
from usuario.models import Usuario
from django.db.models import Max

# ---------------------- MODELOS DE PRODUCTOS Y CATEGORÍAS ----------------------

class CategoriaManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(eliminado=False)

class Categoria(models.Model):
    id_categoria = models.AutoField(primary_key = True)
    nombre = models.CharField(max_length = 100)
    descripcion = models.TextField(blank = True, null = True)
    eliminado = models.BooleanField(default=False)
    fecha_eliminacion = models.DateTimeField(null=True, blank=True)

    objects = CategoriaManager()
    all_objects = models.Manager()

    def __str__(self):
        return self.nombre

    def soft_delete(self):
        self.eliminado = True
        self.fecha_eliminacion = timezone.now()
        self.save()

    def restore(self):
        self.eliminado = False
        self.fecha_eliminacion = None
        self.save()


class ProductoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(eliminado=False)

class Producto(models.Model):
    id_producto = models.AutoField(primary_key=True)
    id_categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    marca = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)  
    stock_actual = models.IntegerField(default=0)  
    stock_minimo = models.IntegerField(null=True, blank=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_actualizacion = models.DateTimeField(null=True, blank=True)
    eliminado = models.BooleanField(default=False)
    fecha_eliminacion = models.DateTimeField(null=True, blank=True)

    objects = ProductoManager()
    all_objects = models.Manager()
    
    def __str__(self):
        return f"{self.nombre} ({self.marca})"

    def soft_delete(self):
        # Verificar si el producto tiene ventas o compras asociadas
        ventas_asociadas = DetalleVenta.objects.filter(producto=self).exists()
        compras_asociadas = DetalleCompra.objects.filter(producto=self).exists()
        
        if ventas_asociadas or compras_asociadas:
            raise ValueError("No se puede eliminar el producto porque está asociado a ventas o compras.")
        
        self.eliminado = True
        self.fecha_eliminacion = timezone.now()
        self.save()

    def restore(self):
        self.eliminado = False
        self.fecha_eliminacion = None
        self.save()

# ---------------------- MODELOS DE VENTAS Y DETALLES ----------------------

class VentaManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(eliminado=False)

class Venta(models.Model):
    id_venta = models.AutoField(primary_key=True)
    numero_venta = models.IntegerField(unique=True, null=True, blank=True, help_text="Número consecutivo de venta para mostrar al usuario")
    fecha = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)
    total_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(
        max_length=30,
        choices=[
            ('COMPLETADA', 'Completada'),
            ('REEMBOLSADA', 'Reembolsada'),
            ('PARCIALMENTE_REEMBOLSADA', 'Parcialmente Reembolsada'),
            ('ANULADA', 'Anulada')
        ],
        default='COMPLETADA'
    )
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    eliminado = models.BooleanField(default=False)
    fecha_eliminacion = models.DateTimeField(null=True, blank=True)

    objects = VentaManager()
    all_objects = models.Manager()

    def __str__(self):
        return f"Venta {self.id_venta} - {self.fecha}"

    def save(self, *args, **kwargs):
        self.fecha_modificacion = timezone.now()
        super().save(*args, **kwargs)

    def actualizar_total(self):
        self.total_venta = sum(detalle.subtotal for detalle in self.detalles.all())
        self.save()

    def actualizar_estado(self):
        reembolsos = self.reembolsos.all()
        if not reembolsos.exists():
            self.estado = 'COMPLETADA'
        else:
            # Verificar si TODAS las cantidades de la venta son 0
            detalles_venta = self.detalles.all()
            todas_cantidades_cero = all(detalle.cantidad == 0 for detalle in detalles_venta)
            
            # Solo es REEMBOLSADA si TODAS las cantidades son 0
            if todas_cantidades_cero:
                self.estado = 'REEMBOLSADA'
            # Si hay reembolsos pero alguna cantidad no es 0
            elif any(reembolso.detalles.exists() for reembolso in reembolsos):
                self.estado = 'PARCIALMENTE_REEMBOLSADA'
            else:
                self.estado = 'COMPLETADA'
        self.save()
    
    def asignar_numero_venta(self):
        """Asigna automáticamente el siguiente número de venta disponible"""
        if not self.numero_venta:
            from django.db.models import Max
            
            # Buscar el siguiente número disponible de forma segura
            # Primero intentar con el máximo de ventas activas
            max_activo = Venta.objects.aggregate(Max('numero_venta'))['numero_venta__max'] or 0
            siguiente_numero = max_activo + 1
            
            # Verificar que no esté ocupado en todas las ventas
            while Venta.all_objects.filter(numero_venta=siguiente_numero).exists():
                siguiente_numero += 1
            
            self.numero_venta = siguiente_numero
            self.save()
    
    @classmethod
    def reorganizar_numeros_venta(cls):
        """Reorganiza todos los números de venta para que sean consecutivos"""
        ventas = cls.objects.filter(numero_venta__isnull=False).order_by('fecha', 'id_venta')
        for i, venta in enumerate(ventas, 1):
            if venta.numero_venta != i:
                venta.numero_venta = i
                venta.save()
    
    @classmethod
    def asignar_numeros_faltantes(cls):
        """Asigna números de venta a todas las ventas que no los tengan"""
        ventas_sin_numero = cls.objects.filter(numero_venta__isnull=True).order_by('fecha', 'id_venta')
        ultimo_numero = cls.objects.filter(numero_venta__isnull=False).aggregate(
            models.Max('numero_venta')
        )['numero_venta__max'] or 0
        
        for venta in ventas_sin_numero:
            ultimo_numero += 1
            venta.numero_venta = ultimo_numero
            venta.save()

    def soft_delete(self):
        self.eliminado = True
        self.fecha_eliminacion = timezone.now()
        self.save()

    def restore(self):
        self.eliminado = False
        self.fecha_eliminacion = None
        self.save()


class DetalleVenta(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_creacion = models.DateTimeField(null=True, blank=True)
    fecha_modificacion = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(
        max_length=30,
        choices=[
            ('ACTIVO', 'Activo'),
            ('REEMBOLSADO', 'Reembolsado'),
            ('PARCIALMENTE_REEMBOLSADO', 'Reembolsado Parcialmente')
        ],
        default='ACTIVO'
    )

    def __str__(self):
        numero_venta = self.venta.numero_venta if self.venta.numero_venta else self.venta.id_venta
        return f"Detalle {self.id_detalle} - Venta {numero_venta} - {self.producto.nombre}"

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        if not self.fecha_creacion:
            self.fecha_creacion = timezone.now()
        self.fecha_modificacion = timezone.now()
        super().save(*args, **kwargs)
        self.venta.actualizar_total()

    def actualizar_estado(self):
        reembolsos = ReembolsoDetalle.objects.filter(
            reembolso__venta=self.venta,
            producto=self.producto
        )
        if not reembolsos.exists():
            self.estado = 'ACTIVO'
        else:
            total_reembolsado = sum(reembolso.cantidad for reembolso in reembolsos)
            
            # Si se reembolsó toda la cantidad actual (queda 0)
            if self.cantidad == 0 and total_reembolsado > 0:
                self.estado = 'REEMBOLSADO'
            # Si se reembolsó parte (queda algo pero no todo)
            elif total_reembolsado > 0 and self.cantidad > 0:
                self.estado = 'PARCIALMENTE_REEMBOLSADO'
            else:
                self.estado = 'ACTIVO'
        self.save()

# ---------------------- MODELOS DE REEMBOLSOS ----------------------

class Reembolso(models.Model):
    id_reembolso = models.AutoField(primary_key=True)
    numero_reembolso = models.IntegerField(unique=True, null=True, blank=True, help_text="Número consecutivo de reembolso para mostrar al usuario")
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='reembolsos')
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True, null=True)
    total_devuelto = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def es_reembolso_total(self):
        venta_original = self.venta
        productos_originales = set(venta_original.detalles.values_list('producto_id', flat=True))
        productos_reembolsados = set(self.detalles.values_list('producto_id', flat=True))
        return productos_originales == productos_reembolsados

    def asignar_numero_reembolso(self):
        """Asigna automáticamente el siguiente número de reembolso disponible"""
        if not self.numero_reembolso:
            ultimo_reembolso = Reembolso.objects.filter(numero_reembolso__isnull=False).order_by('-numero_reembolso').first()
            if ultimo_reembolso:
                self.numero_reembolso = ultimo_reembolso.numero_reembolso + 1
            else:
                self.numero_reembolso = 1
            self.save()
    
    @classmethod
    def reorganizar_numeros_reembolso(cls):
        """Reorganiza todos los números de reembolso para que sean consecutivos"""
        reembolsos = cls.objects.filter(numero_reembolso__isnull=False).order_by('fecha_hora', 'id_reembolso')
        for i, reembolso in enumerate(reembolsos, 1):
            if reembolso.numero_reembolso != i:
                reembolso.numero_reembolso = i
                reembolso.save()
    
    @classmethod
    def asignar_numeros_faltantes(cls):
        """Asigna números de reembolso a todos los reembolsos que no los tengan"""
        reembolsos_sin_numero = cls.objects.filter(numero_reembolso__isnull=True).order_by('fecha_hora', 'id_reembolso')
        ultimo_numero = cls.objects.filter(numero_reembolso__isnull=False).aggregate(
            models.Max('numero_reembolso')
        )['numero_reembolso__max'] or 0
        
        for reembolso in reembolsos_sin_numero:
            ultimo_numero += 1
            reembolso.numero_reembolso = ultimo_numero
            reembolso.save()

    def __str__(self):
        numero_venta = self.venta.numero_venta if self.venta.numero_venta else self.venta.id_venta
        numero_reembolso_mostrar = self.numero_reembolso if self.numero_reembolso else self.id_reembolso
        return f"Reembolso {numero_reembolso_mostrar} de Venta {numero_venta}"


class ReembolsoDetalle(models.Model):
    reembolso = models.ForeignKey(Reembolso, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} (Reembolso {self.reembolso.id_reembolso})"

# ---------------------- MODELOS DE CONFIGURACIÓN ----------------------

class ConfiguracionBoleta(models.Model):
    nombre = models.CharField(max_length=100, default="Ferretería El Ingeniero")
    direccion = models.CharField(max_length=200, default="Av. Principal 123, Ciudad")
    fono = models.CharField(max_length=50, default="Fono: +56 9 1234 5678")
    rut = models.CharField(max_length=20, default="RUT: 12.345.678-9")
    logo = models.ImageField(upload_to='boleta_logos/', null=True, blank=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    correo = models.CharField(max_length=100, blank=True, default="")
    sitio_web = models.CharField(max_length=100, blank=True, default="")
    mensaje_pie = models.CharField(max_length=200, blank=True, default="¡Gracias por su compra!")

    def __str__(self):
        return f"Configuración Boleta ({self.nombre})"

# ---------------------- MODELOS DE CÓDIGOS, PROVEEDORES Y COMPRAS ----------------------

class Codigo(models.Model):
    id_codigo = models.AutoField(primary_key=True)
    id_producto = models.ForeignKey(Producto, on_delete = models.CASCADE)
    codigo = models.CharField(max_length=100)

    def __str__(self):
        return self.codigo


class ProveedoreManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(eliminado=False)


class Proveedore(models.Model):
    id_proveedor = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    correo = models.EmailField()
    telefono = models.CharField(max_length=20)
    direccion = models.CharField(max_length=200)
    pais = models.CharField(max_length=50)
    ciudad = models.CharField(max_length=50)
    comuna = models.CharField(max_length=50)
    eliminado = models.BooleanField(default=False)
    fecha_eliminacion = models.DateTimeField(null=True, blank=True)

    objects = ProveedoreManager()
    all_objects = models.Manager()

    def __str__(self):
        return self.nombre

    def soft_delete(self):
        # Verificar si el proveedor tiene compras asociadas
        compras_asociadas = Compra.objects.filter(proveedor=self).exists()
        
        if compras_asociadas:
            raise ValueError("No se puede eliminar el proveedor porque está asociado a compras.")
        
        self.eliminado = True
        self.fecha_eliminacion = timezone.now()
        self.save()

    def restore(self):
        self.eliminado = False
        self.fecha_eliminacion = None
        self.save()


class ProductoProveedore(models.Model):
    id_proveedor = models.ForeignKey(Proveedore, on_delete=models.CASCADE)
    id_producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    precio_proveedor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Precio al que vende este proveedor este producto")

    class Meta:
        unique_together = (('id_proveedor', 'id_producto'),)

    def __str__(self):
        return f"{self.id_producto.nombre} - {self.id_proveedor.nombre}"

# ---------------------- MODELOS DE COMPRAS Y DETALLES ----------------------

class CompraManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(eliminado=False)

class Compra(models.Model):
    id_compra = models.AutoField(primary_key=True)
    proveedor = models.ForeignKey(Proveedore, on_delete=models.SET_NULL, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(null=True, blank=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)
    total_compra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(
        max_length=30,
        choices=[
            ('PENDIENTE', 'Pendiente de entrega'),
            ('ENTREGADO', 'Entregado'),
            ('ANULADA', 'Anulada')
        ],
        default='PENDIENTE'
    )
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    eliminado = models.BooleanField(default=False)
    fecha_eliminacion = models.DateTimeField(null=True, blank=True)

    objects = CompraManager()
    all_objects = models.Manager()

    def __str__(self):
        return f"Compra {self.id_compra} - {self.fecha}"

    def save(self, *args, **kwargs):
        self.fecha_modificacion = timezone.now()
        super().save(*args, **kwargs)

    def actualizar_total(self):
        self.total_compra = sum(detalle.subtotal for detalle in self.detalles.all())
        self.save()

    def actualizar_estado(self):
        # Actualizar estado basado en si tiene fecha de entrega
        if self.fecha_entrega:
            self.estado = 'ENTREGADO'
        else:
            self.estado = 'PENDIENTE'
        self.save()

    def soft_delete(self):
        self.eliminado = True
        self.fecha_eliminacion = timezone.now()
        self.save()

    def restore(self):
        self.eliminado = False
        self.fecha_eliminacion = None
        self.save()


class DetalleCompraManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(eliminado=False)

class DetalleCompra(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField()
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_creacion = models.DateTimeField(null=True, blank=True)
    fecha_modificacion = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(
        max_length=30,
        choices=[
            ('ACTIVO', 'Activo'),
            ('REEMBOLSADO', 'Reembolsado'),
            ('PARCIALMENTE_REEMBOLSADO', 'Reembolsado Parcialmente')
        ],
        default='ACTIVO'
    )
    eliminado = models.BooleanField(default=False)
    fecha_eliminacion = models.DateTimeField(null=True, blank=True)

    objects = DetalleCompraManager()
    all_objects = models.Manager()

    def __str__(self):
        return f"Detalle {self.id_detalle} - Compra {self.compra.id_compra} - {self.producto.nombre}"

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_compra
        if not self.fecha_creacion:
            self.fecha_creacion = timezone.now()
        self.fecha_modificacion = timezone.now()
        super().save(*args, **kwargs)
        self.compra.actualizar_total()

    def actualizar_estado(self):
        # Como no se usan reembolsos en compras, el estado siempre será ACTIVO
        self.estado = 'ACTIVO'
        self.save()

    def soft_delete(self):
        self.eliminado = True
        self.fecha_eliminacion = timezone.now()
        self.save()

    def restore(self):
        self.eliminado = False
        self.fecha_eliminacion = None
        self.save()
