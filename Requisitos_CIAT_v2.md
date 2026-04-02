# Sistema de Gestión de Expedientes Clínicos Toxicológicos — CIAT

## Contexto del proyecto

Aplicación web local (Django) para el Centro de Información y Atención Toxicológica (CIAT) del Hospital Central "Dr. Ignacio Morones Prieto" / Facultad de Medicina - UASLP, San Luis Potosí. Actualmente registran historias clínicas de intoxicaciones en fichas de papel (formato REDARTOX) que se transcriben a Excel (~1,500 registros en 15+ años). El sistema reemplaza al Excel, NO al papel. La ficha en papel se sigue usando. El sistema corre localmente en la computadora del CIAT, se accede desde el navegador (localhost), no requiere internet.

**Documentos de referencia para el formulario:**
- Ficha de Registro del CIAT (formato físico adjunto — Formato_CIAT.pdf)
- Definiciones de la Ficha de Registro Único de Consultas Toxicológicas, Ministerio de Salud Argentina, REDARTOX (Definiciones.pdf)

### Usuarios
- **Administradoras** (2): Dra. Evelyn y Dra. Susana. Acceso total. Son las únicas que gestionan accesos.
- **Capturistas** (alumnos rotantes de medicina): Solo captura de registros. Rotan cada 3 semanas. Acceso temporal.

### Restricciones técnicas
- Presupuesto CERO. Todo gratuito/open source.
- 100% local. Sin internet. Sin nube. Sin telemetría.
- Computadora con Windows 10, recursos limitados.
- Datos confidenciales de pacientes — cifrado obligatorio.

### Alcance: Etapas 1 y 2

**Etapa 1 — Captura confiable:**
- Formulario digital que replica la ficha CIAT/REDARTOX
- Catálogos cerrados, cálculos automáticos, candados
- Migración de datos desde Excel
- Filtrado y consulta de registros
- Gestión de usuarios y respaldos cifrados

**Etapa 2 — Estadísticas y gráficas:**
- Cruce de 2-4 variables con visualización (gráficas de barras, pastel, líneas)
- Conteos y frecuencias por agente, circunstancia, periodo, edad, sexo, etc.
- Exportación de gráficas para presentaciones
- Dashboard con resumen rápido de datos

**Fuera de alcance (etapa futura):**
- Análisis predictivo y alertas
- Acceso remoto / nube
- Historia clínica electrónica completa (padecimiento actual, examen físico por aparatos y sistemas)

### Stack tecnológico

- **Backend:** Python 3.x + Django
- **Frontend:** Django Templates + HTML/CSS + JavaScript/HTMX
- **Base de datos:** SQLite
- **Estadísticas/Gráficas:** pandas + matplotlib / plotly
- **Migración de Excel:** openpyxl / pandas
- **Cifrado de respaldos:** cryptography (Fernet)
- **Contraseñas:** Django built-in (PBKDF2)
- **Servidor local:** waitress (WSGI para Windows)

---

## Requisitos Funcionales

### Módulo de Captura (RF-01 a RF-16)

El formulario replica EXACTAMENTE los campos de la ficha CIAT/REDARTOX. A continuación se detallan los campos organizados por sección, tal como aparecen en el formulario físico.

**RF-01: Datos del paciente**
- Nombre y Apellido (TEXT)
- Dirección y Localidad (TEXT, lo más específico posible — se usa para geolocalización)
- Teléfono (TEXT)
- Sexo (catálogo excluyente: Masculino, Femenino)
- Edad (calculada automáticamente desde fecha de nacimiento): en días si <1 mes, meses si <1 año, años si ≥1 año
- Fecha de nacimiento (DATE — el sistema calcula la edad, no se captura manualmente)
- Embarazo/Lactancia (catálogo excluyente: Sí, No — solo habilitado si sexo = Femenino)
- Escolaridad (TEXT — último año cerrado/aprobado)
- Antecedentes Patológicos Personales / APP (TEXT libre)
- N° Folio/Expediente (TEXT, obligatorio — vincula con expediente físico del hospital)
- CURP (TEXT, opcional)

