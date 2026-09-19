"""Pruebas automatizadas del método (ejemplos con resultado conocido)."""
import json, sys, unittest, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from datetime import date
import numpy as np
from metodo import *


class TestAgregacion(unittest.TestCase):
    def times(self, start='2026-06-14T00:00', n=72):
        from datetime import datetime, timedelta
        t0 = datetime.fromisoformat(start)
        return [(t0 + timedelta(hours=i)).strftime('%Y-%m-%dT%H:%M') for i in range(n)]

    def test_total_diario_usa_marcas_01_a_00(self):
        t = self.times()
        v = [0.0] * 72
        # día objetivo 2026-06-15: marcas 06-15 01:00 … 06-16 00:00 → índices 25 … 48
        for i in range(25, 49):
            v[i] = 10.0
        v[24] = 999.0   # 06-15 00:00 pertenece al día anterior (hora precedente)
        v[49] = 999.0   # 06-16 01:00 pertenece al día siguiente
        self.assertEqual(total_diario(t, v, '2026-06-15'), 240.0)

    def test_total_diario_falta_una_marca(self):
        t = self.times(); v = [10.0] * 72; v[30] = None
        self.assertIsNone(total_diario(t, v, '2026-06-15'))
        v[30] = 1600.0
        self.assertIsNone(total_diario(t, v, '2026-06-15'))
        v[30] = -1.0
        self.assertIsNone(total_diario(t, v, '2026-06-15'))

    def test_total_diario_pasada_06_con_nulos_iniciales(self):
        t = self.times('2026-06-14T00:00'); v = [None] * 6 + [5.0] * 66
        self.assertEqual(total_diario(t, v, '2026-06-15'), 120.0)

    def test_nubosidad(self):
        t = self.times(); v = [0.0] * 72
        for h in range(6, 19):
            v[24 + h] = 50.0 if h != 12 else 63.0
        self.assertAlmostEqual(nubosidad_diurna(t, v, '2026-06-15'), (12 * 50 + 63) / 13)
        v[24 + 12] = 101.0
        self.assertIsNone(nubosidad_diurna(t, v, '2026-06-15'))

    def test_suma_0618(self):
        t = self.times(); v = [0.0] * 72
        for h in range(7, 19):
            v[24 + h] = 100.0
        v[24 + 6] = 999.0; v[24 + 19] = 999.0
        self.assertEqual(suma_0618(t, v, '2026-06-15'), 1200.0)


class TestBootstrap(unittest.TestCase):
    def test_pesos_suman_n(self):
        W = pesos_bootstrap(110, 7, 500, 1)
        self.assertEqual(W.shape, (500, 110))
        np.testing.assert_array_equal(W.sum(axis=1), 110.0)

    def test_bloques_contiguos_L1_es_iid(self):
        W = pesos_bootstrap(20, 1, 2000, 3)
        self.assertAlmostEqual(W.mean(), 1.0, places=6)
        self.assertTrue((W.max(axis=1) > 1).mean() > 0.99)

    def test_bloques_L7_conservan_contiguidad(self):
        # con L = n, cada réplica es una rotación completa: todos los pesos valen 1
        W = pesos_bootstrap(14, 14, 50, 5)
        np.testing.assert_array_equal(W, 1.0)

    def test_reproducible(self):
        np.testing.assert_array_equal(pesos_bootstrap(30, 7, 100, 20260914), pesos_bootstrap(30, 7, 100, 20260914))


class TestEfecto(unittest.TestCase):
    def test_efecto_y_p(self):
        n = np.array([2.0, 2.0, 2.0, 2.0])
        sumA = np.array([4.0, 4.0, 4.0, 4.0])   # MAE_A = 2
        sumB = np.array([2.0, 2.0, 2.0, 2.0])   # MAE_B = 1
        W = pesos_bootstrap(4, 1, 200, 0)
        r = comparar(sumA, sumB, n, W)
        self.assertEqual(r['n'], 8)
        self.assertAlmostEqual(r['mae_a'], 2.0); self.assertAlmostEqual(r['mae_b'], 1.0)
        self.assertAlmostEqual(r['efecto'], 50.0)
        self.assertAlmostEqual(r['ic95'][0], 50.0); self.assertAlmostEqual(r['ic95'][1], 50.0)
        self.assertEqual(r['p'], 0.0)  # todas las réplicas > 0 → fracción ≤0 es 0

    def test_p_bilateral(self):
        self.assertAlmostEqual(p_bilateral(np.array([-1, 1, 2, 3])), 0.5)
        self.assertAlmostEqual(p_bilateral(np.array([1, 2, 3, 4])), 0.0)
        self.assertAlmostEqual(p_bilateral(np.array([0, 0, 0, 0])), 1.0)
        self.assertAlmostEqual(p_bilateral(np.array([-2, -1, 1, 2, 3, 4, 5, 6, 7, 8])), 0.4)

    def test_efecto_signo(self):
        self.assertAlmostEqual(efecto(10.0, 8.0), 20.0)
        self.assertAlmostEqual(efecto(8.0, 10.0), -25.0)


