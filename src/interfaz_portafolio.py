"""
PROYECTO: Sistema de Seguimiento y Valoración de Portafolio
MÓDULO: interfaz_portafolio.py

Interfaz gráfica profesional desarrollada con Tkinter y Matplotlib.
Visualiza inversiones de renta fija y renta variable en pesos colombianos (COP).
Totalmente alineada con el Diagrama de Clases UML del proyecto.
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import pandas as pd

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.dates import AutoDateLocator, ConciseDateFormatter

from src.accion import Accion
from src.renta_fija import InstrumentoRentaFija


class InterfazPortafolioGUI:
    """Dashboard principal del sistema de seguimiento y valoración (POO & UML)."""

    FONDO = "#101820"
    PANEL = "#192832"
    PANEL_SECUNDARIO = "#223642"
    TEXTO = "#F3F6F8"
    TEXTO_SECUNDARIO = "#AABBC5"
    VERDE = "#36C995"
    ROJO = "#F07178"
    AZUL = "#65A9E8"

    FILTROS = ("1D", "1S", "1M", "6M", "1A", "5A")

    def __init__(self, portafolio):
        self.portafolio = portafolio
        self.root = None
        self.tarjetas = {}
        self.tabla_activos = None

        self.var_accion = None
        self.var_filtro = None
        self.var_estado = None
        self.combo_acciones = None

        self.figura_precios = None
        self.ax_precios = None
        self.canvas_precios = None

        self.figura_distribucion = None
        self.ax_distribucion = None
        self.canvas_distribucion = None

        self.lbl_ganancia = None
        self.lbl_renta_variable = None
        self.lbl_renta_fija = None
        self.lbl_estado_valoracion = None

        self.actualizacion_en_curso = False

        self.var_fecha_exacta = None
        self.var_sim = None
        self.entry_fecha = None
        self.btn_consultar_fecha = None
        self.lbl_sim = None
        self.simulacion = None
        self.consulta_fecha_en_curso = False


    # --------------------------------------------------
    # PROPIEDADES UML
    # --------------------------------------------------

    @property
    def filtro_actual(self) -> str:
        return self.var_filtro.get() if self.var_filtro else "1A"

    @filtro_actual.setter
    def filtro_actual(self, valor: str):
        if self.var_filtro:
            self.var_filtro.set(valor)

    @property
    def ticker_seleccionado(self) -> str:
        return self.var_accion.get() if self.var_accion else ""

    @ticker_seleccionado.setter
    def ticker_seleccionado(self, valor: str):
        if self.var_accion:
            self.var_accion.set(valor)

    @property
    def labels_tarjetas(self) -> dict:
        return self.tarjetas

    # --------------------------------------------------
    # FORMATO DE VALORES
    # --------------------------------------------------

    @staticmethod
    def formatearCOP(valor):
        return "$" + f"{float(valor):,.0f}".replace(",", ".")

    @staticmethod
    def formatoCOP(valor):
        """Método oficial según el Diagrama de Clases UML."""
        return InterfazPortafolioGUI.formatearCOP(valor)

    @staticmethod
    def formatearPorcentaje(valor):
        return (
            f"{float(valor):,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
            + "%"
        )

    # --------------------------------------------------
    # CÁLCULO DE INDICADORES
    # --------------------------------------------------

    def obtenerResumen(self):
        """Obtiene el resumen consolidado directamente desde la clase Portafolio."""
        return self.portafolio.obtenerResumenConsolidadoCOP()

    # --------------------------------------------------
    # INICIAR APLICACIÓN
    # --------------------------------------------------

    def iniciarDashboard(self):
        self.root = tk.Tk()
        self.root.title(
            "Sistema de Seguimiento y Valoración de Portafolio - Bancolombia COP"
        )
        self.root.minsize(1100, 700)
        self.root.configure(bg=self.FONDO)

        try:
            self.root.state("zoomed")
        except tk.TclError:
            ancho = self.root.winfo_screenwidth()
            alto = self.root.winfo_screenheight()
            self.root.geometry(f"{min(1450, ancho)}x{min(900, alto)}")

        self.var_accion = tk.StringVar(master=self.root)
        self.var_filtro = tk.StringVar(master=self.root, value="1A")
        self.var_estado = tk.StringVar(master=self.root, value="Sistema listo")

        self.configurarEstilos()
        self.crearEncabezado()
        self.crearIndicadores()
        self.crearContenido()
        self.actualizarVistaCompleta()

        self.root.mainloop()

    # --------------------------------------------------
    # ESTILOS
    # --------------------------------------------------

    def configurarEstilos(self):
        estilo = ttk.Style(self.root)
        estilo.theme_use("clam")

        estilo.configure(
            "Treeview",
            background=self.PANEL,
            foreground=self.TEXTO,
            fieldbackground=self.PANEL,
            rowheight=27,
            borderwidth=0,
            font=("Segoe UI", 9)
        )

        estilo.configure(
            "Treeview.Heading",
            background=self.PANEL_SECUNDARIO,
            foreground=self.TEXTO,
            font=("Segoe UI", 9, "bold"),
            relief="flat"
        )

        estilo.map(
            "Treeview",
            background=[("selected", "#31566A")]
        )

        estilo.configure("TCombobox", padding=5)
        estilo.configure(
            "TButton",
            padding=7,
            font=("Segoe UI", 9, "bold")
        )

    # --------------------------------------------------
    # ENCABEZADO
    # --------------------------------------------------

    def crearEncabezado(self):
        encabezado = tk.Frame(self.root, bg=self.FONDO)
        encabezado.pack(fill="x", padx=22, pady=(18, 14))

        titulo = tk.Frame(encabezado, bg=self.FONDO)
        titulo.pack(side="left", fill="x", expand=True)

        tk.Label(
            titulo,
            text="PORTAFOLIO DE INVERSIÓN",
            bg=self.FONDO,
            fg=self.TEXTO,
            font=("Segoe UI", 21, "bold")
        ).pack(anchor="w")

        tk.Label(
            titulo,
            text=(
                f"{self.portafolio.nombre_fondo} "
                "· Valores expresados en Pesos Colombianos (COP)"
            ),
            bg=self.FONDO,
            fg=self.TEXTO_SECUNDARIO,
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(4, 0))

        botones_header = tk.Frame(encabezado, bg=self.FONDO)
        botones_header.pack(side="right")

        ttk.Button(
            botones_header,
            text="➕ Registrar Operación",
            command=self.abrirVentanaRegistroOperacion
        ).pack(side="left", padx=4)

        ttk.Button(
            botones_header,
            text="📜 Historial de Operaciones",
            command=self.abrirVentanaHistorial
        ).pack(side="left", padx=4)

        ttk.Button(
            botones_header,
            text="🔄 Actualizar cotizaciones",
            command=self.actualizarMercado
        ).pack(side="left", padx=4)

    # --------------------------------------------------
    # TARJETAS DE INDICADORES
    # --------------------------------------------------

    def crearIndicadores(self):
        contenedor = tk.Frame(self.root, bg=self.FONDO)
        contenedor.pack(fill="x", padx=22, pady=(0, 14))

        indicadores = [
            ("CAPITAL INVERTIDO", "capital_invertido", "cop"),
            ("VALOR ACTUAL", "valor_actual", "cop"),
            ("COMISIONES TOTALES", "comisiones", "cop"),
            ("RENTABILIDAD ACUMULADA", "rentabilidad", "porcentaje"),
            ("RENTABILIDAD E.A. ESTIMADA", "rentabilidad_ea", "porcentaje")
        ]

        for indice, (titulo, clave, formato) in enumerate(indicadores):
            tarjeta = tk.Frame(
                contenedor,
                bg=self.PANEL,
                padx=13,
                pady=13,
                highlightthickness=1,
                highlightbackground="#2D424E"
            )

            tarjeta.grid(
                row=0,
                column=indice,
                sticky="nsew",
                padx=(0, 8)
            )

            contenedor.grid_columnconfigure(indice, weight=1)

            tk.Label(
                tarjeta,
                text=titulo,
                bg=self.PANEL,
                fg=self.TEXTO_SECUNDARIO,
                font=("Segoe UI", 8, "bold")
            ).pack(anchor="w")

            etiqueta = tk.Label(
                tarjeta,
                text="—",
                bg=self.PANEL,
                fg=self.TEXTO,
                font=("Segoe UI", 14, "bold")
            )

            etiqueta.pack(anchor="w", pady=(8, 0))
            self.tarjetas[clave] = (etiqueta, formato)

    # --------------------------------------------------
    # CONTENIDO PRINCIPAL
    # --------------------------------------------------

    def crearContenido(self):
        cuerpo = tk.Frame(self.root, bg=self.FONDO)
        cuerpo.pack(
            fill="both",
            expand=True,
            padx=22,
            pady=(0, 12)
        )

        izquierda = tk.Frame(
            cuerpo,
            bg=self.PANEL,
            padx=13,
            pady=12
        )

        izquierda.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 10)
        )

        derecha = tk.Frame(
            cuerpo,
            bg=self.PANEL,
            padx=13,
            pady=12,
            width=340
        )

        derecha.pack(side="right", fill="y")
        derecha.pack_propagate(False)

        self.crearGraficaPrecios(izquierda)
        self.crearTablaActivos(izquierda)
        self.crearDistribucion(derecha)
        self.crearResumen(derecha)

        tk.Label(
            self.root,
            textvariable=self.var_estado,
            bg=self.FONDO,
            fg=self.TEXTO_SECUNDARIO,
            anchor="w",
            padx=22,
            font=("Segoe UI", 8)
        ).pack(
            side="bottom",
            fill="x",
            pady=5
        )

    # --------------------------------------------------
    # GRÁFICA HISTÓRICA
    # --------------------------------------------------

    def crearGraficaPrecios(self, padre):
        barra = tk.Frame(padre, bg=self.PANEL)
        barra.pack(fill="x", pady=(0, 8))

        tk.Label(
            barra,
            text="Historial de precios de acciones",
            bg=self.PANEL,
            fg=self.TEXTO,
            font=("Segoe UI", 12, "bold")
        ).pack(side="left")

        controles = tk.Frame(barra, bg=self.PANEL)
        controles.pack(side="right")

        tk.Label(
            controles,
            text="Acción:",
            bg=self.PANEL,
            fg=self.TEXTO_SECUNDARIO
        ).pack(side="left", padx=4)

        self.combo_acciones = ttk.Combobox(
            controles,
            textvariable=self.var_accion,
            width=16,
            state="readonly"
        )

        self.combo_acciones.pack(side="left", padx=4)
        self.combo_acciones.bind(
            "<<ComboboxSelected>>",
            self.eventoCambioGrafica
        )

        tk.Label(
            controles,
            text="Periodo:",
            bg=self.PANEL,
            fg=self.TEXTO_SECUNDARIO
        ).pack(side="left", padx=4)

        combo_filtro = ttk.Combobox(
            controles,
            textvariable=self.var_filtro,
            values=self.FILTROS,
            width=6,
            state="readonly"
        )

        combo_filtro.pack(side="left", padx=4)
        combo_filtro.bind(
            "<<ComboboxSelected>>",
            self.eventoCambioGrafica
        )

        # ---- Consulta / simulación por fecha exacta ----
        self.var_fecha_exacta = tk.StringVar(master=self.root, value="")
        self.var_sim = tk.StringVar(master=self.root, value="")

        barra_fecha = tk.Frame(padre, bg=self.PANEL)
        barra_fecha.pack(fill="x", pady=(0, 6))

        tk.Label(
            barra_fecha,
            text="Fecha exacta (YYYY-MM-DD):",
            bg=self.PANEL,
            fg=self.TEXTO_SECUNDARIO
        ).pack(side="left", padx=(0, 4))

        self.entry_fecha = ttk.Entry(
            barra_fecha,
            textvariable=self.var_fecha_exacta,
            width=12
        )
        self.entry_fecha.pack(side="left", padx=4)
        self.entry_fecha.bind("<Return>", lambda e: self.consultarFechaExacta())

        self.btn_consultar_fecha = ttk.Button(
            barra_fecha,
            text="🔎 Consultar / Simular",
            command=self.consultarFechaExacta
        )
        self.btn_consultar_fecha.pack(side="left", padx=4)

        ttk.Button(
            barra_fecha,
            text="Limpiar",
            command=self.limpiarSimulacionFecha
        ).pack(side="left", padx=4)

        self.lbl_sim = tk.Label(
            barra_fecha,
            textvariable=self.var_sim,
            bg=self.PANEL,
            fg=self.TEXTO_SECUNDARIO,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
            justify="left"
        )
        self.lbl_sim.pack(side="left", padx=8, fill="x", expand=True)

        self.figura_precios = Figure(
            figsize=(8.2, 2.55),
            dpi=100,
            facecolor=self.PANEL
        )

        self.ax_precios = self.figura_precios.add_subplot(111)
        self.estilizarGrafica(self.ax_precios)

        self.figura_precios.subplots_adjust(
            left=0.09,
            right=0.985,
            top=0.88,
            bottom=0.22
        )

        self.canvas_precios = FigureCanvasTkAgg(
            self.figura_precios,
            master=padre
        )

        widget_grafica = self.canvas_precios.get_tk_widget()
        widget_grafica.configure(height=225)
        widget_grafica.pack(fill="x", expand=False)

    def eventoCambioGrafica(self, evento=None):
        self.dibujarSerieHistorica()

    def graficarSerieTiempo(self, ticker: str = None, filtro: str = None):
        """Método oficial del Diagrama UML para graficar series de tiempo."""
        if ticker:
            self.var_accion.set(ticker)
        if filtro:
            self.var_filtro.set(filtro)
        self.dibujarSerieHistorica()

    def limpiarSimulacionFecha(self):
        self.simulacion = None
        if self.var_fecha_exacta:
            self.var_fecha_exacta.set("")
        if self.var_sim:
            self.var_sim.set("")
        if self.lbl_sim:
            self.lbl_sim.config(fg=self.TEXTO_SECUNDARIO)
        self.dibujarSerieHistorica()

    def consultarFechaExacta(self):
        """Consulta el precio de una fecha exacta y simula el rendimiento hasta hoy."""
        if self.consulta_fecha_en_curso:
            return

        ticker = self.var_accion.get().strip() if self.var_accion else ""
        texto = self.var_fecha_exacta.get().strip()

        if not ticker:
            self.var_sim.set("Seleccione una acción.")
            self.lbl_sim.config(fg=self.ROJO)
            return

        try:
            datetime.strptime(texto, "%Y-%m-%d")
        except ValueError:
            self.simulacion = None
            self.var_sim.set("Fecha inválida. Use el formato YYYY-MM-DD (ej. 2025-08-20).")
            self.lbl_sim.config(fg=self.ROJO)
            self.dibujarSerieHistorica()
            return

        self.consulta_fecha_en_curso = True
        self.btn_consultar_fecha.state(["disabled"])
        self.var_sim.set("Consultando...")
        self.lbl_sim.config(fg=self.TEXTO_SECUNDARIO)
        self.var_estado.set(f"Consultando {ticker} el {texto}...")

        def tarea():
            resultado = None
            actual = 0.0
            error = None
            try:
                servicio = self.portafolio.servicio_mercado
                resultado = servicio.obtenerPrecioFechaExacta(ticker, texto)
                if resultado.get("ok"):
                    cot = servicio.consultarCotizacionYEPS(ticker)
                    actual = float(cot.get("precio_cop", 0.0) or 0.0)
            except Exception as exc:
                error = exc

            if self.root:
                self.root.after(0, lambda: finalizar(resultado, actual, error))

        def finalizar(resultado, actual, error):
            self.consulta_fecha_en_curso = False
            self.btn_consultar_fecha.state(["!disabled"])

            if error is not None or resultado is None:
                self.simulacion = None
                self.var_sim.set(f"Error en la consulta: {error}")
                self.lbl_sim.config(fg=self.ROJO)
                self.var_estado.set("Error en la consulta por fecha exacta.")
            elif not resultado.get("ok"):
                self.simulacion = None
                self.var_sim.set(resultado.get("mensaje", "Sin cotización para esa fecha."))
                self.lbl_sim.config(fg="#F2C14E")
                self.var_estado.set("Fecha sin cotización bursátil.")
            elif actual <= 0:
                self.simulacion = None
                self.var_sim.set("No se pudo obtener el precio actual en tiempo real.")
                self.lbl_sim.config(fg=self.ROJO)
                self.var_estado.set("Precio actual no disponible.")
            else:
                pf = float(resultado["precio_cop"])
                rend = (actual - pf) / pf * 100.0 if pf > 0 else 0.0
                self.simulacion = {
                    "ticker": ticker,
                    "fecha": resultado["fecha"],
                    "precio_fecha": pf,
                    "precio_actual": actual,
                    "rendimiento": rend
                }
                signo = "+" if rend >= 0 else ""
                self.var_sim.set(
                    f"{resultado['fecha']}: {self.formatoCOP(pf)} → Hoy: {self.formatoCOP(actual)} "
                    f"({signo}{self.formatearPorcentaje(rend)})"
                )
                self.lbl_sim.config(fg=self.VERDE if rend >= 0 else self.ROJO)
                self.var_estado.set(f"Simulación {ticker} desde {resultado['fecha']} calculada.")

            self.dibujarSerieHistorica()

        threading.Thread(target=tarea, daemon=True).start()

    def dibujarSerieHistorica(self):
        if self.ax_precios is None:
            return

        self.ax_precios.clear()
        self.estilizarGrafica(self.ax_precios)

        ticker = self.var_accion.get().strip() if self.var_accion else ""
        filtro = self.var_filtro.get() if self.var_filtro else "1A"

        if not ticker:
            self.ax_precios.text(
                0.5,
                0.5,
                "No hay acciones registradas",
                transform=self.ax_precios.transAxes,
                ha="center",
                va="center",
                color=self.TEXTO_SECUNDARIO
            )
            self.canvas_precios.draw_idle()
            return

        try:
            serie = self.portafolio.servicio_mercado.obtenerSerieTiempo(
                ticker, filtro
            )

            if serie is None or serie.empty:
                raise ValueError("No hay datos históricos disponibles.")

            if "Precio_COP" not in serie.columns:
                raise ValueError("No existe la columna Precio_COP.")

            precios = pd.to_numeric(
                serie["Precio_COP"],
                errors="coerce"
            ).dropna()

            if precios.empty:
                raise ValueError("No se encontraron precios válidos.")

            # Zona horaria: se descarta tz (hora local de la bolsa) para poder
            # combinar el índice con fechas naive de la simulación.
            if isinstance(precios.index, pd.DatetimeIndex) and precios.index.tz is not None:
                precios.index = precios.index.tz_localize(None)

            fechas = precios.index

            self.ax_precios.plot(
                fechas,
                precios.values,
                color=self.VERDE,
                linewidth=1.8
            )

            self.ax_precios.fill_between(
                fechas,
                precios.values,
                color=self.VERDE,
                alpha=0.12
            )

            titulo = f"{ticker} | {filtro}"

            # ---- Simulación por fecha exacta ----
            sim = self.simulacion
            if (
                sim
                and sim.get("ticker") == ticker
                and isinstance(precios.index, pd.DatetimeIndex)
            ):
                f = pd.Timestamp(sim["fecha"])
                pf = sim["precio_fecha"]
                pa = sim["precio_actual"]
                rend = sim["rendimiento"]
                x_hoy = precios.index[-1]
                if x_hoy < f:
                    x_hoy = pd.Timestamp.now().normalize()

                color_r = self.VERDE if rend >= 0 else self.ROJO
                signo = "+" if rend >= 0 else ""

                self.ax_precios.axvline(
                    f, color="#F2C14E", linestyle="--", linewidth=1.0, alpha=0.9
                )
                self.ax_precios.axhline(
                    pa, color=self.AZUL, linestyle="--", linewidth=0.9, alpha=0.8
                )
                self.ax_precios.plot(
                    [f, x_hoy], [pf, pa],
                    color=color_r, linestyle=":", linewidth=1.8,
                    marker="o", markersize=6
                )
                self.ax_precios.annotate(
                    f"{sim['fecha']}: {self.formatoCOP(pf)}",
                    xy=(f, pf), xytext=(6, 10), textcoords="offset points",
                    color=self.TEXTO, fontsize=8
                )
                self.ax_precios.annotate(
                    f"Hoy: {self.formatoCOP(pa)}\n"
                    f"{signo}{self.formatearPorcentaje(rend)}",
                    xy=(x_hoy, pa), xytext=(-6, 10), textcoords="offset points",
                    ha="right", color=color_r, fontsize=8, fontweight="bold"
                )
                titulo += (
                    f" | Simulación desde {sim['fecha']}: "
                    f"{signo}{self.formatearPorcentaje(rend)}"
                )

            self.ax_precios.set_title(
                titulo,
                color=self.TEXTO,
                fontsize=10,
                loc="left"
            )

            self.ax_precios.set_ylabel(
                "Precio (COP)",
                color=self.TEXTO_SECUNDARIO,
                fontsize=8
            )

            if isinstance(precios.index, pd.DatetimeIndex):
                localizador = AutoDateLocator()
                self.ax_precios.xaxis.set_major_locator(localizador)
                self.ax_precios.xaxis.set_major_formatter(
                    ConciseDateFormatter(localizador)
                )

            self.figura_precios.autofmt_xdate()

        except Exception as error:
            self.ax_precios.text(
                0.5,
                0.5,
                f"No fue posible cargar los datos:\n{error}",
                transform=self.ax_precios.transAxes,
                ha="center",
                va="center",
                color=self.TEXTO_SECUNDARIO,
                wrap=True
            )

        self.canvas_precios.draw_idle()

    # --------------------------------------------------
    # TABLA DE INVERSIONES
    # --------------------------------------------------

    def crearTablaActivos(self, padre):
        tk.Label(
            padre,
            text="Detalle de inversiones (Haga clic en una acción para graficar)",
            bg=self.PANEL,
            fg=self.TEXTO,
            font=("Segoe UI", 12, "bold")
        ).pack(
            anchor="w",
            pady=(12, 7)
        )

        columnas = (
            "codigo",
            "nombre",
            "tipo",
            "unidades",
            "capital",
            "valor",
            "rentabilidad"
        )

        marco_tabla = tk.Frame(
            padre,
            bg=self.PANEL,
            height=170
        )

        marco_tabla.pack(
            fill="both",
            expand=True,
            pady=(0, 2)
        )

        marco_tabla.pack_propagate(False)

        self.tabla_activos = ttk.Treeview(
            marco_tabla,
            columns=columnas,
            show="headings",
            height=5
        )

        encabezados = {
            "codigo": "Código",
            "nombre": "Activo",
            "tipo": "Tipo",
            "unidades": "Unidades",
            "capital": "Capital COP",
            "valor": "Valor actual COP",
            "rentabilidad": "Rentab. acum."
        }

        anchos = {
            "codigo": 95,
            "nombre": 145,
            "tipo": 95,
            "unidades": 70,
            "capital": 115,
            "valor": 125,
            "rentabilidad": 95
        }

        for columna in columnas:
            self.tabla_activos.heading(
                columna,
                text=encabezados[columna]
            )

            self.tabla_activos.column(
                columna,
                width=anchos[columna],
                anchor=(
                    "w"
                    if columna in ("codigo", "nombre", "tipo")
                    else "e"
                )
            )

        scroll_vertical = ttk.Scrollbar(
            marco_tabla,
            orient="vertical",
            command=self.tabla_activos.yview
        )

        scroll_horizontal = ttk.Scrollbar(
            marco_tabla,
            orient="horizontal",
            command=self.tabla_activos.xview
        )

        self.tabla_activos.configure(
            yscrollcommand=scroll_vertical.set,
            xscrollcommand=scroll_horizontal.set
        )

        self.tabla_activos.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        scroll_vertical.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        scroll_horizontal.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        marco_tabla.grid_rowconfigure(0, weight=1)
        marco_tabla.grid_columnconfigure(0, weight=1)

        # Enlace interactivo para graficar al seleccionar fila
        self.tabla_activos.bind("<<TreeviewSelect>>", self._on_fila_seleccionada)

    def _on_fila_seleccionada(self, evento=None):
        seleccion = self.tabla_activos.selection()
        if not seleccion:
            return
        item = self.tabla_activos.item(seleccion[0])
        valores = item.get("values", [])
        if valores:
            codigo = str(valores[0]).strip().upper()
            activo = self.portafolio.buscarActivo(codigo)
            if isinstance(activo, Accion):
                self.graficarSerieTiempo(ticker=codigo)

    def actualizarTablaActivos(self):
        for fila in self.tabla_activos.get_children():
            self.tabla_activos.delete(fila)

        for activo in self.portafolio.activos:
            capital = activo.calcularCapitalInvertidoCOP()
            valor = activo.calcularValorActualCOP()
            rentabilidad = activo.calcularRentabilidadAcumulada()

            if isinstance(activo, Accion):
                tipo = "Renta variable"
                unidades = activo.cant_actual
            elif isinstance(activo, InstrumentoRentaFija):
                tipo = activo.tipo
                unidades = "—"
            else:
                tipo = getattr(activo, "tipo_renta", "—")
                unidades = "—"

            self.tabla_activos.insert(
                "",
                "end",
                values=(
                    activo.codigo,
                    activo.nombre,
                    tipo,
                    unidades,
                    self.formatoCOP(capital),
                    self.formatoCOP(valor),
                    self.formatearPorcentaje(rentabilidad)
                )
            )

    # --------------------------------------------------
    # DISTRIBUCIÓN DEL PORTAFOLIO
    # --------------------------------------------------

    def crearDistribucion(self, padre):
        tk.Label(
            padre,
            text="Distribución por tipo de renta",
            bg=self.PANEL,
            fg=self.TEXTO,
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w")

        self.figura_distribucion = Figure(
            figsize=(3.2, 2.35),
            dpi=100,
            facecolor=self.PANEL
        )

        self.ax_distribucion = (
            self.figura_distribucion.add_subplot(111)
        )

        self.canvas_distribucion = FigureCanvasTkAgg(
            self.figura_distribucion,
            master=padre
        )

        self.canvas_distribucion.get_tk_widget().pack(fill="x")

    def actualizarDistribucion(self, resumen):
        self.ax_distribucion.clear()

        valores = [
            resumen.get("renta_variable", 0.0),
            resumen.get("renta_fija", 0.0)
        ]

        etiquetas = [
            "Renta variable",
            "Renta fija"
        ]

        colores = [
            self.AZUL,
            self.VERDE
        ]

        datos = [
            (v, e, c)
            for v, e, c in zip(valores, etiquetas, colores)
            if v > 0
        ]

        if not datos:
            self.ax_distribucion.text(
                0.5,
                0.5,
                "Sin inversiones",
                ha="center",
                va="center",
                color=self.TEXTO_SECUNDARIO
            )
        else:
            total = sum(d[0] for d in datos)
            porcentajes = [
                f"{d[1]} · {d[0] / total:.1%}"
                for d in datos
            ]

            self.ax_distribucion.pie(
                [d[0] for d in datos],
                labels=None,
                colors=[d[2] for d in datos],
                startangle=90,
                autopct="%1.1f%%",
                pctdistance=0.76,
                textprops={
                    "color": self.TEXTO,
                    "fontsize": 8
                },
                wedgeprops={
                    "width": 0.38,
                    "edgecolor": self.PANEL
                }
            )

            self.ax_distribucion.legend(
                porcentajes,
                loc="lower center",
                bbox_to_anchor=(0.5, -0.10),
                frameon=False,
                labelcolor=self.TEXTO_SECUNDARIO,
                fontsize=8,
                ncol=1,
                handlelength=1.0
            )

        self.ax_distribucion.set_facecolor(self.PANEL)
        self.canvas_distribucion.draw_idle()

    # --------------------------------------------------
    # RESUMEN LATERAL
    # --------------------------------------------------

    def crearResumen(self, padre):
        tk.Label(
            padre,
            text="Resumen de valoración",
            bg=self.PANEL,
            fg=self.TEXTO,
            font=("Segoe UI", 12, "bold")
        ).pack(
            anchor="w",
            pady=(12, 8)
        )

        self.lbl_ganancia = tk.Label(
            padre,
            text="Ganancia / pérdida: —",
            bg=self.PANEL,
            fg=self.TEXTO,
            font=("Segoe UI", 10, "bold")
        )
        self.lbl_ganancia.pack(anchor="w", pady=4)

        self.lbl_renta_variable = tk.Label(
            padre,
            text="Renta variable: —",
            bg=self.PANEL,
            fg=self.TEXTO_SECUNDARIO,
            font=("Segoe UI", 9)
        )
        self.lbl_renta_variable.pack(anchor="w", pady=4)

        self.lbl_renta_fija = tk.Label(
            padre,
            text="Renta fija: —",
            bg=self.PANEL,
            fg=self.TEXTO_SECUNDARIO,
            font=("Segoe UI", 9)
        )
        self.lbl_renta_fija.pack(anchor="w", pady=4)

        self.lbl_estado_valoracion = tk.Label(
            padre,
            text="",
            bg=self.PANEL,
            fg=self.VERDE,
            font=("Segoe UI", 9, "bold")
        )
        self.lbl_estado_valoracion.pack(anchor="w", pady=(10, 4))

        tk.Label(
            padre,
            text=(
                "La E.A. consolidada es una estimación anualizada "
                "con días de tenencia ponderados. Las cotizaciones "
                "históricas dependen de ServicioMercado / Yahoo Finance."
            ),
            bg=self.PANEL,
            fg=self.TEXTO_SECUNDARIO,
            wraplength=295,
            justify="left",
            font=("Segoe UI", 8)
        ).pack(
            anchor="w",
            pady=(12, 0)
        )

    # --------------------------------------------------
    # ACTUALIZAR LISTA DE ACCIONES
    # --------------------------------------------------

    def actualizarListaAcciones(self):
        codigos = [
            activo.codigo
            for activo in self.portafolio.activos
            if isinstance(activo, Accion)
        ]

        if not self.combo_acciones:
            return

        seleccion = self.var_accion.get() if self.var_accion else ""
        self.combo_acciones["values"] = codigos

        if seleccion in codigos:
            self.var_accion.set(seleccion)
        else:
            self.var_accion.set(codigos[0] if codigos else "")

    # --------------------------------------------------
    # ACTUALIZAR TODO EL DASHBOARD
    # --------------------------------------------------

    def actualizarDashboard(self):
        """Actualiza todas las vistas numéricas, gráficas y tablas del dashboard."""
        resumen = self.obtenerResumen()

        for clave, (etiqueta, formato) in self.tarjetas.items():
            valor = resumen.get(clave, 0.0)
            if formato == "cop":
                texto = self.formatoCOP(valor)
            else:
                texto = self.formatearPorcentaje(valor)
            etiqueta.config(text=texto)

        color = (
            self.VERDE
            if resumen.get("ganancia", 0.0) >= 0
            else self.ROJO
        )

        if "rentabilidad" in self.tarjetas:
            self.tarjetas["rentabilidad"][0].config(fg=color)
        if "rentabilidad_ea" in self.tarjetas:
            self.tarjetas["rentabilidad_ea"][0].config(fg=color)

        if self.lbl_ganancia:
            self.lbl_ganancia.config(
                text=(
                    "Ganancia / pérdida: "
                    + self.formatoCOP(resumen.get("ganancia", 0.0))
                ),
                fg=color
            )

        if self.lbl_renta_variable:
            self.lbl_renta_variable.config(
                text=(
                    "Renta variable: "
                    + self.formatoCOP(resumen.get("renta_variable", 0.0))
                    + " ("
                    + self.formatearPorcentaje(resumen.get("porcentaje_rv", 0.0))
                    + ")"
                )
            )

        if self.lbl_renta_fija:
            self.lbl_renta_fija.config(
                text=(
                    "Renta fija: "
                    + self.formatoCOP(resumen.get("renta_fija", 0.0))
                    + " ("
                    + self.formatearPorcentaje(resumen.get("porcentaje_rf", 0.0))
                    + ")"
                )
            )

        if self.lbl_estado_valoracion:
            self.lbl_estado_valoracion.config(
                text=resumen.get("estado", "")
            )

        if self.tabla_activos:
            self.actualizarTablaActivos()
        if self.ax_distribucion:
            self.actualizarDistribucion(resumen)
        if self.combo_acciones:
            self.actualizarListaAcciones()
        if self.ax_precios:
            self.dibujarSerieHistorica()

    def actualizarVistaCompleta(self):
        """Método oficial según el Diagrama de Clases UML."""
        self.actualizarDashboard()

    # --------------------------------------------------
    # ESTILO DE GRÁFICAS
    # --------------------------------------------------

    def estilizarGrafica(self, eje):
        eje.set_facecolor(self.PANEL)
        eje.tick_params(
            colors=self.TEXTO_SECUNDARIO,
            labelsize=8
        )
        eje.grid(
            True,
            color="#344955",
            alpha=0.55,
            linewidth=0.6
        )
        for borde in eje.spines.values():
            borde.set_color("#344955")

    # --------------------------------------------------
    # ACTUALIZAR PRECIOS DE MERCADO EN HILO SEPARADO
    # --------------------------------------------------

    def actualizarMercado(self):
        if self.actualizacion_en_curso:
            return

        self.actualizacion_en_curso = True
        self.var_estado.set("Actualizando cotizaciones de mercado en tiempo real...")

        def tarea():
            error = None
            try:
                self.portafolio.actualizarValoracionMercado()
            except Exception as exc:
                error = exc

            if self.root:
                self.root.after(0, lambda: finalizar(error))

        def finalizar(error):
            self.actualizacion_en_curso = False
            if error is not None:
                self.var_estado.set("Error al actualizar cotizaciones de mercado.")
                if self.root:
                    messagebox.showerror(
                        "Error de mercado",
                        str(error),
                        parent=self.root
                    )
            else:
                self.var_estado.set("Cotizaciones actualizadas correctamente.")
                self.actualizarVistaCompleta()

        threading.Thread(
            target=tarea,
            daemon=True
        ).start()

    # --------------------------------------------------
    # VENTANA MODAL: REGISTRAR OPERACIONES (COMPRA/VENTA/RENDIMIENTOS)
    # --------------------------------------------------

    def abrirVentanaRegistroOperacion(self):
        """Abre un diálogo modal interactivo para simular y registrar compras, ventas, cupones y dividendos."""
        from datetime import date, timedelta

        ventana = tk.Toplevel(self.root)
        ventana.title("Registrar Operación de Inversión")
        ventana.configure(bg=self.FONDO)
        ventana.geometry("560x700")
        ventana.minsize(520, 650)
        ventana.transient(self.root)
        ventana.grab_set()

        padre = tk.Frame(ventana, bg=self.FONDO, padx=22, pady=16)
        padre.pack(fill="both", expand=True)

        tk.Label(
            padre,
            text="REGISTRAR NUEVA OPERACIÓN",
            bg=self.FONDO,
            fg=self.TEXTO,
            font=("Segoe UI", 15, "bold")
        ).pack(anchor="w", pady=(0, 2))

        tk.Label(
            padre,
            text="Simulación contable de compra, venta, dividendos y rendimientos",
            bg=self.FONDO,
            fg=self.TEXTO_SECUNDARIO,
            font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(0, 12))

        form = tk.Frame(padre, bg=self.PANEL, padx=16, pady=14)
        form.pack(fill="both", expand=True)
        form.grid_columnconfigure(1, weight=1)

        # 1. Categoría
        tk.Label(form, text="Categoría:", bg=self.PANEL, fg=self.TEXTO, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=4)
        var_cat = tk.StringVar(value="Renta Variable")
        combo_cat = ttk.Combobox(form, textvariable=var_cat, values=("Renta Variable", "Renta Fija"), state="readonly", width=25)
        combo_cat.grid(row=0, column=1, sticky="ew", pady=4, padx=(8, 0))

        # 2. Tipo de Operación
        tk.Label(form, text="Operación:", bg=self.PANEL, fg=self.TEXTO, font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=4)
        var_op = tk.StringVar(value="COMPRA")
        combo_op = ttk.Combobox(form, textvariable=var_op, state="readonly", width=25)
        combo_op.grid(row=1, column=1, sticky="ew", pady=4, padx=(8, 0))

        # 3. Código / Ticker
        tk.Label(form, text="Código / Ticker:", bg=self.PANEL, fg=self.TEXTO, font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w", pady=4)
        var_cod = tk.StringVar()
        combo_cod = ttk.Combobox(form, textvariable=var_cod, width=25)
        combo_cod.grid(row=2, column=1, sticky="ew", pady=4, padx=(8, 0))

        # 4. Nombre Comercial
        tk.Label(form, text="Nombre del Activo:", bg=self.PANEL, fg=self.TEXTO, font=("Segoe UI", 9, "bold")).grid(row=3, column=0, sticky="w", pady=4)
        var_nom = tk.StringVar()
        entry_nom = ttk.Entry(form, textvariable=var_nom, width=27)
        entry_nom.grid(row=3, column=1, sticky="ew", pady=4, padx=(8, 0))

        # 5. Fecha de Operación
        tk.Label(form, text="Fecha (YYYY-MM-DD):", bg=self.PANEL, fg=self.TEXTO, font=("Segoe UI", 9, "bold")).grid(row=4, column=0, sticky="w", pady=4)
        var_fecha = tk.StringVar(value=date.today().isoformat())
        entry_fecha = ttk.Entry(form, textvariable=var_fecha, width=27)
        entry_fecha.grid(row=4, column=1, sticky="ew", pady=4, padx=(8, 0))

        # 6. Cantidad
        lbl_cant = tk.Label(form, text="Cantidad de Acciones:", bg=self.PANEL, fg=self.TEXTO, font=("Segoe UI", 9, "bold"))
        lbl_cant.grid(row=5, column=0, sticky="w", pady=4)
        var_cant = tk.StringVar(value="10")
        entry_cant = ttk.Entry(form, textvariable=var_cant, width=27)
        entry_cant.grid(row=5, column=1, sticky="ew", pady=4, padx=(8, 0))

        # 7. Precio Unitario o Monto COP
        lbl_precio = tk.Label(form, text="Precio Unitario COP:", bg=self.PANEL, fg=self.TEXTO, font=("Segoe UI", 9, "bold"))
        lbl_precio.grid(row=6, column=0, sticky="w", pady=4)
        var_precio = tk.StringVar(value="35000")
        entry_precio = ttk.Entry(form, textvariable=var_precio, width=27)
        entry_precio.grid(row=6, column=1, sticky="ew", pady=4, padx=(8, 0))

        # 8. Comisión del Bróker
        tk.Label(form, text="Comisión Bróker COP:", bg=self.PANEL, fg=self.TEXTO, font=("Segoe UI", 9, "bold")).grid(row=7, column=0, sticky="w", pady=4)
        var_com = tk.StringVar(value="0")
        entry_com = ttk.Entry(form, textvariable=var_com, width=27)
        entry_com.grid(row=7, column=1, sticky="ew", pady=4, padx=(8, 0))

        # 8b. TRM histórica exacta
        tk.Label(form, text="TRM (COP/USD):", bg=self.PANEL, fg=self.TEXTO, font=("Segoe UI", 9, "bold")).grid(row=8, column=0, sticky="w", pady=4)
        marco_trm = tk.Frame(form, bg=self.PANEL)
        marco_trm.grid(row=8, column=1, sticky="ew", pady=4, padx=(8, 0))
        marco_trm.grid_columnconfigure(0, weight=1)
        var_trm = tk.StringVar(value="1.0")
        entry_trm = ttk.Entry(marco_trm, textvariable=var_trm, width=18)
        entry_trm.grid(row=0, column=0, sticky="ew")
        btn_trm = ttk.Button(marco_trm, text="Traer TRM", width=11, command=lambda: traer_trm())
        btn_trm.grid(row=0, column=1, padx=(6, 0))

        # Marco especial para campos de Renta Fija
        frame_rf = tk.LabelFrame(form, text="Condiciones Contractuales (Renta Fija)", bg=self.PANEL, fg=self.AZUL, font=("Segoe UI", 8, "bold"), padx=8, pady=6)
        frame_rf.grid(row=9, column=0, columnspan=2, sticky="nsew", pady=(8, 4))
        frame_rf.grid_columnconfigure(1, weight=1)

        tk.Label(frame_rf, text="Subtipo:", bg=self.PANEL, fg=self.TEXTO, font=("Segoe UI", 8)).grid(row=0, column=0, sticky="w", pady=2)
        var_subtipo = tk.StringVar(value="CDT")
        combo_subtipo = ttk.Combobox(frame_rf, textvariable=var_subtipo, values=("CDT", "BONO", "TES"), state="readonly", width=23)
        combo_subtipo.grid(row=0, column=1, sticky="ew", pady=2, padx=(8, 0))

        tk.Label(frame_rf, text="Tasa E.A. (%):", bg=self.PANEL, fg=self.TEXTO, font=("Segoe UI", 8)).grid(row=1, column=0, sticky="w", pady=2)
        var_tasa = tk.StringVar(value="10.5")
        entry_tasa = ttk.Entry(frame_rf, textvariable=var_tasa, width=25)
        entry_tasa.grid(row=1, column=1, sticky="ew", pady=2, padx=(8, 0))

        tk.Label(frame_rf, text="Vencimiento:", bg=self.PANEL, fg=self.TEXTO, font=("Segoe UI", 8)).grid(row=2, column=0, sticky="w", pady=2)
        default_venc = (date.today() + timedelta(days=360)).isoformat()
        var_venc = tk.StringVar(value=default_venc)
        entry_venc = ttk.Entry(frame_rf, textvariable=var_venc, width=25)
        entry_venc.grid(row=2, column=1, sticky="ew", pady=2, padx=(8, 0))

        tk.Label(frame_rf, text="Frecuencia Cupón:", bg=self.PANEL, fg=self.TEXTO, font=("Segoe UI", 8)).grid(row=3, column=0, sticky="w", pady=2)
        var_frec = tk.StringVar(value="Semestral (2)")
        combo_frec = ttk.Combobox(frame_rf, textvariable=var_frec, values=("Semestral (2)", "Anual (1)", "Trimestral (4)", "Mensual (12)"), state="readonly", width=23)
        combo_frec.grid(row=3, column=1, sticky="ew", pady=2, padx=(8, 0))

        def actualizar_campos_dinamicos(*args):
            cat = var_cat.get()
            if cat == "Renta Variable":
                combo_op["values"] = ("COMPRA", "VENTA", "DIVIDENDO")
                if var_op.get() not in ("COMPRA", "VENTA", "DIVIDENDO"):
                    var_op.set("COMPRA")
                lbl_cant.config(text="Cantidad de Acciones:")
                lbl_precio.config(text="Precio Unitario COP:")
                frame_rf.grid_remove()
                activos_rv = [a.codigo for a in self.portafolio.activos if isinstance(a, Accion)]
                combo_cod["values"] = activos_rv
            else:
                combo_op["values"] = ("COMPRA / APERTURA", "VENTA / LIQUIDACION", "RENDIMIENTO / CUPON", "ABONO A CAPITAL")
                if var_op.get() not in ("COMPRA / APERTURA", "VENTA / LIQUIDACION", "RENDIMIENTO / CUPON", "ABONO A CAPITAL"):
                    var_op.set("COMPRA / APERTURA")
                lbl_cant.config(text="Cantidad de Títulos:")
                lbl_precio.config(text="Capital / Valor COP:")
                if var_op.get() == "COMPRA / APERTURA":
                    frame_rf.grid()
                else:
                    frame_rf.grid_remove()
                activos_rf = [a.codigo for a in self.portafolio.activos if isinstance(a, InstrumentoRentaFija)]
                combo_cod["values"] = activos_rf

        combo_cat.bind("<<ComboboxSelected>>", actualizar_campos_dinamicos)
        combo_op.bind("<<ComboboxSelected>>", actualizar_campos_dinamicos)

        def al_seleccionar_codigo(evento=None):
            cod = var_cod.get().strip().upper()
            activo = self.portafolio.buscarActivo(cod)
            if activo:
                var_nom.set(activo.nombre)
                if isinstance(activo, Accion):
                    var_precio.set(str(activo.precio_mercado_cop or activo.costo_promedio_cop))
                elif isinstance(activo, InstrumentoRentaFija):
                    var_subtipo.set(activo.tipo)
                    var_tasa.set(str(round(activo.tasa_ea * 100, 2)))
                    var_venc.set(activo.fecha_vencimiento)

        combo_cod.bind("<<ComboboxSelected>>", al_seleccionar_codigo)
        combo_cod.bind("<FocusOut>", al_seleccionar_codigo)

        actualizar_campos_dinamicos()

        # --- Comisión sugerida (0,21 %) mientras el usuario no la edite manualmente ---
        com_manual = [False]
        entry_com.bind("<KeyRelease>", lambda e: com_manual.__setitem__(0, True))

        def actualizar_comision_sugerida(*args):
            if com_manual[0]:
                return
            try:
                if var_cat.get() != "Renta Variable":
                    var_com.set("0")
                    return
                precio_v = float(var_precio.get().replace(",", ".") or 0)
                cant_v = 1.0 if var_op.get() == "DIVIDENDO" else float(var_cant.get().replace(",", ".") or 0)
                var_com.set(f"{cant_v * precio_v * 0.0021:.2f}")
            except ValueError:
                pass

        for _v in (var_cat, var_op, var_cant, var_precio):
            _v.trace_add("write", actualizar_comision_sugerida)
        actualizar_comision_sugerida()

        # --- TRM histórica exacta de la fecha digitada ---
        def traer_trm(evento=None):
            cod = var_cod.get().strip().upper()
            fecha_txt = var_fecha.get().strip()

            if var_cat.get() != "Renta Variable" or cod.endswith(".CL"):
                var_trm.set("1.0")
                return
            try:
                datetime.strptime(fecha_txt, "%Y-%m-%d")
            except ValueError:
                messagebox.showwarning("Fecha inválida", "Use el formato YYYY-MM-DD para consultar la TRM.", parent=ventana)
                return

            btn_trm.state(["disabled"])
            var_trm.set("Consultando...")

            def tarea():
                try:
                    valor = self.portafolio.servicio_mercado.obtenerTRMFechaExacta(fecha_txt)
                except Exception:
                    valor = None

                def finalizar():
                    try:
                        btn_trm.state(["!disabled"])
                        var_trm.set(f"{valor:.2f}" if valor else "1.0")
                    except tk.TclError:
                        pass

                try:
                    self.root.after(0, finalizar)
                except Exception:
                    pass

            threading.Thread(target=tarea, daemon=True).start()

        entry_fecha.bind("<FocusOut>", traer_trm)
        entry_fecha.bind("<Return>", traer_trm)
        combo_cod.bind("<<ComboboxSelected>>", traer_trm, add="+")
        combo_cat.bind("<<ComboboxSelected>>", traer_trm, add="+")
        traer_trm()

        # Botones de acción
        barra_botones = tk.Frame(padre, bg=self.FONDO)
        barra_botones.pack(fill="x", pady=(14, 0))

        def confirmar_operacion():
            try:
                cat = var_cat.get()
                op = var_op.get()
                codigo = var_cod.get().strip().upper()
                nombre = var_nom.get().strip()
                fecha = var_fecha.get().strip()

                if not codigo:
                    raise ValueError("Debe ingresar o seleccionar un Código / Ticker.")
                if not nombre:
                    nombre = codigo

                try:
                    cantidad = float(var_cant.get().replace(",", "."))
                    if cantidad <= 0:
                        raise ValueError()
                except ValueError:
                    raise ValueError("La cantidad debe ser un número positivo.")

                try:
                    precio = float(var_precio.get().replace(",", "."))
                    if precio <= 0:
                        raise ValueError()
                except ValueError:
                    raise ValueError("El precio o monto en COP debe ser positivo.")

                try:
                    comision = float(var_com.get().replace(",", ".")) if var_com.get() else 0.0
                    if comision < 0:
                        raise ValueError()
                except ValueError:
                    raise ValueError("La comisión del bróker no puede ser negativa.")

                try:
                    trm_val = float(var_trm.get().replace(",", "."))
                    if trm_val <= 0:
                        trm_val = None
                except ValueError:
                    trm_val = None   # El portafolio la consulta automáticamente

                # Ejecutar según la categoría y operación
                if cat == "Renta Variable":
                    if op == "COMPRA":
                        self.portafolio.registrarCompraAccion(
                            codigo=codigo, nombre=nombre, fecha=fecha,
                            cantidad=int(cantidad), precio_cop=precio,
                            comision_cop=comision, trm=trm_val
                        )
                    elif op == "VENTA":
                        self.portafolio.registrarVentaAccion(
                            codigo=codigo, fecha=fecha,
                            cantidad=int(cantidad), precio_cop=precio,
                            comision_cop=comision, trm=trm_val
                        )
                    elif op == "DIVIDENDO":
                        self.portafolio.registrarDividendoAccion(
                            codigo=codigo, fecha=fecha, monto_cop=precio,
                            comision_cop=comision, trm=trm_val
                        )

                else: # Renta Fija
                    if op == "COMPRA / APERTURA":
                        subtipo = var_subtipo.get()
                        tasa_ea = float(var_tasa.get().replace(",", ".")) / 100.0
                        vencimiento = var_venc.get().strip()
                        mapa_frec = {"Anual (1)": 1, "Semestral (2)": 2, "Trimestral (4)": 4, "Mensual (12)": 12}
                        frec = mapa_frec.get(var_frec.get(), 2)

                        self.portafolio.registrarAperturaRentaFija(
                            codigo=codigo, nombre=nombre, subtipo=subtipo,
                            fecha_apertura=fecha, capital_cop=precio, tasa_ea=tasa_ea,
                            fecha_vencimiento=vencimiento, comision_cop=comision,
                            frecuencia_cupon=frec
                        )
                    elif op == "VENTA / LIQUIDACION":
                        self.portafolio.registrarVentaRentaFija(
                            codigo=codigo, fecha=fecha, valor_venta_cop=precio, comision_cop=comision
                        )
                    elif op == "RENDIMIENTO / CUPON":
                        self.portafolio.registrarRendimientoRentaFija(
                            codigo=codigo, fecha=fecha, monto_cop=precio, comision_cop=comision
                        )
                    elif op == "ABONO A CAPITAL":
                        self.portafolio.registrarAbonoCapitalRentaFija(
                            codigo=codigo, fecha=fecha, monto_cop=precio, comision_cop=comision
                        )

                # Guardar cambios y refrescar el dashboard en tiempo real
                self.portafolio.guardarPortafolio()
                self.actualizarVistaCompleta()

                messagebox.showinfo(
                    "Operación Exitosa",
                    f"Se registró exitosamente la operación de {op} para el activo {codigo}.\n"
                    f"El portafolio y los cálculos de rentabilidad han sido actualizados.",
                    parent=ventana
                )
                ventana.destroy()

            except Exception as exc:
                messagebox.showerror("Error en la Operación", str(exc), parent=ventana)

        ttk.Button(
            barra_botones,
            text="Confirmar Operación",
            command=confirmar_operacion
        ).pack(side="right", padx=(6, 0))

        ttk.Button(
            barra_botones,
            text="Cancelar",
            command=ventana.destroy
        ).pack(side="right")

    # --------------------------------------------------
    # VENTANA MODAL: HISTORIAL DE TRANSACCIONES
    # --------------------------------------------------
    def abrirVentanaHistorial(self):
        """Libro de transacciones en COP (11 columnas) con filtro por activo."""
        ventana = tk.Toplevel(self.root)
        ventana.title("Libro de Transacciones del Portafolio")
        ventana.configure(bg=self.FONDO)
        ventana.geometry("1240x540")
        ventana.minsize(960, 400)
        ventana.transient(self.root)

        padre = tk.Frame(ventana, bg=self.FONDO, padx=20, pady=16)
        padre.pack(fill="both", expand=True)

        tk.Label(
            padre, text="HISTORIAL DE TRANSACCIONES CONTABLES",
            bg=self.FONDO, fg=self.TEXTO, font=("Segoe UI", 15, "bold")
        ).pack(anchor="w", pady=(0, 2))

        tk.Label(
            padre,
            text="Movimientos de caja en COP: inventario, TRM histórica, dividendos, comisiones y saldo acumulado",
            bg=self.FONDO, fg=self.TEXTO_SECUNDARIO, font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(0, 10))

        # --- Filtro por activo ---
        barra_filtro = tk.Frame(padre, bg=self.FONDO)
        barra_filtro.pack(fill="x", pady=(0, 10))

        tk.Label(
            barra_filtro, text="Filtrar por activo:",
            bg=self.FONDO, fg=self.TEXTO, font=("Segoe UI", 9, "bold")
        ).pack(side="left", padx=(0, 8))

        codigos = ["TODOS"]
        for cod in [a.codigo for a in self.portafolio.activos] + \
                   [t.codigo_activo for t in self.portafolio.transacciones]:
            if cod not in codigos:
                codigos.append(cod)

        var_filtro = tk.StringVar(value="TODOS")
        combo_filtro = ttk.Combobox(
            barra_filtro, textvariable=var_filtro, values=codigos,
            state="readonly", width=22
        )
        combo_filtro.pack(side="left")

        # --- Tabla ---
        marco_tabla = tk.Frame(padre, bg=self.PANEL)
        marco_tabla.pack(fill="both", expand=True)

        columnas = ("fecha", "acciones", "valor_cop", "compra", "venta", "trm",
                    "dividendo_cop", "pago", "comision", "saldo", "total")
        tabla = ttk.Treeview(marco_tabla, columns=columnas, show="headings")

        encabezados = {
            "fecha": "Fecha", "acciones": "Acciones", "valor_cop": "Valor COP",
            "compra": "Compra", "venta": "Venta", "trm": "TRM",
            "dividendo_cop": "Dividendo COP", "pago": "Pago",
            "comision": "Comisión", "saldo": "Saldo", "total": "Total"
        }
        anchos = {
            "fecha": 90, "acciones": 80, "valor_cop": 105, "compra": 70, "venta": 70,
            "trm": 85, "dividendo_cop": 110, "pago": 105, "comision": 95,
            "saldo": 125, "total": 120
        }
        for c in columnas:
            tabla.heading(c, text=encabezados[c])
            tabla.column(c, width=anchos[c], anchor="w" if c == "fecha" else "e")

        tabla.tag_configure("saldo_pos", foreground=self.VERDE)
        tabla.tag_configure("saldo_neg", foreground=self.ROJO)

        scroll_y = ttk.Scrollbar(marco_tabla, orient="vertical", command=tabla.yview)
        scroll_x = ttk.Scrollbar(marco_tabla, orient="horizontal", command=tabla.xview)
        tabla.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        tabla.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        marco_tabla.grid_rowconfigure(0, weight=1)
        marco_tabla.grid_columnconfigure(0, weight=1)

        # --- Pie de resumen ---
        pie = tk.Frame(padre, bg=self.FONDO)
        pie.pack(fill="x", pady=(10, 0))

        var_pie = tk.StringVar()
        tk.Label(
            pie, textvariable=var_pie, bg=self.FONDO, fg=self.TEXTO_SECUNDARIO,
            font=("Segoe UI", 9, "bold")
        ).pack(side="left")
        ttk.Button(pie, text="Cerrar", command=ventana.destroy).pack(side="right")

        def dec(valor, decimales=2):
            return (f"{float(valor):,.{decimales}f}"
                    .replace(",", "X").replace(".", ",").replace("X", "."))

        def cantidad_txt(valor):
            if isinstance(valor, str):
                return valor
            return str(int(valor)) if float(valor).is_integer() else dec(valor)

        def cargar_tabla(evento=None):
            filtro = var_filtro.get()
            tabla.delete(*tabla.get_children())
            filas = self.portafolio.obtenerLibroTransaccionesDetallado(filtro)

            total_comisiones = 0.0
            total_pagos = 0.0
            for f in filas:
                total_comisiones += f["comision"]
                total_pagos += f["pago"]
                tabla.insert("", "end", tags=("saldo_neg" if f["saldo"] < 0 else "saldo_pos",), values=(
                    f["fecha"],
                    cantidad_txt(f["acciones"]),
                    self.formatoCOP(f["valor_cop"]),
                    cantidad_txt(f["compra"]),
                    cantidad_txt(f["venta"]),
                    dec(f["trm"]),
                    self.formatoCOP(f["dividendo_cop"]),
                    self.formatoCOP(f["pago"]),
                    self.formatoCOP(f["comision"]),
                    self.formatoCOP(f["saldo"]),
                    self.formatoCOP(f["total"])
                ))

            saldo_final = filas[-1]["saldo"] if filas else 0.0
            texto = (
                f"Activo: {filtro}  |  Movimientos: {len(filas)}  |  "
                f"Comisiones: {self.formatoCOP(total_comisiones)}  |  "
                f"Pagos recibidos: {self.formatoCOP(total_pagos)}  |  "
                f"Saldo final: {self.formatoCOP(saldo_final)}"
            )
            if filtro != "TODOS" and filas and not isinstance(filas[-1]["acciones"], str):
                texto += f"  |  Acciones vigentes: {cantidad_txt(filas[-1]['acciones'])}"
            var_pie.set(texto)

        combo_filtro.bind("<<ComboboxSelected>>", cargar_tabla)
        cargar_tabla()