**RF-02: Datos de la consulta**
- Consulta No. (numérico autoincremental por el sistema)
- Tipo de frecuencia (catálogo excluyente: Por 1ª vez, Ulterior)
  - Por 1ª vez: primer contacto con el CIAT por esta exposición/intoxicación
  - Ulterior: consulta posterior por la misma intoxicación
- Fecha y hora de ingreso (DATETIME — hora de admisión al hospital, aplica si presencial)
- Fecha y hora del Evento/Exposición (DATETIME — hora en que ocurrió la exposición)
- Fecha y hora de consulta (DATETIME — hora de la llamada o contacto)
- Latencia (calculada automáticamente: diferencia entre exposición y consulta/ingreso). Se expresa en minutos, horas, días, meses o años. Puede ser "Desconocida" si la hora de exposición no se conoce.
- Escolaridad (TEXT)
- Médico que atiende (TEXT)

**RF-03: Tipo de consulta y motivo**
El formulario tiene DOS ejes que se combinan:

**Eje 1 — Vía de contacto** (catálogo excluyente):
- Exposición (presencial)
- Telefónico

**Eje 2 — Motivo de consulta** (catálogo excluyente):
- Intoxicación: exposición de uno o más individuos a un agente, o cuando ya hay intoxicación establecida
- Descartar Intoxicación: se sospecha exposición/intoxicación aunque no se conozcan antecedentes
- Asesoramiento: requerimiento de información NO relacionado con un paciente intoxicado o expuesto (ej: uso de sustancias en embarazo, interacciones medicamentosas, identificación de agente, info sobre antídotos)

**Si es presencial**, se habilitan subtipos:
- Urgencias: atención inmediata, manejo ambulatorio, permanece <24 horas
- Internación: ingreso al hospital, ocupa cama en sala general, UCI/UTI, o permanece en urgencias >24 horas
- Consultorio Externo: atención ambulatoria para diagnóstico, tratamiento y/o seguimiento
- Vía electrónico

**Si es telefónico**, se habilitan campos del interlocutor (ver RF-04).

Al seleccionar el tipo, el formulario muestra/oculta los campos correspondientes.

**RF-04: Datos del interlocutor (solo consulta telefónica)**
- Interlocutor nombre (TEXT)
- Categoría del interlocutor (catálogo excluyente):
  - Personal de salud (especificar: farmacológico, veterinario, toxicológico o bromatológico)
  - Familiar (pariente directo: padres, hijo/a, hermano/a, abuelo/a, esposo/a, etc.)
  - Paciente (persona expuesta a un agente o que sospecha estarlo)
  - Otro (especificar: amigo, vecino, trabajador social, fuerzas armadas, periodistas, etc.)
- Ubicación del interlocutor — Nombre del Establecimiento (TEXT)
- Localidad (TEXT)
- Teléfono (TEXT)
- Tipo de establecimiento (catálogo excluyente):
  - Establecimiento de Salud con Internamiento (hospital, clínica, sanatorio — especificar Sector Público o Privado)
  - Establecimiento de Salud sin Internamiento (consultorio, ambulancia, laboratorio, centro de salud — especificar Sector Público o Privado)
  - Hogar
  - Trabajo (fábrica, taller, oficina, comercio, campos de cultivo)
  - Institución educativa
  - Espacio Público (almacén, banco, hotel, estadio, parque, restaurante, etc.)
  - Otro (especificar)

**RF-05: Circunstancias de la exposición**
Catálogo con dos niveles. Primer nivel excluyente (No intencional, Intencional, Reacción adversa, Desconocido). Segundo nivel según la selección:

