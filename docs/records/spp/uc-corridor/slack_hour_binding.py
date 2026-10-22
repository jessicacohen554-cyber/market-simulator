"""UC-SPP-CORRIDOR: what SPP's corridor elements did in the UC-arm slack hours.

For each non-artifact U4b slack hour with an effective-limit series (2022-2023;
`implied_ns_transfer.csv` of FINDING-spp-south-scarcity-2026-10-18), list the
SPP-53 corridor-group constraints (spp14 groups.py rules) that bound in RTBM,
with their effective limit and, for SPP-53's identified constituents,
T* = L / psi. Model hour index = hour-beginning on the local (America/Chicago)
non-leap clock.

Usage: python docs/records/spp/uc-corridor/slack_hour_binding.py <out.csv>
"""
import re, sys
from pathlib import Path
import pandas as pd

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from scripts.lib import clean_io  # noqa: E402

src = (REPO / "docs/records/spp/spp14/groups.py").read_text()
rules = src.split("rows=[]; detail=[]")[0].replace('sl=pd.read_csv("/home/user/market-simulator/', f'sl=pd.read_csv("{REPO}/')
ns = {}; exec(rules, ns)  # tokens(), group(): SPP-14's fixed membership rules, verbatim
T53 = pd.read_csv(REPO / "docs/records/spp/spp53/tstar_table.csv")
PSI = dict(zip(T53[T53.identified]["Constraint Name"], T53[T53.identified].psi))
imp = pd.read_csv(REPO / "docs/records/spp/ucmilp/data/spp_south_scarcity_2026_10_18/implied_ns_transfer.csv")
rows = []
for y in (2022, 2023):
    d = clean_io.read_clean("flowgate-limits-at-bind", iso="SPP", year=y, market="rt")
    d = d.rename(columns={"constraint_name": "Constraint Name", "monitored_facility": "Monitored Facility", "contingent_facility": "Contingent Facility"})
    d["tok"] = d["Contingent Facility"].map(ns["tokens"])
    d["group"] = d.apply(lambda r: ns["group"](r)[0], axis=1)
    for _, r in imp[imp.year == y].iterrows():
        loc = pd.Timestamp(f"{y}-01-01") + pd.Timedelta(hours=int(r.hour))
        utc = loc.tz_localize("America/Chicago").tz_convert("UTC")
        x = d[(d.hour_start_utc == utc) & (d.group == "n_s_corridor")]
        base = {"year": y, "model_hour": int(r.hour), "local": str(loc), "implied_NS_lo": round(r.implied_NS_lo), "implied_NS_hi": round(r.implied_NS_hi)}
        if x.empty:
            rows.append({**base, "constraint": "(no corridor constraint bound)"})
        for _, c in x.iterrows():
            psi = PSI.get(c["Constraint Name"])
            rows.append({**base, "constraint": c["Constraint Name"], "monitored": c["Monitored Facility"],
                         "intervals": int(c.n_binding_intervals + c.n_breached_intervals), "L_eff": c.effective_limit_mw,
                         "shadow": round(c.shadow_price_mean_usd_mwh, 1), "psi": psi,
                         "T_star": round(c.effective_limit_mw / psi) if psi else None})
O = pd.DataFrame(rows); O.to_csv(sys.argv[1], index=False)
pd.set_option("display.width", 250); print(O.to_string(index=False, max_colwidth=30))
