class Transaccion:
    """
    Clase que registra cada operacion de compra, venta, dividendo o rendimiento
    incluyendo fecha, cantidad, precio en COP y comision cobrada por el broker.
    """

    def __init__(self, fecha: str, tipo_operacion: str, codigo_activo: str,
                 cantidad: float, precio_unitario_cop: float, comision_broker_cop: float = 0.0,
                 trm: float = 1.0, dividendo_unitario_cop: float = 0.0):
        self.fecha = fecha
        self.tipo_operacion = tipo_operacion.strip().upper()
        self.codigo_activo = codigo_activo.strip().upper()
        self.cantidad = float(cantidad)
        self.precio_unitario_cop = float(precio_unitario_cop)
        self.comision_broker_cop = float(comision_broker_cop)
        self.trm = float(trm)                                          # TRM histórica aplicada (1.0 = COP)
        self.dividendo_unitario_cop = float(dividendo_unitario_cop)    # Dividendo por acción en COP

    def toDict(self) -> dict:
        """Convierte la transaccion a diccionario para guardarla en el archivo JSON."""
        return {
            "fecha": self.fecha,
            "tipo_operacion": self.tipo_operacion,
            "codigo_activo": self.codigo_activo,
            "cantidad": self.cantidad,
            "precio_unitario_cop": self.precio_unitario_cop,
            "comision_broker_cop": self.comision_broker_cop,
            "trm": self.trm,
            "dividendo_unitario_cop": self.dividendo_unitario_cop,
            "total_neto_cop": self.obtenerTotalNetoCOP()
        }

    @classmethod
    def fromDict(cls, d: dict) -> "Transaccion":
        """Reconstruye la transaccion; compatible con archivos JSON previos sin trm/dividendo."""
        return cls(
            d["fecha"], d["tipo_operacion"], d["codigo_activo"],
            d["cantidad"], d["precio_unitario_cop"],
            d.get("comision_broker_cop", 0.0),
            d.get("trm", 1.0),
            d.get("dividendo_unitario_cop", 0.0)
        )

    def obtenerMontoBrutoCOP(self) -> float:
        """Calcula el valor bruto de la operacion (Cantidad * Precio Unitario en COP)."""
        return round(self.cantidad * self.precio_unitario_cop, 2)

    def obtenerTotalNetoCOP(self) -> float:
        """
        Calcula el flujo de dinero real en COP:
        - En COMPRA: suma la comision al valor pagado.
        - En VENTA o DIVIDENDO: resta la comision al dinero recibido.
        """
        bruto = self.obtenerMontoBrutoCOP()
        if self.tipo_operacion == "COMPRA":
            return round(bruto + self.comision_broker_cop, 2)
        return round(bruto - self.comision_broker_cop, 2)