**NO INTENCIONAL** (cualquier exposición sin intención de causar daño):
- Accidental: exposición inesperada, incluye equivocaciones con productos no medicamentosos
- Ocupacional: ocurrió mientras trabajaba o el agente era parte del proceso de trabajo
- Ambiental: exposición pasiva por contaminación de aire, agua o suelo (natural o artificial)
- Alimentaria: ingesta de alimentos contaminados con agentes tóxicos
- Error terapéutico: uso incorrecto de medicamento por error en dosis, intervalo, vía o persona destinataria
- Mal uso: uso incorrecto o inapropiado de sustancia no medicamentosa
- Medicina tradicional: uso de hierbas medicinales y prácticas de medicación casera
- Accidente químico: exposición no ocupacional por liberación de sustancia química (derrame, escape, explosión)
- Otro (especificar)

**INTENCIONAL** (cualquier exposición con intención de causar daño):
- Tentativa suicida: exposición con intención autodestructiva o manipulativa
- Abuso: exposición deliberada a agente psicotrópico a dosis abusivas o con dependencia
- Automedicación: uso inapropiado o incorrecto de medicamento sin prescripción médica (se excluye abuso de psicotrópicos)
- Aborto: exposición con intención de interrumpir embarazo
- Homicidio/Malicioso: exposición no consentida por el paciente, con intención de daño por tercera persona
- Otro (especificar)

**REACCIÓN ADVERSA:** Evento adverso que ocurre con el uso normal y recomendado de un producto. Incluye efectos no esperados por alergia, hipersensibilidad o idiosincrasia.

**DESCONOCIDO:** No se puede establecer la circunstancia.

**RF-06: Ubicación del evento/exposición**
Catálogo excluyente — lugar donde ocurrió la exposición:
- Hogar y alrededores (casa, pensión, residencia, incluye jardín, patio, garaje)
- Lugar de Trabajo (fábrica, taller, oficina, comercio, campos de cultivo)
- Institución de salud (hospitales, clínicas, sanatorios, consultorios)
- Institución educativa
- Espacio Público (almacén, banco, hotel, estadio, parque, restaurante, transporte)
- Otro (especificar: prisión, base militar, río, océano, etc.)

**RF-07: Tipo de exposición**
Catálogo excluyente:
- Aguda: exposición única o repetida durante periodo <24 horas
- Crónica: exposición continua o repetida al agente por >24 horas
- Aguda sobre crónica: exposición aguda sobre base de exposición crónica al mismo agente
- Desconocida

**RF-08: Duración de la exposición**
Tiempo que el paciente estuvo expuesto al agente. Se aplica principalmente a exposiciones inhalatorias o cutáneas. Se expresa en: minutos, horas, días, meses, años, o Desconocida.

**RF-09: Tipo de agente y agente específico**
Dos campos relacionados:

**Tipo de agente** (catálogo excluyente — clasificación por uso):
- Medicamento
- Producto veterinario
- Producto Industrial/Comercial (solventes, adhesivos, pinturas, blanqueadores, etc.)
- Producto Doméstico/Entretenimiento (limpieza, detergentes, pilas, combustibles, juguetes, etc.)
- Cosmético/Higiene personal (tocador, perfumes, maquillaje, pasta dental, etc.)
- Plaguicida de Uso Doméstico
- Plaguicida de Uso Agrícola
- Plaguicida de Uso Veterinario
- Plaguicida de Uso en Salud Pública
- Droga de Abuso (sustancia con efecto eufórico o psicotrópico no clasificada en otra categoría)
- Alimento/Bebida (procesada o cruda, con o sin alcohol, aditivos, etc.)
- Contaminante ambiental (materia química, biológica o radiológica indeseable en el ambiente)
- Armas Químicas
- Plantas
- Hongos
- Animales (especies que producen reacciones tóxicas o alérgicas)
- Agroquímicos/Armas
- Desconocido
- Otro (especificar)

