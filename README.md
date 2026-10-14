# programacion-architect

Skill para asistentes de IA con soporte de *skills* (probada con Claude Code) que ayuda a cualquier docente a preparar la documentación **auditable** de una materia o módulo: programación didáctica, situaciones de aprendizaje, temporalización real, cuaderno del profesor y entregables en ODT.

La idea de partida: una auditoría se supera con **trazabilidad**, no con volumen. Por eso la skill:

1. Empieza por un **listado de lo que hay que presentar**, con la fuente de cada requisito y si está *verificado* (leído de una norma o documento aportado) o *propuesto* (sugerencia de la skill).
2. Saca el **texto oficial y las cifras con scripts**, no de memoria: el currículo se copia literal del PDF oficial y las sesiones salen de horario × calendario.
3. Termina comparando lo generado con ese listado, documento por documento.

> **Lo que no promete.** Ninguna herramienta garantiza «pasar cualquier auditoría». La skill garantiza cubrir el listado que la docente confirme. Que ese listado sea el que pide su Inspección o su centro depende de la norma de su comunidad y de los documentos que aporte. Lo que no está verificado queda como `_Pendiente_`.

## Etapas y enseñanzas que cubre

| Enseñanza | Estado |
|---|---|
| **ESO y ámbitos de PDC** (Canarias) | Cubierta por esta skill: perfil parcial, extractores de currículo, sesiones, SdA, cuaderno y ODT |
| **Ciclos formativos (FP): programaciones de módulos** | Se generan con la skill hermana [**`fp-module-architect`**](https://github.com/nievespitti/fp-module-architect), publicada en un repositorio aparte (ver la sección siguiente) |
| **FEOE (formación en empresa): seguimiento y ficha de seguimiento** | Ídem: los genera `fp-module-architect` |
| Bachillerato y Primaria | Sin perfil ni extractor todavía; el método (listado, trazabilidad, sesiones reales) es el mismo y se puede crear un perfil |

## Ciclos formativos (FP) y FEOE

La programación de módulos de ciclos formativos y el seguimiento de la FEOE se generan con [`fp-module-architect`](https://github.com/nievespitti/fp-module-architect), una skill con otro flujo (módulo, resultados de aprendizaje y criterios de evaluación, SdA con sus documentos, tabla maestra, cuaderno con hoja de seguimiento de la FEOE y ficha de seguimiento, validador de la documentación). Se ha usado en módulos reales de Sistemas Microinformáticos y Redes. **Hoy esta skill (`programacion-architect`) no genera esos documentos por sí sola.**

Las dos skills se instalan por separado y se pueden usar a la vez. El plan es incorporar FP a este repositorio como un perfil más (`profiles/`), compartiendo el listado de documentos, el cálculo de sesiones y el cuaderno. Si te interesa esa unificación, abre una incidencia para que se priorice.

## Qué incluye

| Carpeta | Contenido |
|---|---|
| `SKILL.md` | Instrucciones de la skill: reglas, fases A a G y capas de perfil |
| `profiles/` | Perfiles por comunidad, etapa y materia, y `plataformas.json` (aulas virtuales y plataformas de calificaciones). Hoy hay un perfil, parcialmente verificado: Tecnología y Digitalización de Canarias (1.º a 3.º ESO). `_plantilla-perfil.json` sirve para crear otros |
| `centros/` | Datos de centro: `ejemplo-centro.json` (ficticio) y `_plantilla-centro.json` (vacía) |
| `scripts/` | Herramientas en Python (ver abajo) |
| `examples/` | Un plan y un currículo **ficticios** para probar los scripts |

### Scripts

| Script | Qué hace |
|---|---|
| `extract_curriculo_eso.py` | Extrae literalmente de un PDF de currículo de ESO (formato de Canarias) las competencias específicas, criterios, descriptores y saberes de un curso |
| `extract_curriculo_pdc.py` | Lo mismo para el anexo del ámbito Lingüístico y Social de los Programas de Diversificación Curricular (Canarias) |
| `sesiones.py` | Calcula las sesiones reales (horario × calendario − festivos y periodos sin clase) y las reparte por trimestres |
| `render_marcadores.py` | Rellena plantillas con el texto oficial literal (`{{CRITERIOS:1.2,1.3}}`, `{{SABERES:I.4}}`, `{{SESIONES:...}}`, etc.) |
| `build_cuaderno_niveles.py` | Genera el cuaderno del profesor (xlsx): sesiones, asistencia, evaluación por criterio con niveles y calificación. Para evaluación **descriptiva por niveles**, sin pesos |
| `md_to_odt.py` | Convierte borradores Markdown a ODT (LibreOffice/OpenOffice) |
| `alexia_items.py` | Lista los ítems que hay que crear en el cuaderno de la plataforma Alexia a partir del currículo |

## Qué hay que instalar

- **Python 3.10 o superior** (probado con 3.13).
- Dependencias: `pip install -r requirements.txt` (`pymupdf`, `odfpy`, `openpyxl`).
- Un asistente con soporte de skills. En **Claude Code**, la carpeta de la skill va en `~/.claude/skills/` (en Windows, `%USERPROFILE%\.claude\skills\`).

```bash
git clone https://github.com/nievespitti/programacion-architect.git ~/.claude/skills/programacion-architect
pip install -r ~/.claude/skills/programacion-architect/requirements.txt
```

No hace falta LibreOffice para generar los ODT, pero sí para abrirlos y exportarlos a PDF. Los ODT no se han probado en todas las versiones de LibreOffice; si algo se ve raro (anchos de tabla, saltos de página), abre una incidencia.

## Cómo se usa

En el asistente, pídele que programe tu materia («usa programacion-architect para programar Lengua de 2.º ESO…»). La skill te preguntará, por este orden:

1. **Fase A. Qué hay que presentar:** comunidad, etapa, materia, curso, quién audita, plataformas (aula virtual y calificaciones) y si el centro tiene plantilla propia. Te muestra el listado con fuentes y estados y espera tu confirmación.
2. **Fase B. Datos del curso:** centro, grupos, horario, calendario del centro (festivos, libre disposición, evaluaciones).
3. **Fase C. Currículo oficial:** extrae del PDF que aportes el texto literal. Tú compruebas el recuento.
4. **Fase D a G:** plan, sesiones reales, situaciones de aprendizaje una a una, cuaderno del profesor e informe final contra el listado.

Para probar los scripts sin datos reales:

```bash
python scripts/sesiones.py examples/plan.ejemplo.json --out sesiones.md
python scripts/build_cuaderno_niveles.py examples/plan.ejemplo.json --curriculo examples/curriculo.ejemplo.json --out cuaderno.xlsx
```

Las entregas para docentes y centros deben ir en **ODT o PDF**, no en Markdown: usa `md_to_odt.py` y exporta el PDF desde LibreOffice.

## Alcance y límites

- **Solo hay material de Canarias, y parcial.** Los extractores leen la estructura de los PDF oficiales de Canarias. Otras comunidades tienen formatos distintos: hay que adaptar el extractor y crear el perfil (ver [CONTRIBUTING.md](CONTRIBUTING.md)).
- **El modelo de evaluación se pregunta siempre.** El cuaderno actual cubre evaluación por niveles (por defecto IN, SU, BI, NT, SB, los de Canarias; se cambian en `plan.json`). Si tu comunidad califica con notas numéricas o ponderaciones, el cuaderno no sirve tal cual.
- **Plataformas.** Solo Alexia, EVAGD y Moodle tienen efectos descritos en el listado; para otras (Séneca, Rayuela, Educamos, Additio…) se registra cómo las usa el centro, pero la skill no añade documentos.
- **Pendiente:** validador automático contra el listado, exportación a Word con cabecera del centro y perfiles de otras comunidades.
- **No es asesoramiento normativo.** Contrasta siempre con la normativa vigente de tu comunidad y con tu centro.

## Datos personales

No subas al repositorio datos del alumnado, programaciones de otros docentes ni documentos internos del centro. El `.gitignore` excluye `proyectos/` y los archivos `*_con_nombres.*`. En los cuadernos, el alumnado se identifica como «Alumno/a n».

## Contribuir

Se agradecen sobre todo **perfiles de otras comunidades y materias** y adaptaciones de los extractores. Lee [CONTRIBUTING.md](CONTRIBUTING.md).

## Licencia

[MIT](LICENSE).
