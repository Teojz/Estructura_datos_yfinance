import os
import sys

from src.servicio_mercado import ServicioMercado
from src.portafolio import Portafolio
from src.accion import Accion
from src.renta_fija import InstrumentoRentaFija
from src.transaccion import Transaccion
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


def inicializarPortafolioSemilla(portafolio: Portafolio) -> None:
    """
    Crea un portafolio inicial de muestra con activos de
    renta variable y renta fija expresados en COP.
    La comisión de corretaje de acciones usa Portafolio.COMISION_ESTANDAR (0,21 %).
    """

    def comision(cantidad: float, precio_cop: float) -> float:
        """Comisión estándar sobre el valor bruto de la operación."""
        return round(cantidad * precio_cop * Portafolio.COMISION_ESTANDAR, 2)

    # 1. Bancolombia Preferencial
    bcolom = Accion("PFBCOLOM.CL", "Bancolombia Preferencial", "2025-05-10")
    bcolom.registrarCompra(120, 32500.0, comision(120, 32500.0))
    bcolom.registrarVenta(20, 35800.0, comision(20, 35800.0))
    bcolom.registrarDividendo(356000.0)
    portafolio.agregarActivo(bcolom)

    # 2. Ecopetrol
    ecopetrol = Accion("ECOPETROL.CL", "Ecopetrol S.A.", "2025-06-15")
    ecopetrol.registrarCompra(1500, 2150.0, comision(1500, 2150.0))
    ecopetrol.registrarDividendo(280000.0)
    portafolio.agregarActivo(ecopetrol)

    # 3. Apple
    apple = Accion("AAPL", "Apple Inc. (USD -> COP)", "2025-04-01")
    apple.registrarCompra(5, 820000.0, comision(5, 820000.0))
    apple.registrarVenta(1, 910000.0, comision(1, 910000.0))
    apple.registrarDividendo(22000.0)
    portafolio.agregarActivo(apple)

    # 4. CDT Bancolombia
    cdt = InstrumentoRentaFija(
        codigo="CDT-BANC-01",
        nombre="CDT Digital Bancolombia 360 Dias",
        subtipo="CDT",
        fecha_apertura="2025-05-01",
        valor_invertido_cop=5000000.0,
        tasa_ea=0.1125,
        plazo_dias=360,
        fecha_vencimiento="2026-04-26",
        comision_cop=0.0
    )
    portafolio.agregarActivo(cdt)

    # 5. TES Colombia
    tes = InstrumentoRentaFija(
        codigo="TES-COL-2028",
        nombre="TES Tasa Fija Nación 2028",
        subtipo="TES",
        fecha_apertura="2025-03-15",
        valor_invertido_cop=4000000.0,
        tasa_ea=0.104,
        plazo_dias=730,
        fecha_vencimiento="2027-03-15",
        comision_cop=10000.0,
        valor_nominal=4000000.0,
        tasa_cupon_ea=0.104,
        frecuencia_cupon=2
    )
    tes.registrarPagoRendimiento(monto_cop=208000.0, fecha="2025-09-15")
    portafolio.agregarActivo(tes)

    # 6. Nike
    nike = Accion("NKE", "Nike Inc. (USD -> COP)", "2025-07-01")
    nike.registrarCompra(10, 280000.0, comision(10, 280000.0))
    nike.registrarDividendo(18000.0)
    portafolio.agregarActivo(nike)

    # 7. Coca-Cola
    coca = Accion("KO", "The Coca-Cola Company (USD -> COP)", "2025-07-10")
    coca.registrarCompra(15, 270000.0, comision(15, 270000.0))
    coca.registrarDividendo(25000.0)
    portafolio.agregarActivo(coca)

    # Registro de transacciones históricas (misma comisión estándar que los activos)
    transacciones = [
        Transaccion("2025-05-10", "COMPRA", "PFBCOLOM.CL", 120, 32500.0, comision(120, 32500.0)),
        Transaccion("2025-08-20", "VENTA", "PFBCOLOM.CL", 20, 35800.0, comision(20, 35800.0)),
        Transaccion("2025-10-01", "DIVIDENDO", "PFBCOLOM.CL", 1, 356000.0, 0.0),
        Transaccion("2025-05-01", "COMPRA", "CDT-BANC-01", 1, 5000000.0, 0.0),
        Transaccion("2025-03-15", "COMPRA", "TES-COL-2028", 1, 4000000.0, 10000.0),
        Transaccion("2025-07-01", "COMPRA", "NKE", 10, 280000.0, comision(10, 280000.0)),
        Transaccion("2025-07-10", "COMPRA", "KO", 15, 270000.0, comision(15, 270000.0)),
    ]

    for transaccion in transacciones:
        portafolio.registrarTransaccion(transaccion)

def main():
    """Inicializa el sistema y abre el dashboard interactivo."""
    base_dir = obtener_ruta_proyecto()
    print("Iniciando Sistema de Portafolio de Inversión (Bancolombia COP)...")
    servicio = ServicioMercado()

    portafolio = Portafolio(
        "Fondo de Inversión Consolidado - Bancolombia COP",
        servicio
    )

    ruta_datos = os.path.join(base_dir, "data", "portafolio_bancolombia.json")
    cargado = portafolio.cargarPortafolio(ruta_datos)

    if not cargado or len(portafolio.activos) == 0:
        print("Inicializando portafolio con datos semilla...")
        inicializarPortafolioSemilla(portafolio)
        portafolio.guardarPortafolio(ruta_datos)
    else:
        print(f"Portafolio cargado con {len(portafolio.activos)} activos desde {ruta_datos}.")

        # Completa la TRM histórica exacta en transacciones antiguas de NKE, KO, AAPL, etc.
    if portafolio.completarTRMHistoricas() > 0:
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