**Agente** (campo de texto con búsqueda):
- Principio Activo / Nombre comercial (TEXT — registrar principio(s) activo(s), nombre científico si es planta/animal, Y nombre comercial/popular/vulgar)
- Cantidad Informada (TEXT — dosis informada por paciente o interlocutor: número de comprimidos, volumen, etc.)

**RF-10: Vía de ingreso**
Catálogo de SELECCIÓN MÚLTIPLE (un paciente puede tener más de una vía simultánea):
- Oral: ingesta a través de la vía digestiva
- Inhalatoria: contacto a través de vías respiratorias
- Cutánea/Mucosa: exposición de piel o mucosas (orofaríngea, nasal, rectal, vaginal, etc.)
- Ocular: exposición de los ojos
- Parenteral: introducción mediante objeto punzante (endovenoso, intramuscular, subcutáneo, etc.)
- Mordedura/Picadura: introducción mediante aparato inoculador de un animal
- Desconocida
- Otra (especificar)

**RF-11: Signos, síntomas y signos vitales**
- Signos y síntomas (TEXT libre — lo que refiere el paciente o interlocutor)
- Signos vitales:
  - FC: Frecuencia cardíaca (numérico)
  - FR: Frecuencia respiratoria (numérico)
  - TEMP: Temperatura (numérico decimal)
  - SAT: Saturación de oxígeno (numérico)
  - TA: Tensión arterial (TEXT, formato sistólica/diastólica)

**RF-12: Severidad Inicial o Mayor**
Catálogo excluyente — según el Poisoning Severity Score (IPCS/OMS):
- Asintomático: no presenta ni refiere síntomas
- Leve: síntomas leves, transitorios o que se resuelven espontáneamente
- Moderada: síntomas prolongados o pronunciados, requieren alguna medida terapéutica
- Severa: síntomas que ponen en peligro la vida, requieren intervención terapéutica enérgica por riesgo de muerte o secuelas
- Fatal: la muerte del paciente
- Sin Relación: los síntomas no se pueden atribuir a la exposición al agente referido

Nota: Si el paciente tiene más de una consulta, se consigna la sintomatología más severa (Mayor).

**RF-13: Estudios solicitados**
TEXT libre — exámenes complementarios solicitados (laboratorio, radiológicos, etc.)

**RF-14: Tratamiento (A-Previo, B-Recomendado)**
Dos columnas idénticas con checkboxes. Columna A = tratamiento realizado previo a la consulta al CIAT. Columna B = tratamiento recomendado por el CIAT.

Opciones de tratamiento (cada una con checkbox A y checkbox B):
- Ninguno
- Derivación a Institución Médica
- Dilución
- **Descontaminación Interna:**
  - Aspiración Gástrica
  - Lavado gástrico
  - Vómito provocado
  - Carbón Activado
  - Lavado intestinal y endoscopía
  - Catárticos
  - Descontaminación Externa (irrigación de piel, ojos u oídos)
  - Control clínico/Observación
- **Sintomático/sostén:**
  - Líquidos/electrolitos vía oral
  - Líquidos/electrolitos endovenoso
  - Nebulizaciones
  - Oxígeno normobárico
  - Oxígeno hiperbárico
  - Demulcentes
  - Intubación
  - Asistencia respiratoria Mecánica
  - Alcalinización (plasma)
  - Otro (especificar)
- **Aumento Eliminación:**
  - Carbón Activado seriado
  - Modificación del pH urinario
  - Métodos Extracorpóreos (diálisis, hemoperfusión, etc.)
- **Antídoto/Quelante/Faboterápico** (especificar cuál)
- **Otro fármaco** (especificar)
- **Consulta especialista** (especificar)
- **Desconocido**
- **Otro** (especificar)

Campo adicional de texto libre para indicaciones de relevancia.

