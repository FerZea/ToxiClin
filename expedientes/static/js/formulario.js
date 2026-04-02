/**
 * formulario.js — Lógica dinámica del formulario de historia clínica
 * ToxiClin — CIAT
 *
 * Contenido:
 *   1. Mostrar/ocultar campos según tipo de contacto (presencial/telefónico)
 *   2. Mostrar campo embarazo solo si sexo = Femenino
 *   3. Cálculo automático de edad desde fecha de nacimiento
 *   4. Cálculo automático de latencia
 *   5. Dropdown dependiente: circunstancia nivel 1 → nivel 2
 *   6. Mostrar campo "especificar" cuando se elige "Otro"
 *   7. Mostrar campo "vía otra" si se marca "Otra" en vías de ingreso
 */

document.addEventListener('DOMContentLoaded', function () {

    // ─── Referencias a los campos del formulario ───────────────────────────
    const tipoContacto     = document.getElementById('id_tipo_contacto');
    const sexoSelect       = document.getElementById('id_sexo');
    const fechaNacimiento  = document.getElementById('id_fecha_nacimiento');
    const fechaConsulta    = document.getElementById('id_fecha_hora_consulta');
    const fechaIngreso     = document.getElementById('id_fecha_hora_ingreso');
    const fechaExposicion  = document.getElementById('id_fecha_hora_evento_exposicion');
    const circN1           = document.getElementById('id_circunstancia_nivel1');
    const circN2           = document.getElementById('id_circunstancia_nivel2');
    const ubicacionEvento  = document.getElementById('id_ubicacion_evento');
    const catInterlocutor  = document.getElementById('id_interlocutor_categoria');
    const ubicInterlocutor = document.getElementById('id_interlocutor_ubicacion_tipo');

    // ─── 1. Tipo de contacto: presencial vs telefónico ─────────────────────

    function actualizarTipoContacto() {
        if (!tipoContacto) return;

        const texto = tipoContacto.options[tipoContacto.selectedIndex]?.text || '';
        const esPresencial  = texto.toLowerCase().includes('presencial');
        const esTelefonico  = texto.toLowerCase().includes('telef');

        mostrar('campo-subtipo-presencial', esPresencial);
        mostrar('campo-fecha-ingreso',      esPresencial);
        mostrar('seccion-interlocutor',     esTelefonico);
    }

    if (tipoContacto) {
        tipoContacto.addEventListener('change', actualizarTipoContacto);
        actualizarTipoContacto(); // Ejecutar al cargar por si ya hay valor
    }

    // ─── 2. Embarazo: solo si sexo = Femenino ──────────────────────────────

    function actualizarEmbarazo() {
        if (!sexoSelect) return;
        const texto = sexoSelect.options[sexoSelect.selectedIndex]?.text || '';
        mostrar('campo-embarazo', texto.toLowerCase().includes('femenino'));
    }

    if (sexoSelect) {
        sexoSelect.addEventListener('change', actualizarEmbarazo);
        actualizarEmbarazo();
    }

    // ─── 3. Cálculo de edad ────────────────────────────────────────────────

    function calcularEdad() {
        const displayEdad = document.getElementById('edad-display');
        if (!displayEdad || !fechaNacimiento) return;

        const nacStr     = fechaNacimiento.value;
        const consultaStr = fechaConsulta ? fechaConsulta.value : null;

        if (!nacStr) { displayEdad.value = ''; return; }

        const nacimiento = new Date(nacStr);
        // Usar la fecha de consulta si está disponible, si no usar hoy
        const referencia = consultaStr ? new Date(consultaStr) : new Date();

        if (isNaN(nacimiento.getTime())) { displayEdad.value = ''; return; }

        const diffMs   = referencia - nacimiento;
        const diffDias = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffDias < 0) {
            displayEdad.value = 'Fecha inválida';
        } else if (diffDias < 30) {
            displayEdad.value = diffDias + ' día' + (diffDias !== 1 ? 's' : '');
        } else if (diffDias < 365) {
            const meses = Math.floor(diffDias / 30);
            displayEdad.value = meses + ' mes' + (meses !== 1 ? 'es' : '');
        } else {
            // Cálculo exacto de años cumplidos
            let anios = referencia.getFullYear() - nacimiento.getFullYear();
            const m = referencia.getMonth() - nacimiento.getMonth();
            if (m < 0 || (m === 0 && referencia.getDate() < nacimiento.getDate())) {
                anios--;
            }
            displayEdad.value = anios + ' año' + (anios !== 1 ? 's' : '');
        }
    }

    if (fechaNacimiento) fechaNacimiento.addEventListener('change', calcularEdad);
    if (fechaConsulta)   fechaConsulta.addEventListener('change', calcularEdad);
    calcularEdad();

    // ─── 4. Cálculo de latencia ────────────────────────────────────────────

    function calcularLatencia() {
        const displayLatencia = document.getElementById('latencia-display');
        if (!displayLatencia) return;

        const expStr = fechaExposicion ? fechaExposicion.value : null;
        if (!expStr) { displayLatencia.value = 'Desconocida'; return; }

        // Referencia: ingreso (presencial) o consulta (telefónico)
        const texto = tipoContacto
            ? (tipoContacto.options[tipoContacto.selectedIndex]?.text || '')
            : '';
        const esPresencial = texto.toLowerCase().includes('presencial');
        const refStr = esPresencial
            ? (fechaIngreso ? fechaIngreso.value : null)
            : (fechaConsulta ? fechaConsulta.value : null);

        if (!refStr) { displayLatencia.value = '—'; return; }

        const exposicion  = new Date(expStr);
        const referencia  = new Date(refStr);
        const diffMinutos = Math.floor((referencia - exposicion) / (1000 * 60));

        if (diffMinutos < 0) {
            displayLatencia.value = 'Fecha inválida';
        } else if (diffMinutos < 60) {
            displayLatencia.value = diffMinutos + ' min';
        } else if (diffMinutos < 1440) {
            displayLatencia.value = Math.floor(diffMinutos / 60) + ' hr';
        } else if (diffMinutos < 43200) {
            displayLatencia.value = Math.floor(diffMinutos / 1440) + ' día(s)';
        } else if (diffMinutos < 525600) {
            displayLatencia.value = Math.floor(diffMinutos / 43200) + ' mes(es)';
        } else {
            displayLatencia.value = Math.floor(diffMinutos / 525600) + ' año(s)';
        }
    }

    if (fechaExposicion) fechaExposicion.addEventListener('change', calcularLatencia);
    if (fechaIngreso)    fechaIngreso.addEventListener('change', calcularLatencia);
    if (fechaConsulta)   fechaConsulta.addEventListener('change', calcularLatencia);
    if (tipoContacto)    tipoContacto.addEventListener('change', calcularLatencia);
    calcularLatencia();

    // ─── 5. Circunstancia nivel 2 dependiente del nivel 1 (AJAX) ──────────

    function cargarCircunstanciasN2() {
        if (!circN1 || !circN2) return;

        const nivel1Id = circN1.value;

        // Limpiar el nivel 2
        circN2.innerHTML = '<option value="">— Seleccionar —</option>';

        if (!nivel1Id) return;

        // Llamada AJAX al servidor para obtener las opciones de nivel 2
        fetch(URL_CIRCUNSTANCIAS_N2 + '?nivel1_id=' + nivel1Id)
            .then(response => response.json())
            .then(data => {
                data.opciones.forEach(function (op) {
                    const option = document.createElement('option');
                    option.value = op.id;
                    option.textContent = op.nombre;
                    circN2.appendChild(option);
                });
            })
            .catch(function () {
                console.error('Error al cargar circunstancias nivel 2');
            });

        // Mostrar "Otro" si el nivel 1 seleccionado lo permite
        const textoN1 = circN1.options[circN1.selectedIndex]?.text || '';
        mostrar('campo-circunstancia-otro',
            textoN1.toLowerCase().includes('otro'));
    }

    if (circN1) {
        circN1.addEventListener('change', cargarCircunstanciasN2);
    }

    // Mostrar "Otro" en nivel 2 cuando se selecciona esa opción
    if (circN2) {
        circN2.addEventListener('change', function () {
            const texto = circN2.options[circN2.selectedIndex]?.text || '';
            mostrar('campo-circunstancia-otro', texto.toLowerCase().includes('otro'));
        });
    }

    // ─── 6. Ubicación del evento: mostrar "otro" ───────────────────────────

    if (ubicacionEvento) {
        ubicacionEvento.addEventListener('change', function () {
            const texto = ubicacionEvento.options[ubicacionEvento.selectedIndex]?.text || '';
            mostrar('campo-ubicacion-otro', texto.toLowerCase().includes('otro'));
        });
        // Estado inicial
        const textoUbic = ubicacionEvento.options[ubicacionEvento.selectedIndex]?.text || '';
        mostrar('campo-ubicacion-otro', textoUbic.toLowerCase().includes('otro'));
    }

    // ─── Interlocutor: categoría "Otro" → mostrar especificar ─────────────

    if (catInterlocutor) {
        catInterlocutor.addEventListener('change', function () {
            const texto = catInterlocutor.options[catInterlocutor.selectedIndex]?.text || '';
            mostrar('campo-interlocutor-especificar', texto.toLowerCase().includes('otro'));
        });
    }

    // ─── Interlocutor: tipo establecimiento salud → mostrar sector ─────────

    if (ubicInterlocutor) {
        ubicInterlocutor.addEventListener('change', function () {
            const texto = ubicInterlocutor.options[ubicInterlocutor.selectedIndex]?.text || '';
            const esSalud = texto.toLowerCase().includes('salud');
            mostrar('campo-sector', esSalud);
        });
    }

    // ─── 7. Vía de ingreso "Otra" → mostrar especificar ────────────────────

    const viasCheckboxes = document.querySelectorAll('input[name="vias_ingreso"]');
    function verificarViaOtra() {
        let hayOtra = false;
        viasCheckboxes.forEach(function (cb) {
            // El label del checkbox contiene el nombre de la vía
            const label = cb.closest('label') || cb.parentElement;
            if (label && label.textContent.toLowerCase().includes('otra') && cb.checked) {
                hayOtra = true;
            }
        });
        mostrar('campo-via-otra', hayOtra);
    }
    viasCheckboxes.forEach(cb => cb.addEventListener('change', verificarViaOtra));
    verificarViaOtra();


    // ─── Utilidad: mostrar/ocultar un elemento por ID ──────────────────────
    function mostrar(id, visible) {
        const el = document.getElementById(id);
        if (el) el.style.display = visible ? '' : 'none';
    }

});
