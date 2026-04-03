@echo off
REM ─────────────────────────────────────────────────────────────────
REM  ToxiClin — Script de arranque
REM  Activa el entorno virtual y lanza el servidor con waitress.
REM  No cerrar esta ventana mientras uses el sistema.
REM ─────────────────────────────────────────────────────────────────

REM Ir a la carpeta donde está este archivo (la raíz del proyecto)
cd /d "%~dp0"

REM Activar el entorno virtual
call venv\Scripts\activate.bat

REM Abrir el navegador después de 3 segundos (tiempo para que el servidor arranque)
start "" timeout /t 3 >nul & start http://localhost:8000

REM Lanzar el servidor con waitress (más estable que runserver en producción local)
REM waitress-serve escucha en el puerto 8000
waitress-serve --port=8000 toxiclin.wsgi:application
