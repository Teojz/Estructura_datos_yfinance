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

    def __init__(self, nombre_fondo: str, servicio_mercado: ServicioMercado):
        self.nombre_fondo = nombre_fondo             # Nombre del portafolio o fondo (ej. FIC Bancolombia)
        self.servicio_mercado = servicio_mercado     # Referencia al servicio de Yahoo Finance
        self.activos = []                            # Lista polimorfica de objetos Activo (Accion / RentaFija)
        self.transacciones = []                      # Historial completo de compras, ventas y dividendos

    def buscarActivo(self, codigo: str):
        """Busca un activo dentro del portafolio por su ticker o codigo."""
        cod = codigo.strip().upper()                 # Estandariza el codigo a mayusculas
        for act in self.activos:                     # Recorre los activos registrados
            if act.codigo == cod:                    # Si coincide el codigo
                return act                           # Retorna la instancia del activo
        return None                                  # Retorna None si no existe aun

    def agregarActivo(self, activo) -> None:
        """Agrega un nuevo instrumento (Accion o Renta Fija) al portafolio."""
        if self.buscarActivo(activo.codigo) is None: # Evita duplicar el mismo codigo de activo
            self.activos.append(activo)              # Inserta el activo en la lista

    def registrarTransaccion(self, transaccion: Transaccion) -> None:
        """Guarda una operacion en el libro contable del portafolio."""
        self.transacciones.append(transaccion)       # Agrega la transaccion al historial

    def actualizarValoracionMercado(self) -> None:
        """Recorre todas las acciones y actualiza su precio en COP y su EPS con yfinance."""
        self.servicio_mercado.obtenerTRM()           # Refresca primero la TRM del dolar en COP
        for act in self.activos:                     # Itera sobre cada inversion
            if isinstance(act, Accion):              # Si el activo es una Accion (Renta Variable)
                datos = self.servicio_mercado.consultarCotizacionYEPS(act.codigo) # Consulta yfinance
                if datos["precio_cop"] > 0:          # Si obtuvo un precio valido en COP
                    act.actualizarDatosMercado(datos["precio_cop"], datos["eps_cop"]) # Actualiza precio y EPS

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
        Calcula los indicadores globales del portafolio en COP (estilo ficha tecnica Bancolombia):
        Capital Invertido, Valor Actual, Ganancia/Perdida, Rentabilidad Acumulada (%) y E.A. (%).
        """
        invertido_total = 0.0                        # Total desembolsado en COP
        valor_actual_total = 0.0                     # Valor presente + efectivo ventas + rendimientos
        comisiones_totales = 0.0                     # Total comisiones pagadas al broker
        dividendos_y_rendimientos = 0.0              # Total flujos recibidos por dividendos e intereses
        suma_dias_ponderada = 0.0                    # Para ponderar los dias de tenencia del portafolio

        for act in self.activos:                     # Recorre todos los instrumentos
            inv = act.calcularCapitalInvertidoCOP()  # Capital invertido en este activo
            val = act.calcularValorActualCOP()       # Valor actual total de este activo
            invertido_total += inv                   # Suma al total invertido
            valor_actual_total += val                # Suma al valor actual consolidado
            comisiones_totales += act.comision_total_cop # Suma comisiones del broker
            suma_dias_ponderada += inv * act.calcularDiasTenencia() # Pondera antigüedad por monto

            if isinstance(act, Accion):              # Si es Accion, suma sus dividendos
                dividendos_y_rendimientos += act.dividendos_recibidos_cop
            elif isinstance(act, InstrumentoRentaFija): # Si es Renta Fija, suma intereses causados + pagados
                dividendos_y_rendimientos += (act.calcularInteresCausadoCOP() + act.rendimientos_pagados_cop)

        ganancia_neta = valor_actual_total - invertido_total # >0 se valorizo, <0 se desvalorizo
        rent_acum = ((ganancia_neta / invertido_total) * 100.0) if invertido_total > 0 else 0.0

        # Calculo de Rentabilidad Efectiva Anual (E.A.) consolidada del portafolio
        rent_ea = 0.0
        if invertido_total > 0 and valor_actual_total > 0:
            dias_prom = max(suma_dias_ponderada / invertido_total, 1.0) # Dias promedio ponderados
            exponente = min(365.0 / dias_prom, 12.0)                  # Anualizacion base 365 dias
            rent_ea = (((valor_actual_total / invertido_total) ** exponente) - 1.0) * 100.0

        distribucion = self.obtenerDistribucionRenta()                # Obtiene % Renta Fija vs Variable

        return {
            "capital_invertido_cop": round(invertido_total, 2),
            "valor_actual_cop": round(valor_actual_total, 2),
            "ganancia_neta_cop": round(ganancia_neta, 2),
            "comisiones_totales_cop": round(comisiones_totales, 2),
            "rendimientos_y_dividendos_cop": round(dividendos_y_rendimientos, 2),
            "rentabilidad_acumulada_porc": round(rent_acum, 2),
            "rentabilidad_ea_porc": round(rent_ea, 2),
            "estado_valoracion": "VALORIZADO" if ganancia_neta >= 0 else "DESVALORIZADO",
            **distribucion
        }

    def guardarPortafolio(self, ruta: str = "data/portafolio_bancolombia.json") -> bool:
        """Serializa los activos y transacciones en un archivo JSON."""
        try:
            os.makedirs(os.path.dirname(ruta), exist_ok=True)         # Crea carpeta data/ si no existe
            datos = {
                "nombre_fondo": self.nombre_fondo,
                "activos": [a.toDict() for a in self.activos],
                "transacciones": [t.toDict() for t in self.transacciones]
            }
            with open(ruta, "w", encoding="utf-8") as f:              # Abre archivo en modo escritura
                json.dump(datos, f, indent=4, ensure_ascii=False)     # Guarda JSON con formato legible
            return True
        except Exception:
            return False

    def cargarPortafolio(self, ruta: str = "data/portafolio_bancolombia.json") -> bool:
        """Carga los activos y transacciones desde el archivo JSON."""
        if not os.path.exists(ruta):                                  # Si no existe el archivo
            return False
        try:
            with open(ruta, "r", encoding="utf-8") as f:              # Abre el JSON en modo lectura
                datos = json.load(f)                                  # Decodifica el contenido
            self.nombre_fondo = datos.get("nombre_fondo", self.nombre_fondo)
            self.activos.clear()                                      # Limpia lista actual
            self.transacciones.clear()                                # Limpia transacciones actuales

            for d in datos.get("activos", []):                        # Reconstruye cada objeto segun su clase
                if d.get("clase") == "Accion":
                    self.activos.append(Accion.fromDict(d))
                elif d.get("clase") == "InstrumentoRentaFija":
                    self.activos.append(InstrumentoRentaFija.fromDict(d))

            for t in datos.get("transacciones", []):                  # Reconstruye historial de operaciones
                self.transacciones.append(Transaccion(
                    t["fecha"], t["tipo_operacion"], t["codigo_activo"],
                    t["cantidad"], t["precio_unitario_cop"], t["comision_broker_cop"]
                ))
            return True
        except Exception:
            return False