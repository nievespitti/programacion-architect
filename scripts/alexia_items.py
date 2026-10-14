#!/usr/bin/env python3
"""Genera la lista de ítems evaluables que hay que crear en el cuaderno de Alexia a partir del currículo oficial extraído.

Uso: python alexia_items.py <curriculo_oficial.json> --prefijo-ce CETECDI --prefijo-cr CTECDI [--out alexia_items.md]

Alexia compone el cuaderno con ítems: competencias clave y descriptores (CC), competencias específicas (CE),
criterios de evaluación (CrE), incidencias, medida especial, notas finales y observaciones.
Los prefijos de código dependen de la materia y se leen de una captura de Alexia (p. ej. CETECDI-1, CTECDI-1.1).
No se inventan textos de descriptores: solo se listan los códigos que el currículo asocia a cada criterio.
"""
import argparse, json, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("curriculo"); ap.add_argument("--prefijo-ce", required=True)
    ap.add_argument("--prefijo-cr", required=True); ap.add_argument("--out", default="alexia_items.md")
    a = ap.parse_args()
    c = json.load(open(a.curriculo, encoding="utf-8"))
    L = [f"# Ítems de Alexia · {c['materia']} · {c['curso']}.º ESO", "",
         "Generado desde el currículo oficial. Los códigos de Alexia se han leído de capturas: comprobar en el cuaderno antes de crear columnas.", "",
         "## Competencias específicas (ítem CE)", "", "| Código Alexia | Competencia específica |", "|---|---|"]
    for k in c["competencias"]:
        L.append(f"| {a.prefijo_ce}-{k['n']} | {k['texto']} |")
    L += ["", "## Criterios de evaluación (ítem CrE)", "", "| Código Alexia | Criterio | Descriptores del Perfil de salida |", "|---|---|---|"]
    desc = []
    for k in c["competencias"]:
        for r in k["criterios"]:
            L.append(f"| {a.prefijo_cr}-{r['id']} | {r['texto']} | {', '.join(r['descriptores'])} |")
            desc += r["descriptores"]
    uniq = sorted(set(desc), key=lambda x: (x.rstrip("0123456789"), int("".join(ch for ch in x if ch.isdigit()) or 0)))
    L += ["", "## Descriptores de competencias clave que aparecen (ítem CC)", "", ", ".join(uniq), "",
          f"Totales: {len(c['competencias'])} competencias específicas, {sum(len(k['criterios']) for k in c['competencias'])} criterios, {len(uniq)} descriptores distintos.", ""]
    open(a.out, "w", encoding="utf-8").write("\n".join(L))
    sys.stdout.reconfigure(encoding="utf-8")
    print(L[-2]); print("->", a.out)


if __name__ == "__main__":
    main()
