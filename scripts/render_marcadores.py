#!/usr/bin/env python3
"""Rellena una plantilla Markdown con datos que NO redacta el modelo: texto oficial literal y cifras del plan.

Uso: python render_marcadores.py <plantilla.md> --curriculo curriculo_oficial.json --plan plan.json --out salida.md

Marcadores:
  {{CRITERIOS:1.2,1.3}}      tabla: competencia específica | criterio (literal) | descriptores
  {{SABERES:I.4,I.8.1}}      lista de saberes básicos literales (bloque.id)
  {{SESIONES:2.ª evaluación}} tabla de sesiones reales del tramo (fecha, franja, minutos efectivos)
  {{MISIONES:2}}             tabla de misiones de la SdA n de plan.json (sesiones, fechas, criterios, tarea)
  {{TAREAS:2}}               tabla de tareas evaluables de la SdA n (código, criterio, ítem Alexia, sesiones)
  {{COBERTURA}}              matriz criterio x SdA a partir de plan.json (cobertura_criterios)
Un marcador con un dato inexistente es un error (el script se detiene): no se rellena nada de memoria.
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sesiones import sesiones, fmt, d  # noqa: E402


def die(msg):
    sys.stdout.reconfigure(encoding="utf-8"); print("ERROR:", msg); sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plantilla"); ap.add_argument("--curriculo", required=True)
    ap.add_argument("--plan", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    cur = json.load(open(a.curriculo, encoding="utf-8"))
    plan = json.load(open(a.plan, encoding="utf-8"))
    ses, _ = sesiones(plan)
    crit = {r["id"]: (k, r) for k in cur["competencias"] for r in k["criterios"]}
    sab = {(i["id"] if i["id"].startswith(b["bloque"] + ".") else f"{b['bloque']}.{i['id']}"): i["texto"] for b in cur["saberes"] for i in b["items"]}

    def criterios(arg):
        L = ["| Competencia específica | Criterio de evaluación | Descriptores |", "|---|---|---|"]
        vista = set()
        for c in [x.strip() for x in arg.split(",")]:
            if c not in crit: die(f"criterio {c} no está en el currículo")
            k, r = crit[c]
            comp = f"Competencia específica {k['n']} (texto completo más arriba)" if k["n"] in vista else f"{k['n']}. {k['texto']}"
            vista.add(k["n"])
            L.append(f"| {comp} | **{r['id']}.** {r['texto']} | {', '.join(r['descriptores'])} |")
        return "\n".join(L)

    def saberes(arg):
        L = []
        for s in [x.strip() for x in arg.split(",")]:
            if s not in sab: die(f"saber {s} no está en el currículo")
            L.append(f"- **{s}** {sab[s]}")
        return "\n".join(L)

    def tramo(nombre):
        t = next((t for t in plan["tramos"] if t["nombre"] == nombre), None)
        if not t: die(f"tramo '{nombre}' no existe en plan.json")
        return [s for s in ses if d(t["inicio"]) <= s["fecha"] <= d(t["fin"])]

    def sesiones_tabla(nombre):
        L = ["| Nº | Fecha | Franja | Min efectivos |", "|---|---|---|---|"]
        for i, s in enumerate(tramo(nombre), 1):
            L.append(f"| {i} | {fmt(s['fecha'])} | {s['inicio']}-{s['fin']} | {s['minutos']} |")
        return "\n".join(L)

    def sda(n):
        x = next((s for s in plan.get("sdas", []) if s["n"] == int(n)), None)
        if not x: die(f"SdA {n} no existe en plan.json")
        return x

    def misiones(n):
        x = sda(n); dentro = tramo(x["tramo"])
        L = ["| Misión | Sesiones | Fechas | Criterio | Tarea |", "|---|---|---|---|---|"]
        for m in x["misiones"]:
            a_, b_ = m["sesiones"]
            if b_ > len(dentro): die(f"misión {m['n']} no cabe en el tramo ({len(dentro)} sesiones)")
            L.append(f"| {m['n']:02d} {m['titulo']} | {a_}–{b_} | {fmt(dentro[a_-1]['fecha'])} y {fmt(dentro[b_-1]['fecha'])} | {', '.join(m.get('criterios', []))} | {m.get('tarea', '')} |")
        ult = x["misiones"][-1]["sesiones"][1]
        L += ["", f"Reserva ({x.get('reserva', 0)} sesiones): " + ", ".join(fmt(s['fecha']) for s in dentro[ult:ult + x.get('reserva', 0)]) + "."]
        if x.get("ajuste"):
            L += ["", f"Sesión de ajuste: " + ", ".join(f"{k} ({fmt(dentro[k-1]['fecha'])})" for k in x["ajuste"]) + ". " + x.get("ajuste_nota", "")]
        return "\n".join(L)

    def tareas(n):
        L = ["| Código | Tarea | Criterio | Ítem Alexia | Sesiones |", "|---|---|---|---|---|"]
        for t in sda(n)["tareas_evaluables"]:
            L.append(f"| {t['codigo']} | {t['nombre']} | {t['criterio']} | {t['alexia'].split(' ')[0]} | {t['sesiones']} |")
        return "\n".join(L)

    def cobertura():
        cols = plan["cobertura_criterios_3eso"]["matriz"]
        ids = list(crit)
        L = ["| Criterio | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
        sin = []
        for c in ids:
            fila = [plan["cobertura_criterios_3eso"]["matriz"][s].get(c, "") for s in cols]
            if not any(fila): sin.append(c)
            L.append(f"| {c} | " + " | ".join(fila) + " |")
        L.append("")
        L.append("Criterios sin ninguna evaluación asignada: " + (", ".join(sin) if sin else "ninguno."))
        return "\n".join(L)

    f = {"CRITERIOS": criterios, "SABERES": saberes, "SESIONES": sesiones_tabla, "MISIONES": misiones, "TAREAS": tareas, "COBERTURA": lambda _="": cobertura()}
    txt = open(a.plantilla, encoding="utf-8").read()

    def sub(m):
        k, arg = m.group(1), (m.group(2) or "")
        if k not in f: die(f"marcador desconocido {k}")
        return f[k](arg)

    out = re.sub(r"\{\{([A-Z]+)(?::([^}]*))?\}\}", sub, txt)
    open(a.out, "w", encoding="utf-8").write(out)
    sys.stdout.reconfigure(encoding="utf-8")
    pend = len(re.findall(r"_Pendiente_", out))
    print(f"-> {a.out} ({len(out)} caracteres; {pend} marcas _Pendiente_)")


if __name__ == "__main__":
    main()