**RF-15: Evolución y hospitalización**
Evolución (catálogo excluyente):
- Recuperación: retorno al estado previo sin secuelas
- Recuperación retardada: retorno al estado previo pero sin recuperación inmediata
- Muerte: especificar en comentarios si fue directa, indirecta o no relacionada con el agente
- Secuela: cualquier discapacidad persistente
- Desconocida

Hospitalización:
- Lugar (catálogo, selección múltiple): Sala General, UCI/UTI, Urgencias
- Tiempo (numérico + unidad: días o meses)
- Responsable (TEXT)

**RF-16: Comentario y firma**
- Comentario (TEXT libre — cualquier mención o consideración adicional)
- Firma del Responsable (TEXT — nombre del profesional responsable de la información/asistencia/asesoramiento)

---

### Módulo de Filtrado y Consulta (RF-17 a RF-21)

**RF-17: Filtrado por variables**
Filtrar registros por: agente tóxico, tipo de agente, rango de fechas, circunstancia, severidad, rango de edad, sexo, tipo de consulta, motivo de consulta, vía de ingreso, ubicación del evento, evolución, y combinaciones de estas variables.

**RF-18: Búsqueda por folio**
Buscar un registro específico por número de folio hospitalario.

**RF-19: Búsqueda de paciente recurrente**
Buscar todas las historias de un mismo paciente (ej: múltiples intentos de suicidio, múltiples mordeduras). Vinculado por nombre + folio.

**RF-20: Visualizar resultados**
Resultados en tabla con columnas principales. Al seleccionar un registro, se muestra el detalle completo.

**RF-21: Conteo de resultados**
Mostrar total de registros que coinciden con el filtro.

---

### Módulo de Estadísticas y Gráficas (RF-22 a RF-27)

**RF-22: Selección de variables para análisis**
Interfaz donde la administradora selecciona de 1 a 4 variables para cruzar. Variables disponibles: agente/tipo de agente, circunstancia, severidad, edad (por rangos), sexo, periodo de tiempo, vía de ingreso, ubicación del evento, tipo de consulta, evolución.

**RF-23: Gráficas básicas**
Generar gráficas a partir de los datos filtrados:
- Barras (ej: intoxicaciones por tipo de agente)
- Pastel/Dona (ej: distribución por circunstancia)
- Líneas temporales (ej: casos por mes/año para detectar tendencias estacionales)
- Barras agrupadas (ej: circunstancia por sexo)

**RF-24: Tabla de frecuencias**
Mostrar tabla con conteos y porcentajes del cruce de variables seleccionado.

**RF-25: Filtrado temporal para estadísticas**
Permitir seleccionar periodo: último mes, último trimestre, último año, rango personalizado, o todos los datos.

**RF-26: Exportar gráficas**
Exportar las gráficas generadas como imagen (PNG/JPG) para usar en presentaciones y reportes. La doctora las usa para pláticas en la Secretaría de Salud y congresos.

**RF-27: Dashboard resumen**
Pantalla inicial (tras login) con resumen rápido:
- Total de registros en la base de datos
- Registros capturados en el último mes
- Top 5 agentes más frecuentes
- Top 3 circunstancias más frecuentes
- Gráfica de tendencia mensual del año actual

---

### Módulo de Migración (RF-28 a RF-29)

**RF-28: Importar Excel**
Importar ~1,500 registros del Excel actual. La codificación numérica existente (mujer=0, hombre=1, accidental=0, ocupacional=1, etc.) se mapea automáticamente a los catálogos del sistema.

**RF-29: Reporte de migración**
Al finalizar: registros importados, registros con errores, registros con valores no mapeables.

---

### Módulo de Administración (RF-30 a RF-35)

**RF-30: Gestión de usuarios**
Solo administradoras crean/desactivan cuentas. Alumnos rotantes reciben cuentas temporales de capturista.

**RF-31: Autenticación**
Usuario y contraseña para acceder. Cada captura queda asociada al usuario que la realizó.

