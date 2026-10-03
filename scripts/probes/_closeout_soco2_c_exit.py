"""(c) exit-carry last-year profile: EIA-923 monthly wind-down vs Y-1, and the R-3 coal take envelope."""

import pandas as pd
import numpy as np
import calendar

OUT = "docs/records/soco/r-soco/closeout-soco-2/"
A = pd.read_csv(
    "docs/records/governance/closeout-2026-10/W0-phase3/carry_audit_w0_2026-10-02.csv"
)
A = A[A.bucket == "EXIT-CARRY"].copy()
g = pd.read_parquet("data/raw/_processed-legacy/eia923_monthly_generation.parquet")
MON = [f"netgen_{calendar.month_name[m].lower()}_mwh" for m in range(1, 13)]
COALF = ["BIT", "SUB", "LIG", "RC", "WC", "SGC"]


def fam_rows(df, fam):
    if fam == "COAL":
        return df[df.fuel_type.isin(COALF)]
    if fam == "ST_GAS":
        return df[(df.prime_mover == "ST") & (df.fuel_type.isin(["NG", "OG", "BFG"]))]
    if fam == "CT":
        return df[df.prime_mover.isin(["GT", "IC"])]
    if fam == "CC":
        return df[df.prime_mover.isin(["CA", "CT", "CS", "CC"])]
    if fam == "NUCLEAR":
        return df[df.fuel_type == "NUC"]
    return df


rows = []
for _, r in A.iterrows():
    y = int(r.year)
    p = int(r.plant)
    mo = int(r.months_online)
    cur = fam_rows(g[(g.year == y) & (g.plant_id == p)], r.family)[MON].sum().values
    prv = fam_rows(g[(g.year == y - 1) & (g.plant_id == p)], r.family)[MON].sum().values
    on = slice(0, mo)
    ratio = cur[on].sum() / prv[on].sum() if prv[on].sum() > 0 else np.nan
    # last-3-online-months vs first-3 share, both years
    l3 = slice(max(0, mo - 3), mo)
    f3 = slice(0, min(3, mo))

    def cfr(v):
        return v[l3].sum() / max(v[f3].sum(), 1)

    rec = dict(
        iso=r.iso,
        year=y,
        plant=p,
        name=r["name"][:22],
        fam=r.family,
        mw=r.carried_mw,
        mo=mo,
        e923=cur[on].sum() / 1e3,
        e923_prev_same=prv[on].sum() / 1e3,
        yoy=ratio,
        last3_first3_Y=cfr(cur),
        last3_first3_Yprev=cfr(prv),
        model=r.model_mwh_plant / 1e3 if pd.notna(r.model_mwh_plant) else np.nan,
        avail=r.model_avail_mwh_plant / 1e3
        if pd.notna(r.model_avail_mwh_plant)
        else np.nan,
        monthly=" ".join(f"{x / 1e3:.0f}" for x in cur[:mo]),
    )
    if r.family == "COAL":
        try:
            rc = pd.read_csv(
                f"data/raw/coal-receipts/coal_receipts_{y}.csv", low_memory=False
            )
            for c in ["QUANTITY", "Average Heat Content"]:
                rc[c] = pd.to_numeric(rc[c], errors="coerce")
            rc = rc[(rc["Plant Id"] == p) & (rc.MONTH <= mo)]
            rec_mmbtu = (rc.QUANTITY * rc["Average Heat Content"]).sum()
            hc = (
                (rc.QUANTITY * rc["Average Heat Content"]).sum()
                / max(rc.QUANTITY.sum(), 1)
                if len(rc)
                else np.nan
            )
            st = pd.read_csv(
                f"data/raw/coal-stocks/coal_stocks_{y - 1}.csv", low_memory=False
            )
            st = st[st["Plant Id"] == p]
            s0 = pd.to_numeric(st["Quantity December"], errors="coerce").sum()
            # heat content fallback: prior-year receipts
            if not np.isfinite(hc) or hc == 0:
                rp = pd.read_csv(
                    f"data/raw/coal-receipts/coal_receipts_{y - 1}.csv",
                    low_memory=False,
                )
                for c in ["QUANTITY", "Average Heat Content"]:
                    rp[c] = pd.to_numeric(rp[c], errors="coerce")
                rp = rp[rp["Plant Id"] == p]
                hc = (rp.QUANTITY * rp["Average Heat Content"]).sum() / max(
                    rp.QUANTITY.sum(), 1
                )
            # HR Y-1 from 923 annual fuel + gen
            gf = pd.read_csv(
                "data/raw/eia-923-generation-fuel/eia923_generation_fuel_2019_2025.csv"
            )
            q = gf[(gf.year == y - 1) & (gf.plant_id == p) & gf.fuel_type.isin(COALF)]
            if q.net_generation_mwh.sum() <= 0:
                q = gf[(gf.year == y) & (gf.plant_id == p) & gf.fuel_type.isin(COALF)]
            hr = q.elec_fuel_mmbtu.sum() / max(q.net_generation_mwh.sum(), 1)
            env = (rec_mmbtu + s0 * hc) / hr / 1e3
            rec.update(
                receipts_gwh=rec_mmbtu / hr / 1e3,
                stock0_gwh=s0 * hc / hr / 1e3,
                r3_ceiling_gwh=env,
                hr=hr,
            )
        except FileNotFoundError:
            rec.update(r3_ceiling_gwh=np.nan)
    rows.append(rec)
