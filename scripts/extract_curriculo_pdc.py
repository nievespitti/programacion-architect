#!/usr/bin/env python3
"""Extrae LITERALES del anexo de currículo de Programas de Diversificación Curricular (PDC) de ESO, Canarias
(ámbito Lingüístico y Social; el formato de los otros ámbitos puede ser distinto): competencias específicas,
criterios de evaluación con sus descriptores del Perfil de salida, y saberes básicos de un curso.

Uso: python extract_curriculo_pdc.py <pdf> --curso 2 [--out curriculo_oficial.json]

Formato que reconoce:
  "Curso N.º. Ámbito ..." abre el bloque del curso (hasta el siguiente "Curso M.º." o el final).
  Por cada competencia: "Competencia específica" / "N. texto" / "Descriptores operativos..." / códigos /
  "Criterios de evaluación" / "N.M[.] texto" + códigos / "Explicación del bloque competencial" (se ignora).
  "Saberes básicos" / "Bloque I. Título" / "N. texto" / "N.M." solo en una línea + texto en las siguientes.
Particularidades que maneja (vistas en el PDF real): números de página sueltos, cabeceras "Descriptores operativos"
que se cuelan en mitad del texto, códigos de un criterio partidos por el salto de página, "5.1" sin punto final.
Salida: {"materia","curso","competencias":[{"n","texto","descriptores","criterios":[{"id","texto","descriptores"}]}],
         "saberes":[{"bloque","titulo","items":[{"id","texto"}]}], "avisos":[...]}
Nunca rellena con texto de memoria: lo que no cuadra va a "avisos".
"""
import argparse, json, re, sys

try:
    import pymupdf
except ImportError:
    import fitz as pymupdf

CODES = re.compile(r"^(?:[A-Z]{2,5}\d(?:,\s*|\s+|$))+$")
PAGE = re.compile(r"^\d{1,3}$")
CURSO = re.compile(r"^Curso (\d)\.º\.\s*(.*)$")
COMP = re.compile(r"^(\d+)\.\s+(\S.*)$")
CRIT = re.compile(r"^(\d+\.\d+)\.?\s+(\S.*)$")
BLOQUE = re.compile(r"^Bloque ([IVX]+)\.\s*(.*?)\s*$")
SUBID = re.compile(r"^(\d+\.\d+)\.\s*$")
TOPITEM = re.compile(r"^(\d+)\.\s+(\S.*)$")
HEAD1 = "Descriptores operativos de las"
HEAD2 = "competencias clave. Perfil de salida"


def lines_of(pdf):
    doc = pymupdf.open(pdf)
    out = []
    for p in doc:
        out += [l.rstrip() for l in p.get_text().splitlines()]
    return out


def curso_block(lines, curso):
    start = end = None
    materia = ""
    for i, l in enumerate(lines):
        m = CURSO.match(l.strip())
        if not m:
            continue
        if int(m.group(1)) == curso and start is None:
            start, materia = i + 1, m.group(2).strip()
        elif start is not None and int(m.group(1)) != curso:
            end = i
            break
    if start is None:
        sys.exit(f"No encuentro 'Curso {curso}.º.' en el PDF")
    return materia, lines[start:end]


def clean(lines):
    """Quita números de página y líneas vacías; conserva el resto."""
    return [l.strip() for l in lines if l.strip() and not PAGE.match(l.strip())]


def codes_of(chunks):
    return [c for c in re.split(r"[,\s]+", " ".join(chunks).strip()) if c]


