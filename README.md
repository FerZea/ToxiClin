# ToxiClin

Sistema de Gestión de Expedientes Clínicos Toxicológicos para el **Centro de Información y Atención Toxicológica (CIAT)** del Hospital Central "Dr. Ignacio Morones Prieto", San Luis Potosí, México.

---

## Descripción

ToxiClin reemplaza el registro en Excel de historias clínicas toxicológicas por una aplicación web local que replica exactamente la ficha CIAT/REDARTOX. El sistema corre en la computadora del CIAT y se accede desde el navegador (`localhost`) — **no requiere internet**.

### Usuarios

| Rol | Descripción |
|---|---|
| **Administrador** (Dra. Evelyn, Dra. Susana) | Acceso total: gestión de usuarios, catálogos, respaldos y estadísticas |
| **Capturista** (alumnos rotantes) | Solo captura de historias clínicas |

---

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Backend | Python 3.11+ + Django 5.x |
| Base de datos | SQLite (un solo archivo `db.sqlite3`) |
| Frontend | Django Templates + HTML/CSS + JavaScript |
| Gráficas | matplotlib / plotly |
| Migración Excel | pandas + openpyxl |
| Cifrado respaldos | cryptography (Fernet / AES-256) |
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

# 6. Crear superusuario (administrador)
python manage.py createsuperuser

# 7. Correr el servidor
python manage.py runserver
```

Abrir en el navegador: [http://localhost:8000](http://localhost:8000)

---

## Estructura del proyecto

```
ToxiClin/
├── manage.py
├── requirements.txt
├── toxiclin/                        # Configuración del proyecto Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── expedientes/                     # App principal
│   ├── models/
│   │   ├── catalogos.py             # 17 catálogos CIAT/REDARTOX
│   │   └── historia.py              # Modelo principal HistoriaClinica
│   ├── views/
│   │   ├── auth.py                  # Login / logout
│   │   ├── inicio.py                # Dashboard
│   │   ├── captura.py               # Formulario de historia clínica (próx.)
│   │   ├── consulta.py              # Listado y detalle (próx.)
│   │   ├── estadisticas.py          # Gráficas (próx.)
│   │   └── admin_custom.py          # Usuarios y respaldos (próx.)
│   ├── templates/expedientes/
│   │   ├── base.html                # Template base con navbar
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── captura/
│   │   ├── consulta/
│   │   ├── estadisticas/
│   │   └── admin/
│   ├── static/
│   │   ├── css/estilos.css
│   │   └── js/formulario.js
│   ├── management/commands/
│   │   └── cargar_catalogos.py      # Carga inicial de catálogos
│   ├── migrations/                  # Migraciones de base de datos
│   ├── admin.py                     # Configuración del admin de Django
│   └── urls.py
├── backups/                         # Respaldos cifrados (no en git)
└── media/                           # Gráficas exportadas (no en git)
```

---

## Modelos principales

### Catálogos (17 tablas)

Todos heredan de `CatalogoBase` que provee: `nombre`, `codigo` (compatible con Excel), `activo`.

| Catálogo | Valores |
|---|---|
| `CatSexo` | Masculino, Femenino |
| `CatSeveridad` | Asintomático, Leve, Moderada, Severa, Fatal, Sin Relación |
| `CatEvolucion` | Recuperación, Recuperación retardada, Muerte, Secuela, Desconocida |
| `CatTipoContacto` | Exposición (presencial), Telefónico |
| `CatMotivoConsulta` | Intoxicación, Descartar Intoxicación, Asesoramiento |
| `CatCircunstanciaNivel1` | No Intencional, Intencional, Reacción Adversa, Desconocido |
| `CatCircunstanciaNivel2` | 15 subcategorías vinculadas al nivel 1 |
| `CatTipoAgente` | 19 tipos (Medicamento, Plaguicida, Animales, Plantas, etc.) |
| `CatViaIngreso` | Oral, Inhalatoria, Cutánea, Ocular, Parenteral, etc. |
| `CatTratamiento` | 28 opciones (columna A=previo, B=recomendado) |
| ... | y 7 catálogos más |

### Historia Clínica

Modelo principal que replica la ficha CIAT/REDARTOX completa:

- **Datos del paciente**: nombre, folio, sexo, fecha de nacimiento, CURP, dirección
- **Edad calculada automáticamente**: en días (<1 mes), meses (<1 año) o años (≥1 año)
- **Datos de la consulta**: tipo de contacto, motivo, fechas, médico
- **Latencia calculada automáticamente**: desde exposición hasta consulta/ingreso
- **Interlocutor** (solo telefónico): nombre, categoría, ubicación
- **Circunstancias**: dropdown dependiente nivel 1 → nivel 2
- **Agente tóxico**: tipo + principio activo (texto libre con búsqueda)
- **Vías de ingreso**: selección múltiple (ManyToMany)
- **Signos vitales**: FC, FR, temperatura, saturación, TA
- **Tratamiento A/B**: 28 opciones en dos columnas con texto de especificación
- **Evolución y hospitalización**: con lugar (múltiple) y días
- **Auditoría**: usuario y fecha de captura automáticos

---

## Fases de desarrollo

| Fase | Descripción | Estado |
|---|---|---|
| **Fase 0** | Esqueleto del proyecto | ✅ Completa |
| **Fase 1** | Modelos y Admin | ✅ Completa |
| **Fase 2** | Autenticación y roles | 🔄 En progreso |
| **Fase 3** | Formulario de captura | ⏳ Pendiente |
| **Fase 4** | Filtrado y consulta | ⏳ Pendiente |
| **Fase 5** | Estadísticas y gráficas | ⏳ Pendiente |
| **Fase 6** | Migración desde Excel | ⏳ Pendiente |
| **Fase 7** | Respaldos y seguridad | ⏳ Pendiente |
| **Fase 8** | Pulido y responsivo | ⏳ Pendiente |

---

## Restricciones del proyecto

- **Sin internet**: cero conexiones externas, sin CDN, sin Google Fonts, sin telemetría
- **Sin Docker**: instalación simple con `pip install -r requirements.txt`
- **SQLite**: no requiere instalar servidor de base de datos
- **Windows 10**: compatible, paths con `pathlib`, servidor `waitress` para producción local
- **Datos confidenciales**: respaldos cifrados con AES-256 (Fernet)

---

## Administración

El admin de Django está disponible en [http://localhost:8000/admin/](http://localhost:8000/admin/) para el superusuario. Permite:

- Gestionar todos los catálogos (agregar/editar/desactivar valores)
- Ver y editar historias clínicas
- Gestionar usuarios

---

## Desarrollador

**Fernando Escobar Jaramillo**
Estudiante de Ingeniería en Sistemas Inteligentes — UASLP
San Luis Potosí, México

---

## Licencia

Uso interno del CIAT — Hospital Central "Dr. Ignacio Morones Prieto". Todos los derechos reservados.
