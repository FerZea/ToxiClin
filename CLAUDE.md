# CLAUDE.md — ToxiClin

## Proyecto
Sistema de Gestión de Expedientes Clínicos Toxicológicos para el Centro de Información y Atención Toxicológica (CIAT) del Hospital Central "Dr. Ignacio Morones Prieto", San Luis Potosí, México.

## Desarrollador
Fernando Escobar Jaramillo — Estudiante de Ing. en Sistemas Inteligentes, UASLP. Está aprendiendo Django mientras construye este proyecto. Nivel: Python intermedio, SQL básico, Django principiante. Necesita explicaciones claras de lo que se genera y por qué.

## Reglas de trabajo

### Comunicación
- Explica cada archivo que crees o modifiques: qué hace y por qué.
- Cuando crees un modelo, explica brevemente qué tipo de campo es cada línea (CharField, ForeignKey, etc.) y qué representa en la ficha del CIAT.
- Si hay múltiples formas de hacer algo, elige la más simple y explica por qué.
- No generes todo de golpe. Trabaja feature por feature, verifica que funcione, y luego avanza.
- Si Fernando pide algo que contradiga la arquitectura existente, avísale antes de hacerlo.

### Desarrollo modular
Sigue este orden. NO avances al siguiente paso sin que Fernando confirme que el anterior funciona:

**Fase 0 — Esqueleto**
1. Crear proyecto Django (`toxiclin`) con app principal (`expedientes`)
2. Configurar settings: SQLite, español (LANGUAGE_CODE='es-mx'), zona horaria ('America/Mexico_City'), static files
3. Crear estructura de carpetas para templates y static
4. Verificar que el servidor corre en localhost

**Fase 1 — Modelos y Admin**
5. Crear modelos de catálogos (empezar con los más simples: CatSexo, CatSeveridad, CatEvolucion)
6. Registrar en admin, migrar, crear superusuario
7. Verificar en admin que se pueden crear/editar registros de catálogos
8. Crear el resto de catálogos (CatCircunstanciaNivel1, Nivel2, CatTipoAgente, CatViaIngreso, CatTratamiento, etc.)
9. Crear modelo principal HistoriaClinica con todas las relaciones
10. Cargar datos iniciales de catálogos (fixtures) basados en la ficha REDARTOX

**Fase 2 — Autenticación**
11. Login/logout con Django auth
12. Dos roles: admin y capturista
13. Middleware o decorador que proteja todas las vistas
14. Página de gestión de usuarios (solo admin)

**Fase 3 — Formulario de captura**
15. Formulario básico con los campos del paciente (nombre, folio, sexo, fecha nacimiento)
16. Cálculo automático de edad desde fecha de nacimiento (JavaScript en frontend)
17. Agregar campos de consulta (tipo de contacto, motivo, fechas)
18. Lógica de mostrar/ocultar campos según tipo de consulta (presencial vs telefónico)
19. Campos del interlocutor (solo si telefónico)
20. Circunstancias de exposición (dropdown dependiente: nivel1 → nivel2)
21. Agente tóxico con búsqueda
22. Vía de ingreso (selección múltiple)
23. Signos vitales
24. Severidad
25. Tratamiento A vs B (checkboxes con dos columnas)
26. Evolución, hospitalización, comentario
27. Cálculo automático de latencia
28. Campos obligatorios — validación que no deje guardar sin ellos
29. Registro de quién capturó y cuándo (automático)

**Fase 4 — Filtrado y consulta**
30. Página de listado de historias clínicas con tabla
31. Filtros por: agente, tipo agente, circunstancia, severidad, sexo, rango de fechas, rango de edad
32. Búsqueda por folio
33. Búsqueda por nombre de paciente
34. Vista de detalle completo de un registro
35. Conteo de resultados

**Fase 5 — Estadísticas y gráficas**
36. Página de estadísticas con selección de variables (1-4)
37. Gráfica de barras (matplotlib/plotly)
38. Gráfica de pastel
39. Gráfica de línea temporal (casos por mes/año)
40. Tabla de frecuencias con conteos y porcentajes
41. Filtro temporal (último mes, trimestre, año, rango, todos)
42. Exportar gráfica como PNG
43. Dashboard resumen en la página de inicio

