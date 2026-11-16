import yfinance as yf  # Libreria para consultar precios e indicadores en Yahoo Finance
import pandas as pd    # Libreria para manejar tablas y series de tiempo


class ServicioMercado:
    """
    Clase encargada de conectar con yfinance, convertir divisas a Pesos Colombianos (COP),
    extraer la Utilidad por Accion (EPS) y descargar series de tiempo historicas.
    """

    def __init__(self):
        self.trm_respaldo = 4150.0              # TRM fija de respaldo por si falla el internet
        self.trm_actual_cop = self.obtenerTRM() # Consulta la TRM del dia al iniciar

        # Datos semilla en COP de respaldo por si falla la red durante la sustentacion
        self.datos_respaldo = {
            "PFBCOLOM.CL": {"precio_cop": 36800.0,  "eps_cop": 6120.0,  "moneda": "COP", "nombre": "Bancolombia Preferencial"},
            "CIB":         {"precio_cop": 152720.0, "eps_cop": 25522.0, "moneda": "USD", "nombre": "Bancolombia ADR (NYSE)"},
            "ECOPETROL.CL":{"precio_cop": 1950.0,   "eps_cop": 385.0,   "moneda": "COP", "nombre": "Ecopetrol S.A."},
            "AAPL":        {"precio_cop": 935000.0, "eps_cop": 26800.0, "moneda": "USD", "nombre": "Apple Inc."},
            "NVDA":        {"precio_cop": 560000.0, "eps_cop": 12200.0, "moneda": "USD", "nombre": "NVIDIA Corp."}
        }

    def obtenerTRM(self) -> float:
        """Consulta en yfinance el valor actual del dolar en Pesos Colombianos (USDCOP=X)."""
        try:
            ticker_trm = yf.Ticker("USDCOP=X")                    # Conecta al indicador Dolar/Peso Colombiano
            hist = ticker_trm.history(period="5d")                # Descarga los ultimos 5 dias de cotizacion
            if not hist.empty:                                    # Verifica que la tabla no llegue vacia
                self.trm_actual_cop = float(hist["Close"].iloc[-1]) # Toma el ultimo precio de cierre en COP
                return round(self.trm_actual_cop, 2)              # Retorna la TRM redondeada a 2 decimales
        except Exception:                                         # Si no hay conexion a internet
            pass                                                  # Continua usando la TRM de respaldo
        return self.trm_respaldo                                  # Retorna 4150.0 COP por defecto

    def consultarCotizacionYEPS(self, ticker: str) -> dict:
        """
        Obtiene el precio actual de mercado y el EPS (Utilidad por Accion),
        expresando todos los resultados en Pesos Colombianos (COP).
        """
        codigo = ticker.strip().upper()                           # Limpia espacios y convierte a mayusculas
        try:
            activo_yf = yf.Ticker(codigo)                         # Instancia el ticker en yfinance
            hist = activo_yf.history(period="5d")                 # Consulta cierres recientes
            info = activo_yf.info                                 # Consulta diccionario de fundamentales (EPS)

            if not hist.empty:                                    # Si obtuvo cotizacion real
                precio_origen = float(hist["Close"].iloc[-1])     # Ultimo precio de mercado
                moneda = info.get("currency", "USD")              # Moneda original del activo
                if codigo.endswith(".CL"):                        # Los activos de la BVC (.CL) estan en COP
                    moneda = "COP"

                # Extrae el EPS (Utilidad por Accion: trailingEps o forwardEps)
                eps_origen = info.get("trailingEps", info.get("forwardEps", 0.0))
                if eps_origen is None:                            # Si el activo no reporta EPS
                    eps_origen = 0.0                              # Asigna 0.0 por seguridad

                # Si la accion cotiza en USD, multiplica por la TRM para pasar todo a COP
                factor_cop = 1.0 if moneda == "COP" else self.trm_actual_cop

                precio_cop = round(precio_origen * factor_cop, 2) # Precio unitario en Pesos Colombianos
                eps_cop = round(float(eps_origen) * factor_cop, 2)# Utilidad por accion (EPS) en COP
                nombre = info.get("shortName", codigo)            # Nombre de la empresa emisora

                return {
                    "ticker": codigo,                             # Simbolo bursatil
                    "nombre": nombre,                             # Nombre de la empresa
                    "precio_cop": precio_cop,                     # Precio actual en COP
                    "eps_cop": eps_cop,                           # EPS en COP
                    "moneda_origen": moneda,                      # Moneda de cotizacion original
                    "trm_aplicada": round(factor_cop, 2)          # Tasa de cambio aplicada
                }
        except Exception:                                         # Si falla la consulta en linea
            pass

        # Respaldo local en COP si no hay internet o el ticker es de prueba
        if codigo in self.datos_respaldo:
            d = self.datos_respaldo[codigo]
            return {
                "ticker": codigo,
                "nombre": d["nombre"],
                "precio_cop": d["precio_cop"],
                "eps_cop": d["eps_cop"],
                "moneda_origen": d["moneda"],
                "trm_aplicada": 1.0 if d["moneda"] == "COP" else self.trm_actual_cop
            }

        return {
            "ticker": codigo,
            "nombre": codigo,
            "precio_cop": 0.0,
            "eps_cop": 0.0,
            "moneda_origen": "COP",
            "trm_aplicada": 1.0
        }

    def obtenerSerieTiempo(self, ticker: str, filtro: str = "1A") -> pd.DataFrame:
        """
        Retorna la serie de tiempo del precio de la accion en COP segun el filtro:
        '1D' (Dia), '1S' (Semana), '1M' (1 Mes), '6M' (6 Meses), '1A' (1 Año), '5A' (5 Años).
        """
        codigo = ticker.strip().upper()                           # Estandariza el ticker
        mapa_filtros = {
            "1D": ("5d",  "15m"),                                 # Intradia cada 15 minutos
            "1S": ("5d",  "1h"),                                  # 1 semana cada hora
            "1M": ("1mo", "1d"),                                  # 1 mes con cierre diario
            "6M": ("6mo", "1d"),                                  # 6 meses con cierre diario
            "1A": ("1y",  "1d"),                                  # 1 año con cierre diario
            "5A": ("5y",  "1wk")                                  # 5 años con cierre semanal
        }
        periodo, intervalo = mapa_filtros.get(filtro.upper(), ("1y", "1d"))

        try:
            activo_yf = yf.Ticker(codigo)                         # Conecta con Yahoo Finance
            df = activo_yf.history(period=periodo, interval=intervalo) # Descarga serie historica

            if not df.empty:                                      # Si hay datos disponibles
                if filtro.upper() == "1D":                        # Si pidio el filtro de 1 Dia
                    df = df.tail(26)                              # Muestra la ultima sesion bursatil

                es_cop = codigo.endswith(".CL")                   # Verifica si ya viene en pesos
                factor_cop = 1.0 if es_cop else self.trm_actual_cop # Aplica TRM si viene en dolares

                df["Precio_COP"] = (df["Close"] * factor_cop).round(2) # Columna convertida a COP
                return df[["Precio_COP"]]                         # Retorna el DataFrame listo para graficar
        except Exception:
            pass

        # Serie de respaldo en COP en caso de no tener internet
        fechas = pd.date_range(end=pd.Timestamp.today(), periods=30, freq="D")
        base_cop = self.datos_respaldo.get(codigo, {}).get("precio_cop", 36800.0)
        precios = [round(base_cop * (1 + 0.003 * ((i % 7) - 3)), 2) for i in range(30)]
        return pd.DataFrame({"Precio_COP": precios}, index=fechas)