# Cómo contribuir

El mayor valor que puede aportar alguien de otra comunidad es un **perfil verificado**: qué documentos exige su Consejería para una etapa y materia, con la fuente de cada uno.

## Añadir un perfil de comunidad, etapa y materia

1. Copia `profiles/_plantilla-perfil.json` a `profiles/<comunidad>-<etapa>-<materia>.json`.
2. Rellena `comunidad`, `etapa`, `materia`, `cursos` y `fuente_curricular` (nombre del PDF o disposición oficial).
3. En `requisitos_verificados_en_curriculo`, anota solo lo que has leído, con la página.
4. En `documentos`, cada entrada lleva `exigido_por`, `fuente` y `estado`:
   - `verificado`: lo exige una norma o documento que citas.
   - `propuesto`: lo sugiere la skill pero no está confirmado.
   - Si no sabes quién lo exige, escribe `_Pendiente_`. **No inventes requisitos normativos.**
5. Escribe en `estado_verificacion` qué es parcial y qué no se ha comprobado.
6. Si el PDF del currículo de tu comunidad tiene otra estructura, adapta o copia `scripts/extract_curriculo_eso.py` y pruébalo con un curso real. Comprueba a mano el número de competencias, criterios y bloques de saberes contra el PDF.

## Añadir una plataforma

En `profiles/plataformas.json`, añade la opción en `opciones` y, si sabes qué documentos genera o condiciona, una entrada en `efectos` con `rol`, `documentos_si` y `afecta_a`.

## Antes de enviar una contribución

- No incluyas datos de alumnado, nombres de docentes que no sean autores, programaciones ajenas ni documentos internos de ningún centro. Los ejemplos deben ser ficticios.
- Si añades un script, que funcione con `examples/` o con datos ficticios que incluyas.
- Comprueba que los textos oficiales salen de un script o de una cita con fuente, no de memoria.
- Ejecuta los scripts de ejemplo del README para ver que siguen funcionando.
