#!/usr/bin/env python3
"""Calcula las sesiones reales de una materia a partir de plan.json (horario x calendario) y las reparte por tramos.

Uso: python sesiones.py <plan.json> [--out sesiones.md]

plan.json (campos que usa):
  horario:    [{"dia": "Jueves", "inicio": "09:53", "fin": "10:49", "minutos": 56}, ...]   una entrada por sesión semanal
  calendario: {"inicio_clases": "2026-09-10", "fin_clases": "2027-06-22",
               "no_lectivos": [{"fecha": "2026-12-04", "motivo": "..."}],
               "periodos_sin_clase": [{"inicio": "...", "fin": "...", "motivo": "Navidad"}]}
  tramos:     [{"nombre": "1.ª evaluación", "inicio": "2026-09-10", "fin": "2026-11-27", "nota": "..."}]
Un día sin clase es el que cae en no_lectivos o en un periodo sin clase. No inventa festivos: solo resta lo que el plan declara.
Sesiones fuera de todos los tramos se listan aparte (p. ej. tras la evaluación final).
"""
import argparse, datetime as dt, json, sys

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def d(s):
    return dt.date.fromisoformat(s)


def fmt(x):
    return f"{DIAS[x.weekday()][:3]} {x.day:02d}/{x.month:02d}/{x.year}"


def blocked(cal):
    out = {}
    for x in cal.get("no_lectivos", []):
        out[d(x["fecha"])] = x.get("motivo", "No lectivo")
    for p in cal.get("periodos_sin_clase", []):
        a, b = d(p["inicio"]), d(p["fin"])
        while a <= b:
            out[a] = p.get("motivo", "Sin clase"); a += dt.timedelta(days=1)
    return out


def sesiones(plan):
    cal = plan["calendario"]
    blk = blocked(cal)
    por_dia = {}
    for h in plan["horario"]:
        por_dia.setdefault(DIAS.index(h["dia"]), []).append(h)
    cur, fin = d(cal["inicio_clases"]), d(cal["fin_clases"])
    res, perdidas = [], []
    while cur <= fin:
        if cur.weekday() in por_dia:
            for h in por_dia[cur.weekday()]:
                if cur in blk:
                    perdidas.append((cur, blk[cur]))
                else:
                    res.append({"fecha": cur, "inicio": h["inicio"], "fin": h["fin"], "minutos": h.get("minutos_efectivos", h["minutos"])})
        cur += dt.timedelta(days=1)
    return res, perdidas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan"); ap.add_argument("--out", default="sesiones.md")
    a = ap.parse_args()
    plan = json.load(open(a.plan, encoding="utf-8"))
    ses, perdidas = sesiones(plan)
    L = [f"# Sesiones reales · {plan.get('materia', '')} · {plan.get('curso', '')}", ""]
    sem = ", ".join(f"{h['dia']} {h['inicio']}-{h['fin']} ({h['minutos']} min)" for h in plan["horario"])
    L += [f"Horario semanal: {sem}.", f"Curso: {plan['calendario']['inicio_clases']} a {plan['calendario']['fin_clases']}.", ""]
    usadas = set()
    for t in plan["tramos"]:
        a_, b_ = d(t["inicio"]), d(t["fin"])
        dentro = [s for s in ses if a_ <= s["fecha"] <= b_]
        usadas |= {id(s) for s in dentro}
        L += [f"## {t['nombre']} ({fmt(a_)} a {fmt(b_)})", ""]
        if t.get("nota"):
            L += [f"_{t['nota']}_", ""]
        L += [f"**{len(dentro)} sesiones · {sum(s['minutos'] for s in dentro)} minutos**", "", "| Nº | Fecha | Franja | Min |", "|---|---|---|---|"]
        for i, s in enumerate(dentro, 1):
            L.append(f"| {i} | {fmt(s['fecha'])} | {s['inicio']}-{s['fin']} | {s['minutos']} |")
        L.append("")
    for sda in plan.get("sdas", []):
        if not sda.get("misiones") or not sda.get("tramo"):
            continue
        t = next((t for t in plan["tramos"] if t["nombre"] == sda["tramo"]), None)
        if not t:
            continue
        dentro = [s for s in ses if d(t["inicio"]) <= s["fecha"] <= d(t["fin"])]
        L += [f"## SdA {sda['n']} · {sda['titulo']}: misiones y fechas", "", "| Misión | Sesiones | Fechas |", "|---|---|---|"]
        for m in sda["misiones"]:
            a_, b_ = m["sesiones"]
            if b_ <= len(dentro):
                L.append(f"| {m['n']:02d} {m['titulo']} | {a_}–{b_} | {fmt(dentro[a_-1]['fecha'])} y {fmt(dentro[b_-1]['fecha'])} |")
            else:
                L.append(f"| {m['n']:02d} {m['titulo']} | {a_}–{b_} | NO CABE: el tramo solo tiene {len(dentro)} sesiones |")
        r = sda.get("reserva", 0)
        ult = sda["misiones"][-1]["sesiones"][1]
        L.append("")
        if r:
            ini = ult + 1
            L.append(f"Reserva ({r} sesiones): " + ", ".join(fmt(x['fecha']) for x in dentro[ult:ult + r]) + ".")
        sobran = len(dentro) - ult - r
        L += [f"Sesiones del tramo no asignadas a la SdA: {max(sobran, 0)}.", ""]
    fuera = [s for s in ses if id(s) not in usadas]
    if fuera:
        L += ["## Sesiones fuera de los tramos definidos", ""] + [f"- {fmt(s['fecha'])} {s['inicio']}-{s['fin']} ({s['minutos']} min)" for s in fuera] + [""]
    if perdidas:
        L += ["## Sesiones perdidas por días sin clase", ""] + [f"- {fmt(x)}: {m}" for x, m in perdidas] + [""]
    L += [f"**Total del curso: {len(ses)} sesiones · {sum(s['minutos'] for s in ses)} minutos.**", ""]
    if plan.get("pendientes_calendario"):
        L += ["## Pendiente de confirmar", ""] + [f"- {p}" for p in plan["pendientes_calendario"]] + [""]
    open(a.out, "w", encoding="utf-8").write("\n".join(L))
    sys.stdout.reconfigure(encoding="utf-8")
    for t in plan["tramos"]:
        n = [s for s in ses if d(t["inicio"]) <= s["fecha"] <= d(t["fin"])]
        print(f"{t['nombre']}: {len(n)} sesiones, {sum(s['minutos'] for s in n)} min")
    print(f"Fuera de tramos: {len(fuera)} · perdidas: {len(perdidas)} · total {len(ses)}")
    print("->", a.out)


if __name__ == "__main__":
    main()
