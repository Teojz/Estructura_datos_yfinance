from abc import ABC, abstractmethod  # Libreria de Python para definir clases abstractas
from datetime import datetime        # Libreria para calcular dias transcurridos desde la compra


class Activo(ABC):
    """
    Clase abstracta padre para cualquier activo del portafolio (Renta Variable o Renta Fija)
    con todos los calculos expresados en Pesos Colombianos (COP).
    """

    def __init__(self, codigo: str, nombre: str, tipo_renta: str, fecha_apertura: str, comision_cop: float = 0.0):
        self.codigo = codigo.strip().upper()          # Codigo o ticker del activo (ej. PFBCOLOM.CL)
        self.nombre = nombre                          # Nombre comercial del activo
        self.tipo_renta = tipo_renta                  # 'Renta Variable' o 'Renta Fija'
        self.fecha_apertura = fecha_apertura          # Fecha inicial de compra (YYYY-MM-DD)
        self.comision_total_cop = float(comision_cop) # Comisiones acumuladas cobradas por el broker en COP

    def calcularDiasTenencia(self) -> int:
        """Calcula cuantos dias lleva abierta la inversion desde la fecha de apertura hasta hoy."""
        try:
            fecha_ini = datetime.strptime(self.fecha_apertura, "%Y-%m-%d") # Convierte texto a fecha
            dias = (datetime.now() - fecha_ini).days                       # Resta hoy menos fecha inicial
            return max(dias, 1)                                            # Minimo 1 dia para evitar division por 0
        except Exception:
            return 365                                                     # Por defecto 365 dias si falla el formato

    @abstractmethod
    def calcularCapitalInvertidoCOP(self) -> float:
        """Retorna el dinero total invertido en COP incluyendo comisiones del broker."""
        pass

    @abstractmethod
    def calcularValorActualCOP(self) -> float:
        """Retorna el valor actual consolidado del activo en COP incluyendo dividendos o intereses."""
        pass

    def calcularGananciaNetaCOP(self) -> float:
        """Calcula en COP si el activo gano dinero (>0 se valorizo) o perdio (<0 se desvalorizo)."""
        return round(self.calcularValorActualCOP() - self.calcularCapitalInvertidoCOP(), 2)

    def calcularRentabilidadAcumulada(self) -> float:
        """
        Calcula el porcentaje de valorizacion o desvalorizacion acumulada:
        ((Valor Actual Total - Capital Invertido) / Capital Invertido) * 100
        """
        invertido = self.calcularCapitalInvertidoCOP()                     # Capital total desembolsado
        if invertido <= 0:
            return 0.0
        actual = self.calcularValorActualCOP()                             # Valor presente total en COP
        return round(((actual - invertido) / invertido) * 100.0, 2)        # Porcentaje acumulado

    def calcularRentabilidadEA(self) -> float:
        """
        Calcula la Rentabilidad Efectiva Anual (E.A. %) estilo informe Bancolombia:
        E.A. = ((Valor Actual / Capital Invertido) ^ (365 / dias_transcurridos) - 1) * 100
        """
        invertido = self.calcularCapitalInvertidoCOP()
        actual = self.calcularValorActualCOP()
        if invertido <= 0 or actual <= 0:
            return 0.0

        dias = self.calcularDiasTenencia()                                 # Dias de tenencia del activo
        razon = actual / invertido                                         # Factor de crecimiento
        exponente = min(365.0 / float(dias), 12.0)                         # Anualizacion sobre base de 365 dias
        ea = ((razon ** exponente) - 1.0) * 100.0                          # Formula de interes compuesto E.A.
        return round(ea, 2)