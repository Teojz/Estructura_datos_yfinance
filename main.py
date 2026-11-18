import os
import sys

from src.servicio_mercado import ServicioMercado
from src.portafolio import Portafolio
from src.interfaz_portafolio import InterfazPortafolioGUI


def obtener_ruta_proyecto() -> str:
    """Retorna la ruta absoluta base del proyecto (compatible con ejecutable congelado o script)."""
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass and os.path.exists(os.path.join(meipass, "data", "portafolio_bancolombia.json")):
            return meipass
        exe_dir = os.path.dirname(sys.executable)
        if os.path.exists(os.path.join(exe_dir, "data", "portafolio_bancolombia.json")):
            return exe_dir
        return exe_dir
    return os.path.dirname(os.path.abspath(__file__))


def solicitarCapitalInicial() -> float:
    """
    Pide por ventana el valor total inicial del portafolio en COP.
    Acepta formatos como 10000000, 10.000.000 o $10.000.000 (punto = miles, coma = decimales).
    Retorna 0.0 si el usuario cancela.
    """
    import tkinter as tk
    from tkinter import simpledialog, messagebox

    raiz = tk.Tk()
    raiz.withdraw()
    raiz.attributes("-topmost", True)
    try:
        while True:
            texto = simpledialog.askstring(
                "Capital inicial del portafolio",
                "Ingrese el valor total inicial del portafolio en COP:\n(ejemplo: 10.000.000)",
                parent=raiz
            )
            if texto is None:
                return 0.0
            limpio = texto.replace("$", "").replace(" ", "").replace(".", "").replace(",", ".")
            try:
                valor = float(limpio)
                if valor <= 0:
                    raise ValueError()
                return valor
            except ValueError:
                messagebox.showerror(
                    "Valor inválido",
                    "Ingrese un número positivo, por ejemplo 10.000.000.",
                    parent=raiz
                )
    finally:
        raiz.destroy()


def main():
    """Inicializa el sistema, solicita el capital inicial si aplica y abre el dashboard."""
    base_dir = obtener_ruta_proyecto()
    print("Iniciando Sistema de Portafolio de Inversión (Bancolombia COP)...")
    servicio = ServicioMercado()

    portafolio = Portafolio(
        "Fondo de Inversión Consolidado - Bancolombia COP",
        servicio
    )

    REINICIAR_HISTORIAL = True   # Ejecutar una vez para empezar de cero; luego cambiar a False

    ruta_datos = os.path.join(base_dir, "data", "portafolio_bancolombia.json")

    if REINICIAR_HISTORIAL:
        print("Portafolio iniciado en cero (sin activos ni transacciones).")
    elif portafolio.cargarPortafolio(ruta_datos):
        print(f"Portafolio cargado con {len(portafolio.activos)} activos desde {ruta_datos}.")
        if portafolio.completarTRMHistoricas() > 0:
            portafolio.guardarPortafolio(ruta_datos)
    else:
        print("Portafolio nuevo y vacío.")

    # Solicita el capital inicial si aún no está definido
    if portafolio.capital_inicial_cop <= 0:
        capital = solicitarCapitalInicial()
        if capital <= 0:
            print("No se ingresó un capital inicial. Cerrando el sistema.")
            return
        portafolio.establecerCapitalInicial(capital)

    portafolio.guardarPortafolio(ruta_datos)

    # Actualiza la valoración de las acciones
    print("Consultando cotizaciones de mercado y TRM...")
    portafolio.actualizarValoracionMercado()

    # Abre la interfaz gráfica
    print("Abriendo dashboard gráfico...")
    app = InterfazPortafolioGUI(portafolio)
    app.iniciarDashboard()


if __name__ == "__main__":
    main()