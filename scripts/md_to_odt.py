#!/usr/bin/env python3
"""Convierte uno o varios Markdown a un documento ODT (LibreOffice/OpenOffice) con odfpy.

Uso: python md_to_odt.py <salida.odt> <a.md> [<b.md> ...] [--titulo "Texto de cabecera"] [--saltar-pagina]

Cada .md se añade en orden; con --saltar-pagina cada archivo (salvo el primero) empieza en página nueva.
Soporta: # ## ### títulos, párrafos, citas (>), listas con - o 1., tablas con |, **negrita**, *cursiva*, `código`.
Las entregas para docentes van en ODT o PDF, nunca en .md.
"""
import argparse, re, sys

from odf.opendocument import OpenDocumentText
from odf import style, text, table as otable
from odf.style import (Style, TextProperties, ParagraphProperties, TableCellProperties, TableColumnProperties,
                       TableProperties, PageLayout, PageLayoutProperties, MasterPage, Footer, Header, FontFace)

NEGRO = "#000000"


def estilos(doc, titulo):
    ff = FontFace(name="Liberation Sans", fontfamily="'Liberation Sans'", fontfamilygeneric="swiss", fontpitch="variable")
    doc.fontfacedecls.addElement(ff)
    S = doc.styles
    base = Style(name="Standard", family="paragraph")
    base.addElement(TextProperties(fontsize="10.5pt", fontname="Liberation Sans"))
    base.addElement(ParagraphProperties(marginbottom="0.18cm", textalign="left"))
    S.addElement(base)
    for n, size, mt, mb, color in (("Heading_20_1", "17pt", "0.5cm", "0.3cm", "#1F3864"), ("Heading_20_2", "13.5pt", "0.45cm", "0.2cm", "#1F3864"), ("Heading_20_3", "11.5pt", "0.35cm", "0.15cm", "#2F5496")):
        h = Style(name=n, family="paragraph", displayname=n.replace("_20_", " "), parentstylename="Standard")
        h.addElement(TextProperties(fontsize=size, fontweight="bold", color=color, fontname="Liberation Sans"))
        h.addElement(ParagraphProperties(margintop=mt, marginbottom=mb, keepwithnext="always"))
        S.addElement(h)
    q = Style(name="Cita", family="paragraph", parentstylename="Standard")
    q.addElement(TextProperties(fontsize="9.5pt", fontstyle="italic", color="#444444"))
    q.addElement(ParagraphProperties(marginleft="0.5cm", marginright="0.3cm", borderleft="0.08cm solid #8EAADB", paddingleft="0.25cm", marginbottom="0.25cm"))
    S.addElement(q)
    li = Style(name="Lista", family="paragraph", parentstylename="Standard")
    li.addElement(ParagraphProperties(marginleft="0.9cm", textindent="-0.45cm", marginbottom="0.08cm"))
    S.addElement(li)
    tc = Style(name="Celda", family="paragraph", parentstylename="Standard")
    tc.addElement(TextProperties(fontsize="8.5pt"))
    tc.addElement(ParagraphProperties(marginbottom="0.05cm"))
    S.addElement(tc)
    tcb = Style(name="CeldaCab", family="paragraph", parentstylename="Celda")
    tcb.addElement(TextProperties(fontsize="8.5pt", fontweight="bold", color="#FFFFFF"))
    S.addElement(tcb)
    A = doc.automaticstyles
    cell = Style(name="TC", family="table-cell")
    cell.addElement(TableCellProperties(border="0.5pt solid #7F7F7F", padding="0.1cm"))
    A.addElement(cell)
    cellh = Style(name="TCH", family="table-cell")
    cellh.addElement(TableCellProperties(border="0.5pt solid #7F7F7F", padding="0.1cm", backgroundcolor="#1F3864"))
    A.addElement(cellh)
    brk = Style(name="Salto", family="paragraph", parentstylename="Standard")
    brk.addElement(ParagraphProperties(breakbefore="page"))
    A.addElement(brk)
    bold = Style(name="Negrita", family="text"); bold.addElement(TextProperties(fontweight="bold")); A.addElement(bold)
    ital = Style(name="Cursiva", family="text"); ital.addElement(TextProperties(fontstyle="italic")); A.addElement(ital)
    cod = Style(name="Codigo", family="text"); cod.addElement(TextProperties(fontname="Liberation Sans", backgroundcolor="#F2F2F2")); A.addElement(cod)
    pl = PageLayout(name="PL")
    pl.addElement(PageLayoutProperties(pagewidth="21cm", pageheight="29.7cm", margintop="1.6cm", marginbottom="1.6cm", marginleft="1.8cm", marginright="1.8cm"))
    A.addElement(pl)
    mp = MasterPage(name="Standard", pagelayoutname=pl)
    if titulo:
        hd = Header(); p = text.P(stylename="Celda", text=titulo); hd.addElement(p); mp.addElement(hd)
    ft = Footer(); p = text.P(stylename="Celda"); p.addText("Página "); p.addElement(text.PageNumber(selectpage="current")); ft.addElement(p); mp.addElement(ft)
    doc.masterstyles.addElement(mp)


