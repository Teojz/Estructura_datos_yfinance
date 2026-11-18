"""
MÓDULO: renta_fija.py
PROYECTO: Sistema de Seguimiento y Valoración de Portafolio

Gestiona inversiones de renta fija:
- CDT
- Bonos
- TES

Incluye control de capital, intereses, cupones,
amortizaciones, comisiones y valoración contractual/mercado.
Compatible al 100% con el Diagrama de Clases UML y la interfaz contable.
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
        *args,
        tipo=None,
        subtipo=None,
        capital_invertido=None,
        valor_invertido_cop=None,
        tasa_ea=None,
        tasa_efectiva_anual=None,
        fecha_apertura=None,
        fecha_vencimiento=None,
        plazo_dias=None,
        comision_cop=0.0,
        valor_nominal=None,
        tasa_cupon_ea=None,
        frecuencia_cupon=2,
        precio_mercado_por_100=None,
        rendimientos_pagados_cop=None,
        **kwargs
    ):
        """
        Constructor adaptable: acepta tanto la signatura del Diagrama UML:
        (codigo, nombre, subtipo, fecha_apertura, valor_invertido_cop, tasa_ea, plazo_dias, fecha_vencimiento, comision_cop)
        como la signatura con argumentos por nombre (tipo, capital_invertido, ...).
        """
        # 1. Resolver argumentos posicionales en *args
        if len(args) > 0:
            # args[0] es tipo/subtipo
            if subtipo is None and tipo is None:
                subtipo = args[0]

            if len(args) > 1:
                segundo_arg = args[1]
                # Determinar si es orden UML: (subtipo, fecha_apertura, valor_invertido_cop, tasa_ea, plazo_dias, fecha_vencimiento, comision_cop)
                # O si es orden anterior: (tipo, capital_invertido, tasa_ea, fecha_apertura, fecha_vencimiento, comision_cop)
                if isinstance(segundo_arg, (str, date, datetime)) and not str(segundo_arg).replace(".", "").isdigit():
                    # Orden UML
                    fecha_apertura = segundo_arg
                    if len(args) > 2 and valor_invertido_cop is None:
                        valor_invertido_cop = args[2]
                    if len(args) > 3 and tasa_ea is None:
                        tasa_ea = args[3]
                    if len(args) > 4 and plazo_dias is None:
                        plazo_dias = args[4]
                    if len(args) > 5 and fecha_vencimiento is None:
                        fecha_vencimiento = args[5]
                    if len(args) > 6:
                        comision_cop = args[6]
                else:
                    # Orden anterior
                    capital_invertido = segundo_arg
                    if len(args) > 2 and tasa_ea is None:
                        tasa_ea = args[2]
                    if len(args) > 3 and fecha_apertura is None:
                        fecha_apertura = args[3]
                    if len(args) > 4 and fecha_vencimiento is None:
                        fecha_vencimiento = args[4]
                    if len(args) > 5:
                        comision_cop = args[5]

        # 2. Homogeneizar alias de parámetros
        tipo_final = (subtipo or tipo or "CDT").strip().upper()
        if tipo_final not in self.TIPOS_VALIDOS:
            raise ValueError(f"Tipo inválido: {tipo_final}. Debe ser CDT, BONO o TES.")

        monto_capital = valor_invertido_cop if valor_invertido_cop is not None else capital_invertido
        if monto_capital is None:
            monto_capital = 0.0

        tasa_final = tasa_efectiva_anual if tasa_efectiva_anual is not None else tasa_ea
        if tasa_final is None:
            tasa_final = 0.0

        self._validar_numero(monto_capital, "Capital invertido")
        self._validar_numero(comision_cop, "Comisión")

        if monto_capital <= 0:
            raise ValueError("El capital debe ser positivo.")
        if comision_cop < 0:
            raise ValueError("La comisión no puede ser negativa.")

        self._validar_tasa(tasa_final, "Tasa E.A.")

        if tasa_cupon_ea is not None:
            self._validar_tasa(tasa_cupon_ea, "Tasa del cupón")

        if frecuencia_cupon not in self.FRECUENCIAS_VALIDAS:
            raise ValueError("Frecuencia válida: 1, 2, 4 o 12.")

        apertura = self._convertir_fecha(fecha_apertura)
        vencimiento = self._convertir_fecha(fecha_vencimiento)

        if apertura > date.today():
            raise ValueError("La apertura no puede ser futura.")

        if vencimiento <= apertura:
            raise ValueError("El vencimiento debe ser posterior.")

        if valor_nominal is None:
            valor_nominal = monto_capital

        self._validar_numero(valor_nominal, "Valor nominal")

        if valor_nominal <= 0:
            raise ValueError("El valor nominal debe ser positivo.")

        if precio_mercado_por_100 is not None:
            self._validar_numero(precio_mercado_por_100, "Precio de mercado")
            if precio_mercado_por_100 <= 0:
                raise ValueError("Precio de mercado inválido.")

        # Calcular plazo en días si no se proporcionó
        dias_calculados = (vencimiento - apertura).days
        plazo_dias_final = int(plazo_dias) if plazo_dias is not None else dias_calculados

        super().__init__(
            codigo=codigo,
            nombre=nombre,
            tipo_renta="Renta Fija",
            fecha_apertura=fecha_apertura,
            comision_cop=comision_cop
        )

        # Atributos oficiales y alias conforme al diagrama UML
        self.tipo = tipo_final
        self.subtipo = tipo_final
        self.capital_invertido = float(monto_capital)
        self.valor_invertido_cop = float(monto_capital)
        self.tasa_ea = float(tasa_final)
        self.tasa_efectiva_anual = float(tasa_final)
        self.plazo_dias = plazo_dias_final
        self.fecha_vencimiento = fecha_vencimiento

        self.valor_nominal = float(valor_nominal)
        self.tasa_cupon_ea = (
            float(tasa_cupon_ea)
            if tasa_cupon_ea is not None
            else float(tasa_final)
        )

        self.frecuencia_cupon = frecuencia_cupon
        self.precio_mercado_por_100 = precio_mercado_por_100

        self.rendimientos_recibidos = float(rendimientos_pagados_cop or 0.0)
        self.abonos_capital = 0.0
        self.liquidaciones_capital = 0.0
        self.ventas_realizadas_cop = 0.0
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

        import math
        if not (numero >= 0 and not math.isinf(numero) and not math.isnan(numero)):
            raise ValueError(f"{nombre} debe ser finito y positivo.")

        return numero

    @staticmethod
    def _validar_tasa(valor, nombre):
        tasa = InstrumentoRentaFija._validar_numero(valor, nombre)
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
            return datetime.strptime(str(fecha).strip(), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            raise ValueError(f"Fecha inválida: {fecha}. Formato YYYY-MM-DD.")

    @staticmethod
    def _sumar_meses(fecha, meses):
        mes_total = fecha.month - 1 + meses
        anio = fecha.year + mes_total // 12
        mes = mes_total % 12 + 1
        dia = min(fecha.day, monthrange(anio, mes)[1])
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

        vencimiento = self._convertir_fecha(self.fecha_vencimiento)
        return max((vencimiento - fecha_corte).days, 0)

    def calcularDiasTenencia(self):
        return max(self.calcularDiasTranscurridos(), 1)

    def estaVencido(self, fecha_corte=None):
        if fecha_corte is None:
            fecha_corte = date.today()
        else:
            fecha_corte = self._convertir_fecha(fecha_corte)

        return fecha_corte >= self._convertir_fecha(self.fecha_vencimiento)

    # --------------------------------------------------
    # CAPITAL
    # --------------------------------------------------

    def calcularCapitalPendienteCOP(self):
        capital_amortizado = self.abonos_capital + getattr(self, "liquidaciones_capital", 0.0)
        return round(max(self.valor_nominal - capital_amortizado, 0.0), 2)

    def calcularCapitalInvertidoCOP(self):
        """
        Retorna el capital invertido vigente en cartera.
        Disminuye proporcionalmente con amortizaciones, abonos o liquidaciones.
        Si se liquida o vence totalmente, retorna 0.0 COP.
        """
        pendiente = self.calcularCapitalPendienteCOP()
        if self.valor_nominal <= 0 or pendiente <= 0:
            return 0.0
        factor = pendiente / self.valor_nominal
        return round(self.capital_invertido * factor, 2)

    def calcularCapitalInvertidoHistoricoCOP(self):
        """Retorna el capital total histórico desembolsado más comisiones en COP."""
        return round(self.capital_invertido + self.comision_total_cop, 2)

    # --------------------------------------------------
    # CALENDARIO DE CUPONES
    # --------------------------------------------------

    def obtenerCalendarioCupones(self):
        if self.tipo == "CDT":
            return []

        apertura = self._convertir_fecha(self.fecha_apertura)
        vencimiento = self._convertir_fecha(self.fecha_vencimiento)
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
        vencimiento = self._convertir_fecha(self.fecha_vencimiento)

        if fecha_corte < apertura:
            raise ValueError("Fecha anterior a la apertura.")

        fecha_calculo = min(fecha_corte, vencimiento)
        capital = self.calcularCapitalPendienteCOP()

        if capital <= 0:
            return 0.0

        # CDT: capitalización compuesta ACT/365
        if self.tipo == "CDT":
            dias = (fecha_calculo - apertura).days
            valor_futuro = capital * ((1 + self.tasa_ea) ** (dias / 365))
            return round(valor_futuro - capital, 2)

        # BONOS Y TES: interés corrido del cupón actual
        calendario = self.obtenerCalendarioCupones()
        inicio = apertura

        for fecha_texto in calendario:
            fin = self._convertir_fecha(fecha_texto)
            if fecha_calculo <= fin:
                dias_periodo = (fin - inicio).days
                dias_transcurridos = (fecha_calculo - inicio).days

                if dias_periodo <= 0:
                    return 0.0

                tasa_periodica = ((1 + self.tasa_cupon_ea) ** (1 / self.frecuencia_cupon)) - 1
                cupon = capital * tasa_periodica
                return round(cupon * dias_transcurridos / dias_periodo, 2)

            inicio = fin

        return 0.0

    def calcularInteresCausadoCOP(self, fecha_corte=None):
        """Intereses causados devengados a la fecha (conforme al Diagrama UML)."""
        return self.calcularInteresesGenerados(fecha_corte)

    def calcularInteresesPendientesCOP(self, fecha_corte=None):
        intereses = self.calcularInteresesGenerados(fecha_corte)
        if self.tipo == "CDT":
            return round(max(intereses - self.rendimientos_recibidos, 0), 2)
        return intereses

    # --------------------------------------------------
    # REGISTRO DE RENDIMIENTOS Y PAGOS
    # --------------------------------------------------

    def registrarRendimiento(self, valor, fecha=None, concepto="Interés"):
        """Registra el cobro de un rendimiento o cupón en COP."""
        valor = self._validar_numero(valor, "Rendimiento")
        if valor <= 0:
            raise ValueError("El rendimiento debe ser positivo.")

        venc = self._convertir_fecha(self.fecha_vencimiento)
        if fecha is None:
            fecha = min(date.today(), venc)
        else:
            fecha = self._convertir_fecha(fecha)

        if fecha < self._convertir_fecha(self.fecha_apertura):
            raise ValueError("Fecha anterior a la apertura.")
        if fecha > date.today():
            raise ValueError("No se admiten pagos futuros.")
        if fecha > venc:
            raise ValueError("Fecha posterior al vencimiento.")

        self.rendimientos_recibidos += valor

        self.historial_movimientos.append({
            "tipo": "RENDIMIENTO",
            "concepto": concepto,
            "fecha": fecha.isoformat(),
            "valor_cop": round(valor, 2)
        })

    def registrarPagoRendimiento(self, monto_cop: float, fecha=None) -> None:
        """Alias conforme al método del Diagrama de Clases UML."""
        self.registrarRendimiento(valor=monto_cop, fecha=fecha, concepto="Pago de Rendimiento")

    # --------------------------------------------------
    # ABONOS DE CAPITAL
    # --------------------------------------------------

    def registrarAbonoCapital(self, valor, fecha=None):
        valor = self._validar_numero(valor, "Abono de capital")
        if valor <= 0:
            raise ValueError("El abono debe ser positivo.")

        if self.tipo == "CDT":
            raise ValueError("Los CDT de este modelo no permiten amortizaciones parciales.")

        venc = self._convertir_fecha(self.fecha_vencimiento)
        if fecha is None:
            fecha = min(date.today(), venc)
        else:
            fecha = self._convertir_fecha(fecha)

        if fecha < self._convertir_fecha(self.fecha_apertura):
            raise ValueError("Fecha anterior a la apertura.")
        if fecha > date.today():
            raise ValueError("No se admiten abonos futuros.")
        if fecha > venc:
            raise ValueError("Fecha posterior al vencimiento.")

        if valor > self.calcularCapitalPendienteCOP():
            raise ValueError("El abono supera el capital pendiente.")

        self.abonos_capital += valor

        self.historial_movimientos.append({
            "tipo": "ABONO_CAPITAL",
            "fecha": fecha.isoformat(),
            "valor_cop": round(valor, 2)
        })

    def registrarVentaOLiquidacion(self, valor_venta_cop: float, comision_cop: float = 0.0, fecha=None) -> None:
        """
        Registra la venta anticipada o liquidación al vencimiento del título en COP.
        Reduce el capital pendiente a 0 y acredita el flujo de dinero recibido.
        """
        valor_venta = self._validar_numero(valor_venta_cop, "Valor de venta/liquidación")
        comision = self._validar_numero(comision_cop, "Comisión de venta")

        venc = self._convertir_fecha(self.fecha_vencimiento)
        if fecha is None:
            fecha = min(date.today(), venc)
        else:
            fecha = self._convertir_fecha(fecha)

        self.liquidaciones_capital = self.valor_nominal
        self.ventas_realizadas_cop = getattr(self, "ventas_realizadas_cop", 0.0) + valor_venta
        self.comision_total_cop += comision

        self.historial_movimientos.append({
            "tipo": "VENTA_LIQUIDACION",
            "fecha": fecha.isoformat(),
            "valor_cop": round(valor_venta, 2),
            "comision_cop": round(comision, 2)
        })

    # --------------------------------------------------
    # VALORACIÓN CONTRACTUAL Y DE MERCADO
    # --------------------------------------------------

    def calcularValorContractualCOP(self, fecha_corte=None):
        capital = self.calcularCapitalPendienteCOP()
        if capital <= 0:
            return 0.0
        intereses = self.calcularInteresesPendientesCOP(fecha_corte)
        return round(capital + intereses, 2)

    def actualizarPrecioMercado(self, precio_por_100):
        if self.tipo == "CDT":
            raise ValueError("El CDT utiliza valoración contractual.")

        precio = self._validar_numero(precio_por_100, "Precio de mercado")
        if precio <= 0:
            raise ValueError("Precio inválido.")

        self.precio_mercado_por_100 = precio

    def calcularValorMercadoCOP(self, fecha_corte=None):
        if self.tipo == "CDT":
            return self.calcularValorContractualCOP(fecha_corte)

        capital = self.calcularCapitalPendienteCOP()
        if capital <= 0:
            return 0.0

        if self.precio_mercado_por_100 is None:
            valor_titulo = capital
        else:
            valor_titulo = (capital * self.precio_mercado_por_100 / 100)

        interes_corrido = self.calcularInteresesGenerados(fecha_corte)
        return round(valor_titulo + interes_corrido, 2)

    def calcularValorActualCOP(self):
        if self.tipo == "CDT":
            return self.calcularValorContractualCOP()
        return self.calcularValorMercadoCOP()

    # --------------------------------------------------
    # RENTABILIDAD
    # --------------------------------------------------

    def calcularGananciaNetaCOP(self):
        """
        Ganancia neta total histórica generada por el instrumento de renta fija:
        (Valor actual en cartera + Rendimientos cobrados + Abonos/Ventas recibidas) - (Capital histórico + Comisiones).
        """
        total_generado = (
            self.calcularValorActualCOP()
            + self.rendimientos_recibidos
            + self.abonos_capital
            + getattr(self, "ventas_realizadas_cop", 0.0)
        )
        total_costos = self.calcularCapitalInvertidoHistoricoCOP()
        return round(total_generado - total_costos, 2)

    def calcularRentabilidadAcumulada(self):
        historico = self.calcularCapitalInvertidoHistoricoCOP()
        if historico <= 0:
            return 0.0
        ganancia = self.calcularGananciaNetaCOP()
        return round((ganancia / historico) * 100.0, 2)

    def calcularRentabilidadEA(self):
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

    # --------------------------------------------------
    # PROPIEDADES UML
    # --------------------------------------------------

    @property
    def rendimientos_pagados_cop(self):
        """Atributo conforme al Diagrama UML."""
        return self.rendimientos_recibidos

    @rendimientos_pagados_cop.setter
    def rendimientos_pagados_cop(self, valor):
        self.rendimientos_recibidos = self._validar_numero(valor, "Rendimientos pagados")

    # --------------------------------------------------
    # SERIALIZACIÓN Y PERSISTENCIA JSON
    # --------------------------------------------------

    def toDict(self):
        """Convierte el instrumento en un diccionario serializable a JSON con soporte UML."""
        return {
            "clase": "InstrumentoRentaFija",
            "codigo": self.codigo,
            "nombre": self.nombre,
            "tipo": self.tipo,
            "subtipo": self.subtipo,
            "tipo_renta": self.tipo_renta,
            "capital_invertido": self.capital_invertido,
            "valor_invertido_cop": self.valor_invertido_cop,
            "tasa_ea": self.tasa_ea,
            "tasa_efectiva_anual": self.tasa_efectiva_anual,
            "plazo_dias": self.plazo_dias,
            "fecha_apertura": self._convertir_fecha(self.fecha_apertura).isoformat(),
            "fecha_vencimiento": self._convertir_fecha(self.fecha_vencimiento).isoformat(),
            "comision_cop": self.comision_total_cop,
            "comision_total_cop": self.comision_total_cop,
            "valor_nominal": self.valor_nominal,
            "tasa_cupon_ea": self.tasa_cupon_ea,
            "frecuencia_cupon": self.frecuencia_cupon,
            "precio_mercado_por_100": self.precio_mercado_por_100,
            "rendimientos_recibidos": self.rendimientos_recibidos,
            "rendimientos_pagados_cop": self.rendimientos_recibidos,
            "abonos_capital": self.abonos_capital,
            "liquidaciones_capital": getattr(self, "liquidaciones_capital", 0.0),
            "ventas_realizadas_cop": getattr(self, "ventas_realizadas_cop", 0.0),
            "historial_movimientos": [m.copy() for m in self.historial_movimientos]
        }

    @classmethod
    def fromDict(cls, datos):
        """Reconstruye un instrumento de renta fija desde un diccionario JSON."""
        tipo_valor = datos.get("subtipo") or datos.get("tipo", "CDT")
        capital_valor = datos.get("valor_invertido_cop") if "valor_invertido_cop" in datos else datos.get("capital_invertido", 0.0)
        tasa_valor = datos.get("tasa_efectiva_anual") if "tasa_efectiva_anual" in datos else datos.get("tasa_ea", 0.0)

        instrumento = cls(
            codigo=datos["codigo"],
            nombre=datos["nombre"],
            tipo=tipo_valor,
            subtipo=tipo_valor,
            capital_invertido=capital_valor,
            valor_invertido_cop=capital_valor,
            tasa_ea=tasa_valor,
            tasa_efectiva_anual=tasa_valor,
            fecha_apertura=datos["fecha_apertura"],
            fecha_vencimiento=datos["fecha_vencimiento"],
            plazo_dias=datos.get("plazo_dias"),
            comision_cop=datos.get("comision_cop", datos.get("comision_total_cop", 0.0)),
            valor_nominal=datos.get("valor_nominal"),
            tasa_cupon_ea=datos.get("tasa_cupon_ea"),
            frecuencia_cupon=datos.get("frecuencia_cupon", 2),
            precio_mercado_por_100=datos.get("precio_mercado_por_100")
        )

        rend_val = datos.get("rendimientos_pagados_cop") if "rendimientos_pagados_cop" in datos else datos.get("rendimientos_recibidos", 0.0)
        instrumento.rendimientos_recibidos = cls._validar_numero(rend_val, "Rendimientos recibidos")
        instrumento.abonos_capital = cls._validar_numero(datos.get("abonos_capital", 0.0), "Abonos de capital")
        instrumento.liquidaciones_capital = cls._validar_numero(datos.get("liquidaciones_capital", 0.0), "Liquidaciones capital")
        instrumento.ventas_realizadas_cop = cls._validar_numero(datos.get("ventas_realizadas_cop", 0.0), "Ventas realizadas")
        instrumento.historial_movimientos = [m.copy() for m in datos.get("historial_movimientos", [])]

        return instrumento

    def obtenerInformacion(self):
        return {
            "codigo": self.codigo,
            "nombre": self.nombre,
            "tipo": self.tipo,
            "subtipo": self.subtipo,
            "tipo_renta": self.tipo_renta,
            "capital_invertido_cop": self.capital_invertido,
            "valor_nominal_cop": self.valor_nominal,
            "capital_pendiente_cop": self.calcularCapitalPendienteCOP(),
            "tasa_ea": self.tasa_ea * 100,
            "tasa_efectiva_anual": self.tasa_efectiva_anual * 100,
            "tasa_cupon_ea": self.tasa_cupon_ea * 100,
            "frecuencia_cupon": self.frecuencia_cupon,
            "plazo_dias": self.plazo_dias,
            "fecha_apertura": self.fecha_apertura,
            "fecha_vencimiento": self.fecha_vencimiento,
            "dias_transcurridos": self.calcularDiasTranscurridos(),
            "dias_restantes": self.calcularDiasRestantes(),
            "vencido": self.estaVencido(),
            "comisiones_cop": self.comision_total_cop,
            "intereses_generados_cop": self.calcularInteresesGenerados(),
            "intereses_pendientes_cop": self.calcularInteresesPendientesCOP(),
            "rendimientos_recibidos_cop": round(self.rendimientos_recibidos, 2),
            "rendimientos_pagados_cop": round(self.rendimientos_recibidos, 2),
            "abonos_capital_cop": round(self.abonos_capital, 2),
            "precio_mercado_por_100": self.precio_mercado_por_100,
            "valor_contractual_cop": self.calcularValorContractualCOP(),
            "valor_mercado_cop": self.calcularValorMercadoCOP(),
            "capital_total_desembolsado_cop": self.calcularCapitalInvertidoCOP(),
            "valor_actual_cop": self.calcularValorActualCOP(),
            "ganancia_neta_cop": self.calcularGananciaNetaCOP(),
            "rentabilidad_acumulada": self.calcularRentabilidadAcumulada(),
            "rentabilidad_ea": self.calcularRentabilidadEA(),
            "historial_movimientos": self.historial_movimientos.copy()
        }

    def __str__(self):
        return (
            f"{self.tipo} | {self.nombre} | "
            f"Capital: ${self.capital_invertido:,.2f} COP | "
            f"Valor actual: ${self.calcularValorActualCOP():,.2f} COP"
        )