class TestHolm(unittest.TestCase):
    def test_holm_dos(self):
        r = holm({'H1': 0.01, 'H2': 0.04})
        self.assertAlmostEqual(r['H1']['p_ajustado'], 0.02); self.assertTrue(r['H1']['rechaza'])
        self.assertAlmostEqual(r['H2']['p_ajustado'], 0.04); self.assertTrue(r['H2']['rechaza'])
        r = holm({'H1': 0.03, 'H2': 0.20})
        self.assertAlmostEqual(r['H1']['p_ajustado'], 0.06); self.assertFalse(r['H1']['rechaza'])
        self.assertAlmostEqual(r['H2']['p_ajustado'], 0.20); self.assertFalse(r['H2']['rechaza'])
        r = holm({'H1': 0.0, 'H2': 0.6})
        self.assertTrue(r['H1']['rechaza']); self.assertAlmostEqual(r['H2']['p_ajustado'], 0.6)

    def test_holm_monotono(self):
        r = holm({'A': 0.02, 'B': 0.021})
        self.assertAlmostEqual(r['A']['p_ajustado'], 0.04); self.assertAlmostEqual(r['B']['p_ajustado'], 0.04)


class TestH0(unittest.TestCase):
    def test_fao56_ejemplo(self):
        # FAO-56 ejemplo 8: 20°S, 3 de septiembre → Ra ≈ 32,2 MJ/m²/día
        self.assertAlmostEqual(h0_fao56(-20.0, date(2001, 9, 3)), 32.2, delta=0.15)

    def test_h0_verano_espana(self):
        self.assertAlmostEqual(h0_fao56(40.0, date(2026, 6, 21)), 41.7, delta=0.5)


class TestRutasPortables(unittest.TestCase):
    """El manifiesto heredado guardaba separadores de Windows. En POSIX eso no separa nada:
    Path('raw\\heredado\\x.json') es un unico nombre de fichero y la seccion 6.5 desaparecia
    en silencio. Estas pruebas fallan en cualquier sistema si el defecto vuelve."""

    def test_ruta_acepta_los_dos_separadores(self):
        from comun import ruta
        esperado = ('raw', 'heredado', 'AL01_cal', 'obs_0.json')
        self.assertEqual(ruta('raw' + chr(92) + 'heredado' + chr(92) + 'AL01_cal' + chr(92) + 'obs_0.json').parts, esperado)
        self.assertEqual(ruta('raw/heredado/AL01_cal/obs_0.json').parts, esperado)
        self.assertEqual(ruta(Path('raw/heredado/AL01_cal/obs_0.json')).parts, esperado)

    def test_manifiesto_heredado_es_posix(self):
        """Ninguna ruta guardada puede llevar separador de Windows."""
        from comun import DATOS
        f = DATOS / 'heredado_manifiesto.json'
        if not f.exists():
            self.skipTest('no hay manifiesto heredado en este arbol')
        m = json.loads(f.read_text(encoding='utf-8'))
        malas = [o['destino'] for fu in m['fuentes'].values() for k in ('obs', 'forecasts')
                 for o in fu.get(k, []) if isinstance(o, dict) and chr(92) in o.get('destino', '')]
        self.assertEqual(malas[:3], [], f'{len(malas)} rutas con separador de Windows')

    def test_el_lector_resuelve_todas_las_entradas_del_manifiesto(self):
        """Resolver cada entrada con ruta() debe dar mas de un componente. Pasa con el
        manifiesto nuevo y tambien con el viejo: es la garantia de que el lector tolera
        los dos formatos, no una deteccion del formato viejo."""
        from comun import DATOS, ruta
        f = DATOS / 'heredado_manifiesto.json'
        if not f.exists():
            self.skipTest('no hay manifiesto heredado en este arbol')
        m = json.loads(f.read_text(encoding='utf-8'))
        n = 0
        for fu in m['fuentes'].values():
            for k in ('obs', 'forecasts'):
                for o in fu.get(k, []):
                    if not isinstance(o, dict) or 'destino' not in o:
                        continue
                    n += 1
                    partes = ruta(o['destino']).parts
                    self.assertGreater(len(partes), 1, f'ruta sin separar: {o["destino"]!r}')
                    self.assertEqual(partes[0], 'raw', f'ruta inesperada: {o["destino"]!r}')
        self.assertGreater(n, 1000, 'el manifiesto deberia tener mas de mil entradas')


    def test_el_consumo_antiguo_se_rompia_en_posix(self):
        """Reproduce el defecto de v1.0.1 sin depender del sistema donde corre la prueba.
        Antes se hacia BASE / valor con Path; en POSIX la barra invertida no separa, asi que
        toda la ruta colapsaba en un unico nombre de fichero y la seccion 6.5 se perdia."""
        from pathlib import PurePosixPath, PureWindowsPath
        guardada = 'raw' + chr(92) + 'heredado' + chr(92) + 'AL01_cal' + chr(92) + 'obs_0.json'
        self.assertEqual(len(PurePosixPath(guardada).parts), 1)          # asi se rompia
        self.assertEqual(len(PureWindowsPath(guardada).parts), 4)        # asi se arregla
        from comun import ruta
        self.assertEqual(len(ruta(guardada).parts), 4)


if __name__ == '__main__':
    unittest.main(verbosity=2)
