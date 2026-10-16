import json,sys
def recs(p):
    d=json.load(open(p)); out={}
    def walk(o):
        if isinstance(o,dict):
            if 'criterion' in o and 'status' in o and 'year' in o:
                out[(o['criterion'],str(o.get('key')),o['year'])]=(o['status'],o.get('magnitude'),o.get('model'),o.get('actual'))
            for v in o.values(): walk(v)
        elif isinstance(o,list):
            for v in o: walk(v)
    walk(d); return out
c=recs(sys.argv[1]); a=recs(sys.argv[2]); u=recs(sys.argv[3]) if len(sys.argv)>3 else {}
yrs=set(int(y) for y in sys.argv[4].split(',')) if len(sys.argv)>4 else None
for k in sorted(set(a)&set(c), key=lambda k:(k[2] or 0,k[0],k[1])):
    if yrs and (k[2] or 0) not in yrs: continue
    cs,as_=c[k][0],a[k][0]
    flag = 'FLIP' if cs=='PASS' and as_=='FAIL' else ('fix' if cs=='FAIL' and as_=='PASS' else '')
    if cs!=as_ or k[0] in ('c1_class_volumes','price_level','c3a','c3b','c3c','c4','c8') or flag:
        print(k[2],k[0],k[1],'|',cs,c[k][1],'->',(u.get(k,('',''))[0],u.get(k,('',''))[1]),'->',as_,a[k][1],flag)
