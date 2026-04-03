# ToxiClin

Sistema de Gestión de Expedientes Clínicos Toxicológicos para el **Centro de Información y Atención Toxicológica (CIAT)** del Hospital Central "Dr. Ignacio Morones Prieto", San Luis Potosí, México.

---

## Descripción

ToxiClin reemplaza el registro en Excel de historias clínicas toxicológicas por una aplicación web local que replica exactamente la ficha CIAT/REDARTOX. El sistema corre en la computadora del CIAT y se accede desde el navegador (`localhost`) — **no requiere internet**.

### Usuarios

| Rol | Descripción |
|---|---|
| **Administrador** (Dra. Evelyn, Dra. Susana) | Acceso total: gestión de usuarios, estadísticas, respaldos y bitácora |
| **Capturista** (alumnos rotantes) | Solo captura y consulta de historias clínicas |

---

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Backend | Python 3.11+ + Django 5.x |
| Base de datos | SQLite (un solo archivo `db.sqlite3`) |
| Frontend | Django Templates + HTML/CSS + JavaScript |
| Gráficas | matplotlib |
| Cifrado respaldos | cryptography (Fernet / PBKDF2-SHA256) |
| Servidor local | waitress (WSGI para Windows) |

> **Sin CDN, sin Docker, sin internet.** Todo funciona 100% local.

---

## Instalación

### Requisitos previos

- Python 3.11 o superior
- pip

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/FerZea/ToxiClin.git
cd ToxiClin

# 2. Crear entorno virtual
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / Mac
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar base de datos
python manage.py migrate

# 5. Cargar catálogos iniciales (REDARTOX)
python manage.py cargar_catalogos

# 6. (Opcional) Cargar datos de ejemplo para demostración
python manage.py crear_datos_ejemplo

# O generar más volumen de prueba
python manage.py crear_datos_ejemplo --cantidad 100

# 7. Crear superusuario (administrador técnico)
python manage.py createsuperuser

