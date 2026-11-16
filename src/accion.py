from src.activo import Activo  # Importa la clase base Activo creada por Carlos10marin


class Accion(Activo):
    """
    Clase que representa una Accion (Renta Variable) en Pesos Colombianos (COP).
    Controla acciones compradas, acciones vendidas, posicion actual, dividendos y EPS.
    """

    def __init__(self, codigo: str, nombre: str, fecha_apertura: str):
        super().__init__(codigo, nombre, "Renta Variable", fecha_apertura, 0.0)
        self.cant_comprada = 0               # Total historico de acciones compradas
        self.cant_vendida = 0                # Total historico de acciones vendidas
        self.cant_actual = 0                 # Cantidad de acciones que tengo hoy en cartera
        self.costo_promedio_cop = 0.0        # Costo promedio ponderado por accion en COP
        self.capital_compras_cop = 0.0       # Total dinero destinado a comprar acciones en COP
        self.ventas_realizadas_cop = 0.0     # Total dinero recibido por vender acciones en COP
        self.precio_mercado_cop = 0.0        # Precio actual en COP traido desde yfinance
        self.utilidad_por_accion_eps = 0.0   # EPS (Utilidad por Accion) en COP traido desde yfinance
        self.dividendos_recibidos_cop = 0.0  # Dividendos pagados por la empresa en COP

    def registrarCompra(self, cantidad: int, precio_cop: float, comision_cop: float = 0.0) -> None:
        """Registra una compra de acciones sumando al inventario y actualizando el costo promedio."""
        cant = int(cantidad)
        precio = float(precio_cop)
        comision = float(comision_cop)

        costo_nuevo = cant * precio                                        # Valor de las nuevas acciones
        costo_anterior = self.cant_actual * self.costo_promedio_cop        # Valor de las acciones previas
        nueva_tenencia = self.cant_actual + cant                           # Nuevo total de acciones en mano

        if nueva_tenencia > 0:
            self.costo_promedio_cop = round((costo_anterior + costo_nuevo) / nueva_tenencia, 2)

        self.cant_comprada += cant                                         # Aumenta contador de compradas
        self.cant_actual = nueva_tenencia                                  # Actualiza acciones actuales
        self.capital_compras_cop += costo_nuevo                            # Suma al capital invertido
        self.comision_total_cop += comision                                # Suma la comision del broker
        if self.precio_mercado_cop <= 0:
            self.precio_mercado_cop = precio                               # Precio inicial de referencia

    def registrarVenta(self, cantidad: int, precio_cop: float, comision_cop: float = 0.0) -> bool:
        """Registra la venta de acciones validando que existan unidades suficientes en cartera."""
        cant = int(cantidad)
        if cant <= 0 or cant > self.cant_actual:                           # No permite vender mas de lo que tiene
            return False

        self.cant_vendida += cant                                          # Aumenta contador de acciones vendidas
        self.cant_actual -= cant                                           # Descuenta de las acciones en tenencia
        self.ventas_realizadas_cop += (cant * float(precio_cop))           # Suma el dinero recibido por la venta
        self.comision_total_cop += float(comision_cop)                     # Suma la comision de salida del broker
        return True

    def registrarDividendo(self, monto_cop: float) -> None:
        """Registra un pago de dividendos en Pesos Colombianos (COP)."""
        self.dividendos_recibidos_cop += float(monto_cop)

    def actualizarDatosMercado(self, precio_cop: float, eps_cop: float) -> None:
        """Actualiza el precio actual de la accion y su EPS desde Yahoo Finance en COP."""
        self.precio_mercado_cop = round(float(precio_cop), 2)
        self.utilidad_por_accion_eps = round(float(eps_cop), 2)

    def calcularCapitalInvertidoCOP(self) -> float:
        """Capital total desembolsado = Compras acumuladas + Comisiones del broker en COP."""
        return round(self.capital_compras_cop + self.comision_total_cop, 2)

    def calcularValorActualCOP(self) -> float:
        """
        Valor Actual Total en COP:
        (Acciones en tenencia * Precio Hoy) + Dinero recibido por ventas + Dividendos cobrados
        """
        valor_en_tenencia = self.cant_actual * self.precio_mercado_cop
        return round(valor_en_tenencia + self.ventas_realizadas_cop + self.dividendos_recibidos_cop, 2)

    def toDict(self) -> dict:
        """Convierte el estado de la accion a diccionario para guardarlo en JSON."""
        return {
            "clase": "Accion",
            "codigo": self.codigo,
            "nombre": self.nombre,
            "fecha_apertura": self.fecha_apertura,
            "cant_comprada": self.cant_comprada,
            "cant_vendida": self.cant_vendida,
            "cant_actual": self.cant_actual,
            "costo_promedio_cop": self.costo_promedio_cop,
            "capital_compras_cop": self.capital_compras_cop,
            "ventas_realizadas_cop": self.ventas_realizadas_cop,
            "precio_mercado_cop": self.precio_mercado_cop,
            "utilidad_por_accion_eps": self.utilidad_por_accion_eps,
            "dividendos_recibidos_cop": self.dividendos_recibidos_cop,
            "comision_total_cop": self.comision_total_cop
        }

    @classmethod
    def fromDict(cls, d: dict):
        """Reconstruye una instancia de Accion desde el archivo JSON."""
        obj = cls(d["codigo"], d["nombre"], d["fecha_apertura"])
        obj.cant_comprada = int(d.get("cant_comprada", 0))
        obj.cant_vendida = int(d.get("cant_vendida", 0))
        obj.cant_actual = int(d.get("cant_actual", 0))
        obj.costo_promedio_cop = float(d.get("costo_promedio_cop", 0.0))
        obj.capital_compras_cop = float(d.get("capital_compras_cop", 0.0))
        obj.ventas_realizadas_cop = float(d.get("ventas_realizadas_cop", 0.0))
        obj.precio_mercado_cop = float(d.get("precio_mercado_cop", 0.0))
        obj.utilidad_por_accion_eps = float(d.get("utilidad_por_accion_eps", 0.0))
        obj.dividendos_recibidos_cop = float(d.get("dividendos_recibidos_cop", 0.0))
        obj.comision_total_cop = float(d.get("comision_total_cop", 0.0))
        return obj