def parse_competencias(lines, avisos):
    comps, cur, crit = [], None, None
    mode = None  # 'ctext','cdesc','crit'
    ctext, cdesc, ttext, tdesc = [], [], [], []

    def close_crit():
        nonlocal crit, ttext, tdesc
        if crit is not None:
            crit["texto"] = " ".join(ttext).strip()
            crit["descriptores"] = codes_of(tdesc)
            cur["criterios"].append(crit)
        crit, ttext, tdesc = None, [], []

    def close_comp():
        nonlocal cur, ctext, cdesc
        if cur is not None:
            close_crit()
            cur["texto"] = " ".join(ctext).strip()
            cur["descriptores"] = codes_of(cdesc)
            comps.append(cur)
        cur, ctext, cdesc = None, [], []

    for l in lines:
        if l == "Competencia específica":
            close_comp()
            cur = {"n": None, "texto": "", "descriptores": [], "criterios": []}
            mode = "ctext"
            continue
        if cur is None:
            continue
        if l == "Criterios de evaluación":
            mode = "crit"
            continue
        if l == "Explicación del bloque competencial":
            close_crit()
            mode = "skip"
            continue
        if mode == "skip":
            continue
        if l in (HEAD1, HEAD2):
            if mode == "ctext":
                mode = "cdesc_wait"  # los códigos siguen; el texto puede continuar tras el salto de página
            continue
        if mode in ("ctext", "cdesc_wait"):
            if CODES.match(l):
                cdesc.append(l)
                mode = "cdesc"
            elif mode == "ctext" or mode == "cdesc_wait":
                m = COMP.match(l) if cur["n"] is None else None
                if m:
                    cur["n"] = int(m.group(1))
                    ctext.append(m.group(2))
                else:
                    ctext.append(l)
            continue
        if mode == "cdesc":
            if CODES.match(l):
                cdesc.append(l)
            else:  # el texto de la competencia puede seguir tras los códigos (salto de página)
                ctext.append(l)
            continue
        if mode == "crit":
            m = CRIT.match(l)
            if m and not CODES.match(l):
                close_crit()
                crit = {"id": m.group(1)}
                ttext = [m.group(2)]
                continue
            if crit is None:
                continue
            if CODES.match(l):
                tdesc.append(l)
            else:
                ttext.append(l)
    close_comp()
    for c in comps:
        if not c["criterios"]:
            avisos.append(f"Competencia {c['n']} sin criterios")
        if not c["descriptores"]:
            avisos.append(f"Competencia {c['n']} sin descriptores")
        for k in c["criterios"]:
            if not k["descriptores"]:
                avisos.append(f"Criterio {k['id']} sin descriptores")
            if not k["id"].startswith(f"{c['n']}."):
                avisos.append(f"Criterio {k['id']} bajo la competencia {c['n']}")
    return comps


def parse_saberes(lines, avisos):
    bloques, cur = [], None
    item = None
    top = None

    def close_item():
        nonlocal item
        if item is not None and cur is not None:
            item["texto"] = " ".join(item["texto"]).strip()
            cur["items"].append(item)
        item = None

    for l in lines:
        m = BLOQUE.match(l)
        if m:
            close_item()
            cur = {"bloque": m.group(1), "titulo": m.group(2), "items": []}
            bloques.append(cur)
            top = None
            continue
        if cur is None:
            continue
        m = SUBID.match(l)
        if m and top is not None:
            close_item()
            item = {"id": f"{cur['bloque']}.{m.group(1)}", "texto": []}
            continue
        m = TOPITEM.match(l)
        if m and (item is None or int(m.group(1)) == (top or 0) + 1):
            close_item()
            top = int(m.group(1))
            item = {"id": f"{cur['bloque']}.{top}", "texto": [m.group(2)]}
            continue
        if item is None:
            cur["introduccion"] = (cur.get("introduccion", "") + " " + l).strip()
        else:
            item["texto"].append(l)
    close_item()
    return bloques


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--curso", type=int, required=True)
    ap.add_argument("--out", default="curriculo_oficial.json")
    a = ap.parse_args()
    avisos = []
    materia, block = curso_block(lines_of(a.pdf), a.curso)
    block = clean(block)
    idx = next((i for i, l in enumerate(block) if l == "Saberes básicos"), None)
    if idx is None:
        avisos.append("No encuentro 'Saberes básicos' en el bloque del curso")
        idx = len(block)
    comps = parse_competencias(block[:idx], avisos)
    saberes = parse_saberes(block[idx + 1:], avisos)
    out = {"materia": materia, "curso": a.curso, "fuente": a.pdf, "competencias": comps, "saberes": saberes,
           "avisos": avisos}
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    nc = sum(len(c["criterios"]) for c in comps)
    ns = sum(len(b["items"]) for b in saberes)
    print(f"{materia} · curso {a.curso}: {len(comps)} competencias, {nc} criterios, {len(saberes)} bloques de saberes, {ns} saberes")
    for av in avisos:
        print("AVISO:", av)
    print("->", a.out)


if __name__ == "__main__":
    main()
