from src.activo import Activo


class Accion(Activo):
    """
    Clase que representa una Accion (Renta Variable) en Pesos Colombianos (COP).
    Controla inventario de acciones (compradas, vendidas y tenencia actual),
    costo promedio ponderado, ventas realizadas, dividendos y cotizacion de mercado (yfinance).
    """

    def __init__(self, codigo: str, nombre: str, fecha_apertura: str):
        super().__init__(codigo, nombre, "Renta Variable", fecha_apertura, 0.0)
        self.cant_comprada = 0               # Total historico de acciones compradas
        self.cant_vendida = 0                # Total historico de acciones vendidas
        self.cant_actual = 0                 # Cantidad de acciones vivas hoy en cartera
        self.costo_promedio_cop = 0.0        # Costo promedio ponderado por accion en COP
        self.capital_compras_cop = 0.0       # Total dinero historico destinado a comprar acciones en COP
        self.ventas_realizadas_cop = 0.0     # Total dinero en efectivo recibido por ventas en COP
        self.precio_mercado_cop = 0.0        # Precio actual en COP traido desde yfinance
        self.utilidad_por_accion_eps = 0.0   # EPS (Utilidad por Accion) en COP traido desde yfinance
        self.dividendos_recibidos_cop = 0.0  # Dividendos pagados por la empresa en COP

    def registrarCompra(self, cantidad: int, precio_cop: float, comision_cop: float = 0.0) -> None:
        """Registra una compra de acciones sumando al inventario y actualizando el costo promedio."""
        cant = int(cantidad)
        precio = float(precio_cop)
        comision = float(comision_cop)

        costo_nuevo = cant * precio
        costo_anterior = self.cant_actual * self.costo_promedio_cop
        nueva_tenencia = self.cant_actual + cant

        if nueva_tenencia > 0:
            self.costo_promedio_cop = round((costo_anterior + costo_nuevo) / nueva_tenencia, 2)

        self.cant_comprada += cant
        self.cant_actual = nueva_tenencia
        self.capital_compras_cop += costo_nuevo
        self.comision_total_cop += comision
        if self.precio_mercado_cop <= 0:
            self.precio_mercado_cop = precio

    def registrarVenta(self, cantidad: int, precio_cop: float, comision_cop: float = 0.0) -> bool:
        """
        Registra la venta de acciones validando que existan unidades suficientes en cartera.
        Al vender, la cantidad en cartera disminuye, reduciendo el capital vigente y el valor actual.
        """
        cant = int(cantidad)
        if cant <= 0 or cant > self.cant_actual:
            return False

        self.cant_vendida += cant
        self.cant_actual -= cant
        self.ventas_realizadas_cop += round(cant * float(precio_cop), 2)
        self.comision_total_cop += float(comision_cop)

        # Si se vendieron todas las unidades, el costo promedio se resetea para futuras compras
        if self.cant_actual == 0:
            self.costo_promedio_cop = 0.0

        return True

    def registrarDividendo(self, monto_cop: float) -> None:
        """Registra un pago de dividendos en Pesos Colombianos (COP)."""
        self.dividendos_recibidos_cop += round(float(monto_cop), 2)

    def actualizarDatosMercado(self, precio_cop: float, eps_cop: float) -> None:
        """Actualiza el precio actual de la accion y su EPS desde Yahoo Finance en COP."""
        self.precio_mercado_cop = round(float(precio_cop), 2)
        self.utilidad_por_accion_eps = round(float(eps_cop), 2)

    def calcularCapitalInvertidoCOP(self) -> float:
        """
        Capital invertido vigente en cartera (Costo de las acciones vivas en poder del inversor).
        - Si se compran acciones: Sube.
        - Si se venden acciones: Baja proporcionalmente.
        - Si se vendió todo (cant_actual == 0): Es 0.0 COP.
        """
        if self.cant_actual <= 0:
            return 0.0
        return round(self.cant_actual * self.costo_promedio_cop, 2)

    def calcularCapitalInvertidoHistoricoCOP(self) -> float:
        """Retorna el capital histórico total desembolsado en compras y comisiones."""
        return round(self.capital_compras_cop + self.comision_total_cop, 2)

    def calcularValorActualCOP(self) -> float:
        """
        Valor actual de mercado de las acciones que componen la cartera hoy:
        cant_actual * precio_mercado_cop.
        - Si se compran acciones o sube el precio: Sube.
        - Si se venden acciones: Baja.
        - Si se vendió el 100%: Es 0.0 COP.
        """
        if self.cant_actual <= 0:
            return 0.0
        return round(self.cant_actual * self.precio_mercado_cop, 2)

    def calcularGananciaNetaCOP(self) -> float:
        """
        Ganancia neta total generada por la acción (no realizada + realizada + dividendos - comisiones):
        (Valor acciones vigentes + Ventas realizadas + Dividendos) - (Compras históricas + Comisiones).
        """
        total_ingresos_y_valor = (
            self.calcularValorActualCOP()
            + self.ventas_realizadas_cop
            + self.dividendos_recibidos_cop
        )
        total_costos = self.calcularCapitalInvertidoHistoricoCOP()
        return round(total_ingresos_y_valor - total_costos, 2)

    def calcularRentabilidadAcumulada(self) -> float:
        """
        Rentabilidad porcentual histórica total considerando flujos, costos y valor vigente:
        (Ganancia Neta / Capital Histórico Total) * 100.
        """
        historico = self.calcularCapitalInvertidoHistoricoCOP()
        if historico <= 0:
            return 0.0
        ganancia = self.calcularGananciaNetaCOP()
        return round((ganancia / historico) * 100.0, 2)

    def calcularRentabilidadEA(self) -> float:
        """Rentabilidad Efectiva Anual (E.A. %) basada en la rentabilidad acumulada y días de tenencia."""
        historico = self.calcularCapitalInvertidoHistoricoCOP()
        if historico <= 0:
            return 0.0

        rent_acum = self.calcularRentabilidadAcumulada()
        factor = 1.0 + (rent_acum / 100.0)
        if factor <= 0:
            return -100.0

        dias = self.calcularDiasTenencia()
        exponente = min(365.0 / float(dias), 12.0)
        ea = ((factor ** exponente) - 1.0) * 100.0
        return round(ea, 2)

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
