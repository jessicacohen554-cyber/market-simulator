"""D61 zero-solve re-clearing: the arm-A offer stacks re-cleared with class E&AS deltas (observable bounds only)."""
import json, sys, glob
sys.path.insert(0, "src")
from market_sim.model.capacity_evolution.adequacy import capacity_supply_curve, clear_capacity_supply_stack, CapacityOffer
from market_sim.config.scenarios import ScenarioConfig
CFG = ScenarioConfig(iso="PJM", mode="forecast", hindcast=True)
EFORD={"gas_cc":0.05,"gas_ct":0.06,"gas_st":0.07,"coal":0.08,"nuclear":0.03,"oil":0.10,"biomass":0.08,"gas_cc_ccs":0.05}
ELCC={"coal":0.83,"gas_cc":0.74,"gas_ct":0.60,"gas_st":0.73,"oil":0.91,"nuclear":0.95}
BAR={"coal":58.5,"gas_cc":30.0,"gas_ct":21.0,"gas_st":35.0,"oil":25.0,"nuclear":130.0}
PUB={2022:(50.00,1.0510),2023:(34.13,1.0552),2024:(28.92,1.0555),2025:(269.92,1.0049)}
b=glob.glob("results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing/PJM/*/")[0]
def afrac(fuel,y): return (1-EFORD.get(fuel,0.08)) if y<=2024 else ELCC.get(fuel,1-EFORD.get(fuel,0.08))
def run(label, delta_by_year, coal_bar=None):
    """delta_by_year[y][fuel] = E&AS uplift $/kW-yr NAMEPLATE added to that class's screen margin in screen year y."""
    print(f"\n### {label}")
    print(f"{'DY':8s} {'price':>8s} {'pub':>7s} {'ratio':>6s} {'pos':>7s} {'pub':>7s} {'Δpt':>6s} {'how / marginal':32s} uncleared firm by fuel")
    res={}
    for y in (2022,2023,2024,2025):
        d=json.load(open(f"{b}/evolution_{y}.json")); cc=d["capacity_clearing"]
        curve=capacity_supply_curve(CFG,"PJM",y); dl=delta_by_year.get(y,{})
        offers=[]
        for uid,fuel,offer,a_mw,_c in cc["offer_stack"]:
            af=afrac(fuel,y); o=offer
            if coal_bar is not None and fuel=="coal" and offer>0:
                # re-express coal's offer on the alternative bar: offer = max(0, bar' - eas)/(af*365); eas = bar - offer*365*af/1000
                eas=BAR["coal"]-offer*365*af/1000.0; o=max(0.0,(coal_bar-eas))*1000.0/(af*365.0)
            o=max(0.0, o - dl.get(fuel,0.0)*1000.0/(af*365.0))
            offers.append(CapacityOffer(unit_id=uid,fuel=fuel,offer_usd_per_mw_day=o,firm_mw=a_mw) if hasattr(CapacityOffer,"__dataclass_fields__") else (uid,fuel,o,a_mw,0.0))
        c=clear_capacity_supply_stack(offers, cc["price_takers_mw"], cc["requirement_mw"], curve)
        unc={}
        for o in getattr(c,"offer_stack",[]) or []:
            pass
        # uncleared by fuel: offers with offer > price (strict) plus marginal partial ignored
        for uid,fuel,o,a_mw,*_ in [(x.unit_id,x.fuel,x.offer_usd_per_mw_day,x.firm_mw) if hasattr(x,"unit_id") else x for x in offers]:
            if o > c.price_usd_per_mw_day + 1e-9: unc[fuel]=unc.get(fuel,0.0)+a_mw
        pub_p,pub_pos=PUB[y]
        print(f"{y}/{y+1-2000:02d}  {c.price_usd_per_mw_day:8.2f} {pub_p:7.2f} {c.price_usd_per_mw_day/pub_p:6.2f} {c.cleared_position:7.4f} {pub_pos:7.4f} {100*(c.cleared_position-pub_pos):+6.2f} {(c.how+' '+str(getattr(c,'marginal_unit','')))[:32]:32s} { {k:round(v) for k,v in sorted(unc.items())} }")
        res[y]=dict(price=c.price_usd_per_mw_day,ratio=c.price_usd_per_mw_day/pub_p,pos=c.cleared_position,dpos=100*(c.cleared_position-pub_pos),uncleared=unc,how=c.how)
    return res

