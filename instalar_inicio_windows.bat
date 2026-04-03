@echo off
REM ─────────────────────────────────────────────────────────────────
REM  ToxiClin — Instalador de inicio automático en Windows
REM
REM  Registra ToxiClin como tarea programada que se ejecuta
REM  automáticamente cuando el usuario inicia sesión.
REM
REM  Ejecutar UNA SOLA VEZ, como administrador.
REM ─────────────────────────────────────────────────────────────────

REM Ir a la carpeta del proyecto
cd /d "%~dp0"

REM Crear la tarea programada:
REM   - Nombre: ToxiClin
REM   - Disparador: al iniciar sesión el usuario actual
REM   - Acción: ejecutar iniciar_toxiclin.bat
REM   - Se ejecuta aunque el usuario no esté conectado: no
REM   - Nivel más alto de privilegios: no (no requiere admin para correr)

schtasks /create ^
  /tn "ToxiClin" ^
  /tr "\"%~dp0iniciar_toxiclin.bat\"" ^
  /sc onlogon ^
  /ru "%USERNAME%" ^
  /f

if %errorlevel%==0 (
    echo.
    echo  [OK] ToxiClin se iniciará automáticamente en el próximo inicio de sesión.
    echo.
    echo  Para desactivarlo:
    echo    Panel de control ^> Herramientas administrativas ^> Programador de tareas
    echo    O ejecuta: schtasks /delete /tn "ToxiClin" /f
    echo.
) else (
    echo.
    echo  [ERROR] No se pudo crear la tarea. Intenta ejecutar este archivo
    echo  como Administrador ^(clic derecho ^> Ejecutar como administrador^).
    echo.
)

pause
