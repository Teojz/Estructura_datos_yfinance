
from src.servicio_mercado import ServicioMercado
from src.portafolio import Portafolio
from src.accion import Accion
from src.renta_fija import InstrumentoRentaFija
from src.transaccion import Transaccion
from src.interfaz_portafolio import InterfazPortafolioGUI


def inicializarPortafolioSemilla(portafolio: Portafolio) -> None:
    """
    Crea un portafolio inicial de muestra con activos de
    renta variable y renta fija expresados en COP.
    """

    # 1. Bancolombia Preferencial
    bcolom = Accion(
        "PFBCOLOM.CL",
        "Bancolombia Preferencial",
        "2025-05-10"
    )

    bcolom.registrarCompra(120, 32500.0, 15000.0)
    bcolom.registrarVenta(20, 35800.0, 8000.0)
    bcolom.registrarDividendo(356000.0)

    portafolio.agregarActivo(bcolom)

    # 2. Ecopetrol
    ecopetrol = Accion(
        "ECOPETROL.CL",
        "Ecopetrol S.A.",
        "2025-06-15"
    )

    ecopetrol.registrarCompra(1500, 2150.0, 12000.0)
    ecopetrol.registrarDividendo(280000.0)

    portafolio.agregarActivo(ecopetrol)

    # 3. Apple
    apple = Accion(
        "AAPL",
        "Apple Inc. (USD -> COP)",
        "2025-04-01"
    )

    apple.registrarCompra(5, 820000.0, 18000.0)
    apple.registrarVenta(1, 910000.0, 9000.0)
    apple.registrarDividendo(22000.0)

    portafolio.agregarActivo(apple)

    # 4. CDT Bancolombia
    cdt = InstrumentoRentaFija(
        codigo="CDT-BANC-01",
        nombre="CDT Digital Bancolombia 360 Dias",
        tipo="CDT",
        capital_invertido=5000000.0,
        tasa_ea=0.1125,
        fecha_apertura="2025-05-01",
        fecha_vencimiento="2026-04-26",
        comision_cop=0.0
    )

    portafolio.agregarActivo(cdt)

    # 5. TES Colombia
    tes = InstrumentoRentaFija(
        codigo="TES-COL-2028",
        nombre="TES Tasa Fija Nación 2028",
        tipo="TES",
        capital_invertido=4000000.0,
        tasa_ea=0.104,
        fecha_apertura="2025-03-15",
        fecha_vencimiento="2027-03-15",
        comision_cop=10000.0,
        valor_nominal=4000000.0,
        tasa_cupon_ea=0.104,
        frecuencia_cupon=2
    )

    tes.registrarRendimiento(
        valor=208000.0,
        fecha="2025-09-15",
        concepto="Cupón semestral recibido"
    )

    portafolio.agregarActivo(tes)

    # Registro de transacciones
    transacciones = [
        Transaccion(
            "2025-05-10", "COMPRA",
            "PFBCOLOM.CL", 120, 32500.0, 15000.0
        ),
        Transaccion(
            "2025-08-20", "VENTA",
            "PFBCOLOM.CL", 20, 35800.0, 8000.0
        ),
        Transaccion(
            "2025-10-01", "DIVIDENDO",
            "PFBCOLOM.CL", 1, 356000.0, 0.0
        ),
        Transaccion(
            "2025-05-01", "COMPRA",
            "CDT-BANC-01", 1, 5000000.0, 0.0
        ),
        Transaccion(
            "2025-03-15", "COMPRA",
            "TES-COL-2028", 1, 4000000.0, 10000.0
        )
    ]

    for transaccion in transacciones:
        portafolio.registrarTransaccion(transaccion)


def main():
    """Inicializa el sistema y abre el dashboard."""

    servicio = ServicioMercado()

    portafolio = Portafolio(
        "Fondo de Inversión Consolidado - Bancolombia COP",
        servicio
    )

    # Inicializa los datos de muestra
    inicializarPortafolioSemilla(portafolio)

    # Actualiza la valoración de las acciones
    portafolio.actualizarValoracionMercado()

    # Abre la interfaz gráfica
    app = InterfazPortafolioGUI(portafolio)
    app.iniciarDashboard()


if __name__ == "__main__":
    main()