def scenarios(out):
    # Screen year -> dispatch year whose prices built the offers (2022 bridged: 2022 & 2023 screens read 2021's solve)
    DISP={2022:2021,2023:2021,2024:2023,2025:2024}
    # (i) reactive: PJM's own demand-curve E&AS-offset reactive component, $2,199/MW-yr (2024 SOM sec10) -> 2.2 $/kW-yr, every thermal class
    REACT={f:2.2 for f in BAR}
    # (ii) uplift credits by unit type, SOM Table 4-4 ($M) / model class nameplate (MW) -> $/kW-yr; an OBSERVABLE BOUND, not an input
    UPL_M={2021:{"gas_ct":153.5,"gas_cc":5.9,"coal":13.5,"steam_other":3.3},
           2022:{"gas_ct":174.5,"gas_cc":33.7,"coal":35.2,"steam_other":39.8},
           2023:{"gas_ct":92.8,"gas_cc":5.3,"coal":36.1,"steam_other":19.8},
           2024:{"gas_ct":119.9,"gas_cc":11.8,"coal":61.1,"steam_other":71.1}}
    NAME={2022:{"coal":40896,"gas_cc":48920,"gas_ct":24939,"gas_st":9464,"oil":3329},  # ledger fleet_by_fuel_before (nameplate MW), filled below
          2023:{},2024:{},2025:{}}
    import json,glob
    for y in (2022,2023,2024,2025):
        d=json.load(open(f"{b}/evolution_{y}.json")); NAME[y]={k:v for k,v in d["fleet_by_fuel_before"].items()}
    def upl(y):
        dy=DISP[y]; n=NAME[y]; u=UPL_M[dy]
        st_oil=n.get("gas_st",0)+n.get("oil",0)
        return {"gas_ct":u["gas_ct"]*1e6/(n["gas_ct"]*1000),"gas_cc":u["gas_cc"]*1e6/(n["gas_cc"]*1000),"coal":u["coal"]*1e6/(n["coal"]*1000),
                "gas_st":u["steam_other"]*1e6/(st_oil*1000) if st_oil else 0,"oil":u["steam_other"]*1e6/(st_oil*1000) if st_oil else 0}
    for y in (2022,2023,2024,2025): print("uplift $/kW-yr by class, screen",y,"(dispatch",DISP[y],"):",{k:round(v,1) for k,v in upl(y).items()})
    out["S1"]=run("S1 — reactive only (+2.2 $/kW-yr every thermal class; PJM's own E&AS-offset reactive component)", {y:REACT for y in DISP})
    out["S2"]=run("S2 — reactive + uplift-by-unit-type bound (SOM Table 4-4 / model class nameplate, dispatch-year matched)", {y:{f:REACT[f]+upl(y).get(f,0) for f in BAR} for y in DISP})
    out["S4"]=run("S4 — coal bar at Manual 18 default gross ACR ($80/MW-day nameplate = 29.2 $/kW-yr) instead of 1.3x45; no E&AS delta", {}, coal_bar=29.2)
    out["S5"]=run("S5 — S2 + S4 together", {y:{f:REACT[f]+upl(y).get(f,0) for f in BAR} for y in DISP}, coal_bar=29.2)
    return out

PUBBAR={"coal":80*365/1000,"gas_cc":56*365/1000,"gas_ct":50*365/1000,"gas_st":64*365/1000,"oil":64*365/1000,"nuclear":445*365/1000}  # Manual 18 Rev 62 default gross ACR, $/MW-day nameplate -> $/kW-yr (steam oil&gas: the 2026/27 column, n/a earlier)
def run_bars(label, delta_by_year, bars):
    print(f"\n### {label}")
    print(f"{'DY':8s} {'price':>8s} {'pub':>7s} {'ratio':>6s} {'pos':>7s} {'pub':>7s} {'Δpt':>6s} {'how':28s} {'marginal':30s} uncleared firm by fuel (strictly above price)")
    res={}
    for y in (2022,2023,2024,2025):
        d=json.load(open(f"{b}/evolution_{y}.json")); cc=d["capacity_clearing"]
        curve=capacity_supply_curve(CFG,"PJM",y); dl=delta_by_year.get(y,{}); offers=[]; fuel_of={}
        for uid,fuel,offer,a_mw,_c in cc["offer_stack"]:
            af=afrac(fuel,y); eas=BAR[fuel]-offer*365*af/1000.0 if offer>0 else None
            if eas is None: o=0.0   # offer 0: EAS >= bar (censored); stays a price taker under a lower bar too
            else: o=max(0.0,bars[fuel]-eas-dl.get(fuel,0.0))*1000.0/(af*365.0)
            offers.append((uid,fuel,o,a_mw,0.0)); fuel_of[uid]=fuel
        c=clear_capacity_supply_stack(offers, cc["price_takers_mw"], cc["requirement_mw"], curve)
        unc={}
        for uid,fuel,o,a_mw,_ in offers:
            if o > c.price_usd_per_mw_day + 1e-9: unc[fuel]=unc.get(fuel,0.0)+a_mw
        pub_p,pub_pos=PUB[y]; mu=getattr(c,"marginal_unit",None)
        print(f"{y}/{y+1-2000:02d}  {c.price_usd_per_mw_day:8.2f} {pub_p:7.2f} {c.price_usd_per_mw_day/pub_p:6.2f} {c.cleared_position:7.4f} {pub_pos:7.4f} {100*(c.cleared_position-pub_pos):+6.2f} {c.how[:28]:28s} {(str(mu)+' '+fuel_of.get(mu,''))[:30]:30s} { {k:round(v) for k,v in sorted(unc.items())} }")
        res[y]=dict(price=c.price_usd_per_mw_day,ratio=c.price_usd_per_mw_day/pub_p,pos=c.cleared_position,dpos=100*(c.cleared_position-pub_pos),uncleared=unc,how=c.how,marginal=str(mu),marginal_fuel=fuel_of.get(mu,""))
    return res

