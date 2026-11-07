# Estructura_datos_yfinance
# Sistema de Seguimiento y Valoración de Portafolio de Inversión (Python & yfinance)

Proyecto desarrollado en **Python** bajo el paradigma de Programación Orientada a Objetos (POO) para el monitoreo contable, valoración en tiempo real y cálculo de rentabilidades de un portafolio mixto (**Renta Variable** y **Renta Fija**) expresado en **Pesos Colombianos (COP)**, inspirado en los informes de rentabilidad de Fondos de Inversión Colectiva (FIC) de Bancolombia.

## Descripción del Proyecto
El sistema permite administrar la contabilidad de un conjunto de inversiones registrando operaciones de compra, venta, cobro de dividendos, pago de cupones/intereses y comisiones de bróker, evaluando en todo momento si cada activo y el portafolio consolidado se valorizaron o se desvalorizaron:

1. **Activos de Renta Variable (Acciones con `yfinance`):**
   - Control de inventario de títulos: cantidad de acciones compradas, cantidad de acciones vendidas, posición actual en tenencia y ganancias realizadas/no realizadas.
   - Integración en vivo con la API de Yahoo Finance (`yfinance`) para consultar precios de mercado, **EPS (Utilidad por Acción)** y conversión automática de divisas a **Pesos Colombianos (COP)** mediante la TRM en tiempo real (`USDCOP=X`).
   - Registro y contabilización de dividendos pagados por las empresas emisoras.
2. **Activos de Renta Fija (CDT, Bonos y TES):**
   - Valoración contractual considerando capital invertido, plazo en días, fecha de apertura, fecha de vencimiento, tasa Efectiva Anual (E.A.) pactada y rendimientos o pagos de capital recibidos.
3. **Series de Tiempo e Interfaz Gráfica (Dashboard):**
   - Visualización interactiva del comportamiento histórico de cualquier acción con filtros de temporalidad: **1 Día (`1D`), 1 Semana (`1S`), 1 Mes (`1M`), 6 Meses (`6M`), 1 Año (`1A`) y 5 Años (`5A`)**.
   - Tablero consolidado con Valor Total Invertido, Valor Actual en COP, Comisiones Totales, Rentabilidad Acumulada (%), Rentabilidad Efectiva Anual (E.A. %) y distribución porcentual entre Renta Fija y Renta Variable.

## Diagrama de Clases UML
<img width="1317" height="1047" alt="Diagrama_UML" src="https://github.com/user-attachments/assets/cb06b9c7-52c0-46a5-8a1e-772ab24092d9" />

## Modelo Matemático y Financiero
- **Rentabilidad Acumulada ($R_{\text{acum}}$):**
  $$R_{\text{acum}} = \left( \frac{\text{Valor Actual + Rendimientos/Dividendos - Comisiones} - \text{Capital Invertido}}{\text{Capital Invertido}} \right) \times 100$$
- **Rentabilidad Efectiva Anual ($E.A.$ - Estándar FIC Bancolombia):**
  $$E.A. = \left[ \left( 1 + \frac{R_{\text{acum}}}{100} \right)^{\frac{365}{\text{Días Transcurridos}}} - 1 \right] \times 100$$

## Arquitectura Modular (Una Clase por Archivo)
- `src/activo.py`: Clase abstracta `Activo` con la estructura común e interfaz de valoración.
- `src/accion.py`: Clase `Accion` para renta variable, control de unidades compradas/vendidas, dividendos y EPS.
- `src/renta_fija.py`: Clase `InstrumentoRentaFija` para CDT, Bonos y TES.
- `src/transaccion.py`: Clase `Transaccion` para el libro contable de operaciones y comisiones del bróker.
- `src/servicio_mercado.py`: Clase `ServicioMercado` conectada a `yfinance` para precios, EPS, TRM en COP y series de tiempo.
- `src/portafolio.py`: Clase controladora `Portafolio` para consolidación financiera y persistencia en JSON.
- `src/interfaz_portafolio.py`: Clase `InterfazPortafolioGUI` con dashboard visual (`Tkinter` + `Matplotlib`).
- `main.py`: Punto de entrada principal de la aplicación.

## Distribución de Actividades, Ramas y Commits
- **[Carlos10marin] (Rama `feature/modelos-activos`):** Implementación de la clase base `Activo` (`src/activo.py`) y la clase `Transaccion` (`src/transaccion.py`) con control de fechas, precios y comisiones de bróker.
- **[Carlos10marin] (Rama `feature/instrumentos-inversion`):** Implementación de las clases `Accion` (`src/accion.py`) e `InstrumentoRentaFija` (`src/renta_fija.py`) para acciones, dividendos, CDT, Bonos y TES.
- **[Teojz] (Rama `feature/mercado-y-portafolio`):** Implementación de `ServicioMercado` (`src/servicio_mercado.py`) con `yfinance`, conversión a COP, EPS y series de tiempo, y motor financiero `Portafolio` (`src/portafolio.py`) para cálculo de Rentabilidad Acumulada y Efectiva Anual (E.A.).
- **[Teojz] (Rama `feature/dashboard-visual`):** Implementación de la interfaz gráfica `InterfazPortafolioGUI` (`src/interfaz_portafolio.py`), archivo principal `main.py`, portafolio semilla estilo Bancolombia y documentación del repositorio.
