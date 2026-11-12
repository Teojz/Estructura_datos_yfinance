
"""
MÓDULO: renta_fija.py
PROYECTO: Sistema de Seguimiento y Valoración de Portafolio

Gestiona inversiones de renta fija:
- CDT
- Bonos
- TES

Incluye control de capital, intereses, cupones,
amortizaciones, comisiones y valoración.
"""

from datetime import datetime, date
from calendar import monthrange

from .activo import Activo


class InstrumentoRentaFija(Activo):

    TIPOS_VALIDOS = ("CDT", "BONO", "TES")
    FRECUENCIAS_VALIDAS = (1, 2, 4, 12)

    def __init__(
        self,
        codigo,
        nombre,
        tipo,
        capital_invertido,
        tasa_ea,
        fecha_apertura,
        fecha_vencimiento,
        comision_cop=0.0,
        valor_nominal=None,
        tasa_cupon_ea=None,
        frecuencia_cupon=2,
        precio_mercado_por_100=None
    ):

        tipo = tipo.strip().upper()

        if tipo not in self.TIPOS_VALIDOS:
            raise ValueError("Tipo inválido: CDT, BONO o TES.")

        self._validar_numero(
            capital_invertido, "Capital invertido"
        )

        self._validar_numero(
            comision_cop, "Comisión"
        )

        if capital_invertido <= 0:
            raise ValueError("El capital debe ser positivo.")

        if comision_cop < 0:
            raise ValueError("La comisión no puede ser negativa.")

        self._validar_tasa(tasa_ea, "Tasa E.A.")

        if tasa_cupon_ea is not None:
            self._validar_tasa(
                tasa_cupon_ea, "Tasa del cupón"
            )

        if frecuencia_cupon not in self.FRECUENCIAS_VALIDAS:
            raise ValueError(
                "Frecuencia válida: 1, 2, 4 o 12."
            )

        apertura = self._convertir_fecha(fecha_apertura)
        vencimiento = self._convertir_fecha(fecha_vencimiento)

        if apertura > date.today():
            raise ValueError("La apertura no puede ser futura.")

        if vencimiento <= apertura:
            raise ValueError("El vencimiento debe ser posterior.")

        if valor_nominal is None:
            valor_nominal = capital_invertido

        self._validar_numero(valor_nominal, "Valor nominal")

        if valor_nominal <= 0:
            raise ValueError("El valor nominal debe ser positivo.")

        if precio_mercado_por_100 is not None:
            self._validar_numero(
                precio_mercado_por_100, "Precio de mercado"
            )

            if precio_mercado_por_100 <= 0:
                raise ValueError("Precio de mercado inválido.")

        super().__init__(
            codigo=codigo,
            nombre=nombre,
            tipo_renta="Renta Fija",
            fecha_apertura=fecha_apertura,
            comision_cop=comision_cop
        )

        self.tipo = tipo
        self.capital_invertido = float(capital_invertido)
        self.tasa_ea = float(tasa_ea)
        self.fecha_vencimiento = fecha_vencimiento

        self.valor_nominal = float(valor_nominal)

        self.tasa_cupon_ea = (
            float(tasa_cupon_ea)
            if tasa_cupon_ea is not None
            else float(tasa_ea)
        )

        self.frecuencia_cupon = frecuencia_cupon
        self.precio_mercado_por_100 = precio_mercado_por_100

        self.rendimientos_recibidos = 0.0
        self.abonos_capital = 0.0

        self.historial_movimientos = []

    # --------------------------------------------------
    # VALIDACIONES
    # --------------------------------------------------

    @staticmethod
    def _validar_numero(valor, nombre):

        try:
            numero = float(valor)
        except (TypeError, ValueError):
            raise ValueError(f"{nombre} debe ser numérico.")

        if not (numero >= 0 and numero < float("inf")):
            raise ValueError(f"{nombre} debe ser finito y positivo.")

        return numero

    @staticmethod
    def _validar_tasa(valor, nombre):

        tasa = InstrumentoRentaFija._validar_numero(
            valor, nombre
        )

        if tasa >= 10:
            raise ValueError("La tasa no puede superar 999%.")

        return tasa

    @staticmethod
    def _convertir_fecha(fecha):

        if isinstance(fecha, datetime):
            return fecha.date()

        if isinstance(fecha, date):
            return fecha

        try:
            return datetime.strptime(
                fecha, "%Y-%m-%d"
            ).date()

        except (ValueError, TypeError):
            raise ValueError("Fecha inválida. Formato YYYY-MM-DD.")

    @staticmethod
    def _sumar_meses(fecha, meses):

        mes_total = fecha.month - 1 + meses

        anio = fecha.year + mes_total // 12
        mes = mes_total % 12 + 1

        dia = min(
            fecha.day,
            monthrange(anio, mes)[1]
        )

        return date(anio, mes, dia)

    # --------------------------------------------------
    # FECHAS
    # --------------------------------------------------

    def calcularDiasTranscurridos(self, fecha_corte=None):

        if fecha_corte is None:
            fecha_corte = date.today()
        else:
            fecha_corte = self._convertir_fecha(fecha_corte)

        apertura = self._convertir_fecha(self.fecha_apertura)

        if fecha_corte < apertura:
            raise ValueError("Fecha de corte anterior a la apertura.")

        return (fecha_corte - apertura).days

    def calcularDiasRestantes(self, fecha_corte=None):

        if fecha_corte is None:
            fecha_corte = date.today()
        else:
            fecha_corte = self._convertir_fecha(fecha_corte)

        vencimiento = self._convertir_fecha(
            self.fecha_vencimiento
        )

        return max((vencimiento - fecha_corte).days, 0)

    def calcularDiasTenencia(self):

        return max(self.calcularDiasTranscurridos(), 1)

    def estaVencido(self, fecha_corte=None):

        if fecha_corte is None:
            fecha_corte = date.today()
        else:
            fecha_corte = self._convertir_fecha(fecha_corte)

        return fecha_corte >= self._convertir_fecha(
            self.fecha_vencimiento
        )

    # --------------------------------------------------
    # CAPITAL
    # --------------------------------------------------

    def calcularCapitalPendienteCOP(self):

        return round(
            max(self.valor_nominal - self.abonos_capital, 0),
            2
        )

    def calcularCapitalInvertidoCOP(self):

        return round(
            self.capital_invertido + self.comision_total_cop,
            2
        )

    # --------------------------------------------------
    # CALENDARIO DE CUPONES
    # --------------------------------------------------

    def obtenerCalendarioCupones(self):

        if self.tipo == "CDT":
            return []

        apertura = self._convertir_fecha(self.fecha_apertura)
        vencimiento = self._convertir_fecha(
            self.fecha_vencimiento
        )

        meses = 12 // self.frecuencia_cupon

        calendario = []
        fecha_actual = apertura

        while fecha_actual < vencimiento:

            siguiente = self._sumar_meses(fecha_actual, meses)

            if siguiente > vencimiento:
                siguiente = vencimiento

            calendario.append(siguiente.isoformat())
            fecha_actual = siguiente

        return calendario

    # --------------------------------------------------
    # INTERESES
    # --------------------------------------------------

    def calcularInteresesGenerados(self, fecha_corte=None):

        if fecha_corte is None:
            fecha_corte = date.today()
        else:
            fecha_corte = self._convertir_fecha(fecha_corte)

        apertura = self._convertir_fecha(self.fecha_apertura)
        vencimiento = self._convertir_fecha(
            self.fecha_vencimiento
        )

        if fecha_corte < apertura:
            raise ValueError("Fecha anterior a la apertura.")

        fecha_calculo = min(fecha_corte, vencimiento)

        capital = self.calcularCapitalPendienteCOP()

        if capital <= 0:
            return 0.0

        # CDT: capitalización compuesta ACT/365
        if self.tipo == "CDT":

            dias = (fecha_calculo - apertura).days

            valor_futuro = capital * (
                (1 + self.tasa_ea) ** (dias / 365)
            )

            return round(valor_futuro - capital, 2)

        # BONOS Y TES: interés corrido del cupón actual
        calendario = self.obtenerCalendarioCupones()

        inicio = apertura

        for fecha_texto in calendario:

            fin = self._convertir_fecha(fecha_texto)

            if fecha_calculo <= fin:

                dias_periodo = (fin - inicio).days

                dias_transcurridos = (
                    fecha_calculo - inicio
                ).days

                if dias_periodo <= 0:
                    return 0.0

                tasa_periodica = (
                    (1 + self.tasa_cupon_ea)
                    ** (1 / self.frecuencia_cupon)
                ) - 1

                cupon = capital * tasa_periodica

                return round(
                    cupon * dias_transcurridos / dias_periodo,
                    2
                )

            inicio = fin

        return 0.0

    def calcularInteresesPendientesCOP(self, fecha_corte=None):

        intereses = self.calcularInteresesGenerados(
            fecha_corte
        )

        if self.tipo == "CDT":

            return round(
                max(intereses - self.rendimientos_recibidos, 0),
                2
            )

        return intereses

    # --------------------------------------------------
    # REGISTRO DE RENDIMIENTOS
    # --------------------------------------------------

    def registrarRendimiento(
        self,
        valor,
        fecha=None,
        concepto="Interés"
    ):

        valor = self._validar_numero(valor, "Rendimiento")

        if valor <= 0:
            raise ValueError("El rendimiento debe ser positivo.")

        if fecha is None:
            fecha = date.today()
        else:
            fecha = self._convertir_fecha(fecha)

        if fecha < self._convertir_fecha(self.fecha_apertura):
            raise ValueError("Fecha anterior a la apertura.")

        if fecha > date.today():
            raise ValueError("No se admiten pagos futuros.")

        if fecha > self._convertir_fecha(self.fecha_vencimiento):
            raise ValueError("Fecha posterior al vencimiento.")

        self.rendimientos_recibidos += valor

        self.historial_movimientos.append({
            "tipo": "RENDIMIENTO",
            "concepto": concepto,
            "fecha": fecha.isoformat(),
            "valor_cop": round(valor, 2)
        })

    # --------------------------------------------------
    # ABONOS DE CAPITAL
    # --------------------------------------------------

    def registrarAbonoCapital(self, valor, fecha=None):

        valor = self._validar_numero(valor, "Abono de capital")

        if valor <= 0:
            raise ValueError("El abono debe ser positivo.")

        if self.tipo == "CDT":
            raise ValueError(
                "Los CDT de este modelo no permiten "
                "amortizaciones parciales."
            )

        if fecha is None:
            fecha = date.today()
        else:
            fecha = self._convertir_fecha(fecha)

        if fecha < self._convertir_fecha(self.fecha_apertura):
            raise ValueError("Fecha anterior a la apertura.")

        if fecha > date.today():
            raise ValueError("No se admiten abonos futuros.")

        if fecha > self._convertir_fecha(self.fecha_vencimiento):
            raise ValueError("Fecha posterior al vencimiento.")

        if valor > self.calcularCapitalPendienteCOP():
            raise ValueError("El abono supera el capital pendiente.")

        self.abonos_capital += valor

        self.historial_movimientos.append({
            "tipo": "ABONO_CAPITAL",
            "fecha": fecha.isoformat(),
            "valor_cop": round(valor, 2)
        })

    # --------------------------------------------------
    # VALORACIÓN CONTRACTUAL
    # --------------------------------------------------

    def calcularValorContractualCOP(self, fecha_corte=None):

        capital = self.calcularCapitalPendienteCOP()

        intereses = self.calcularInteresesPendientesCOP(
            fecha_corte
        )

        return round(
            capital
            + intereses
            + self.rendimientos_recibidos
            + self.abonos_capital,
            2
        )

    # --------------------------------------------------
    # VALORACIÓN DE MERCADO
    # --------------------------------------------------

    def actualizarPrecioMercado(self, precio_por_100):

        if self.tipo == "CDT":
            raise ValueError(
                "El CDT utiliza valoración contractual."
            )

        precio = self._validar_numero(
            precio_por_100, "Precio de mercado"
        )

        if precio <= 0:
            raise ValueError("Precio inválido.")

        self.precio_mercado_por_100 = precio

    def calcularValorMercadoCOP(self, fecha_corte=None):

        if self.tipo == "CDT":
            return self.calcularValorContractualCOP(
                fecha_corte
            )

        capital = self.calcularCapitalPendienteCOP()

        if self.precio_mercado_por_100 is None:
            valor_titulo = capital
        else:
            valor_titulo = (
                capital * self.precio_mercado_por_100 / 100
            )

        interes_corrido = self.calcularInteresesGenerados(
            fecha_corte
        )

        return round(
            valor_titulo
            + interes_corrido
            + self.rendimientos_recibidos
            + self.abonos_capital,
            2
        )

    # --------------------------------------------------
    # VALOR ACTUAL
    # --------------------------------------------------

    def calcularValorActualCOP(self):

        if self.tipo == "CDT":
            return self.calcularValorContractualCOP()

        return self.calcularValorMercadoCOP()

    # --------------------------------------------------
    # RENTABILIDAD
    # --------------------------------------------------

    def calcularGananciaNetaCOP(self):

        return round(
            self.calcularValorActualCOP()
            - self.calcularCapitalInvertidoCOP(),
            2
        )

    def calcularRentabilidadAcumulada(self):

        return super().calcularRentabilidadAcumulada()

    def calcularRentabilidadEA(self):

        return super().calcularRentabilidadEA()

    # --------------------------------------------------
    # INFORMACIÓN PARA EL DASHBOARD
    # --------------------------------------------------

    def obtenerInformacion(self):

        return {
            "codigo": self.codigo,
            "nombre": self.nombre,
            "tipo": self.tipo,
            "tipo_renta": self.tipo_renta,

            "capital_invertido_cop":
                self.capital_invertido,

            "valor_nominal_cop":
                self.valor_nominal,

            "capital_pendiente_cop":
                self.calcularCapitalPendienteCOP(),

            "tasa_ea":
                self.tasa_ea * 100,

            "tasa_cupon_ea":
                self.tasa_cupon_ea * 100,

            "frecuencia_cupon":
                self.frecuencia_cupon,

            "fecha_apertura":
                self.fecha_apertura,

            "fecha_vencimiento":
                self.fecha_vencimiento,

            "dias_transcurridos":
                self.calcularDiasTranscurridos(),

            "dias_restantes":
                self.calcularDiasRestantes(),

            "vencido":
                self.estaVencido(),

            "comisiones_cop":
                self.comision_total_cop,

            "intereses_generados_cop":
                self.calcularInteresesGenerados(),

            "intereses_pendientes_cop":
                self.calcularInteresesPendientesCOP(),

            "rendimientos_recibidos_cop":
                round(self.rendimientos_recibidos, 2),

            "abonos_capital_cop":
                round(self.abonos_capital, 2),

            "precio_mercado_por_100":
                self.precio_mercado_por_100,

            "valor_contractual_cop":
                self.calcularValorContractualCOP(),

            "valor_mercado_cop":
                self.calcularValorMercadoCOP(),

            "capital_total_desembolsado_cop":
                self.calcularCapitalInvertidoCOP(),

            "valor_actual_cop":
                self.calcularValorActualCOP(),

            "ganancia_neta_cop":
                self.calcularGananciaNetaCOP(),

            "rentabilidad_acumulada":
                self.calcularRentabilidadAcumulada(),

            "rentabilidad_ea":
                self.calcularRentabilidadEA(),

            "historial_movimientos":
                self.historial_movimientos.copy()
        }

    def __str__(self):

        return (
            f"{self.tipo} | {self.nombre} | "
            f"Capital: ${self.capital_invertido:,.2f} COP | "
            f"Valor actual: "
            f"${self.calcularValorActualCOP():,.2f} COP"
        )