def run_eas_replace(label, eas_by_year, bars):
    """Replace every screened unit's E&AS with a per-class OBSERVED median (SOM Table 7-40/7-36), $/kW-yr nameplate; offer = max(0, bar - eas)/(af*365)."""
    print(f"\n### {label}")
    print(f"{'DY':8s} {'price':>8s} {'pub':>7s} {'ratio':>6s} {'pos':>7s} {'pub':>7s} {'Δpt':>6s} {'how':28s} uncleared firm by fuel (strictly above price)")
    res={}
    for y in (2022,2023,2024,2025):
        d=json.load(open(f"{b}/evolution_{y}.json")); cc=d["capacity_clearing"]
        curve=capacity_supply_curve(CFG,"PJM",y); e=eas_by_year[y]; offers=[]
        for uid,fuel,offer,a_mw,_c in cc["offer_stack"]:
            af=afrac(fuel,y); o=max(0.0, bars[fuel]-e.get(fuel,0.0))*1000.0/(af*365.0)
            offers.append((uid,fuel,o,a_mw,0.0))
        c=clear_capacity_supply_stack(offers, cc["price_takers_mw"], cc["requirement_mw"], curve)
        unc={}
        for uid,fuel,o,a_mw,_ in offers:
            if o > c.price_usd_per_mw_day + 1e-9: unc[fuel]=unc.get(fuel,0.0)+a_mw
        pub_p,pub_pos=PUB[y]
        print(f"{y}/{y+1-2000:02d}  {c.price_usd_per_mw_day:8.2f} {pub_p:7.2f} {c.price_usd_per_mw_day/pub_p:6.2f} {c.cleared_position:7.4f} {pub_pos:7.4f} {100*(c.cleared_position-pub_pos):+6.2f} {c.how[:28]:28s} { {k:round(v) for k,v in sorted(unc.items())} }")
        res[y]=dict(price=c.price_usd_per_mw_day,ratio=c.price_usd_per_mw_day/pub_p,pos=c.cleared_position,dpos=100*(c.cleared_position-pub_pos),uncleared=unc,how=c.how)
    return res


if __name__ == "__main__":
    # Run from the repo root: python3 docs/handoffs/d61/reclear-2026-09-05.py docs/handoffs/d61/reclear-2026-09-05.json
    out = {}
    out["S0"] = run("S0 — reproduction of the committed arm-A clearing (zero delta)", {})
    scenarios(out)
    out["S6"] = run_bars("S6 — every class bar at PJM's PUBLISHED default gross ACR (Manual 18 Rev 62; steam at the 2026/27 column); no E&AS delta", {}, PUBBAR)
    DISP = {2022: 2021, 2023: 2021, 2024: 2023, 2025: 2024}
    SOM = {2021: {"gas_cc": 27.779, "gas_ct": 3.24, "coal": 27.209, "gas_st": -0.784, "oil": 10.590, "nuclear": 272.263},
           2022: {"gas_cc": 83.538, "gas_ct": 19.234, "coal": 31.458, "gas_st": 0.0, "oil": 36.190, "nuclear": 518.160},
           2023: {"gas_cc": 55.088, "gas_ct": 4.971, "coal": -7.937, "gas_st": 0.0, "oil": 0.0, "nuclear": 213.144},
           2024: {"gas_cc": 72.691, "gas_ct": 8.157, "coal": 11.257, "gas_st": 0.280, "oil": 6.721, "nuclear": 213.144}}
    out["S3a"] = run_eas_replace("S3a — E&AS := SOM existing-unit MEDIAN by class (Tables 7-36/7-40), dispatch-year matched; MODEL bars", {y: SOM[DISP[y]] for y in DISP}, BAR)
    out["S3b"] = run_eas_replace("S3b — same E&AS; PUBLISHED bars", {y: SOM[DISP[y]] for y in DISP}, PUBBAR)
    json.dump(out, open(sys.argv[1] if len(sys.argv) > 1 else "/dev/null", "w"), indent=1)
