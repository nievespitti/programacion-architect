---
name: programacion-architect
description: Genera la documentación auditable de una materia o módulo (programación didáctica, situaciones de aprendizaje, instrumentos de evaluación, temporalización real y cuaderno del profesor) para cualquier docente, etapa y comunidad. Empieza SIEMPRE por el listado de lo que hay que presentar (checklist verificado con su fuente) y valida al final contra ese listado. Úsala cuando una docente pida programar una materia (ESO, Bachillerato, FP, Primaria...), preparar una inspección o crear su cuaderno. Para módulos de FP existe la skill hermana fp-module-architect (no incluida en este repositorio); esta no la sustituye.
---

# programacion-architect

Estado: **v0.2.** Hecho: Fase A (checklist y perfiles), extractores de currículo (ESO de Canarias y ámbito de PDC de Canarias), cálculo de sesiones reales, marcadores con texto oficial literal, cuaderno del profesor en hoja de cálculo (evaluación descriptiva por niveles) y conversión de borradores a ODT. Pendiente: validador contra el checklist, exportación a Word con cabecera del centro, perfiles de otras comunidades. No decir que la skill "completa" algo que aún no genera.

## Idea central
La auditoría se supera con trazabilidad, no con volumen. Por eso:
1. Primero se fija **qué hay que presentar** (checklist con fuente y estado).
2. El texto oficial y las cifras salen de scripts, nunca de memoria.
3. Al final un informe compara lo generado con el checklist, documento por documento.
Ninguna skill garantiza "pasar cualquier auditoría": garantiza cobertura del checklist que la docente confirmó. Que ese checklist sea el que pide su Inspección depende de la norma de su comunidad.

## Reglas que no se saltan
0. Las entregas para docentes van en **ODT o PDF**, nunca en `.md` (los `.md` son borradores internos). `scripts/md_to_odt.py` convierte; no hay LibreOffice garantizado, así que el PDF se genera desde el ODT en la máquina de la docente.
1. No inventar requisitos normativos. Lo que no esté en un perfil verificado o en un documento aportado va como `_Pendiente_` y se pregunta.
2. Currículo literal: se extrae del PDF oficial con el extractor del perfil. Nunca reformulado ni de memoria.
3. Nada de datos inventados: alumnado, fechas, festivos, pesos, NEAE. Si falta, se pregunta o queda `[[REDACTAR: ...]]` (el validador lo rechaza).
4. Una SdA por vez: redactar, generar, validar, corregir, y solo entonces la siguiente.
5. No decir "completo" sin ejecutar el validador y adjuntar su informe literal.
6. Trato con la docente: tuteo o "ustedes" según su preferencia; sin infantilizar.
7. Sin datos personales del alumnado ni de terceros en el proyecto (alumnos como «Alumno/a n»; las programaciones de otros docentes se usan como modelo pero no se copian ni se suben).

## Fases (cada una termina con una puerta)

**A. Qué hay que presentar.**
1. Preguntar: comunidad autónoma, etapa/enseñanza, materia o módulo, curso/s, tipo de centro, quién audita y si el centro tiene modelo de programación.
   **Plataformas** (se preguntan siempre; ver `profiles/plataformas.json`): aula virtual (EVAGD, Moodle propio, Classroom, Teams, otra, ninguna), plataforma de calificaciones (Alexia, otra, Excel propio) y, si aplica, la de seguimiento de la FEOE. Guardarlas en `plan.json` bajo `plataformas`.
2. Buscar un perfil en `profiles/`. Si existe, mostrar su listado con estado (`verificado` = leído de una fuente; `propuesto` = sugerencia de la skill). Si no existe, pedir la norma o el modelo del centro y construir el listado desde ahí.
   Añadir al listado los `documentos_si` de cada plataforma elegida (p. ej. Alexia añade el mapeo de columnas y fórmulas; EVAGD o Moodle añaden la estructura del aula). Las plataformas también adaptan el cuaderno (columna de evidencia y fechas de cierre de notas) y los materiales del alumnado.
3. Mostrar a la docente el listado como tabla: documento, exigido por, fuente, estado. Recoger qué documentos añade o quita su centro.
Puerta: la docente confirma el listado. Guardarlo en `<carpeta>/checklist_documentos.md`.