INLINE = re.compile(r"(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|`[^`]+`)")


def inline(parent, s, base_style=None):
    for part in INLINE.split(s):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            parent.addElement(text.Span(stylename="Negrita", text=part[2:-2]))
        elif part.startswith("`") and part.endswith("`"):
            parent.addElement(text.Span(stylename="Codigo", text=part[1:-1]))
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            parent.addElement(text.Span(stylename="Cursiva", text=part[1:-1]))
        else:
            parent.addText(part)


def parrafo(s, estilo="Standard"):
    p = text.P(stylename=estilo)
    inline(p, s)
    return p


def split_row(l):
    l = l.strip()
    if l.startswith("|"): l = l[1:]
    if l.endswith("|"): l = l[:-1]
    return [c.strip().replace("\\|", "|") for c in l.split("|")]


def tabla(doc, rows, n):
    ncol = max(len(r) for r in rows)
    lens = [min(max((len(r[c]) if c < len(r) else 0) for r in rows), 140) for c in range(ncol)]
    lens = [max(l, 6) for l in lens]
    tot = sum(lens)
    ancho = 17.4
    ws = [max(1.3, ancho * l / tot) for l in lens]
    k = ancho / sum(ws); ws = [w * k for w in ws]
    ts = Style(name=f"T{n}", family="table")
    ts.addElement(TableProperties(width=f"{ancho}cm", align="left", marginbottom="0.3cm"))
    doc.automaticstyles.addElement(ts)
    t = otable.Table(name=f"Tabla{n}", stylename=ts)
    for c, w in enumerate(ws):
        cs = Style(name=f"T{n}C{c}", family="table-column")
        cs.addElement(TableColumnProperties(columnwidth=f"{w:.2f}cm"))
        doc.automaticstyles.addElement(cs)
        t.addElement(otable.TableColumn(stylename=cs))
    for i, r in enumerate(rows):
        if i == 0:
            hr = otable.TableHeaderRows(); tr = otable.TableRow(); hr.addElement(tr)
        else:
            tr = otable.TableRow()
        for c in range(ncol):
            val = r[c] if c < len(r) else ""
            tcell = otable.TableCell(stylename="TCH" if i == 0 else "TC", valuetype="string")
            inline_p = text.P(stylename="CeldaCab" if i == 0 else "Celda")
            inline(inline_p, val)
            tcell.addElement(inline_p); tr.addElement(tcell)
        t.addElement(hr if i == 0 else tr)
    doc.text.addElement(t)


def convertir(doc, md, nuevo_salto, cont):
    L = md.split("\n")
    i = 0; primero = True
    while i < len(L):
        l = L[i]
        if not l.strip():
            i += 1; continue
        if l.startswith("|"):
            rows = []
            while i < len(L) and L[i].startswith("|"):
                r = split_row(L[i])
                if not all(re.fullmatch(r":?-{2,}:?", c.strip()) for c in r if c.strip()) or not any(c.strip() for c in r):
                    rows.append(r)
                i += 1
            cont[0] += 1
            tabla(doc, rows, cont[0]); continue
        m = re.match(r"^(#{1,3})\s+(.*)$", l)
        if m:
            n = len(m.group(1))
            h = text.H(outlinelevel=n, stylename=f"Heading_20_{n}")
            inline(h, m.group(2))
            if primero and nuevo_salto:
                h2 = text.P(stylename="Salto"); doc.text.addElement(h2)
            doc.text.addElement(h); primero = False; i += 1; continue
        primero = False
        if l.startswith(">"):
            buf = []
            while i < len(L) and L[i].startswith(">"):
                buf.append(L[i].lstrip("> ").rstrip()); i += 1
            doc.text.addElement(parrafo(" ".join(buf), "Cita")); continue
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", l)
        if m:
            marca = "•" if m.group(2) in "-*" else m.group(2)
            p = text.P(stylename="Lista"); p.addText(marca + "\t"); inline(p, m.group(3)); doc.text.addElement(p); i += 1; continue
        buf = [l.strip()]; i += 1
        while i < len(L) and L[i].strip() and not re.match(r"^(#{1,3}\s|>|\||\s*([-*]|\d+\.)\s)", L[i]):
            buf.append(L[i].strip()); i += 1
        doc.text.addElement(parrafo(" ".join(buf)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("salida"); ap.add_argument("md", nargs="+")
    ap.add_argument("--titulo", default=""); ap.add_argument("--saltar-pagina", action="store_true")
    a = ap.parse_args()
    doc = OpenDocumentText()
    estilos(doc, a.titulo)
    cont = [0]
    for k, f in enumerate(a.md):
        convertir(doc, open(f, encoding="utf-8").read(), a.saltar_pagina and k > 0, cont)
    doc.save(a.salida)
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"-> {a.salida} ({cont[0]} tablas)")


if __name__ == "__main__":
    main()