# 8. Correr el servidor
python manage.py runserver
```

Abrir en el navegador: [http://localhost:8000](http://localhost:8000)

### Usuarios de demostración (después de `crear_datos_ejemplo`)

| Usuario | Contraseña | Rol |
|---|---|---|
| `demo_admin` | `demo1234` | Administrador |
| `demo_cap` | `demo1234` | Capturista |

---

## Funcionalidades implementadas

### Captura de historias clínicas (Fase 3)
- Formulario completo que replica la ficha CIAT/REDARTOX
- Cálculo automático de edad (días / meses / años) y latencia
- Dropdowns dependientes: circunstancia nivel 1 → nivel 2
- Mostrar/ocultar campos según tipo de consulta (presencial / telefónico)
- Validación de campos obligatorios con mensajes en español
- Tratamiento A/B con 28 opciones en tabla de dos columnas

### Filtrado y consulta (Fase 4)
- Listado con filtros por: tipo de agente, circunstancia, severidad, sexo, rango de fechas, rango de edad
- Búsqueda por folio y por nombre de paciente
- Vista de detalle completo del expediente
- Paginación de resultados

### Estadísticas y gráficas (Fase 5)
- Selección de 1–4 variables para análisis
- Gráficas de barras, pastel, línea temporal y barras agrupadas (cruce de 2 variables)
- Tabla de frecuencias con conteos y porcentajes
- Filtro temporal: último mes, trimestre, año o rango personalizado
- Exportar gráficas como PNG o JPG
- Dashboard con resumen estadístico en tiempo real

### Respaldos cifrados (Fase 7)
- Exportar la base de datos completa como archivo `.toxiclin` cifrado con PBKDF2-SHA256 + Fernet
- Restaurar desde respaldo cifrado con verificación de contraseña
- Recordatorio automático en el dashboard si llevan ≥7 días sin respaldar
- Historial de respaldos locales en `backups/`

### Bitácora de actividad (Fase 7)
- Registro automático de: login, logout, captura, edición, respaldo y restauración
- Vista de los últimos 500 eventos (solo administradoras)

### Gestión de usuarios (Fase 2)
- Crear, editar y desactivar usuarios capturistas
- Cambiar contraseña desde panel de administración
- Dos roles: Administrador y Capturista

### Pulido UI (Fase 8)
- Diseño responsivo para pantallas de 600px a 1200px+
- Páginas de error 404 y 500 personalizadas
- Mensajes flash con botón de cierre y auto-desaparición
- Stub para importación desde Excel (próximamente)

---

## Pruebas automatizadas

```bash
python manage.py test expedientes
```

**36 tests** cubriendo:
- Acceso y permisos (login, roles, decoradores)
- Validación del formulario de captura
- Permisos de edición (solo autor o admin)
- Estadísticas: filtros temporales, cruce de variables, exportación PNG/JPG
- Clasificación por rangos de edad, conteo de vías M2M
- Respaldos: creación con contraseña, rechazo de contraseña incorrecta, archivo inválido
- Bitácora: registro de login, logout, captura y edición
- ConfigSistema: get/set/sobreescritura
- Stub de importación Excel: acceso por rol
- Páginas de error: 404

---

## Estructura del proyecto

```
ToxiClin/
├── manage.py
├── requirements.txt
├── Requisitos_CIAT_v2.md          # Especificación funcional completa
├── toxiclin/                       # Configuración del proyecto Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── expedientes/                    # App principal
│   ├── models/
│   │   ├── catalogos.py            # 17 catálogos CIAT/REDARTOX
│   │   ├── historia.py             # Modelo principal HistoriaClinica
│   │   └── sistema.py              # ConfigSistema + RegistroActividad
│   ├── views/
│   │   ├── auth.py                 # Login / logout + registro de actividad
│   │   ├── inicio.py               # Dashboard con recordatorio de respaldo
│   │   ├── captura.py              # Formulario de historia clínica
│   │   ├── consulta.py             # Listado y detalle
│   │   ├── estadisticas.py         # Gráficas y estadísticas (solo admin)
│   │   └── admin_custom.py         # Usuarios, respaldos, bitácora, stub Excel
│   ├── forms/
│   │   ├── captura.py              # Formulario principal con validaciones
│   │   └── filtrado.py             # Formulario de filtros
│   ├── templates/expedientes/
│   │   ├── base.html               # Template base con navbar
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── captura/                # formulario.html
│   │   ├── consulta/               # listado.html, detalle.html
│   │   ├── estadisticas/           # graficas.html
│   │   └── admin/                  # usuarios, respaldos, actividad, importar_excel
│   ├── templates/
│   │   ├── 404.html                # Página de error 404
│   │   └── 500.html                # Página de error 500
│   ├── static/
│   │   ├── css/estilos.css         # Estilos + responsive
│   │   └── js/formulario.js        # Lógica dinámica del formulario
│   ├── management/commands/
│   │   ├── cargar_catalogos.py     # Carga inicial de catálogos REDARTOX
│   │   └── crear_datos_ejemplo.py  # 20 casos clínicos de muestra
│   ├── graficas.py                 # Generación de gráficas matplotlib
│   ├── decoradores.py              # @login_requerido, @solo_admin
│   └── tests.py                    # 36 pruebas automatizadas
├── backups/                        # Respaldos cifrados (no en git)
└── media/                          # Gráficas exportadas (no en git)
```

---

## Fases de desarrollo

| Fase | Descripción | Estado |
|---|---|---|
| **Fase 0** | Esqueleto del proyecto | ✅ Completa |
| **Fase 1** | Modelos y catálogos REDARTOX | ✅ Completa |
| **Fase 2** | Autenticación y roles | ✅ Completa |
| **Fase 3** | Formulario de captura completo | ✅ Completa |
| **Fase 4** | Filtrado, búsqueda y paginación | ✅ Completa |
| **Fase 5** | Estadísticas, gráficas y dashboard | ✅ Completa |
| **Fase 6** | Migración desde Excel (~1,500 registros) | ⏳ Pendiente (requiere archivo Excel) |
| **Fase 7** | Respaldos cifrados, bitácora, recordatorio | ✅ Completa |
| **Fase 8** | Pulido, responsive, páginas de error | ✅ Completa |

---

## Restricciones del proyecto

- **Sin internet**: cero conexiones externas, sin CDN, sin Google Fonts, sin telemetría
- **Sin Docker**: instalación simple con `pip install -r requirements.txt`
- **SQLite**: no requiere instalar servidor de base de datos
- **Windows 10**: compatible, paths con `pathlib`, servidor `waitress` para producción local
- **Datos confidenciales**: respaldos cifrados con PBKDF2-SHA256 + Fernet (AES-128-CBC)

---

## Notas de seguridad

- Contraseñas almacenadas con hash (PBKDF2 + SHA256, Django default)
- Respaldos cifrados: `[16 bytes salt][datos cifrados Fernet]`. Sin la contraseña el archivo es ilegible.
- Acceso exclusivo por localhost (`ALLOWED_HOSTS = ['localhost', '127.0.0.1']`)
- Historial de accesos y cambios registrado en bitácora

---

## Desarrollador

**Fernando Escobar Jaramillo**
Estudiante de Ingeniería en Sistemas Inteligentes — UASLP
San Luis Potosí, México

---

## Licencia

Uso interno del CIAT — Hospital Central "Dr. Ignacio Morones Prieto". Todos los derechos reservados.
