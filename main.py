from src.servicio_mercado import ServicioMercado          # Conector con Yahoo Finance (yfinance)
from src.portafolio import Portafolio                     # Motor financiero del portafolio
from src.accion import Accion                             # Modelo de Renta Variable
from src.renta_fija import InstrumentoRentaFija           # Modelo de Renta Fija (CDT, Bonos, TES)
from src.transaccion import Transaccion                   # Registro contable de operaciones
from src.interfaz_portafolio import InterfazPortafolioGUI # Dashboard visual estilo Bancolombia


def inicializarPortafolioSemilla(portafolio: Portafolio) -> None:
    """
    Crea un portafolio inicial de muestra inspirado en productos de Bancolombia y la BVC
    en Pesos Colombianos (COP) si aun no existe el archivo JSON guardado.
    """
    # 1. Accion Preferencial Bancolombia (BVC - Renta Variable en COP)
    bcolom = Accion("PFBCOLOM.CL", "Bancolombia Preferencial", "2025-05-10")
    bcolom.registrarCompra(cantidad=120, precio_cop=32500.0, comision_cop=15000.0) # Compra 120 acciones
    bcolom.registrarVenta(cantidad=20, precio_cop=35800.0, comision_cop=8000.0)    # Vende 20 acciones
    bcolom.registrarDividendo(monto_cop=356000.0)                                  # Dividendos recibidos
    portafolio.agregarActivo(bcolom)

    # 2. Ecopetrol S.A. (BVC - Renta Variable en COP)
    ecopetrol = Accion("ECOPETROL.CL", "Ecopetrol S.A.", "2025-06-15")
    ecopetrol.registrarCompra(cantidad=1500, precio_cop=2150.0, comision_cop=12000.0)
    ecopetrol.registrarDividendo(monto_cop=280000.0)
    portafolio.agregarActivo(ecopetrol)

    # 3. Apple Inc. (NYSE - Convertida automaticamente a COP con yfinance)
    apple = Accion("AAPL", "Apple Inc. (USD -> COP)", "2025-04-01")
    apple.registrarCompra(cantidad=5, precio_cop=820000.0, comision_cop=18000.0)
    apple.registrarVenta(cantidad=1, precio_cop=910000.0, comision_cop=9000.0)
    apple.registrarDividendo(monto_cop=22000.0)
    portafolio.agregarActivo(apple)

    # 4. CDT Bancolombia Tasa Fija (Renta Fija en COP)
    cdt = InstrumentoRentaFija(
        codigo="CDT-BANC-01",
        nombre="CDT Digital Bancolombia 360 Dias",
        subtipo="CDT",
        fecha_apertura="2025-05-01",
        valor_invertido_cop=5000000.0,
        tasa_ea=11.25,
        plazo_dias=360,
        fecha_vencimiento="2026-04-26",
        comision_cop=0.0
    )
    portafolio.agregarActivo(cdt)

    # 5. Titulo de Deuda Publica TES Colombia (Renta Fija en COP)
    tes = InstrumentoRentaFija(
        codigo="TES-COL-2028",
        nombre="TES Tasa Fija Nación 2028",
        subtipo="TES",
        fecha_apertura="2025-03-15",
        valor_invertido_cop=4000000.0,
        tasa_ea=10.40,
        plazo_dias=730,
        fecha_vencimiento="2027-03-15",
        comision_cop=10000.0
    )
    tes.registrarPagoRendimiento(208000.0) # Pago de cupon semestral recibido
    portafolio.agregarActivo(tes)

    # Registra las transacciones iniciales en el libro contable
    portafolio.registrarTransaccion(Transaccion("2025-05-10", "COMPRA", "PFBCOLOM.CL", 120, 32500.0, 15000.0))
    portafolio.registrarTransaccion(Transaccion("2025-08-20", "VENTA", "PFBCOLOM.CL", 20, 35800.0, 8000.0))
    portafolio.registrarTransaccion(Transaccion("2025-10-01", "DIVIDENDO", "PFBCOLOM.CL", 1, 356000.0, 0.0))
    portafolio.registrarTransaccion(Transaccion("2025-05-01", "COMPRA", "CDT-BANC-01", 1, 5000000.0, 0.0))
    portafolio.registrarTransaccion(Transaccion("2025-03-15", "COMPRA", "TES-COL-2028", 1, 4000000.0, 10000.0))

    portafolio.guardarPortafolio("data/portafolio_bancolombia.json")


def main():
    """Funcion principal que articula los servicios, el portafolio y el Dashboard visual."""
    servicio = ServicioMercado()
    portafolio = Portafolio("Fondo de Inversión Consolidado - Bancolombia COP", servicio)

    # Si no hay archivo previo, carga el portafolio semilla de muestra
    if not portafolio.cargarPortafolio("data/portafolio_bancolombia.json"):
        inicializarPortafolioSemilla(portafolio)

    # Actualiza precios y EPS desde Yahoo Finance al arrancar
    portafolio.actualizarValoracionMercado()

    # Inicia la interfaz grafica (GUI)
    app = InterfazPortafolioGUI(portafolio)
    app.iniciarDashboard()


if __name__ == "__main__":
    main()