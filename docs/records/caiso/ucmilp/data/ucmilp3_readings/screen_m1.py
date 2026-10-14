import sys, json
from pathlib import Path
sys.path.insert(0,'/home/user/market-simulator/scripts/probes'); sys.path.insert(0,'/home/user/market-simulator/src')
import _ucmilp_benefit_screen as s
b=Path(sys.argv[1]); out={}
cp=s.committed_pct('CAISO')
for y in map(int,sys.argv[3:]):
    r=s.screen_year('CAISO',b,y,cp); out[y]=r
    print(y, json.dumps({k:v for k,v in r.items() if k in('classes',)}, default=str)[:1500], flush=True)
json.dump(out,open(sys.argv[2],'w'),default=s._js if hasattr(s,'_js') else str,indent=1)
