"""ercot-223 Phase-0: diagnose the promoted keeper's manufactured 2024 h3066 shed.

Read-only, NO LP (dispatch fence): every number below is computed from the
COMMITTED ercot-221 A/B bundles (`results/calibration/ercot221_control_A`,
`ercot221_adaptive_B` — the CURRENT keeper) plus the committed measured
inputs the keeper's own storage overlays read (`data/raw/ercot-AS/*`,
`data/raw/ercot-storage-capability.csv`). Rule 22 data-not-score: only
2023–2025 artifacts are touched.

The question (dispatch card): WHY does 2024 hour 3066 (May-8-2024, the
h17–20 floor window; actual RT $2,451) shed 17.9 MW under the armed
adaptive-expectation floor and not under the control, when the floor there
($523.12) is far below VOLL ($5,000)?

Candidate mechanisms discriminated:
  (a) SOC-path re-timing (storage arrives empty),
  (b) the measured AS carve-out (award dock / SOC-backing freeze /
      deployment floor hold the fleet's HASL),
  (c) a co-opt interaction (the floor re-prices the reserve stack).

VERDICT (see FINDING-ercot223): (c) in a precise form, transmitted through
(a); (b) is stage-setting but identical across the two runs and therefore
not the discriminator. The reserve co-optimization counts storage upward
headroom (cap − Dis + Chg) as reserve supply in the shared headroom rows
(`model/lp/reserve_rows.py`, pooled spec — the duration gate is off in the
keeper config). Because the adaptive floor enters the LP as a discharge
COST, it debases the model's PRIVATE value of stored energy (the SOC shadow
mu) one-for-one, while the reserve-side headroom value sigma carries no
floor. The keeper's evening equilibrium mu = eta*(lambda − floor − sigma)
collapses from ~$576/MWh (control) to ~$184/MWh (arm), which (i) fails the
control's h3065 pre-peak top-up charge economics (+$79 -> −$225/MWh), (ii)
swaps 195 MW of storage energy into reserve-counted headroom at h3066
(Delta NonSpin held = +17.89 = the shed, exactly), and (iii) leaves the
thermal backfill one CT_PEAKER short: +177.3 MW is all the stack has, so
the residual 17.887 MW is served by slack at VOLL. Both runs exit h3067
with fleet SOC pinned at the measured AS-backing freeze (~3,091.5 MWh) —
the "arrives empty" form of (a) is FALSE; the deficit is the forgone
top-up plus a ~46 MWh entering gap, ~207 MWh across the two VOLL hours.

Emits `results/calibration/ercot223_shed_phase0.json` with every identity
and its closure error. Constants cited from the committed run_config
(rule 5): eta = sqrt(storage_rte_4hr = 0.85), battery_dispatch_adder = 10,
ordc_voll = voll = 5000, ERCOT_ADAPTIVE_WINDOW_HOURS = (17,18,19,20),
ERCOT_ADAPTIVE_EVENT_USD = 1000 (results/scarcity.py).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CTL = REPO / "results/calibration/ercot221_control_A/hourly"
ARM = REPO / "results/calibration/ercot221_adaptive_B/hourly"
OUT = REPO / "results/calibration/ercot223_shed_phase0.json"

ETA = float(np.sqrt(0.85))  # storage_rte_4hr split symmetrically (model basis)
VOM = 10.0  # battery_dispatch_adder (run_config.scenario_config)
VOLL = 5000.0  # ordc_voll == voll (run_config.scenario_config)
EVENT_USD = 1000.0  # results/scarcity.ERCOT_ADAPTIVE_EVENT_USD (frozen)
H = {"h3064": 3064, "h3065": 3065, "h3066": 3066, "h3067": 3067,
     "h3068": 3068, "h3069": 3069}


def _shed_rows(d: Path, year: int) -> list[dict]:
    sy = pd.read_parquet(d / f"system_{year}.parquet")
    s = sy[sy["slack"] > 1e-6]
    return [
        {"hour": int(r.hour), "zone": str(r.zone), "slack_mw": float(r.slack),
         "price": float(r.price)}
        for r in s.itertuples()
    ]


def _wavg_price_model(d: Path, year: int) -> np.ndarray:
    """Demand-weighted model-side settle proxy: price − measured RTORDPA."""
    sy = pd.read_parquet(d / f"system_{year}.parquet")
    sy = sy.assign(pm=sy.price - sy.rtordpa_overlay)
    g = sy.groupby("hour").apply(
        lambda x: np.average(x.pm, weights=np.maximum(x.demand, 1e-9))
    )
    return g.reindex(range(8760)).to_numpy(dtype=float)


def main() -> None:
    out: dict = {"session": "ercot-223", "phase": "0 (read-only, no LP)"}

    # --- 1. shed localization ------------------------------------------------
    out["shed_2024"] = {"control": _shed_rows(CTL, 2024),
                        "arm": _shed_rows(ARM, 2024)}
    arm_only = {r["hour"] for r in out["shed_2024"]["arm"]} - {
        r["hour"] for r in out["shed_2024"]["control"]}
    assert arm_only == {3066}, arm_only

    # --- 2. window ledger ----------------------------------------------------
    stC = pd.read_parquet(CTL / "storage_2024.parquet").sort_values("hour")
    stA = pd.read_parquet(ARM / "storage_2024.parquet").sort_values("hour")
    ad = pd.read_parquet(ARM / "adaptive_2024.parquet").sort_values("hour")
    ledger = {}
    for name, h in H.items():
        ledger[name] = {
            "floor_usd": round(float(ad.floor_usd.iloc[h]), 3),
            "ctl_chg": round(float(stC.charge_mw.iloc[h]), 3),
            "ctl_dis": round(float(stC.discharge_mw.iloc[h]), 3),
            "arm_chg": round(float(stA.charge_mw.iloc[h]), 3),
            "arm_dis": round(float(stA.discharge_mw.iloc[h]), 3),
        }
    out["window_ledger"] = ledger
    out["window_deficit_mwh_3066_67"] = round(
        float(stC.discharge_mw.iloc[3066] + stC.discharge_mw.iloc[3067]
              - stA.discharge_mw.iloc[3066] - stA.discharge_mw.iloc[3067]), 3)

    # --- 3. class backfill + the NonSpin identity at 3066 --------------------
    cC = pd.read_parquet(CTL / "class_hourly_2024.parquet")
    cA = pd.read_parquet(ARM / "class_hourly_2024.parquet")
    a = cC[cC.hour == 3066].set_index("klass")["mw"]
    b = cA[cA.hour == 3066].set_index("klass")["mw"]
    delta = (b - a).astype(float)
    out["class_backfill_3066"] = {
        k: round(float(v), 3) for k, v in delta.items() if abs(v) > 0.01}
    rfC = pd.read_parquet(CTL / "reserve_family_2024.parquet")
    rfA = pd.read_parquet(ARM / "reserve_family_2024.parquet")
    nsC = rfC[(rfC.hour == 3066) & (rfC.family == "NonSpin")].held_mw.iloc[0]
    nsA = rfA[(rfA.hour == 3066) & (rfA.family == "NonSpin")].held_mw.iloc[0]
    shed = out["shed_2024"]["arm"][
        [r["hour"] for r in out["shed_2024"]["arm"]].index(3066)]["slack_mw"]
    d_dis = float(stA.discharge_mw.iloc[3066] - stC.discharge_mw.iloc[3066])
    d_ct = float(delta.get("CT_PEAKER", 0.0))
    out["nonspin_identity_3066"] = {
        "delta_nonspin_held_mw": round(float(nsA - nsC), 4),
        "shed_mw": round(shed, 4),
        "delta_storage_dis_mw": round(d_dis, 3),
        "delta_ct_peaker_mw": round(d_ct, 3),
        "identity |dNS - shed|": round(abs(float(nsA - nsC) - shed), 4),
        "identity |dStorHeadroom + dThermalHeadroom - dNS|": round(
            abs((-d_dis) + (-d_ct) - float(nsA - nsC)), 4),
    }

    # --- 4. AS-backing freeze arithmetic (measured inputs, both runs share) --
    tot = pd.read_parquet(REPO / "data/raw/ercot-AS/ercot_2024_as_by_restype_hourly.parquet")
    prod = pd.read_parquet(REPO / "data/raw/ercot-AS/ercot_2024_storage_as_products_hourly.parquet")
    award = tot["storage"].to_numpy(float)
    per = np.stack([prod[n].to_numpy(float)
                    for n in ["regup", "rrs", "ecrs", "nonspin"]])
    tt = per.sum(axis=0)
    share = np.where(tt > 0, per / tt, 0.0)
    freeze_raw = (share * np.array([1.0, 1.0, 2.0, 4.0])[:, None]).sum(axis=0) * award
    day = np.arange(8760) // 24
    cummax = pd.DataFrame({"a": award, "d": day}).groupby("d")["a"].cummax().to_numpy()
    drawdown = np.maximum(cummax - award, 0.0)
    # deployment gate on day 127 inferred from the runs themselves: the forced
    # values 34.5/169.6/137.7/9.1/261.3 appear verbatim in BOTH runs' discharge
    dep_hours = [3059, 3061, 3062, 3064, 3065, 3066, 3067]
    cum_dep = float(drawdown[dep_hours].sum())
    fz67 = float(freeze_raw[3067]) - cum_dep
    fz68 = float(freeze_raw[3068]) - cum_dep
    fz69 = float(freeze_raw[3069]) - cum_dep
    ctl69 = float(stC.discharge_mw.iloc[3069])
    ctl68 = float(stC.discharge_mw.iloc[3068])
    arm69 = float(stA.discharge_mw.iloc[3069])
    out["freeze_arithmetic"] = {
        "deploy_floor_h3065_forced_mw": round(float(drawdown[3065]), 3),
        "both_runs_dis_h3065": [round(float(stC.discharge_mw.iloc[3065]), 3),
                                round(float(stA.discharge_mw.iloc[3065]), 3)],
        "freeze_net_mwh": {"h3067": round(fz67, 1), "h3068": round(fz68, 1),
                           "h3069": round(fz69, 1)},
        "ctl_dis_3068 vs eta*(SOCexit67-fz68), SOCexit67=fz67": [
            round(ctl68, 2), round(ETA * (fz67 - fz68), 2)],
        "ctl_dis_3069 vs eta*(fz68-fz69)": [round(ctl69, 2),
                                            round(ETA * (fz68 - fz69), 2)],
        "arm_dis_3069 vs eta*(fz67-fz69)": [round(arm69, 2),
                                            round(ETA * (fz67 - fz69), 2)],
        "note": "both runs exit h3067 with fleet SOC pinned at the freeze; "
                "the post-window discharges are exactly the eta-scaled freeze "
                "releases, re-timed by the floor (938 MWh h3068->h3069).",
    }

    # --- 5. marginal identities (duals from committed sidecars) --------------
    def lam(d: Path, h: int) -> float:
        sy = pd.read_parquet(d / "system_2024.parquet")
        r = sy[(sy.hour == h) & (sy.zone == "Houston")].iloc[0]
        return float(r.price - r.ordc_adder - r.rtordpa_overlay)

    def sigma(rf: pd.DataFrame, h: int) -> float:
        ns = float(rf[(rf.hour == h) & (rf.family == "NonSpin")].dual.iloc[0])
        oc = float(rf[(rf.hour == h) & (rf.family == "ercot_ordc_total")].dual.iloc[0])
        return ns + oc

    fl66 = float(ad.floor_usd.iloc[3066])
    mu_ctl = ETA * (lam(CTL, 3066) - VOM - sigma(rfC, 3066))
    mu_arm = ETA * (lam(ARM, 3066) - fl66 - sigma(rfA, 3066))
    out["marginal_identities"] = {
        "sigma_3066": {"ctl": round(sigma(rfC, 3066), 2),
                       "arm": round(sigma(rfA, 3066), 2)},
        "mu_soc_shadow_3066": {"ctl": round(mu_ctl, 1), "arm": round(mu_arm, 1)},
        "h3065_topup_margin (sigma + mu*eta - lambda)": {
            "ctl": round(sigma(rfC, 3065) + mu_ctl * ETA - lam(CTL, 3065), 1),
            "arm": round(sigma(rfA, 3065) + mu_arm * ETA - lam(ARM, 3065), 1)},
        "h3068_energy_vs_reserve": {
            "ctl_margin (lam - vom)": round(lam(CTL, 3068) - VOM, 1),
            "arm_margin (lam - floor)": round(
                lam(ARM, 3068) - float(ad.floor_usd.iloc[3068]), 1),
            "sigma_3068": round(sigma(rfA, 3068), 1),
            "flip": "ctl margin > sigma (discharge); arm margin < sigma "
                    "(hold as reserve-counted headroom, dump at h3069)"},
    }

    # --- 6. event-realized-release breadth (Phase-1 pre-measurement) ---------
    breadth = {}
    for yr in (2023, 2024):
        ady = pd.read_parquet(ARM / f"adaptive_{yr}.parquet")
        settle = _wavg_price_model(CTL, yr)
        floored = (ady.floor_usd.to_numpy() > VOM)
        ev = settle >= EVENT_USD
        breadth[yr] = {
            "floored_window_hours": int(floored.sum()),
            "would_be_exempt": int((floored & ev).sum()),
            "kill_window_exempt": [int(h) for h in (3065, 3066, 3067)
                                   if yr == 2024 and settle[h] >= EVENT_USD],
        }
    out["event_release_breadth"] = breadth

    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
