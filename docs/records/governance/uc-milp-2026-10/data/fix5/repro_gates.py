import json,sys
d=json.load(open(sys.argv[1]))
want={('fuelmix','CC_REGULAR'),('fuelmix','CT_PEAKER'),('fuelmix','ST_GAS'),('fuelmix','CC_CHP'),('price_mean',None),('price_shape',None),('price_tail',None),('dispatch_corr','gas'),('co2',None)}
seen=set()
def walk(x):
    if isinstance(x,dict):
        k=(x.get('criterion'),x.get('key'))
        if x.get('year')==2023 and k in want and k not in seen:
            seen.add(k); print(k, x.get('status'), x.get('model'), x.get('actual'), x.get('magnitude'))
        for v in x.values(): walk(v)
    elif isinstance(x,list):
        for v in x: walk(v)
walk(d)