**Fase 6 — Migración de Excel**
44. Script para importar el Excel existente (~1,500 registros)
45. Mapeo de codificación numérica a catálogos
46. Reporte de migración (exitosos, errores, no mapeables)

**Fase 7 — Respaldos y seguridad**
47. Exportar base de datos cifrada a archivo
48. Restaurar desde respaldo cifrado
49. Recordatorio de respaldo al iniciar sesión
50. Registro de actividad (quién hizo qué)

**Fase 8 — Pulido**
51. Que el formulario siga el mismo orden visual que la ficha en papel
52. Responsive para que se vea bien en la pantalla del CIAT
53. Mensajes de éxito/error claros
54. Manejo de errores (cierre inesperado, datos corruptos)

## Stack técnico

```
Python 3.11+
Django 5.x
SQLite (default, un solo archivo db.sqlite3)
Django Templates + HTML/CSS + JavaScript (vanilla o HTMX para interactividad)
matplotlib / plotly (gráficas)
pandas + openpyxl (migración de Excel)
cryptography (Fernet) (cifrado de respaldos)
waitress (servidor WSGI para Windows en producción local)
```

## Estructura del proyecto

```
toxiclin/
├── manage.py
├── toxiclin/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── expedientes/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── catalogos.py      # Todos los catálogos
│   │   ├── historia.py       # Modelo principal HistoriaClinica
│   │   └── usuarios.py       # Extensión de User si se necesita
│   ├── forms/
│   │   ├── __init__.py
│   │   ├── captura.py        # Formulario de historia clínica
│   │   └── filtrado.py       # Formulario de filtros
│   ├── views/
│   │   ├── __init__.py
│   │   ├── captura.py        # Vistas de captura
│   │   ├── consulta.py       # Vistas de filtrado y detalle
│   │   ├── estadisticas.py   # Vistas de gráficas
│   │   ├── admin_custom.py   # Gestión de usuarios, catálogos, respaldos
│   │   └── auth.py           # Login/logout
│   ├── templates/
│   │   └── expedientes/
│   │       ├── base.html           # Template base con navbar
│   │       ├── login.html
│   │       ├── dashboard.html      # Página de inicio con resumen
│   │       ├── captura/
│   │       │   ├── formulario.html
│   │       │   └── exito.html
│   │       ├── consulta/
│   │       │   ├── listado.html
│   │       │   └── detalle.html
│   │       ├── estadisticas/
│   │       │   └── graficas.html
│   │       └── admin/
│   │           ├── usuarios.html
│   │           ├── catalogos.html
│   │           └── respaldos.html
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   │   └── formulario.js  # Lógica de mostrar/ocultar campos, cálculos
│   │   └── img/
│   ├── management/
│   │   └── commands/
│   │       ├── importar_excel.py    # Comando de migración
│   │       └── cargar_catalogos.py  # Carga inicial de catálogos
│   ├── fixtures/
│   │   └── catalogos_iniciales.json # Datos de catálogos REDARTOX
│   ├── admin.py
│   ├── urls.py
│   └── tests.py
├── backups/           # Carpeta local para respaldos
├── media/             # Gráficas exportadas
└── requirements.txt
```

## Modelos clave (referencia rápida)

Los modelos deben replicar EXACTAMENTE los campos de la ficha CIAT/REDARTOX. El documento completo de requisitos está en `Requisitos_CIAT_v2.md` en la raíz del proyecto. Consúltalo para los campos detallados, definiciones de cada catálogo, y la tabla de campos múltiple vs excluyente.

### Catálogos
Todos heredan de una clase base:
```python
class CatalogoBase(models.Model):
    nombre = models.CharField(max_length=200)
    codigo = models.IntegerField(null=True, blank=True)  # Compatibilidad con Excel
    activo = models.BooleanField(default=True)
    
    class Meta:
        abstract = True
    
    def __str__(self):
        return self.nombre
```

