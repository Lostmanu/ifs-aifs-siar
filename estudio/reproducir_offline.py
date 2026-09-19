"""Lanzador portable: valida archivos y reproduce en una copia, sin conectarse a red.

Uso: python reproducir_offline.py [--figuras]
Requisitos: Python >=3.12, numpy. matplotlib opcional.
No ejecuta descargadores ni modifica la especificación o las salidas entregadas.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, shutil, sys, os, runpy, math, time

BASE = Path(__file__).resolve().parent
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
sys.dont_write_bytecode = True

def load(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p, v): p.write_text(json.dumps(v, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')

def comparison(a, b, path='', s=None):
    if s is None: s = {'numeros': 0, 'diferencia_maxima': 0.0, 'diferencias': [], 'excluidos': []}
    if isinstance(a, dict) and isinstance(b, dict):
        if a.keys() != b.keys(): s['diferencias'].append([path, 'claves distintas'])
        for k in sorted(a.keys() & b.keys()):
            if k == 'generado_utc': s['excluidos'].append(path + '/' + k)
            else: comparison(a[k], b[k], path + '/' + k, s)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b): s['diferencias'].append([path, 'longitudes distintas'])
        for i, (x, y) in enumerate(zip(a, b)): comparison(x, y, path + '/' + str(i), s)
    elif isinstance(a, (int, float)) and not isinstance(a, bool) and isinstance(b, (int, float)):
        s['numeros'] += 1; s['diferencia_maxima'] = max(s['diferencia_maxima'], abs(a-b))
        if not math.isclose(a, b, rel_tol=1e-11, abs_tol=1e-10): s['diferencias'].append([path, a, b])
    elif a != b: s['diferencias'].append([path, a, b])
    return s

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--figuras', action='store_true'); args = ap.parse_args()
    manifest = load(BASE / 'manifest_portable_sha256.json')
    for rel, h in manifest['files'].items():
        p = (BASE / rel).resolve()
        if not p.is_relative_to(BASE) or not p.is_file() or sha(p) != h:
            raise RuntimeError('Fichero fuera de raíz, ausente o hash distinto: ' + rel)
    print('Manifiesto comprobado:', len(manifest['files']), 'archivos', flush=True)
    run = BASE / 'reproduccion' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run.mkdir(parents=True, exist_ok=False)
    for name in ['code', 'raw', 'datos', 'state', 'outputs']:
        shutil.copytree(BASE / name, run / name, ignore=shutil.ignore_patterns('__pycache__', '*.zip', 'verificacion.json', 'integridad_paquete.json'))
    shutil.copyfile(BASE / 'metodo_fijado.json', run / 'metodo_fijado.json')
    sys.path.insert(0, str(run / 'code'))
    os.environ['MPLCONFIGDIR'] = str(run / 'mplconfig')
    import comun
    assert comun.OUT.resolve().is_relative_to(run)
    blocked = []
    def audit(event, vals):
        if event in ('socket.connect', 'socket.getaddrinfo', 'subprocess.Popen', 'os.system'):
            blocked.append(event)
            raise RuntimeError('Conexiones y procesos externos desactivados: ' + event)
        if event == 'open' and isinstance(vals[0], (str, bytes, os.PathLike)):
            mode, flags = vals[1], vals[2]
            writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
            if writing and not Path(os.fsdecode(vals[0])).resolve().is_relative_to(run):
                raise RuntimeError('Escritura fuera de copia de reproducción: ' + str(vals[0]))
    sys.addaudithook(audit)
    import numpy as np
    r = {'inicio_utc': datetime.now(timezone.utc).isoformat(), 'python': sys.version, 'numpy': np.__version__,
         'manifest_archivos': len(manifest['files']), 'carpeta': str(run), 'pasos': [], 'comparaciones': {},
         'control_red': 'audit hook del proceso; no cortafuegos del sistema'}
    names = ['test_metodo.py', 'preparar_observaciones.py', 'analizar.py', 'diagnostico_posterior.py', 'verificar.py', 'informe.py']
    if args.figuras: names.append('figuras.py')
    for name in names:
        start = time.monotonic(); print('Ejecutando', name, flush=True)
        sys.argv = [str(run / 'code' / name)]
        try: runpy.run_path(sys.argv[0], run_name='__main__')
        except SystemExit as e:
            if e.code not in (None, 0): raise
        r['pasos'].append({'script': name, 'segundos': time.monotonic()-start})
    for name in ['outputs/resultados.json', 'outputs/estaciones.json', 'outputs/panel_analisis.json',
                 'datos/observaciones_diarias.json', 'datos/cobertura_observaciones.json', 'datos/diagnostico_posterior.json']:
        r['comparaciones'][name] = comparison(load(BASE / name), load(run / name))
    r['intentos_red_o_subprocesos_bloqueados'] = blocked
    r['verificacion_decimal_y_recibos'] = load(run / 'outputs/verificacion.json')['estado']
    r['estado'] = 'PASS' if all(not x['diferencias'] for x in r['comparaciones'].values()) and r['verificacion_decimal_y_recibos'] == 'PASS' and not blocked else 'FAIL'
    r['fin_utc'] = datetime.now(timezone.utc).isoformat()
    save(run / 'comprobacion_offline.json', r)
    print(r['estado'], 'Informe:', run / 'comprobacion_offline.json', flush=True)
    if r['estado'] != 'PASS': raise SystemExit(1)

if __name__ == '__main__': main()
