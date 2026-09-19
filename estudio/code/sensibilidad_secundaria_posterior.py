"""Corrección de cierre: cálculo POSTERIOR de escala en la ventana secundaria.

La ventana fue preespecificada; esta extensión de sensibilidad y la rejilla de cruce
se calculan después de conocer los resultados. No alteran el veredicto primario.
Lee el panel existente y escribe un archivo nuevo, no resultados.json.
"""
from comun import *
from metodo import pesos_bootstrap, comparar
import numpy as np

COMPS={'H1':('IFS_00','IFS_06'),'H2':('IFS_00','AIFS_00')}

def main():
    p=load(OUT/'panel_analisis.json'); sp=spec(); official=load(OUT/'resultados.json')
    orig=load(DATOS/'diagnostico_posterior.json')
    arr=lambda name: np.asarray(p[name],dtype=float)
    observation=arr('obs_wh_m2'); forecasts={s:arr(s) for s in ['IFS_00','IFS_06','AIFS_00','AIFS_06']}
    replicas=sp['analisis']['bootstrap']['replicas']; seed=sp['analisis']['bootstrap']['semilla']
    result={'generado_utc':now(),'tipo':'Extensión posterior solicitada en la corrección de cierre; no preespecificada como resultado primario',
            'ventana_secundaria_prefijada':True,'sensibilidad_secundaria_calculada_despues_de_ver_resultados':True,
            'replicas':replicas,'semilla':seed,'rejilla_cruces':{'inicio':0.8,'fin':1.10,'paso':0.0025,
            'regla':'Cambios de signo entre nodos e interpolación lineal; rango ampliado después de recibir los cruces alegados. No estima el k real.'},
            'ventanas':{},'control':{}}
    maxdiff=0.0
    for window in ['primaria','secundaria']:
        first,last=official[window]['dias']
        ids=np.array([i for i,d in enumerate(p['calendario']) if first<=d<=last])
        O=observation[:,ids]; F={s:v[:,ids] for s,v in forecasts.items()}
        mean=np.nanmean(O,axis=1)[:,None]
        weights={L:pesos_bootstrap(len(ids),L,replicas,seed) for L in [1,7,14]}
        w={'dias':[first,last],'n_dias':len(ids),'comparaciones':{}}
        for h,(a,b) in COMPS.items():
            mask=np.isfinite(O)&np.isfinite(F[a])&np.isfinite(F[b])
            n=mask.sum(axis=0).astype(float)
            def sums(k):
                # Algebraicamente equivalente a usar O/k y media(O/k), para k>0.
                return [np.where(mask,np.abs(k*F[s]-O)/mean,0).sum(axis=0) for s in [a,b]]
            def effect(k):
                A,B=sums(k); return float(100*(A.sum()-B.sum())/A.sum())
            cases={}
            for k in [.95,1.,1.05]:
                A,B=sums(k)
                cases[f'{k:.2f}']={str(L):{kk:vv for kk,vv in comparar(A,B,n,W).items() if kk!='replicas'} for L,W in weights.items()}
            ks=np.round(np.arange(.8,1.10001,.0025),4); es=[effect(k) for k in ks]
            crosses=[]
            for i in range(1,len(ks)):
                if es[i-1]*es[i]<0:
                    crosses.append(float(ks[i-1]+(ks[i]-ks[i-1])*abs(es[i-1])/(abs(es[i-1])+abs(es[i]))))
            inband=[e for k,e in zip(ks,es) if .95<=k<=1.05]
            c={'n_pares':int(n.sum()),'por_k':cases,'efecto_k_0_99':effect(.99),'cruces':crosses,
               'curva':{f'{k:.4f}':e for k,e in zip(ks,es)},'positivo_en_nodos_banda_5pct':all(e>0 for e in inband)}
            # Control contra lo ya entregado: las cifras de k=1 para ambas ventanas y los
            # escenarios k=.95/1.05 de la primaria deben conservar los cálculos originales.
            for L in [1,7,14]:
                ref=official[window]['comparaciones'][h]['por_bloque'][str(L)]
                for field in ['efecto','mae_a','mae_b','p']:
                    maxdiff=max(maxdiff,abs(cases['1.00'][str(L)][field]-ref[field]))
                maxdiff=max(maxdiff,max(abs(x-y) for x,y in zip(cases['1.00'][str(L)]['ic95'],ref['ic95'])))
                assert int(n.sum())==ref['n']
                if window=='primaria':
                    for k in ['0.95','1.00','1.05']:
                        old=official['sensibilidad_determinista']['por_k'][k]['comparaciones'][h][str(L)]
                        maxdiff=max(maxdiff,abs(cases[k][str(L)]['efecto']-old['efecto']),
                                    max(abs(x-y) for x,y in zip(cases[k][str(L)]['ic95'],old['ic95'])))
            # Confirmación separada de puntos por iteración Python, sin reutilizar sums().
            sample=[]
            for s in range(O.shape[0]):
                for d in range(O.shape[1]):
                    if mask[s,d]: sample.append((float(O[s,d]),float(F[a][s,d]),float(F[b][s,d]),float(mean[s,0])))
            a95=sum(abs(a-o/.95)/(mu/.95) for o,a,b,mu in sample)/len(sample)
            b95=sum(abs(b-o/.95)/(mu/.95) for o,a,b,mu in sample)/len(sample)
            direct=100*(a95-b95)/a95
            c['verificacion_punto_k095_iteracion_python']={'efecto':direct,'diferencia_abs':abs(direct-cases['0.95']['7']['efecto'])}
            assert c['verificacion_punto_k095_iteracion_python']['diferencia_abs']<1e-10
            w['comparaciones'][h]=c
        result['ventanas'][window]=w
    assert maxdiff<1e-9,maxdiff
    result['control']={'max_diff_cifras_previas':maxdiff,'tolerancia':1e-9,'estado':'PASS'}
    # Comprobación de la descomposición descriptiva original (global, no por estación).
    ids=[i for i,d in enumerate(p['calendario']) if official['primaria']['dias'][0]<=d<=official['primaria']['dias'][1]]
    decomp={}
    for s in forecasts:
        d=forecasts[s][:,ids]-observation[:,ids]; v=d[np.isfinite(d)]
        mse=float(np.mean(v**2)); bias2=float(np.mean(v)**2); var=float(np.var(v))
        prev=orig['sesgo_dispersion'][s]
        assert abs(mse-prev['mse'])<1e-6
        assert abs(bias2-prev['mse_parte_sesgo'])<1e-6
        assert abs(var-prev['mse_parte_varianza'])<1e-6
        decomp[s]={'n':len(v),'mse':mse,'media_residuo_al_cuadrado':bias2,'varianza_residuo':var}
    result['descomposicion_global_verificada']=decomp
    dump(DATOS/'sensibilidad_secundaria_posterior.json',result)
    print(json.dumps({'control':result['control'],'k095':{w:{h:v['por_k']['0.95']['7'] for h,v in x['comparaciones'].items()} for w,x in result['ventanas'].items()},
        'cruces':{w:{h:v['cruces'] for h,v in x['comparaciones'].items()} for w,x in result['ventanas'].items()}},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