R = pd.DataFrame(rows)
R.to_csv(OUT + "c_exit.csv", index=False)
pd.set_option("display.width", 320)
pd.set_option("display.max_colwidth", 60)
print(R.drop(columns=["monthly"]).round(2).to_string())
print(R[["iso", "year", "name", "monthly"]].to_string())
# control: ISO coal fleet yoy over same online months, excluding exit plants; by BA code
print("--- control")
BA = {
    "MISO": ["MISO"],
    "PJM": ["PJM"],
    "SOCO": ["SOCO"],
    "ERCOT": ["ERCO"],
    "SPP": ["SWPP"],
    "NWPP": ["BPAT", "PACW", "PACE", "NWMT", "AVA", "PSEI", "PGE", "IPCO", "NEVP"],
    "CAISO": ["CISO"],
}
ctl = []
for _, r in R.iterrows():
    y = r.year
    mo = r.mo
    bas = BA.get(r.iso, [])
    cur = g[(g.year == y) & g.ba_code.isin(bas)]
    prv = g[(g.year == y - 1) & g.ba_code.isin(bas)]
    ex = set(R.plant)
    fam = r.fam
    c = fam_rows(cur[~cur.plant_id.isin(ex)], fam)[MON[:mo]].sum().sum()
    pv = fam_rows(prv[~prv.plant_id.isin(ex)], fam)[MON[:mo]].sum().sum()
    # dark terminal months
    m = [float(x) for x in r.monthly.split()]
    dark = 0
    for x in reversed(m):
        if x <= 0.5:
            dark += 1
        else:
            break
    ctl.append(
        dict(
            iso=r.iso,
            year=y,
            name=r["name"],
            fam=fam,
            yoy=r.yoy,
            ctl_yoy=c / pv if pv > 0 else np.nan,
            rel=r.yoy / (c / pv) if pv > 0 else np.nan,
            dark_tail_months=dark,
            mo=mo,
            e923=r.e923,
            model=r.model,
            r3=r.get("r3_ceiling_gwh", np.nan),
        )
    )
K = pd.DataFrame(ctl)
print(K.round(2).to_string())
K.to_csv(OUT + "c_exit_ctl.csv", index=False)
ok = K[K.model.notna()]
print(
    "rows with model:",
    len(ok),
    " model>e923:",
    (ok.model > ok.e923).sum(),
    " excess TWh",
    round((ok.model - ok.e923).clip(lower=0).sum() / 1e3, 2),
)
print(
    "dark tail>=1:", (K.dark_tail_months >= 1).sum(), " rel<0.8:", (K.rel < 0.8).sum()
)
