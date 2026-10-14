#!/usr/bin/env python3
"""Extrae LITERALES de un PDF de currículo LOMLOE de ESO (formato Canarias) los elementos de un curso:
competencias específicas, criterios de evaluación (con sus descriptores del Perfil de salida) y saberes básicos.

Uso: python extract_curriculo_eso.py <pdf> --curso 3 [--out curriculo_oficial.json]

Formato que reconoce (probado con Tecnología y Digitalización, Canarias):
  "3.º ESO" abre el bloque del curso; dentro, por cada competencia:
    "Competencia específica" / "N. texto" / "Descriptores operativos..." / códigos / "Criterios de evaluación"
    / "N.M. texto" + línea de códigos / "Explicación del bloque competencial"
  "Saberes básicos" / "I. Título" / "N. texto" / "N.M. texto"
Se detiene en el siguiente "N.º ESO" o al final del documento.
Salida: {"materia", "curso", "competencias": [{"n","texto","descriptores","criterios":[{"id","texto","descriptores"}]}],
         "saberes": [{"bloque","titulo","items":[{"id","texto"}]}]}
Si algo no cuadra, se ve en "avisos"; nunca se rellena con texto de memoria.
"""
import argparse, json, re, sys

try:
    import pymupdf
except ImportError:  # versiones antiguas
    import fitz as pymupdf

CODES = re.compile(r"^(?:[A-Z]{2,5}\d(?:,\s*|\s+|$))+$")
PAGE = re.compile(r"^\d{1,3}$")
CURSO = re.compile(r"^(\d)\.º ESO\s*$")
COMP = re.compile(r"^(\d+)\.\s+(\S.*)$")
CRIT = re.compile(r"^(\d+\.\d+)\.\s+(\S.*)$")
BLOQUE = re.compile(r"^([IVX]+)\.\s+(\S.*)$")
ITEM = re.compile(r"^\W{0,3}\s*(\d+(?:\.\d+)*)\.\s+(\S.*)$")


def lines_of(pdf):
    doc = pymupdf.open(pdf)
    out = []
    for p in doc:
        out += [l.rstrip() for l in p.get_text().splitlines()]
    return out


def curso_block(lines, curso):
    start = end = None
    for i, l in enumerate(lines):
        m = CURSO.match(l.strip())
        if m and int(m.group(1)) == curso and start is None:
            start = i + 1
        elif m and start is not None:
            end = i
            break
    if start is None:
        sys.exit(f"No encuentro el bloque '{curso}.º ESO' en el PDF")
    return lines[start:end]


def parse_competencias(block, avisos):
    # parte antes de "Saberes básicos"
    idx = next((i for i, l in enumerate(block) if l.strip() == "Saberes básicos"), len(block))
    comp_lines, saber_lines = block[:idx], block[idx + 1:]
    comps, cur, mode, buf = [], None, None, []

    def flush_text(c, key, b):
        if c is not None and b:
            c[key] = " ".join(x.strip() for x in b).strip()

    i = 0
    crit = None
    crit_buf, crit_codes_done = [], False
    while i < len(comp_lines):
        l = comp_lines[i].strip()
        i += 1
        if not l or PAGE.match(l):
            continue
        if l == "Competencia específica":
            if crit is not None:
                crit["texto"] = " ".join(crit_buf).strip(); crit = None
            flush_text(cur, "texto", buf) if mode == "comp" else None
            cur = {"n": None, "texto": "", "descriptores": [], "criterios": []}
            comps.append(cur); mode, buf = "comp_wait", []
            continue
        if cur is None:
            continue
        if mode == "comp_wait":
            m = COMP.match(l)
            if m:
                cur["n"] = int(m.group(1)); buf = [m.group(2)]; mode = "comp"
            continue
        if mode == "comp":
            if l.startswith("Descriptores operativos"):
                cur["texto"] = " ".join(buf).strip(); mode = "desc_head"
            else:
                buf.append(l)
            continue
        if mode == "desc_head":
            if l.startswith("competencias clave"):
                mode = "desc"
            continue
        if mode == "desc":
            if CODES.match(l):
                cur["descriptores"] += re.findall(r"[A-Z]{2,5}\d", l)
            elif l == "Criterios de evaluación":
                mode = "crit"
            continue
        if mode == "crit":
            if l.startswith("Explicación del bloque"):
                if crit is not None:
                    crit["texto"] = " ".join(crit_buf).strip(); crit = None
                mode = "expl"; continue
            m = CRIT.match(l)
            if m:
                if crit is not None:
                    crit["texto"] = " ".join(crit_buf).strip()
                crit = {"id": m.group(1), "texto": "", "descriptores": []}
                cur["criterios"].append(crit); crit_buf = [m.group(2)]; crit_codes_done = False
                continue
            if crit is not None:
                if CODES.match(l):
                    crit["descriptores"] += re.findall(r"[A-Z]{2,5}\d", l); crit_codes_done = True
                elif not crit_codes_done:
                    crit_buf.append(l)
            continue
    if crit is not None:
        crit["texto"] = " ".join(crit_buf).strip()
    for c in comps:
        if c["n"] is None or not c["criterios"]:
            avisos.append(f"Competencia sin número o sin criterios: {c}")
        for k in c["criterios"]:
            if not k["descriptores"]:
                avisos.append(f"Criterio {k['id']} sin descriptores")
            if not k["id"].startswith(f"{c['n']}."):
                avisos.append(f"Criterio {k['id']} dentro de la competencia {c['n']}")
    return comps, saber_lines


def parse_saberes(lines, avisos):
    bloques, blq, item = [], None, None
    for raw in lines:
        l = raw.strip()
        if not l or PAGE.match(l):
            continue
        m = BLOQUE.match(l)
        if m and (item is None or not item["texto"].endswith(",")):
            blq = {"bloque": m.group(1), "titulo": m.group(2), "items": []}
            bloques.append(blq); item = None
            continue
        if blq is None:
            continue
        m = ITEM.match(raw)
        if m:
            item = {"id": m.group(1), "texto": m.group(2).strip()}
            blq["items"].append(item)
        elif item is not None:
            item["texto"] += " " + l
        else:
            blq["titulo"] += " " + l
    if len(bloques) != 5:
        avisos.append(f"Se esperaban 5 bloques de saberes y hay {len(bloques)}")
    return bloques


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf"); ap.add_argument("--curso", type=int, required=True)
    ap.add_argument("--out", default="curriculo_oficial.json")
    a = ap.parse_args()
    lines = lines_of(a.pdf)
    materia = next((l.strip() for l in lines if l.strip()), "")
    avisos = []
    block = curso_block(lines, a.curso)
    comps, saber_lines = parse_competencias(block, avisos)
    saberes = parse_saberes(saber_lines, avisos)
    res = {"materia": materia, "curso": a.curso, "competencias": comps, "saberes": saberes, "avisos": avisos}
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    nc = sum(len(c["criterios"]) for c in comps)
    ns = sum(len(b["items"]) for b in saberes)
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"{materia} · {a.curso}.º ESO: {len(comps)} competencias, {nc} criterios, {len(saberes)} bloques, {ns} saberes")
    for av in avisos:
        print("AVISO:", av)
    print("->", a.out)


if __name__ == "__main__":
    main()
