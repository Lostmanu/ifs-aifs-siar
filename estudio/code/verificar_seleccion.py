"""Re-deriva las 34 estaciones desde el catalogo publicado y las compara con outputs/estaciones.json.

Sirve para que la seleccion sea verificable SOLO con lo que hay en este repositorio, sin el arbol de
trabajo original. El programa que se uso en su dia, code/seleccion_rejilla.py, se conserva sin tocar
porque esta en el manifiesto de conservacion, pero lee rutas de la maquina donde se ejecuto; este no.

Regla verificada (metodo_fijado.json, apartado "estaciones"):
  - solo estaciones con Estado = Activa y huso UTM 30 para la rejilla peninsular y balear
  - rejilla de 1,5 grados: latitudes 36,0 37,5 39,0 40,5 42,0 43,5 y longitudes -9,0 ... 3,0
  - una estacion por celda: la mas proxima al centro por haversine, R = 6371,0088 km
  - mas una estacion de Canarias: la primera activa por orden alfabetico de nombre (casefold)
  - conversion UTM ETRS89 -> geograficas por inversa de Mercator transversa, series de Karney hasta n^6

Uso:  python verificar_seleccion.py        (desde code/, o desde la raiz del repositorio)
Salida: PASS si las 34 coinciden en codigo, orden y coordenadas; FAIL con el detalle si no.
"""
from pathlib import Path
import csv, hashlib, io, json, math, sys

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent                                  # estudio/
CATALOGO = RAIZ / 'datos' / 'catalogo_siar_20260914T0741Z.csv'
ESPEC = RAIZ / 'metodo_fijado.json'
ESTACIONES = RAIZ / 'outputs' / 'estaciones.json'

A = 6378137.0
F = 1 / 298.257222101      # GRS80
K0 = 0.9996
FE, FN = 500000.0, 0.0
R_TIERRA = 6371.0088


def tm_inversa(x, y, lon0_deg):
    """Inversa de Mercator transversa (Karney 2011, serie hasta n^6). Devuelve (lat, lon) en grados."""
    n = F / (2 - F)
    n2, n3, n4, n5, n6 = n**2, n**3, n**4, n**5, n**6
    A_rect = A / (1 + n) * (1 + n2 / 4 + n4 / 64 + n6 / 256)
    beta = [n / 2 - 2 * n2 / 3 + 37 * n3 / 96 - n4 / 360 - 81 * n5 / 512 + 96199 * n6 / 604800,
            n2 / 48 + n3 / 15 - 437 * n4 / 1440 + 46 * n5 / 105 - 1118711 * n6 / 3870720,
            17 * n3 / 480 - 37 * n4 / 840 - 209 * n5 / 4480 + 5569 * n6 / 90720,
            4397 * n4 / 161280 - 11 * n5 / 504 - 830251 * n6 / 7257600,
            4583 * n5 / 161280 - 108847 * n6 / 3991680,
            20648693 * n6 / 638668800]
    delta = [2 * n - 2 * n2 / 3 - 2 * n3 + 116 * n4 / 45 + 26 * n5 / 45 - 2854 * n6 / 675,
             7 * n2 / 3 - 8 * n3 / 5 - 227 * n4 / 45 + 2704 * n5 / 315 + 2323 * n6 / 945,
             56 * n3 / 15 - 136 * n4 / 35 - 1262 * n5 / 105 + 73814 * n6 / 2835,
             4279 * n4 / 630 - 332 * n5 / 35 - 399572 * n6 / 14175,
             4174 * n5 / 315 - 144838 * n6 / 6237,
             601676 * n6 / 22275]
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
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R_TIERRA * math.asin(math.sqrt(h))


def main():
    fallos = []
    if not CATALOGO.exists():
        print(f'FALTA el catalogo: {CATALOGO}'); return 2
    crudo = CATALOGO.read_bytes()
    h = hashlib.sha256(crudo).hexdigest()
    espec = json.loads(ESPEC.read_text(encoding='utf-8'))
    declarado = espec['estaciones']['catalogo']['sha256']
    print(f'catalogo     : {CATALOGO.name}  {len(crudo)} bytes')
    print(f'  sha-256    : {h}')
    print(f'  declarado  : {declarado}   {"COINCIDE" if h == declarado else "NO COINCIDE"}')
    if h != declarado:
        fallos.append('el catalogo no es el que fija la especificacion congelada')

    filas = list(csv.DictReader(io.StringIO(crudo.decode('cp1252')), delimiter=';'))
    activas = [r for r in filas if r['Estado'] == 'Activa']
    print(f'  filas {len(filas)}, activas {len(activas)}')

    estaciones = []
    for r in activas:
        huso = int(r['Huso'])
        lat, lon = tm_inversa(float(r['UTMX']), float(r['UTMY']), -183 + 6 * huso)
        estaciones.append({'codigo': r['Id Estación'], 'nombre': r['Denominación'], 'huso': huso,
                           'centro': r['Centro Zonal'], 'lat': lat, 'lon': lon})

    rej = espec['estaciones']['rejilla']
    seleccion = []
    for la in rej['celdas_lat']:
        for lo in rej['celdas_lon']:
            dentro = [s for s in estaciones if s['huso'] == 30
                      and abs(s['lat'] - la) <= rej['semiancho_grados']
                      and abs(s['lon'] - lo) <= rej['semiancho_grados']]
            if not dentro:
                continue
            for s in dentro:
                s['_d'] = haversine_km(s['lat'], s['lon'], la, lo)
            dentro.sort(key=lambda s: (s['_d'], s['codigo']))
            seleccion.append(dentro[0])
    canarias = sorted([s for s in estaciones if s['centro'] == 'Canarias'], key=lambda s: s['nombre'].casefold())
    if canarias:
        seleccion.append(canarias[0])
    print(f'  celdas con estacion {len(seleccion) - 1}, mas 1 de Canarias -> {len(seleccion)} estaciones')

    oficial = json.loads(ESTACIONES.read_text(encoding='utf-8'))['estaciones']
    if len(oficial) != len(seleccion):
        fallos.append(f'numero de estaciones: re-derivadas {len(seleccion)}, publicadas {len(oficial)}')
    for i, (mio, suyo) in enumerate(zip(seleccion, oficial)):
        if mio['codigo'] != suyo['codigo']:
            fallos.append(f'posicion {i}: re-derivada {mio["codigo"]}, publicada {suyo["codigo"]}')
            continue
        dlat = abs(mio['lat'] - suyo['latitud']); dlon = abs(mio['lon'] - suyo['longitud'])
        if max(dlat, dlon) > 1e-9:
            fallos.append(f'{mio["codigo"]}: coordenadas difieren en {max(dlat, dlon):.2e} grados')
    print()
    if fallos:
        print('FAIL')
        for f in fallos:
            print('  -', f)
        return 1
    print('PASS: las', len(seleccion), 'estaciones se re-derivan del catalogo publicado,')
    print('      en el mismo orden y con coordenadas iguales por debajo de 1e-9 grados.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
