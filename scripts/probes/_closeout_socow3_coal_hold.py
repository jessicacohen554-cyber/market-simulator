"""closeout-SOCO-w3 zero LP: upper bound of a coal commitment state on the BTM-holdout probe.

Holds each coal plant at its metered online P5 through every day the model already commits it.
"""

import sys
import json,gzip,re,base64,numpy as np,pandas as pd
SP=sys.argv[1]  # dir with arm_run.js (probe payload) and bench_arm/<Y>.json.gz (probe bench parts, from claude/closeout-soco-w3-reg)
p=json.loads(gzip.decompress(base64.b64decode(re.search(r'="([A-Za-z0-9+/=]+)"',open(SP+'/arm_run.js').read()).group(1))))
out=[]
for y in range(2019,2026):
    yb=json.load(gzip.open(f'{SP}/bench_arm/{y}.json.gz'))['bench']; yp=p['years'][str(y)]
    T=8760; D=T//24
    tot=0; per={}
    for k,b in yb['plants'].items():
        if not str(b.get('group','')).startswith('COAL') or not b.get('campd') or b.get('nodata'): continue
        m=yp['plants'].get(k)
        if not m or not m.get('m'): continue
        s=b['npl']/100
        a=np.frombuffer(base64.b64decode(b['campd'])[:T],dtype=np.uint8)*s
        mm=np.frombuffer(base64.b64decode(m['m'])[:T],dtype=np.uint8)*s
        on=a>0.01*b['npl']
        if not on.any(): continue
        pmin=np.percentile(a[on],5)
        md=mm[:D*24].reshape(D,24)
        dayon=(md[:,7:22]>0.01*b['npl']).any(axis=1)
        cap=md.max(axis=1)  # proxy for that day's available capacity
        floor=np.minimum(pmin,cap)[:,None]*dayon[:,None]
        inc=np.clip(floor-md,0,None)
        per[k]=inc.sum()/1e6; tot+=inc.sum()/1e6
    out.append(dict(year=y,hold_twh=round(tot,2),**{k:round(v,2) for k,v in per.items() if v>0.05}))
print(pd.DataFrame(out).fillna(0).to_string(index=False))
