@echo off
title Sistema de Portafolio de Inversion - Bancolombia COP
color 0A
cls
echo =====================================================================
echo       SISTEMA DE SEGUIMIENTO Y VALORACION DE PORTAFOLIO DE INVERSION
echo              (Renta Fija, Renta Variable, yfinance y Tkinter)
echo =====================================================================
echo.
echo Iniciando el dashboard financiero...

if exist "dist\PortafolioInversiones\PortafolioInversiones.exe" (
    start "" "dist\PortafolioInversiones\PortafolioInversiones.exe"
) else (
    python main.py
)

exit
