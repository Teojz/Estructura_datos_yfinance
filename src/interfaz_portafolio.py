
"""
PROYECTO: Sistema de Seguimiento y Valoración de Portafolio
MÓDULO: interfaz_portafolio.py

Interfaz gráfica desarrollada con Tkinter y Matplotlib.
Visualiza inversiones de renta fija y renta variable
en pesos colombianos (COP).
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox

import pandas as pd

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.dates import AutoDateLocator, ConciseDateFormatter

from src.accion import Accion
from src.renta_fija import InstrumentoRentaFija


class InterfazPortafolioGUI:
    """Dashboard principal del sistema de seguimiento y valoración."""

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

    # FORMATO DE VALORES

    @staticmethod
    def formatearCOP(valor):
        return "$" + f"{float(valor):,.0f}".replace(",", ".")

    @staticmethod
    def formatearPorcentaje(valor):
        return (
            f"{float(valor):,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
            + "%"
        )

    # CÁLCULO DE INDICADORES

    def obtenerResumen(self):
        capital_total = 0.0
        valor_total = 0.0
        comisiones_totales = 0.0
        dias_ponderados = 0.0

        valor_renta_variable = 0.0
        valor_renta_fija = 0.0

        dividendos = 0.0
        rendimientos = 0.0

        for activo in self.portafolio.activos:
            capital = activo.calcularCapitalInvertidoCOP()
            valor = activo.calcularValorActualCOP()
            comision = activo.comision_total_cop
            dias = activo.calcularDiasTenencia()

            capital_total += capital
            valor_total += valor
            comisiones_totales += comision
            dias_ponderados += capital * dias

            if isinstance(activo, Accion):
                valor_renta_variable += valor
                dividendos += activo.dividendos_recibidos_cop

            elif isinstance(activo, InstrumentoRentaFija):
                valor_renta_fija += valor
                rendimientos += activo.rendimientos_recibidos

        ganancia = valor_total - capital_total

        rentabilidad = (
            ganancia / capital_total * 100
            if capital_total > 0 else 0.0
        )

        # Rentabilidad E.A. estimada mediante días de tenencia ponderados.
        dias_promedio = (
            max(dias_ponderados / capital_total, 1.0)
            if capital_total > 0 else 1.0
        )

        if capital_total > 0 and valor_total > 0:
            exponente = min(365.0 / dias_promedio, 12.0)
            rentabilidad_ea = (
                (valor_total / capital_total) ** exponente - 1
            ) * 100
        else:
            rentabilidad_ea = 0.0

        total_distribucion = valor_renta_variable + valor_renta_fija

        porcentaje_rv = (
            valor_renta_variable / total_distribucion * 100
            if total_distribucion > 0 else 0.0
        )

        porcentaje_rf = (
            valor_renta_fija / total_distribucion * 100
            if total_distribucion > 0 else 0.0
        )

        return {
            "capital_invertido": capital_total,
            "valor_actual": valor_total,
            "comisiones": comisiones_totales,
            "ganancia": ganancia,
            "rentabilidad": rentabilidad,
            "rentabilidad_ea": rentabilidad_ea,
            "renta_variable": valor_renta_variable,
            "renta_fija": valor_renta_fija,
            "porcentaje_rv": porcentaje_rv,
            "porcentaje_rf": porcentaje_rf,
            "dividendos": dividendos,
            "rendimientos": rendimientos,
            "estado": (
                "VALORIZADO" if ganancia >= 0 else "DESVALORIZADO"
            )
        }

    # INICIAR APLICACIÓN

    def iniciarDashboard(self):
        self.root = tk.Tk()
        self.root.title(
            "Sistema de Seguimiento y Valoración de Portafolio"
        )
        self.root.minsize(1100, 700)
        self.root.configure(bg=self.FONDO)

        try:
            self.root.state("zoomed")
        except tk.TclError:
            ancho = self.root.winfo_screenwidth()
            alto = self.root.winfo_screenheight()
            self.root.geometry(
                f"{min(1450, ancho)}x{min(900, alto)}"
            )

        self.var_accion = tk.StringVar(master=self.root)
        self.var_filtro = tk.StringVar(
            master=self.root, value="1A"
        )
        self.var_estado = tk.StringVar(
            master=self.root, value="Sistema listo"
        )

        self.configurarEstilos()
        self.crearEncabezado()
        self.crearIndicadores()
        self.crearContenido()
        self.actualizarDashboard()

        self.root.mainloop()

    # ESTILOS

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

    # ENCABEZADO

    def crearEncabezado(self):
        encabezado = tk.Frame(self.root, bg=self.FONDO)
        encabezado.pack(
            fill="x", padx=22, pady=(18, 14)
        )

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
                "· Valores expresados en COP"
            ),
            bg=self.FONDO,
            fg=self.TEXTO_SECUNDARIO,
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(4, 0))

        ttk.Button(
            encabezado,
            text="Actualizar cotizaciones",
            command=self.actualizarMercado
        ).pack(side="right")

    # TARJETAS DE INDICADORES

    def crearIndicadores(self):
        contenedor = tk.Frame(self.root, bg=self.FONDO)
        contenedor.pack(
            fill="x", padx=22, pady=(0, 14)
        )

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

    # CONTENIDO PRINCIPAL

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

    # GRÁFICA HISTÓRICA

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

    def dibujarSerieHistorica(self):
        if self.ax_precios is None:
            return

        self.ax_precios.clear()
        self.estilizarGrafica(self.ax_precios)

        ticker = self.var_accion.get().strip()
        filtro = self.var_filtro.get()

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
                raise ValueError(
                    "No hay datos históricos disponibles."
                )

            if "Precio_COP" not in serie.columns:
                raise ValueError(
                    "No existe la columna Precio_COP."
                )

            precios = pd.to_numeric(
                serie["Precio_COP"],
                errors="coerce"
            ).dropna()

            if precios.empty:
                raise ValueError(
                    "No se encontraron precios válidos."
                )

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

            self.ax_precios.set_title(
                f"{ticker} | {filtro}",
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

                self.ax_precios.xaxis.set_major_locator(
                    localizador
                )

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

    # TABLA DE INVERSIONES

    def crearTablaActivos(self, padre):
        tk.Label(
            padre,
            text="Detalle de inversiones",
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
                tipo = activo.tipo_renta
                unidades = "—"

            self.tabla_activos.insert(
                "",
                "end",
                values=(
                    activo.codigo,
                    activo.nombre,
                    tipo,
                    unidades,
                    self.formatearCOP(capital),
                    self.formatearCOP(valor),
                    self.formatearPorcentaje(rentabilidad)
                )
            )

    # DISTRIBUCIÓN DEL PORTAFOLIO

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

        self.canvas_distribucion.get_tk_widget().pack(
            fill="x"
        )

    def actualizarDistribucion(self, resumen):
        self.ax_distribucion.clear()

        valores = [
            resumen["renta_variable"],
            resumen["renta_fija"]
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

    # RESUMEN LATERAL

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

        self.lbl_estado_valoracion.pack(
            anchor="w",
            pady=(10, 4)
        )

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

    # ACTUALIZAR LISTA DE ACCIONES

    def actualizarListaAcciones(self):
        codigos = [
            activo.codigo
            for activo in self.portafolio.activos
            if isinstance(activo, Accion)
        ]

        seleccion = self.var_accion.get()
        self.combo_acciones["values"] = codigos

        if seleccion in codigos:
            self.var_accion.set(seleccion)
        else:
            self.var_accion.set(
                codigos[0] if codigos else ""
            )

    # ACTUALIZAR TODO EL DASHBOARD

    def actualizarDashboard(self):
        resumen = self.obtenerResumen()

        for clave, (etiqueta, formato) in self.tarjetas.items():
            valor = resumen[clave]

            if formato == "cop":
                texto = self.formatearCOP(valor)
            else:
                texto = self.formatearPorcentaje(valor)

            etiqueta.config(text=texto)

        color = (
            self.VERDE
            if resumen["ganancia"] >= 0
            else self.ROJO
        )

        self.tarjetas["rentabilidad"][0].config(fg=color)
        self.tarjetas["rentabilidad_ea"][0].config(fg=color)

        self.lbl_ganancia.config(
            text=(
                "Ganancia / pérdida: "
                + self.formatearCOP(resumen["ganancia"])
            ),
            fg=color
        )

        self.lbl_renta_variable.config(
            text=(
                "Renta variable: "
                + self.formatearCOP(resumen["renta_variable"])
                + " ("
                + self.formatearPorcentaje(resumen["porcentaje_rv"])
                + ")"
            )
        )

        self.lbl_renta_fija.config(
            text=(
                "Renta fija: "
                + self.formatearCOP(resumen["renta_fija"])
                + " ("
                + self.formatearPorcentaje(resumen["porcentaje_rf"])
                + ")"
            )
        )

        self.lbl_estado_valoracion.config(
            text=resumen["estado"]
        )

        self.actualizarTablaActivos()
        self.actualizarDistribucion(resumen)
        self.actualizarListaAcciones()
        self.dibujarSerieHistorica()

    # ESTILO DE GRÁFICAS

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

    # ACTUALIZAR PRECIOS DE MERCADO

    def actualizarMercado(self):
        if self.actualizacion_en_curso:
            return

        self.actualizacion_en_curso = True

        self.var_estado.set(
            "Actualizando cotizaciones de mercado..."
        )

        def tarea():
            error = None

            try:
                self.portafolio.actualizarValoracionMercado()
            except Exception as exc:
                error = exc

            self.root.after(
                0,
                lambda: finalizar(error)
            )

        def finalizar(error):
            self.actualizacion_en_curso = False

            if error is not None:
                self.var_estado.set(
                    "Error al actualizar cotizaciones."
                )

                messagebox.showerror(
                    "Error de mercado",
                    str(error),
                    parent=self.root
                )

            else:
                self.var_estado.set(
                    "Cotizaciones actualizadas correctamente."
                )

                self.actualizarDashboard()

        threading.Thread(
            target=tarea,
            daemon=True
        ).start()
