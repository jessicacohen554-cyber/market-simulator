import sys, re, pandas as pd
S=sys.argv[1]
res=pd.read_parquet(f"{S}/bc/psi_all.parquet"); c=res[res.group.eq("n_s_corridor")].copy()
pm=pd.read_parquet(f"{S}/bc/registry_perm_monitored.parquet"); tm=pd.read_parquet(f"{S}/bc/registry_temp_monitored.parquet")
def key(s):
    s=str(s).upper(); s=re.sub(r"^(XFMR|XF|LN)\s+","",s); s=re.sub(r"\s+\d+(/\d+)?\s*KV$","",s)
    a=[re.sub(r"\d+$","",x.strip()) for x in s.split(" - ")]   # VIOLA7 -> VIOLA, FRANKLN5 -> FRANKLN
    if len(a)==1: return a[0]
    if len(a)==2 and a[0]==a[1]: return a[0]                       # XFMR A - A  ==  XF A
    return " - ".join(sorted(a)) if len(a)==2 else s
pm["k"]=pm.Element.map(key); tm["k"]=tm.Element.map(key); c["k"]=c["Monitored Facility"].map(key)
rows=[]
for _,r in c.iterrows():
    p=pm[pm.k.eq(r.k)]; t=tm[tm.k.eq(r.k)]
    pf=p[p.fg.eq(r["Constraint Name"])]; tf=t[t.fg.eq(r["Constraint Name"])]
    rows.append({"Constraint Name":r["Constraint Name"],"mon":r["Monitored Facility"],"hours":r.hours,"psi":round(r.psi,4),"t":round(r.t,1),"ident":r.identified,
      "perm_fg_match":len(pf),"perm_normal_mean":pf.normal_mean.iloc[0] if len(pf) else None,"perm_emerg_mean":pf.emerg_mean.iloc[0] if len(pf) else None,
      "temp_fg_match":len(tf),"temp_norm":tf.NormLimit.iloc[0] if len(tf) else None,"temp_emer":tf.EmerLimit.iloc[0] if len(tf) else None,
      "elem_perm_n":len(p),"elem_perm_normal_range":(p.normal_mean.min(),p.normal_mean.max()) if len(p) else None,
      "elem_temp_n":len(t),"elem_temp_norm_range":(t.NormLimit.min(),t.NormLimit.max()) if len(t) else None,"elem_volt":p.Voltage.iloc[0] if len(p) else (t.Element.iloc[0][-10:] if len(t) else None)})
R=pd.DataFrame(rows).sort_values("hours",ascending=False); pd.set_option("display.width",300)
print(R.to_string(index=False,max_colwidth=30)); R.to_csv(f"{S}/bc/registry_xcheck.csv",index=False)
