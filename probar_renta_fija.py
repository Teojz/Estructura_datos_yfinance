
from src.renta_fija import InstrumentoRentaFija

print("\n========== PRUEBA DE RENTA FIJA ==========")

cdt = InstrumentoRentaFija(
    codigo="CDT001",
    nombre="CDT Bancolombia",
    tipo="CDT",
    capital_invertido=10_000_000,
    tasa_ea=0.105,
    fecha_apertura="2026-01-01",
    fecha_vencimiento="2027-01-01",
    comision_cop=20_000
)

bono = InstrumentoRentaFija(
    codigo="BONO001",
    nombre="Bono Corporativo",
    tipo="BONO",
    capital_invertido=5_000_000,
    tasa_ea=0.09,
    tasa_cupon_ea=0.09,
    frecuencia_cupon=2,
    fecha_apertura="2026-01-01",
    fecha_vencimiento="2028-01-01",
    valor_nominal=5_000_000,
    comision_cop=15_000,
    precio_mercado_por_100=98.50
)

tes = InstrumentoRentaFija(
    codigo="TES001",
    nombre="TES Gobierno Nacional",
    tipo="TES",
    capital_invertido=8_000_000,
    tasa_ea=0.08,
    tasa_cupon_ea=0.08,
    frecuencia_cupon=2,
    fecha_apertura="2026-01-01",
    fecha_vencimiento="2029-01-01",
    valor_nominal=8_000_000,
    comision_cop=25_000,
    precio_mercado_por_100=102.30
)

instrumentos = [cdt, bono, tes]

for instrumento in instrumentos:
    print("\n------------------------------------")
    print(instrumento)
    print("Capital invertido:", instrumento.calcularCapitalInvertidoCOP())
    print("Intereses generados:", instrumento.calcularInteresesGenerados())
    print("Valor actual:", instrumento.calcularValorActualCOP())
    print("Ganancia neta:", instrumento.calcularGananciaNetaCOP())
    print(
        "Rentabilidad acumulada:",
        instrumento.calcularRentabilidadAcumulada(), "%"
    )
    print("Rentabilidad E.A.:", instrumento.calcularRentabilidadEA(), "%")

bono.registrarRendimiento(valor=225_000, concepto="Cupón recibido")
tes.registrarAbonoCapital(valor=500_000)

print("\n========== MOVIMIENTOS ==========")
print("Cupón del bono:", bono.rendimientos_recibidos)
print("Capital pendiente del TES:", tes.calcularCapitalPendienteCOP())

print("\n========== PRUEBA FINALIZADA ==========")
