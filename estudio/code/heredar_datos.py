"""Copia con procedencia (ruta origen + SHA-256) los semihorarios y pronósticos YA descargados por trabajos previos,
para la sección enlace_06_18. No descarga nada.
"""
from comun import *
import shutil

WORK = ROOT / 'work'
SOURCES = {
    'AL01_cal': {'obs': WORK / 'calibration_validation/stations/AL01/raw/siar_1.json', 'forecasts': WORK / 'calibration_validation/stations/AL01/raw/forecasts', 'station': WORK / 'calibration_validation/stations/AL01/station.json'},
    'C01_cal': {'obs': WORK / 'calibration_validation/stations/C01/raw/siar_1.json', 'forecasts': WORK / 'calibration_validation/stations/C01/raw/forecasts', 'station': WORK / 'calibration_validation/stations/C01/station.json'},
    'AL01_rep': {'obs': WORK / 'replication/stations/AL01/raw/siar_1.json', 'forecasts': WORK / 'replication/stations/AL01/raw/forecasts', 'station': WORK / 'replication/stations/AL01/station.json'},
    'C01_rep': {'obs': WORK / 'replication/stations/C01/raw/siar_1.json', 'forecasts': WORK / 'replication/stations/C01/raw/forecasts', 'station': WORK / 'replication/stations/C01/station.json'},
    'M01_pil': {'obs': WORK / 'pilot_1/month_run/raw/siar_1.json', 'forecasts': WORK / 'pilot_1/month_run/raw/forecasts', 'station': WORK / 'pilot_1/month_run/station.json'},
    'AL10_nb': {'obs': [WORK / 'neighbor_audit/raw/siar/AL10/1_2026-06-16_2026-07-08/derived.json', WORK / 'neighbor_audit/raw/siar/AL10/1_2026-07-09_2026-07-31/derived.json']},
    'LU01_nb': {'obs': [WORK / 'neighbor_audit/raw/siar/LU01/1_2026-06-16_2026-07-08/derived.json', WORK / 'neighbor_audit/raw/siar/LU01/1_2026-07-09_2026-07-31/derived.json']},
}


def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return {'origen': str(src), 'destino': dst.relative_to(BASE).as_posix(), 'sha256': sha256_file(dst), 'bytes': dst.stat().st_size}


def main():
    manifest = {}
    for tag, spec_ in SOURCES.items():
        entry = {'obs': [], 'forecasts': [], 'station': None}
        obs = spec_['obs'] if isinstance(spec_['obs'], list) else [spec_['obs']]
        for i, p in enumerate(obs):
            if not p.exists():
                entry['obs'].append({'origen': str(p), 'error': 'no existe'}); continue
            entry['obs'].append(copy(p, RAW / 'heredado' / tag / f'obs_{i}.json'))
        if spec_.get('station') and spec_['station'].exists():
            entry['station'] = copy(spec_['station'], RAW / 'heredado' / tag / 'station.json')
        if spec_.get('forecasts') and spec_['forecasts'].exists():
            for p in sorted(spec_['forecasts'].glob('*.json')):
                entry['forecasts'].append(copy(p, RAW / 'heredado' / tag / 'forecasts' / p.name))
        manifest[tag] = entry
        print(tag, 'obs', len(entry['obs']), 'forecast files', len(entry['forecasts']), 'station', bool(entry['station']))
    dump(DATOS / 'heredado_manifiesto.json', {'generado_utc': now(), 'fuentes': manifest})


if __name__ == '__main__':
    main()