**B. Datos del curso (preguntar, no suponer).** Centro, grupo/s y nº de alumnado, horario semanal por franjas, calendario del centro (inicio, evaluaciones, vacaciones, festivos, días no lectivos y de libre disposición, actos). Si vienen en foto o PDF, leerlos con cuidado y devolver una transcripción para confirmar: los colores de leyenda se confunden. Distinguir días que restan clase (festivos, vacaciones, libre disposición) de los que no (claustro, reuniones).
Puerta: transcripción confirmada.

**C. Currículo oficial.** `python scripts/extract_curriculo_eso.py <pdf> --curso N --out <carpeta>/curriculo_oficial.json` (materias de ESO). Para el anexo del ámbito Lingüístico y Social de PDC (Canarias): `python scripts/extract_curriculo_pdc.py <pdf> --curso N --out ...`. Comprobar a mano el nº de competencias, criterios y bloques de saberes contra el PDF y revisar los `avisos`.

**D. plan.json y horas reales.** (pendiente de construir)

**E. Documentos por SdA.** (pendiente de construir)

**F. Cuaderno del profesor.** Para evaluación descriptiva por niveles (sin pesos): `python scripts/build_cuaderno_niveles.py <plan.json> --curriculo curriculo_oficial.json --out Cuaderno_profesor.xlsx`. Necesita `sdas` con unidades, tramos de sesiones y criterios en plan.json. Hojas: Léame, Calendario, Unidades, Sesiones, Alumnado, Asistencia, Eval 1-3 y Calificación (sin nombres reales; fórmulas COUNTIF probadas con la librería `formulas`). Para evaluación por pesos hay que construir otro script (el de FP, `fp-module-architect`, usa módulos y pesos).

**G. Informe final.** (pendiente de construir) Tabla: cada documento del checklist con "generado y validado", "falta" o "pendiente de confirmar fuente".

## Capas de perfil (se combinan)
1. **Currículo** (comunidad + etapa + materia): `profiles/*.json` y su extractor.
2. **Centro** (plantilla propia, modelo pedagógico, calendario): `centros/*.json`. Lo que el centro exige puede ser más que la norma. Pedir siempre la plantilla real del centro y, si hay, una programación de un curso anterior como modelo.
3. **Plataformas** (aula virtual y calificaciones): `profiles/plataformas.json`.
4. **Modelo de evaluación**: preguntar siempre. Puede ser *numérico por pesos* (cada producto aporta un % al criterio; el validador exige que sumen 100) o *descriptivo por niveles* (rúbrica sin porcentajes ni media automática). Condiciona el cuaderno y el mapeo de calificaciones. No asumir uno.

## Material ya en uso
Si la docente ya trabaja con un paquete o curso en marcha (p. ej. un curso Moodle con tareas y rúbricas), ese paquete es la referencia prioritaria: leerlo entero antes de proponer nada, copiarlo como original al proyecto y alinear plan.json con él (SdA, tareas, criterios, modelo de evaluación). Señalar sus desajustes (alumnado, fechas) sin reescribirlo a espaldas de la docente.

## Calendarios
Un calendario de ciclos formativos no sirve para ESO (y al revés). Antes de calcular sesiones, comprobar que el documento trae el curso y la etapa correctos y que el año es el del curso que se programa. Pedir por separado: inicio y fin de clases, fechas de evaluación y días no lectivos del centro.

## Perfiles disponibles
- `canarias-eso-tecnologia-digitalizacion` (1.º a 3.º ESO). Parcial: ver `estado_verificacion` en el JSON.
- Para cualquier otra comunidad o materia no hay perfil verificado: se construye uno desde la norma y el currículo que aporte la docente, partiendo de `profiles/_plantilla-perfil.json`. Ver `CONTRIBUTING.md`.

Centros: `centros/ejemplo-centro.json` es un ejemplo ficticio; `centros/_plantilla-centro.json` es la plantilla vacía.

Para añadir un perfil: copiar `_plantilla-perfil.json`, cambiar comunidad, etapa y materia, y marcar `estado` honestamente (`verificado` solo si se leyó de una fuente que se cita). Un perfil nuevo necesita su propio extractor si el PDF tiene otra estructura.
