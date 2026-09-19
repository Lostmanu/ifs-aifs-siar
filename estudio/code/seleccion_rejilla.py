"""Grid-based SiAR station selection (encargo §6.1), stdlib only.

UTM (ETRS89 = GRS80) -> geographic via Karney/Krüger series (order n^6).
Verified below against pyproj-derived coordinates saved by prior work.
"""
import csv, io, json, math, sys, collections
from pathlib import Path

CATALOG = Path(r"C:\Users\manue\Documents\Codex\2026-09-11\qu\work\neighbor_audit\raw\catalog.csv")
FORM = Path(r"C:\Users\manue\Documents\Codex\2026-09-11\qu\work\neighbor_audit\raw\active_form.html")
KNOWN = Path(r"C:\Users\manue\Documents\Codex\2026-09-11\qu\work\neighbor_audit\scope.json")

A = 6378137.0
F = 1 / 298.257222101  # GRS80
K0 = 0.9996
FE, FN = 500000.0, 0.0


def tm_inverse(x, y, lon0_deg):
    """Inverse transverse Mercator (Karney 2011, series to n^6). Returns (lat, lon) degrees."""
    n = F / (2 - F)
    n2, n3, n4, n5, n6 = n**2, n**3, n**4, n**5, n**6
    A_rect = A / (1 + n) * (1 + n2 / 4 + n4 / 64 + n6 / 256)
    beta = [
        n / 2 - 2 * n2 / 3 + 37 * n3 / 96 - n4 / 360 - 81 * n5 / 512 + 96199 * n6 / 604800,
        n2 / 48 + n3 / 15 - 437 * n4 / 1440 + 46 * n5 / 105 - 1118711 * n6 / 3870720,
        17 * n3 / 480 - 37 * n4 / 840 - 209 * n5 / 4480 + 5569 * n6 / 90720,
        4397 * n4 / 161280 - 11 * n5 / 504 - 830251 * n6 / 7257600,
        4583 * n5 / 161280 - 108847 * n6 / 3991680,
        20648693 * n6 / 638668800,
    ]
    delta = [
        2 * n - 2 * n2 / 3 - 2 * n3 + 116 * n4 / 45 + 26 * n5 / 45 - 2854 * n6 / 675,
        7 * n2 / 3 - 8 * n3 / 5 - 227 * n4 / 45 + 2704 * n5 / 315 + 2323 * n6 / 945,
        56 * n3 / 15 - 136 * n4 / 35 - 1262 * n5 / 105 + 73814 * n6 / 2835,
        4279 * n4 / 630 - 332 * n5 / 35 - 399572 * n6 / 14175,
        4174 * n5 / 315 - 144838 * n6 / 6237,
        601676 * n6 / 22275,
    ]
    xi = (y - FN) / (K0 * A_rect)
    eta = (x - FE) / (K0 * A_rect)
    xi_p, eta_p = xi, eta
    for j, b in enumerate(beta, start=1):
        xi_p -= b * math.sin(2 * j * xi) * math.cosh(2 * j * eta)
        eta_p -= b * math.cos(2 * j * xi) * math.sinh(2 * j * eta)
    chi = math.asin(math.sin(xi_p) / math.cosh(eta_p))
    phi = chi
    for j, d in enumerate(delta, start=1):
        phi += d * math.sin(2 * j * chi)
    lam = math.atan2(math.sinh(eta_p), math.cos(xi_p))
    return math.degrees(phi), lon0_deg + math.degrees(lam)


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def load_catalog():
    text = CATALOG.read_bytes().decode("cp1252")
    rows = list(csv.DictReader(io.StringIO(text), delimiter=";"))
    return rows


def form_ids():
    import re
    form = FORM.read_bytes().decode("utf-8", "replace")
    m = re.findall(r'<input[^>]+id="checkEstacion_([^"]+)"[^>]+data-caEstacion="([^"]+)"[^>]*>\s*<span[^>]+>([A-Z]+\d+[A-Z]*\d*) - ([^<]*)<', form)
    return {code: {"id": sid, "region": reg, "form_name": name} for sid, reg, code, name in m}


def main():
    rows = load_catalog()
    ids = form_ids()
    stations = []
    for r in rows:
        if r["Estado"] != "Activa":
            continue
        zone = int(r["Huso"])
        lon0 = -183 + 6 * zone
        lat, lon = tm_inverse(float(r["UTMX"]), float(r["UTMY"]), lon0)
        code = r["Id Estación"]
        stations.append({
            "code": code, "name": r["Denominación"], "zone_center": r["Centro Zonal"], "province": r["Provincia"],
            "utm_zone": zone, "utmx": float(r["UTMX"]), "utmy": float(r["UTMY"]), "latitude": lat, "longitude": lon,
            "installed": r["Fecha instalación"], "owner": r["Propiedad"], **ids.get(code, {}),
        })
    # verification against pyproj values saved by prior work
    known = json.loads(KNOWN.read_text(encoding="utf-8"))
    worst = 0.0
    for g in known["groups"].values():
        for k in g:
            s = next(x for x in stations if x["code"] == k["code"])
            d = haversine_km(s["latitude"], s["longitude"], k["latitude"], k["longitude"]) * 1000
            worst = max(worst, d)
            print(f"verify {k['code']}: mine=({s['latitude']:.9f},{s['longitude']:.9f}) pyproj=({k['latitude']:.9f},{k['longitude']:.9f}) diff={d*1000:.3f} mm")
    print("worst diff mm:", worst * 1000)

    lats = [36.0, 37.5, 39.0, 40.5, 42.0, 43.5]
    lons = [-9.0, -7.5, -6.0, -4.5, -3.0, -1.5, 0.0, 1.5, 3.0]
    cells = []
    for la in lats:
        for lo in lons:
            inside = [s for s in stations if s["utm_zone"] == 30 and abs(s["latitude"] - la) <= 0.75 and abs(s["longitude"] - lo) <= 0.75]
            if not inside:
                cells.append({"center": [la, lo], "n_stations": 0, "selected": None})
                continue
            for s in inside:
                s_d = haversine_km(s["latitude"], s["longitude"], la, lo)
                s["_d"] = s_d
            inside.sort(key=lambda s: (s["_d"], s["code"]))
            sel = inside[0]
            cells.append({"center": [la, lo], "n_stations": len(inside), "selected": sel["code"], "selected_name": sel["name"],
                          "distance_km": round(sel["_d"], 3), "runner_up": inside[1]["code"] if len(inside) > 1 else None,
                          "runner_up_distance_km": round(inside[1]["_d"], 3) if len(inside) > 1 else None})
    can = sorted([s for s in stations if s["zone_center"] == "Canarias"], key=lambda s: s["name"].casefold())
    print("\nCells with stations:", sum(1 for c in cells if c["selected"]))
    for c in cells:
        if c["selected"]:
            print(c)
    print("\nCanarias alphabetical first 5:", [(s["code"], s["name"]) for s in can[:5]])
    # Stations in more than one cell? (cells are disjoint half-open? they are closed: boundary stations could be in two)
    boundary = [s for s in stations if s["utm_zone"] == 30 and (any(abs(abs(s["latitude"] - la) - 0.75) < 1e-9 for la in lats) or any(abs(abs(s["longitude"] - lo) - 0.75) < 1e-9 for lo in lons))]
    print("boundary ambiguity stations:", [s["code"] for s in boundary])
    out = {"stations_active": stations, "cells": cells, "canarias_alphabetical": [{"code": s["code"], "name": s["name"], "latitude": s["latitude"], "longitude": s["longitude"]} for s in can[:5]]}
    Path(sys.argv[1]).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
