"""SPP-57 leg 1: the 2026 daily RTBM BC files -> the reduced OKLAHOMA sidecar (PRECOMMIT §5) and
per-constituent limit-at-bind stats for the OK<->S / Oklahoma-entry candidate set:
`oklahoma_internal` + `sps_tie` + the CSWS-only `other` rows, under spp14/groups.py's rules
(copied VERBATIM below, unchanged). Same parse as spp53/extract_2026.py; only the group filter and
the added `group` column differ."""

import csv
import glob
import re
import sys

import numpy as np
import pandas as pd

S = sys.argv[1]
OUT = sys.argv[2]
# ---- groups.py rules, verbatim -------------------------------------------------------------
KANSAS = {"WR", "SECI", "KCPL", "MPS", "KACY"}
OKLA = {"OKGE", "WFEC", "GRDA"}
OKLA_PLUS = OKLA | {"CSWS"}
WEST = {"WACM", "WAUW", "PSCO", "BHBA", "PRPA", "BEPM", "TSGT", "CRCG", "WAPA", "BLKH", "MPC"}
sl = pd.read_csv(
    "/home/user/market-simulator/data/raw/spp-planning/SL_to_Pnode_to_Zone_with_Area.csv",
    dtype=str,
    usecols=["NODE_AREA"],
)
AREAS = (
    set(sl.NODE_AREA.dropna().unique())
    | WEST
    | {"SPA", "AECI", "AMRN", "MEC", "OTP", "GRE", "NSP", "ALTW", "DPC", "MDU", "MHEB", "SOUC",
       "TVA", "EES", "CLEC", "LAFA", "EDE", "SPRM", "INDN", "SPS", "WAUE", "NPPD", "OPPD", "LES"}
)


def tokens(cf):
    if not isinstance(cf, str) or cf.strip() == "BASE":
        return frozenset()
    head = cf.split(":")[0]
    return frozenset(t for t in re.split(r"[\s/]+", head.strip()) if t in AREAS)


def group(row):
    name = row["Constraint Name"]
    mon = str(row["Monitored Facility"])
    t = row["tok"]
    if name in ("SPPSPSTIES", "SPSNMTIES"):
        return "sps_tie", "named ITP interface"
    if "OSAGE_OG - WEBBTAP4" in mon:
        return "oklahoma_internal", "named Osage-Webber Tap"
    if "RUSSETT - SBROWN" in mon:
        return "oklahoma_internal", "named Russett-S Brown"
    if "POTTER_S" in mon:
        return "sps_tie", "Potter County interchange (monitored)"
    if t & WEST:
        return "other", "west"
    if "SPS" in t and (t - {"SPS"}):
        return "sps_tie", "SPS + East-area contingency"
    if t and t <= OKLA_PLUS and (t & OKLA):
        return "oklahoma_internal", "contingency areas within OK utilities"
    if t & KANSAS:
        return "n_s_corridor", "contingency touches a Kansas-corridor area"
    if t == {"SPS"}:
        return "other", "SPS-internal"
    if not t:
        return "other", "BASE / no area token"
    return "other", "other areas: " + "+".join(sorted(t))


# ---------------------------------------------------------------------------------------------
# PRECOMMIT-spp-57 §3.2 membership for the OK<->S / Oklahoma-entry candidate set
def admitted(g, why):
    return g in ("oklahoma_internal", "sps_tie") or (g == "other" and why == "other areas: CSWS")


C14 = ["Interval", "GMTIntervalEnd", "Constraint Name", "Constraint Type", "NERCID", "TLR Level",
       "State", "Shadow Price", "Monitored Facility", "Contingent Facility", "Source Limit",
       "Real Time Effective Limit", "Initial Effective Limit", "Interconnect"]
files = sorted(glob.glob(f"{S}/daily/RTBM-DAILY-BC-*.csv"))
rows = []
n14_days = 0
for f in files:
    with open(f, newline="") as fh:
        rd = csv.reader(fh)
        next(rd)
        recs = [r for r in rd if r]
    if not any(len(r) == 14 for r in recs):
        continue
    n14_days += 1
    d = pd.DataFrame([r + [None] * (14 - len(r)) for r in recs if len(r) in (10, 14)], columns=C14)
    d = d[d["Real Time Effective Limit"].notna()]
    d = d[d.State.isin(["BINDING", "BREACHED", "ACTIVATED"])].copy()
    d["tok"] = d["Contingent Facility"].map(tokens)
    g = d.apply(group, axis=1, result_type="expand")
    d["group"] = g[0]
    d["why"] = g[1]
    d = d[[admitted(a, b) for a, b in zip(d["group"], d["why"])]]
    rows.append(d[["Constraint Name", "Monitored Facility", "Contingent Facility", "State",
                   "Shadow Price", "Source Limit", "Real Time Effective Limit",
                   "Initial Effective Limit", "Interconnect", "GMTIntervalEnd", "group"]])
print("files", len(files), "14-column days", n14_days)
D = pd.concat(rows, ignore_index=True)
for c in ("Shadow Price", "Source Limit", "Real Time Effective Limit", "Initial Effective Limit"):
    D[c] = pd.to_numeric(D[c], errors="coerce")
D["GMTIntervalEnd"] = pd.to_datetime(D["GMTIntervalEnd"], format="mixed", utc=True)
D = D.sort_values(["GMTIntervalEnd", "Constraint Name"]).reset_index(drop=True)
D.to_parquet(OUT, index=False)
print("sidecar rows", len(D), "span", D.GMTIntervalEnd.min(), D.GMTIntervalEnd.max(),
      "constraints", D["Constraint Name"].nunique(), D.State.value_counts().to_dict(),
      D.group.value_counts().to_dict())
b = D[D.State.isin(["BINDING", "BREACHED"])]
st = (
    b.groupby(["Constraint Name", "Monitored Facility", "group"])
    .agg(
        n_bind=("State", "size"),
        rtel_med=("Real Time Effective Limit", "median"),
        rtel_p10=("Real Time Effective Limit", lambda s: s.quantile(0.1)),
        rtel_p90=("Real Time Effective Limit", lambda s: s.quantile(0.9)),
        src_med=("Source Limit", "median"),
        init_med=("Initial Effective Limit", "median"),
        derate_share=("Real Time Effective Limit",
                      lambda s: float((s < b.loc[s.index, "Source Limit"] - 1e-9).mean())),
        mean_asp=("Shadow Price", lambda s: s.abs().mean()),
    )
    .reset_index()
    .sort_values("n_bind", ascending=False)
)
st.to_csv(f"{S}/bc/limits_2026_oklahoma_by_constraint.csv", index=False)
pd.set_option("display.width", 300)
print(st.head(40).to_string(index=False, max_colwidth=34))
print("derate share over binding rows:", float((b["Real Time Effective Limit"] < b["Source Limit"] - 1e-9).mean()),
      "median ratio", float((b["Real Time Effective Limit"] / b["Source Limit"]).median()))