**RF-32: Respaldo cifrado**
Exportar base de datos completa a USB con cifrado. Nombre automático con fecha (ej: respaldo_CIAT_2026-03-23.db). Solo restaurable con contraseña de administrador.

**RF-33: Recordatorio de respaldo**
Aviso al iniciar sesión si han pasado más de X días sin respaldar (X configurable).

**RF-34: Editar catálogos**
Administradoras pueden agregar valores a catálogos. No pueden eliminar valores con registros asociados.

**RF-35: Registro de actividad**
Registrar qué usuario capturó cada registro y cuándo.

---

## Requisitos No Funcionales

**RNF-01: Usabilidad**
Un alumno nuevo completa su primer registro en < 15 minutos tras inducción básica. Catálogos muestran texto descriptivo, NO códigos numéricos. El formulario sigue el mismo orden visual que la ficha en papel para facilitar la transcripción.

**RNF-02: Rendimiento**
Carga de formulario < 3 segundos. Búsqueda/filtrado < 5 segundos sobre 1,500+ registros. Generación de gráficas < 10 segundos. Todo en computadora Windows 10 con recursos limitados.

**RNF-03: Seguridad**
Autenticación obligatoria. Contraseñas almacenadas con hash. Respaldos cifrados (AES-256 o equivalente). Solo administradoras gestionan accesos.

**RNF-04: Confidencialidad**
100% local. Cero conexiones externas. Sin telemetría. Sin nube. Datos de pacientes nunca salen de la computadora excepto en respaldos cifrados.

**RNF-05: Confiabilidad**
No perder datos ante cierre inesperado. Auto-guardado o guardado frecuente. Recuperación tras fallo.

**RNF-06: Portabilidad**
Migrar a otra computadora en < 30 minutos si la actual falla. Todo open source/gratuito. Sin licencias.

**RNF-07: Mantenibilidad**
Código documentado para que un futuro desarrollador continúe el proyecto. Catálogos editables desde la interfaz sin tocar código.

---

## Estructura de datos principal

### Historia clínica (tabla principal)

**Datos del paciente:**
- folio_expediente (TEXT, obligatorio, índice de búsqueda)
- nombre (TEXT)
- apellido (TEXT)
- direccion (TEXT)
- localidad (TEXT)
- telefono (TEXT)
- curp (TEXT, opcional)
- sexo (FK catálogo, excluyente: M/F)
- fecha_nacimiento (DATE)
- edad_valor (INTEGER, calculado)
- edad_unidad (CHAR: 'd'=días, 'm'=meses, 'a'=años, calculado)
- embarazo_lactancia (BOOLEAN, nullable, solo si sexo=F)
- escolaridad (TEXT)
- antecedentes_patologicos (TEXT libre)
- medico (TEXT)

**Datos de la consulta:**
- consulta_numero (INTEGER, autoincremental)
- tipo_frecuencia (FK catálogo: primera_vez / ulterior)
- tipo_contacto (FK catálogo: exposicion_presencial / telefonico)
- motivo_consulta (FK catálogo: intoxicacion / descartar_intoxicacion / asesoramiento)
- subtipo_presencial (FK catálogo, nullable: urgencias / internacion / consultorio_externo / via_electronico)
- fecha_hora_ingreso (DATETIME, nullable)
- fecha_hora_evento_exposicion (DATETIME, nullable — puede ser desconocida)
- fecha_hora_consulta (DATETIME)
- latencia_valor (INTEGER, calculado, nullable)
- latencia_unidad (CHAR: 'mi'=minutos, 'hr'=horas, 'di'=días, 'ms'=meses, 'a'=años, 'desc'=desconocida)