### Campos de selección múltiple
Usar relación ManyToMany para:
- Vía de ingreso (un paciente puede tener oral + inhalatoria)
- Tratamiento A (múltiples tratamientos previos)
- Tratamiento B (múltiples tratamientos recomendados)
- Antecedentes patológicos
- Hospitalización lugar (Sala General + UCI)

### Campos condicionales
El formulario debe mostrar/ocultar campos con JavaScript según:
- Tipo de contacto = telefónico → mostrar campos de interlocutor
- Tipo de contacto = presencial → mostrar subtipo (urgencias/internación/consultorio)
- Sexo = femenino → habilitar embarazo/lactancia
- Circunstancia nivel 1 → filtrar opciones de nivel 2
- Cualquier catálogo = "Otro" → mostrar campo de texto para especificar

### Campos calculados automáticamente
- Edad: desde fecha_nacimiento y fecha del evento. Mostrar en días (<1 mes), meses (<1 año), o años (≥1 año)
- Latencia: desde fecha_hora_exposicion y fecha_hora_ingreso (presencial) o fecha_hora_consulta (telefónico). Mostrar en minutos, horas, días, meses o años
- Consulta número: autoincremental
- Usuario que capturó: request.user automático
- Fecha de captura: auto_now_add

## Restricciones NO NEGOCIABLES

1. **CERO conexiones externas.** No CDNs, no Google Fonts, no APIs externas. Todo CSS/JS debe ser local (descargar Bootstrap/Tailwind y servirlo desde static).
2. **Sin Docker.** La computadora del CIAT es Windows 10 básico. Instrucciones de instalación deben ser: instalar Python, pip install -r requirements.txt, python manage.py migrate, python manage.py runserver.
3. **SQLite.** No proponer PostgreSQL ni MySQL. SQLite es suficiente y no requiere instalar nada.
4. **Sin telemetría.** Django DEBUG puede estar en True para desarrollo local pero ALLOWED_HOSTS debe ser solo localhost/127.0.0.1.
5. **Formulario en español.** Todo label, placeholder, mensaje de error, y texto de interfaz debe estar en español.
6. **Compatibilidad Windows.** Paths con os.path.join o pathlib. No asumir Linux.

## Convenciones de código

- Modelos en español: `HistoriaClinica`, `CatTipoAgente`, `CatCircunstanciaNivel1`
- Campos en español con snake_case: `fecha_nacimiento`, `tipo_consulta`, `agente_principio_activo`
- Catálogos prefijados con `Cat`: `CatSexo`, `CatSeveridad`, `CatEvolucion`
- Templates organizados por módulo: `templates/expedientes/captura/`, `templates/expedientes/consulta/`
- Vistas como funciones (no clases) para mayor claridad dado el nivel del desarrollador
- Comentarios en español explicando la lógica de negocio

## Para ejecutar

```bash
# Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos
python manage.py makemigrations
python manage.py migrate

# Cargar catálogos iniciales
python manage.py cargar_catalogos

# Crear superusuario (Dra. Evelyn)
python manage.py createsuperuser

# Correr servidor
python manage.py runserver
# Abrir http://localhost:8000
```

## Notas para Claude Code

- Fernando está aprendiendo Django. Cuando generes código, agrega comentarios breves que expliquen qué hace cada parte importante.
- No generes todo el proyecto de una vez. Espera confirmación de que cada fase funciona antes de avanzar.
- Si Fernando pide algo que rompa la arquitectura (ej: meter React), explícale por qué no conviene para este proyecto y sugiere la alternativa en Django.
- Los requisitos completos con todos los campos, catálogos y definiciones están en `Requisitos_CIAT_v2.md`. Consúltalo cuando necesites detalle sobre un campo específico.
- La ficha física del CIAT (Formato_CIAT.pdf) y las definiciones de REDARTOX (Definiciones.pdf) son la fuente de verdad para los campos del formulario.
