import json                                          # Libreria para guardar y cargar el portafolio en JSON
import os                                            # Libreria para verificar si existe el archivo de datos
from src.accion import Accion                        # Importa la clase de Renta Variable
from src.renta_fija import InstrumentoRentaFija      # Importa la clase de Renta Fija (CDT, Bonos, TES)
from src.transaccion import Transaccion              # Importa la clase de Transacciones
from src.servicio_mercado import ServicioMercado     # Importa el conector de yfinance


class Portafolio:
    """
    Clase controladora que administra todos los activos de Renta Fija y Renta Variable,
    actualiza precios desde yfinance y calcula la Rentabilidad Acumulada y Efectiva Anual (E.A.) en COP.
    """

    COMISION_ESTANDAR = 0.002   # 0,2 % sobre el valor bruto

    # Catálogo de instrumentos disponibles para seleccionar (no son posiciones ni movimientos)
    CATALOGO_RV = {
        "PFBCOLOM.CL": "Bancolombia Preferencial",
        "ECOPETROL.CL": "Ecopetrol S.A.",
        "AAPL": "Apple Inc. (USD -> COP)",
        "NKE": "Nike Inc. (USD -> COP)",
        "KO": "The Coca-Cola Company (USD -> COP)",
        "CIB": "Bancolombia ADR (NYSE)",
        "NVDA": "NVIDIA Corp. (USD -> COP)"
    }
    CATALOGO_RF = {
        "CDT-BANC-01": {"nombre": "CDT Digital Bancolombia 360 Dias", "subtipo": "CDT", "tasa_ea": 0.1125},
        "TES-COL-2028": {"nombre": "TES Tasa Fija Nación 2028", "subtipo": "TES", "tasa_ea": 0.104}
    }

    def __init__(self, nombre_fondo: str, servicio_mercado: ServicioMercado):
        self.nombre_fondo = nombre_fondo             # Nombre del portafolio o fondo (ej. FIC Bancolombia)
        self.servicio_mercado = servicio_mercado     # Referencia al servicio de Yahoo Finance
        self.activos = []                            # Lista polimorfica de objetos Activo (Accion / RentaFija)
        self.transacciones = []                      # Historial completo de compras, ventas y dividendos
        self.capital_inicial_cop = 0.0               # Valor total inicial del portafolio (caja inicial en COP)

    def buscarActivo(self, codigo: str):
        """Busca un activo dentro del portafolio por su ticker o codigo."""
        cod = codigo.strip().upper()                 # Estandariza el codigo a mayusculas
        for act in self.activos:                     # Recorre los activos registrados
            if act.codigo == cod:                    # Si coincide el codigo
                return act                           # Retorna la instancia del activo
        return None
    
    def listarCodigosDisponibles(self, categoria: str) -> list:
        """Códigos del portafolio + catálogo, sin duplicados (categoria: 'Renta Variable' o 'Renta Fija')."""
        if categoria == "Renta Variable":
            propios = [a.codigo for a in self.activos if isinstance(a, Accion)]
            catalogo = list(self.CATALOGO_RV.keys())
        else:
            propios = [a.codigo for a in self.activos if isinstance(a, InstrumentoRentaFija)]
            catalogo = list(self.CATALOGO_RF.keys())
        return propios + [c for c in catalogo if c not in propios]

    def obtenerInfoCatalogo(self, codigo: str):
        """Datos del catálogo para autocompletar el formulario (None si no existe)."""
        cod = codigo.strip().upper()
        if cod in self.CATALOGO_RV:
            return {"nombre": self.CATALOGO_RV[cod]}
        return self.CATALOGO_RF.get(cod)                                  # Retorna None si no existe aun

    def agregarActivo(self, activo) -> None:
        """Agrega un nuevo instrumento (Accion o Renta Fija) al portafolio."""
        if self.buscarActivo(activo.codigo) is None: # Evita duplicar el mismo codigo de activo
            self.activos.append(activo)              # Inserta el activo en la lista

    def registrarTransaccion(self, transaccion: Transaccion) -> None:
        """Guarda una operacion en el libro contable del portafolio."""
        self.transacciones.append(transaccion)       # Agrega la transaccion al historial

    def establecerCapitalInicial(self, valor_cop: float) -> None:
        """Define el capital inicial con el que arranca el flujo de caja del libro."""
        if float(valor_cop) <= 0:
            raise ValueError("El capital inicial debe ser positivo.")
        self.capital_inicial_cop = float(valor_cop)

    def _resolverTRM(self, codigo: str, fecha: str, trm: float = None) -> float:
        """1.0 para .CL; TRM explícita si se recibe; si no, TRM histórica exacta de la fecha."""
        if codigo.endswith(".CL"):
            return 1.0
        if trm is not None and float(trm) > 0:
            return float(trm)
        return float(self.servicio_mercado.obtenerTRMFechaExacta(fecha))

    def _resolverComision(self, bruto: float, comision_cop: float = None) -> float:
        """
        Comisión manual si se especifica; si no, 0,2 % del valor bruto.
        Igual que el Excel: Comision = (Valor COP * Compra + Valor COP * Venta) * 0,002
        (sin redondear, para que el saldo coincida al peso con la hoja de cálculo).
        """
        if comision_cop is None:
            return float(bruto) * self.COMISION_ESTANDAR
        return float(comision_cop)

    def _resolverPrecioCOP(self, precio_cop: float, precio_usd: float, trm_aplicada: float) -> float:
        """Valor COP = Valor US * TRM (si se ingresó el precio en USD); si no, el precio COP recibido."""
        if precio_usd is not None and float(precio_usd) > 0:
            return float(precio_usd) * float(trm_aplicada)
        if precio_cop is None or float(precio_cop) <= 0:
            raise ValueError("Debe indicar un precio positivo en COP o en USD.")
        return float(precio_cop)

    def accionesEnCartera(self, codigo: str, fecha: str = None) -> float:
        """
        Acciones en poder del inversor ANTES de la fecha indicada (columna 'Acciones' del Excel:
        D = D_anterior + Compra_anterior - Venta_anterior). Sin fecha, retorna la tenencia total.
        """
        cod = codigo.strip().upper()
        total = 0.0
        for t in self.transacciones:
            if t.codigo_activo != cod or (fecha is not None and t.fecha >= fecha):
                continue
            if t.tipo_operacion == "COMPRA":
                total += t.cantidad
            elif t.tipo_operacion == "VENTA":
                total -= t.cantidad
        return max(total, 0.0)

    def registrarCompraAccion(self, codigo: str, nombre: str, fecha: str, cantidad: int,
                              precio_cop: float = None, comision_cop: float = None,
                              trm: float = None, precio_usd: float = None) -> Accion:
        """
        Registra la compra de acciones y su asiento contable en transacciones.
        El precio puede llegar en COP (precio_cop) o en USD (precio_usd -> Valor COP = Valor US * TRM).
        """
        cod = codigo.strip().upper()
        activo = self.buscarActivo(cod)
        if activo is None:
            activo = Accion(cod, nombre, fecha)
            self.agregarActivo(activo)
        elif not isinstance(activo, Accion):
            raise ValueError(f"El activo {cod} ya existe y no es de tipo Accion.")

        trm_aplicada = self._resolverTRM(cod, fecha, trm)
        precio_cop = self._resolverPrecioCOP(precio_cop, precio_usd, trm_aplicada)
        comision = self._resolverComision(cantidad * precio_cop, comision_cop)

        activo.registrarCompra(cantidad, precio_cop, comision)
        transaccion = Transaccion(fecha, "COMPRA", cod, cantidad, precio_cop, comision, trm_aplicada)
        self.registrarTransaccion(transaccion)
        return activo

    def registrarVentaAccion(self, codigo: str, fecha: str, cantidad: int,
                             precio_cop: float = None, comision_cop: float = None,
                             trm: float = None, precio_usd: float = None) -> bool:
        """Registra la venta de acciones (precio en COP o en USD) y su asiento contable."""
        cod = codigo.strip().upper()
        activo = self.buscarActivo(cod)
        if activo is None or not isinstance(activo, Accion):
            raise ValueError(f"No existe la accion {cod} en el portafolio.")

        trm_aplicada = self._resolverTRM(cod, fecha, trm)
        precio_cop = self._resolverPrecioCOP(precio_cop, precio_usd, trm_aplicada)
        comision = self._resolverComision(cantidad * precio_cop, comision_cop)

        if not activo.registrarVenta(cantidad, precio_cop, comision):
            raise ValueError(f"No dispone de unidades suficientes de {cod} para vender {cantidad} acciones. Disponibles: {activo.cant_actual}")

        transaccion = Transaccion(fecha, "VENTA", cod, cantidad, precio_cop, comision, trm_aplicada)
        self.registrarTransaccion(transaccion)
        return True

    def registrarDividendoAccion(self, codigo: str, fecha: str, monto_cop: float = None,
                                 comision_cop: float = 0.0, trm: float = None,
                                 dividendo_unitario: float = None, moneda: str = "USD") -> float:
        """
        Registra el cobro de dividendos con la lógica del Excel:
          Dividendo COP = Dividendo (por acción, USD) * TRM
          Pago          = Dividendo COP * Acciones en cartera antes de la fecha
        - dividendo_unitario: dividendo por acción en USD (o en COP si moneda='COP' o el ticker es .CL).
        - monto_cop: alternativa legada (monto total en COP).
        En el Excel los dividendos no pagan comisión (solo compra/venta), por eso el valor por defecto es 0.
        Retorna el pago total en COP.
        """
        cod = codigo.strip().upper()
        activo = self.buscarActivo(cod)
        if activo is None or not isinstance(activo, Accion):
            raise ValueError(f"No existe la accion {cod} en el portafolio.")

        trm_aplicada = self._resolverTRM(cod, fecha, trm)
        acciones = self.accionesEnCartera(cod, fecha)
        if acciones <= 0:
            raise ValueError(f"No había acciones de {cod} en cartera antes del {fecha}: el dividendo sería 0.")

        if dividendo_unitario is not None and float(dividendo_unitario) > 0:
            en_cop = cod.endswith(".CL") or str(moneda).upper() == "COP"
            div_unitario = float(dividendo_unitario) * (1.0 if en_cop else trm_aplicada)
            monto_cop = div_unitario * acciones
        elif monto_cop is not None and float(monto_cop) > 0:
            monto_cop = float(monto_cop)
            div_unitario = monto_cop / acciones
        else:
            raise ValueError("Debe indicar el dividendo por acción o el monto total del dividendo.")

        comision = float(comision_cop or 0.0)
        activo.registrarDividendo(monto_cop)
        transaccion = Transaccion(fecha, "DIVIDENDO", cod, 1, monto_cop, comision,
                                  trm_aplicada, div_unitario)
        self.registrarTransaccion(transaccion)
        return monto_cop

    def registrarAperturaRentaFija(self, codigo: str, nombre: str, subtipo: str,
                                   fecha_apertura: str, capital_cop: float, tasa_ea: float,
                                   fecha_vencimiento: str, plazo_dias: int = None,
                                   comision_cop: float = 0.0, valor_nominal: float = None,
                                   tasa_cupon_ea: float = None, frecuencia_cupon: int = 2) -> InstrumentoRentaFija:
        """Registra la apertura de CDT o compra de Bonos/TES y su asiento contable."""
        cod = codigo.strip().upper()
        if self.buscarActivo(cod) is not None:
            raise ValueError(f"Ya existe un instrumento con el codigo {cod}.")

        instrumento = InstrumentoRentaFija(
            codigo=cod,
            nombre=nombre,
            subtipo=subtipo,
            tipo=subtipo,
            capital_invertido=capital_cop,
            valor_invertido_cop=capital_cop,
            tasa_ea=tasa_ea,
            tasa_efectiva_anual=tasa_ea,
            fecha_apertura=fecha_apertura,
            fecha_vencimiento=fecha_vencimiento,
            plazo_dias=plazo_dias,
            comision_cop=comision_cop,
            valor_nominal=valor_nominal,
            tasa_cupon_ea=tasa_cupon_ea,
            frecuencia_cupon=frecuencia_cupon
        )
        self.agregarActivo(instrumento)
        transaccion = Transaccion(fecha_apertura, "COMPRA", cod, 1, capital_cop, comision_cop)
        self.registrarTransaccion(transaccion)
        return instrumento

    def registrarRendimientoRentaFija(self, codigo: str, fecha: str, monto_cop: float,
                                      comision_cop: float = 0.0, concepto: str = "Cupón/Interés") -> None:
        """Registra el cobro de rendimiento de renta fija y su asiento contable."""
        cod = codigo.strip().upper()
        activo = self.buscarActivo(cod)
        if activo is None or not isinstance(activo, InstrumentoRentaFija):
            raise ValueError(f"No existe el instrumento de renta fija {cod}.")

        activo.registrarRendimiento(valor=monto_cop, fecha=fecha, concepto=concepto)
        transaccion = Transaccion(fecha, "RENDIMIENTO", cod, 1, monto_cop, comision_cop)
        self.registrarTransaccion(transaccion)

    def registrarAbonoCapitalRentaFija(self, codigo: str, fecha: str, monto_cop: float,
                                       comision_cop: float = 0.0) -> None:
        """Registra una amortizacion/abono de capital de renta fija y su asiento contable."""
        cod = codigo.strip().upper()
        activo = self.buscarActivo(cod)
        if activo is None or not isinstance(activo, InstrumentoRentaFija):
            raise ValueError(f"No existe el instrumento de renta fija {cod}.")

        activo.registrarAbonoCapital(valor=monto_cop, fecha=fecha)
        transaccion = Transaccion(fecha, "ABONO_CAPITAL", cod, 1, monto_cop, comision_cop)
        self.registrarTransaccion(transaccion)

    def registrarVentaRentaFija(self, codigo: str, fecha: str, valor_venta_cop: float,
                                comision_cop: float = 0.0) -> None:
        """Registra la liquidación o venta de un instrumento de renta fija y su asiento contable."""
        cod = codigo.strip().upper()
        activo = self.buscarActivo(cod)
        if activo is None or not isinstance(activo, InstrumentoRentaFija):
            raise ValueError(f"No existe el instrumento de renta fija {cod}.")

        activo.registrarVentaOLiquidacion(valor_venta_cop=valor_venta_cop, comision_cop=comision_cop, fecha=fecha)
        transaccion = Transaccion(fecha, "VENTA", cod, 1, valor_venta_cop, comision_cop)
        self.registrarTransaccion(transaccion)

    def actualizarValoracionMercado(self) -> None:
        """Recorre todas las acciones y actualiza su precio en COP y su EPS con yfinance."""
        try:
            self.servicio_mercado.obtenerTRM()       # Refresca primero la TRM del dolar en COP
        except Exception:
            pass

        for act in self.activos:                     # Itera sobre cada inversion
            if isinstance(act, Accion):              # Si el activo es una Accion (Renta Variable)
                try:
                    datos = self.servicio_mercado.consultarCotizacionYEPS(act.codigo) # Consulta yfinance
                    if datos.get("precio_cop", 0) > 0: # Si obtuvo un precio valido en COP
                        act.actualizarDatosMercado(datos["precio_cop"], datos.get("eps_cop", 0.0))
                except Exception:
                    pass

    def obtenerDistribucionRenta(self) -> dict:
        """Calcula cuanto dinero y que porcentaje esta en Renta Fija vs Renta Variable."""
        valor_rv = 0.0                               # Acumulador en COP para Renta Variable
        valor_rf = 0.0                               # Acumulador en COP para Renta Fija

        for act in self.activos:                     # Recorre los activos del portafolio
            val = act.calcularValorActualCOP()       # Valor actual del activo en COP
            if act.tipo_renta == "Renta Variable":   # Si es accion
                valor_rv += val                      # Suma a Renta Variable
            else:                                    # Si es CDT, Bono o TES
                valor_rf += val                      # Suma a Renta Fija

        total = valor_rv + valor_rf                  # Patrimonio total actual en COP
        porc_rv = round((valor_rv / total) * 100.0, 2) if total > 0 else 0.0 # % Renta Variable
        porc_rf = round((valor_rf / total) * 100.0, 2) if total > 0 else 0.0 # % Renta Fija

        return {
            "valor_renta_variable_cop": round(valor_rv, 2),
            "valor_renta_fija_cop": round(valor_rf, 2),
            "porcentaje_renta_variable": porc_rv,
            "porcentaje_renta_fija": porc_rf
        }

    def obtenerResumenConsolidadoCOP(self) -> dict:
        """
        Calcula los indicadores globales del portafolio en COP (estilo ficha técnica Bancolombia):
        Capital Invertido Vigente, Valor Actual en Cartera, Ganancia Neta Total, Rentabilidad Acumulada (%) y E.A. (%).
        Ofrece claves completas para cálculo contable y compatibilidad directa con GUI.
        """
        capital_vigente_total = 0.0                  # Total comprometido hoy en activos vivos
        capital_historico_total = 0.0                # Total histórico desembolsado en compras y comisiones
        valor_actual_total = 0.0                     # Valor de mercado/contractual actual de activos en cartera
        comisiones_totales = 0.0                     # Total comisiones cobradas por el bróker
        ventas_totales = 0.0                         # Total recaudado por ventas
        dividendos_totales = 0.0                     # Total dividendos de renta variable
        rendimientos_totales = 0.0                   # Total intereses/cupones pagados de renta fija
        abonos_capital_total = 0.0                   # Total abonos de capital / liquidaciones recibidas
        suma_dias_ponderada = 0.0                    # Para ponderar la antigüedad de la cartera

        valor_renta_variable = 0.0
        valor_renta_fija = 0.0

        for act in self.activos:
            inv_vigente = act.calcularCapitalInvertidoCOP()
            val_actual = act.calcularValorActualCOP()
            comisiones_totales += act.comision_total_cop
            dias_tenencia = act.calcularDiasTenencia()

            if hasattr(act, "calcularCapitalInvertidoHistoricoCOP"):
                inv_hist = act.calcularCapitalInvertidoHistoricoCOP()
            else:
                inv_hist = inv_vigente + act.comision_total_cop

            capital_vigente_total += inv_vigente
            capital_historico_total += inv_hist
            valor_actual_total += val_actual
            suma_dias_ponderada += inv_hist * dias_tenencia

            if isinstance(act, Accion) or act.tipo_renta == "Renta Variable":
                valor_renta_variable += val_actual
                dividendos_totales += getattr(act, "dividendos_recibidos_cop", 0.0)
                ventas_totales += getattr(act, "ventas_realizadas_cop", 0.0)
            elif isinstance(act, InstrumentoRentaFija) or act.tipo_renta == "Renta Fija":
                valor_renta_fija += val_actual
                rendimientos_totales += getattr(act, "rendimientos_recibidos", 0.0)
                abonos_capital_total += (getattr(act, "abonos_capital", 0.0) + getattr(act, "liquidaciones_capital", 0.0))
                ventas_totales += getattr(act, "ventas_realizadas_cop", 0.0)

        # Ganancia neta total histórica:
        # (Valor actual en cartera + Ventas realizadas + Dividendos + Rendimientos + Abonos) - Costos Históricos
        total_recursos_generados = (
            valor_actual_total
            + ventas_totales
            + dividendos_totales
            + rendimientos_totales
            + abonos_capital_total
        )
        ganancia_neta = total_recursos_generados - capital_historico_total
        rent_acum = ((ganancia_neta / capital_historico_total) * 100.0) if capital_historico_total > 0 else 0.0

        # Rentabilidad Efectiva Anual (E.A.) compuesta anualizada
        rent_ea = 0.0
        if capital_historico_total > 0:
            factor = 1.0 + (rent_acum / 100.0)
            if factor > 0:
                dias_prom = max(suma_dias_ponderada / capital_historico_total, 1.0)
                exponente = min(365.0 / dias_prom, 12.0)
                rent_ea = ((factor ** exponente) - 1.0) * 100.0

        total_patrimonio_cartera = valor_renta_variable + valor_renta_fija
        porc_rv = round((valor_renta_variable / total_patrimonio_cartera) * 100.0, 2) if total_patrimonio_cartera > 0 else 0.0
        porc_rf = round((valor_renta_fija / total_patrimonio_cartera) * 100.0, 2) if total_patrimonio_cartera > 0 else 0.0

        estado = "VALORIZADO" if ganancia_neta >= 0 else "DESVALORIZADO"

        return {
            # Claves estándar con sufijo COP
            "capital_invertido_cop": round(capital_vigente_total, 2),
            "capital_historico_cop": round(capital_historico_total, 2),
            "valor_actual_cop": round(valor_actual_total, 2),
            "ganancia_neta_cop": round(ganancia_neta, 2),
            "comisiones_totales_cop": round(comisiones_totales, 2),
            "ventas_realizadas_cop": round(ventas_totales, 2),
            "dividendos_cop": round(dividendos_totales, 2),
            "rendimientos_cop": round(rendimientos_totales, 2),
            "abonos_capital_cop": round(abonos_capital_total, 2),
            "rendimientos_y_dividendos_cop": round(dividendos_totales + rendimientos_totales, 2),
            "rentabilidad_acumulada_porc": round(rent_acum, 2),
            "rentabilidad_ea_porc": round(rent_ea, 2),
            "estado_valoracion": estado,
            "valor_renta_variable_cop": round(valor_renta_variable, 2),
            "valor_renta_fija_cop": round(valor_renta_fija, 2),
            "porcentaje_renta_variable": porc_rv,
            "porcentaje_renta_fija": porc_rf,

            # Claves compatibles con InterfazPortafolioGUI
            "capital_invertido": round(capital_vigente_total, 2),
            "valor_actual": round(valor_actual_total, 2),
            "ganancia": round(ganancia_neta, 2),
            "comisiones": round(comisiones_totales, 2),
            "rentabilidad": round(rent_acum, 2),
            "rentabilidad_ea": round(rent_ea, 2),
            "dividendos": round(dividendos_totales, 2),
            "rendimientos": round(rendimientos_totales, 2),
            "estado": estado,
            "renta_variable": round(valor_renta_variable, 2),
            "renta_fija": round(valor_renta_fija, 2),
            "porcentaje_rv": porc_rv,
            "porcentaje_rf": porc_rf
        }

    def guardarPortafolio(self, ruta: str = "data/portafolio_bancolombia.json") -> bool:
        """Serializa los activos y transacciones en un archivo JSON."""
        try:
            ruta_abs = os.path.abspath(ruta)
            directorio = os.path.dirname(ruta_abs)
            if directorio:
                os.makedirs(directorio, exist_ok=True)
            datos = {
                "nombre_fondo": self.nombre_fondo,
                "activos": [a.toDict() for a in self.activos],
                "transacciones": [t.toDict() for t in self.transacciones],
                "capital_inicial_cop": self.capital_inicial_cop,
            }
            with open(ruta_abs, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
            return True
        except Exception:
            return False

    def cargarPortafolio(self, ruta: str = "data/portafolio_bancolombia.json") -> bool:
        """Carga los activos y transacciones desde el archivo JSON."""
        ruta_abs = os.path.abspath(ruta)
        if not os.path.exists(ruta_abs):
            return False
        try:
            with open(ruta_abs, "r", encoding="utf-8") as f:
                datos = json.load(f)
            self.nombre_fondo = datos.get("nombre_fondo", self.nombre_fondo)
            self.capital_inicial_cop = float(datos.get("capital_inicial_cop", 0.0))
            self.activos.clear()
            self.transacciones.clear()

            for d in datos.get("activos", []):
                clase = d.get("clase")
                if clase == "Accion" or "cant_actual" in d or "costo_promedio_cop" in d:
                    self.activos.append(Accion.fromDict(d))
                elif clase == "InstrumentoRentaFija" or "tasa_ea" in d or "subtipo" in d or "tipo" in d:
                    self.activos.append(InstrumentoRentaFija.fromDict(d))

            for t in datos.get("transacciones", []):
                self.transacciones.append(Transaccion.fromDict(t))
                t["fecha"], t["tipo_operacion"], t["codigo_activo"],
                t["cantidad"], t["precio_unitario_cop"], t.get("comision_broker_cop", 0.0)
            return True
        except Exception:
            return False

    def completarTRMHistoricas(self) -> int:
        """Rellena la TRM de transacciones antiguas de acciones internacionales (trm == 1.0)."""
        cache = self.servicio_mercado.__dict__.setdefault("_cache_trm_fecha", {})
        actualizadas = 0
        for t in self.transacciones:
            act = self.buscarActivo(t.codigo_activo)
            if not isinstance(act, Accion) or t.codigo_activo.endswith(".CL") or t.trm != 1.0:
                continue
            valor = self.servicio_mercado.obtenerTRMFechaExacta(t.fecha)
            if t.fecha in cache:               # Solo si fue una TRM real consultada
                t.trm = valor
                actualizadas += 1
        return actualizadas

    # Prioridad dentro del mismo día: los dividendos/rendimientos se liquidan sobre las
    # acciones que había ANTES de las compras/ventas de ese día (igual que la fila del Excel,
    # donde 'Acciones' = acciones previas y la compra del día se suma en la fila siguiente).
    _ORDEN_MISMO_DIA = {"DIVIDENDO": 0, "RENDIMIENTO": 0}

    def obtenerLibroTransaccionesDetallado(self, codigo_activo: str = "TODOS") -> list:
        """
        Libro de operaciones con el mismo formato y fórmulas del Excel 'Prueba portafolio.xlsx':

        Fecha | Acciones | Valor US | Valor COP | Compra | Venta | TRM | Dividendo |
        Dividendo cop | Pago | Comision | Saldo | Variacion | Total

          Acciones      = Acciones_ant + Compra_ant - Venta_ant      (tenencia ANTES de la fila)
          Valor COP     = Valor US * TRM
          Dividendo cop = Dividendo (USD por acción) * TRM
          Pago          = Dividendo cop * Acciones
          Comision      = (Valor COP * Compra + Valor COP * Venta) * 0,002
          Saldo         = Saldo_ant - Valor COP * Compra + Valor COP * Venta + Dividendo cop * Acciones - Comision
                          (la primera fila parte del capital inicial, celda N5 del Excel)
          Variacion     = Saldo - Saldo_ant
          Total         = Saldo + valor de las posiciones vivas (acciones * último Valor COP
                          de cada activo + capital vigente de renta fija)

        Los valores se devuelven SIN redondear (como Excel); la interfaz los formatea.
        """
        filtro = (codigo_activo or "TODOS").strip().upper()
        transacciones = list(self.transacciones)
        if filtro != "TODOS":
            transacciones = [t for t in transacciones if t.codigo_activo == filtro]
        # sort estable: misma fecha -> dividendos primero, luego el orden de registro
        transacciones.sort(key=lambda t: (t.fecha, self._ORDEN_MISMO_DIA.get(t.tipo_operacion, 1)))

        inventario = {}          # acciones por activo
        ultimo_precio = {}       # último Valor COP conocido por activo (para 'Total')
        capital_rf = {}          # capital vigente de renta fija por código (para 'Total')
        saldo = float(self.capital_inicial_cop)
        libro = []

        for t in transacciones:
            cod = t.codigo_activo
            op = t.tipo_operacion
            activo = self.buscarActivo(cod)
            es_rf = isinstance(activo, InstrumentoRentaFija)
            es_usd = (not es_rf) and (not cod.endswith(".CL"))
            trm = float(t.trm) if t.trm else 1.0

            acciones = inventario.get(cod, 0.0)          # Columna D: tenencia antes de la operación
            compra = venta = 0.0
            valor_cop = dividendo_cop = pago = 0.0

            if op == "COMPRA":
                compra = t.cantidad
                valor_cop = t.precio_unitario_cop
            elif op == "VENTA":
                venta = t.cantidad
                valor_cop = t.precio_unitario_cop
            elif op == "DIVIDENDO":
                if t.dividendo_unitario_cop > 0:
                    dividendo_cop = t.dividendo_unitario_cop
                    pago = dividendo_cop * acciones
                else:                                    # Registro legado: monto total en precio_unitario
                    pago = t.obtenerMontoBrutoCOP()
                    dividendo_cop = (pago / acciones) if acciones > 0 else 0.0
            elif op in ("RENDIMIENTO", "ABONO_CAPITAL"):
                pago = t.obtenerMontoBrutoCOP()

            valor_us = (valor_cop / trm) if (es_usd and trm > 0) else 0.0
            dividendo_us = (dividendo_cop / trm) if (es_usd and trm > 0) else dividendo_cop
            comision = float(t.comision_broker_cop)

            saldo_anterior = saldo
            saldo = saldo - (valor_cop * compra) + (valor_cop * venta) + pago - comision

            # Estado después de la operación
            if es_rf:
                if op == "COMPRA":
                    capital_rf[cod] = capital_rf.get(cod, 0.0) + t.obtenerMontoBrutoCOP()
                elif op == "ABONO_CAPITAL":
                    capital_rf[cod] = max(capital_rf.get(cod, 0.0) - pago, 0.0)
                elif op == "VENTA":
                    capital_rf[cod] = 0.0
                acciones_despues = acciones
            else:
                acciones_despues = max(acciones + compra - venta, 0.0)
                inventario[cod] = acciones_despues
                if valor_cop > 0:
                    ultimo_precio[cod] = valor_cop

            valor_posiciones = sum(inventario[c] * ultimo_precio.get(c, 0.0) for c in inventario) \
                + sum(capital_rf.values())

            libro.append({
                "fecha": t.fecha,
                "activo": cod,
                "operacion": op,
                "acciones": "—" if es_rf else acciones,
                "acciones_despues": "—" if es_rf else acciones_despues,
                "valor_us": valor_us,
                "valor_cop": valor_cop,
                "compra": compra,
                "venta": venta,
                "trm": trm,
                "dividendo_us": dividendo_us,
                "dividendo_cop": dividendo_cop,
                "pago": pago,
                "comision": comision,
                "saldo": saldo,
                "variacion": saldo - saldo_anterior,
                "total": saldo + valor_posiciones,
                "total_neto": t.obtenerTotalNetoCOP(),
                "moneda": "USD" if es_usd else "COP"
            })

        return libro