**Datos del interlocutor (solo si telefónico):**
- interlocutor_nombre (TEXT, nullable)
- interlocutor_categoria (FK catálogo: personal_salud / familiar / paciente / otro)
- interlocutor_categoria_especificar (TEXT, nullable)
- interlocutor_ubicacion_nombre (TEXT, nullable — nombre del establecimiento)
- interlocutor_ubicacion_tipo (FK catálogo: salud_con_internamiento / salud_sin_internamiento / hogar / trabajo / institucion_educativa / espacio_publico / otro)
- interlocutor_ubicacion_sector (FK catálogo, nullable: publico / privado)
- interlocutor_localidad (TEXT, nullable)
- interlocutor_telefono (TEXT, nullable)

**Datos de la intoxicación:**
- circunstancia_nivel1 (FK catálogo: no_intencional / intencional / reaccion_adversa / desconocido)
- circunstancia_nivel2 (FK catálogo según nivel1 — ver RF-05)
- circunstancia_otro_texto (TEXT, nullable)
- ubicacion_evento (FK catálogo: hogar / trabajo / inst_salud / inst_educativa / espacio_publico / otro)
- ubicacion_evento_otro (TEXT, nullable)
- tipo_exposicion (FK catálogo: aguda / cronica / aguda_sobre_cronica / desconocida)
- duracion_exposicion_valor (INTEGER, nullable)
- duracion_exposicion_unidad (CHAR, nullable)
- tipo_agente (FK catálogo — ver RF-09)
- agente_principio_activo (TEXT — nombre del agente/principio activo/nombre comercial)
- agente_cantidad_informada (TEXT, nullable)
- signos_sintomas (TEXT libre)
- fc (INTEGER, nullable — frecuencia cardíaca)
- fr (INTEGER, nullable — frecuencia respiratoria)
- temp (DECIMAL, nullable — temperatura)
- sat (INTEGER, nullable — saturación O2)
- ta (TEXT, nullable — tensión arterial)
- severidad (FK catálogo: asintomatico / leve / moderada / severa / fatal / sin_relacion)
- estudios_solicitados (TEXT libre, nullable)

**Vía de ingreso:** (relación muchos-a-muchos — selección múltiple)
- Tabla intermedia: historia_id + via_ingreso_id
- Valores: oral, inhalatoria, cutanea_mucosa, ocular, parenteral, mordedura_picadura, desconocida, otra
- otra_especificar (TEXT, nullable)

**Tratamiento:** (relación muchos-a-muchos con columna A/B)
- Tabla intermedia: historia_id + tratamiento_id + columna (A o B) + especificar (TEXT nullable)
- Cada tratamiento puede estar marcado en A, en B, o en ambos
- Campo adicional: tratamiento_notas (TEXT libre)

**Evolución y hospitalización:**
- evolucion (FK catálogo: recuperacion / recuperacion_retardada / muerte / secuela / desconocida)
- hospitalizacion_sala_general (BOOLEAN)
- hospitalizacion_uci_uti (BOOLEAN)
- hospitalizacion_urgencias (BOOLEAN)
- hospitalizacion_dias (INTEGER, nullable)
- hospitalizacion_responsable (TEXT, nullable)
- comentario (TEXT libre)
- firma_responsable (TEXT)

**Auditoría:**
- usuario_captura (FK a usuarios, automático)
- fecha_captura (DATETIME, automático)

### Catálogos (tablas separadas)
Cada catálogo tiene: id, nombre_descriptivo, codigo_numerico (compatible con Excel actual), activo (boolean). Los catálogos son editables desde la interfaz de administración.

- cat_sexo
- cat_tipo_frecuencia (primera_vez, ulterior)
- cat_tipo_contacto (presencial, telefonico)
- cat_motivo_consulta (intoxicacion, descartar, asesoramiento)
- cat_subtipo_presencial (urgencias, internacion, consultorio_externo, via_electronico)
- cat_categoria_interlocutor (personal_salud, familiar, paciente, otro)
- cat_ubicacion_interlocutor (salud_con_internamiento, salud_sin_internamiento, hogar, trabajo, inst_educativa, espacio_publico, otro)
- cat_sector (publico, privado)
- cat_circunstancia_nivel1 (no_intencional, intencional, reaccion_adversa, desconocido)
- cat_circunstancia_nivel2 (accidental, ocupacional, ambiental, alimentaria, error_terapeutico, mal_uso, medicina_tradicional, accidente_quimico, tentativa_suicida, abuso, automedicacion, aborto, homicidio, otro) — con FK a nivel1
- cat_ubicacion_evento (hogar, trabajo, inst_salud, inst_educativa, espacio_publico, otro)
- cat_tipo_exposicion (aguda, cronica, aguda_sobre_cronica, desconocida)
- cat_tipo_agente (medicamento, producto_veterinario, producto_industrial, producto_domestico, cosmetico, plaguicida_domestico, plaguicida_agricola, plaguicida_veterinario, plaguicida_salud_publica, droga_abuso, alimento_bebida, contaminante_ambiental, armas_quimicas, plantas, hongos, animales, agroquimicos, desconocido, otro)
- cat_via_ingreso (oral, inhalatoria, cutanea_mucosa, ocular, parenteral, mordedura_picadura, desconocida, otra)
- cat_severidad (asintomatico, leve, moderada, severa, fatal, sin_relacion)
- cat_tratamiento (ninguno, derivacion, dilucion, aspiracion_gastrica, lavado_gastrico, vomito_provocado, carbon_activado, lavado_intestinal, catarticos, descontaminacion_externa, control_clinico, liquidos_oral, liquidos_endovenoso, nebulizaciones, oxigeno_normobarico, oxigeno_hiperbarico, demulcentes, intubacion, asistencia_respiratoria, alcalinizacion, carbon_activado_seriado, modificacion_ph, metodos_extracorporeos, antidoto_quelante, otro_farmaco, consulta_especialista, desconocido, otro)
- cat_evolucion (recuperacion, recuperacion_retardada, muerte, secuela, desconocida)

### Usuarios
- id, nombre, usuario, password_hash, rol (admin/capturista), activo, fecha_alta, fecha_baja

---

## Referencia: campos de selección múltiple vs. excluyente

| Campo | Tipo | Notas |
|---|---|---|
| Sexo | Excluyente | M o F |
| Tipo de frecuencia | Excluyente | 1ª vez o Ulterior |
| Tipo de contacto | Excluyente | Presencial o Telefónico |
| Motivo de consulta | Excluyente | Intoxicación, Descartar, Asesoramiento |
| Subtipo presencial | Excluyente | Urgencias, Internación, Consultorio, Electrónico |
| Categoría interlocutor | Excluyente | Personal salud, Familiar, Paciente, Otro |
| Circunstancia nivel 1 | Excluyente | No intencional, Intencional, Reacción adversa, Desconocido |
| Circunstancia nivel 2 | Excluyente | Depende de nivel 1 |
| Ubicación evento | Excluyente | Hogar, Trabajo, Inst. salud, etc. |
| Tipo de exposición | Excluyente | Aguda, Crónica, Aguda s/crónica, Desconocida |
| Tipo de agente | Excluyente | Medicamento, Plaguicida, Animal, etc. |
| **Vía de ingreso** | **MÚLTIPLE** | Puede ser Oral Y Inhalatoria simultáneamente |
| Severidad | Excluyente | Asintomático, Leve, Moderada, Severa, Fatal, Sin relación |
| **Tratamiento A** | **MÚLTIPLE** | Múltiples tratamientos previos posibles |
| **Tratamiento B** | **MÚLTIPLE** | Múltiples tratamientos recomendados posibles |
| Evolución | Excluyente | Recuperación, Muerte, Secuela, etc. |
| **Hospitalización lugar** | **MÚLTIPLE** | Puede estar en Urgencias Y luego Sala General |
| Embarazo/Lactancia | Excluyente | Sí o No (solo si sexo=F) |
