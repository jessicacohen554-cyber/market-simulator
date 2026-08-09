"""caiso-186 — P0-3: SIZE THE PUBLISHED SEASONAL CAPABILITY BASIS. **NO LP.**

Discharges, in one read-only pass over the **shipped path**
(``load_or_synthesize_bins`` -> ``bins_to_fleet`` -> ``generators_to_fleet_arrays``),
built twice from the incumbent keeper's OWN ``run_config.json`` and identical in every
respect except ``ScenarioConfig.cc_winter_capability_basis``:

* **P0-3 (PRECHECK §4)** — per CC plant, LP ``capacity_mw`` and effective **summer** /
  **off-summer** capability under (a) the keeper and (b) the winter-basis arm, against
  EIA-860 published summer / winter / nameplate and against CEMS seasonal p999. Both the
  ``max_t`` statistic (caiso-185's, so the two sessions are commensurable) and the seasonal
  **mean** (the anchors are mean-statistics). Plus **GW.h of capability moved and its sign,
  by season**.
* **G-NOCONTRA (PRECHECK §5)** — the arm must not push any plant's effective seasonal
  capability below its own CEMS-demonstrated seasonal output in EITHER season. A NEW
  contradiction, or the DEEPENING of an existing one, is **stop-the-line**. A pre-existing
  contradiction the arm IMPROVES is reported, not failed — it is the defect being repaired.
* **G-MONO (PRECHECK §5)** — the per-plant sign rule, checked against each plant's own
  published pair.
* **G-DENOM (PRECHECK §5)** — ``outages._iso_plant_capacity`` identical on both arms, so
  caiso-184's numerator/denominator identity is preserved bit-for-bit.
* **BRANCH C materiality (PRECHECK §9)** — < 0.1 % of CC seasonal capability moved in BOTH
  seasons is INERT.

**The CEMS record enters ONLY as a check** (PRECHECK §2 / G-CHECKONLY): every CEMS-derived
figure below lives under a ``cems_*`` key and none is written into any capacity slot or any
multiplier.

Usage::

    python scripts/probes/_caiso186_seasonal_capability.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

ISO = "CAISO"
YEARS = [2023, 2024, 2025]
CC_GROUPS = ("CC_REGULAR", "CC_CHP")
KEEPER = REPO / "results" / "calibration" / "caiso184_c1_lpbasis"
OUT = REPO / "results" / "calibration" / "_caiso186_seasonal_capability.json"
# The caiso-185 deriver's gross->net factor, so the CEMS check sits on the same
# basis both prior sessions used (derive_cc_capacity_reconcile._CC_NET_OF_GROSS).
CC_NET_OF_GROSS = 0.975
# BRANCH C (PRECHECK §9): inert if capability moves < this share in BOTH seasons.
INERT_FRAC = 0.001
# A contradiction is scored with the same 1 % tolerance caiso-185 used.
CONTRA_TOL = 0.99


def _config(arm: bool, year: int):
    """The keeper's own ScenarioConfig with one field overridden.

    Read from the keeper bundle's committed ``run_config.json`` ``scenario_config``
    block — never a remembered CLI string. ``weather_year`` is pinned to the solve
    year exactly as the backcast harness pins it, so the temperature curve is keyed
    on the same measured 8760 the solve would use.
    """
    import dataclasses

    from market_sim.config.scenarios import ScenarioConfig

    sc = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    fields = {f.name for f in dataclasses.fields(ScenarioConfig)}
    unmapped = [k for k in sc if k not in fields]
    assert not unmapped, f"run_config carries unmapped keys: {unmapped}"
    kw = {k: v for k, v in sc.items() if k in fields}
    kw["cc_winter_capability_basis"] = arm
    kw["weather_year"] = year
    return ScenarioConfig(**kw)


def _bins_and_fleet(cfg, year: int):
    """Return ``(bins, generators, fleet_arrays)`` for a config, shipped path only."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet.arrays import generators_to_fleet_arrays
    from market_sim.data.fleet.assembly import bins_to_fleet, load_or_synthesize_bins

    iso_cfg = get_iso_config(ISO)
    bins = load_or_synthesize_bins(cfg, ISO, iso_cfg, [])
    zone_names = [z.name for z in iso_cfg.zones]
    gens, _ = bins_to_fleet(bins, zone_names, cfg)
    fa = generators_to_fleet_arrays(
        gens, zone_names, hours=8760, iso=ISO, config=cfg, year=year
    )
    return bins, gens, fa


def _capability(gens, fa, summer_mask):
    """Per CC plant: effective capability MW and MWh by season, plus the raw 8760.

    ``pmax x availability`` summed over the plant's tranches; ``max`` and ``mean``
    within each season, plus the seasonal energy integral (MWh) whose delta is the
    GW.h-moved figure P0-3 reports. The hourly array is returned alongside so
    G-MONO can test the ratio's WITHIN-SEASON CONSTANCY (below).
    """
    eff = fa.pmax[:, None] * fa.availability
    acc: dict[int, np.ndarray] = {}
    for i, g in enumerate(gens):
        if g.plant_group not in CC_GROUPS:
            continue
        code = int(g.plant_code)
        acc[code] = eff[i] if code not in acc else acc[code] + eff[i]
    out: dict[int, dict[str, float]] = {}
    for code, arr in acc.items():
        s, o = arr[summer_mask], arr[~summer_mask]
        out[code] = {
            "pmax_sum_mw": float(arr.max()),
            "summer_max_mw": float(s.max()),
            "summer_mean_mw": float(s.mean()),
            "summer_mwh": float(s.sum()),
            "offsummer_max_mw": float(o.max()),
            "offsummer_mean_mw": float(o.mean()),
            "offsummer_mwh": float(o.sum()),
        }
    return out, acc


def _pure_play_cc_plants() -> set[int]:
    """The model-fleet plants where CAMPD's plant total and the CC bins are ONE object.

    **A commensurability screen for the CEMS CHECK leg only — it changes no
    mechanism, no capacity and no gate bar.** The CEMS figure is a CAMPD
    *plant* total (every unit at the site), while the model capability sums only
    the CC_REGULAR / CC_CHP bins, so at a mixed-technology site the two are not
    the same object and their ratio measures fleet composition, not capability.
    Discovered in P0 when the whole-population extension of caiso-185's 7-plant
    check produced "contradictions" the KEEPER already carries at 0.5x (plant
    10294: keeper 80.6 MW against a 157.0 MW CAMPD plant total).

    The screen is the DERIVER'S OWN, reused verbatim rather than invented here:
    ``derive_cc_capacity_reconcile._model_cc_capacity`` keeps a plant only when
    its CC_REGULAR capacity is at least ``_PURE_PLAY_CC_SHARE`` (0.90) of the
    plant's total model capacity. Non-commensurable plants are still REPORTED in
    full (``noncommensurable_rows``) — nothing is hidden, they are simply not
    scored against a total that includes machines the number does not cover.
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import load_fleet_from_csv

    gens = load_fleet_from_csv(ISO, get_iso_config(ISO), apply_cc_summer_guard=False)
    plant_cap: dict[int, float] = {}
    cc_cap: dict[int, float] = {}
    for g in gens:
        pc = int(g.plant_code)
        if pc <= 0:
            continue
        plant_cap[pc] = plant_cap.get(pc, 0.0) + float(g.pmax_mw)
        if g.plant_group == "CC_REGULAR":
            cc_cap[pc] = cc_cap.get(pc, 0.0) + float(g.pmax_mw)
    return {
        pc
        for pc, cap in cc_cap.items()
        if plant_cap.get(pc, 0.0) > 0.0 and cap / plant_cap[pc] >= 0.90
    }


def _cems_seasonal(codes: set[int], summer_by_year: dict[int, np.ndarray]):
    """Per-plant CAMPD p999 of net MW, split summer / off-summer, pooled over YEARS.

    CHECK ONLY (PRECHECK §2). Same construction as
    ``_caiso185_seasonal_stack._seasonal_peaks`` so the two sessions' figures are
    directly comparable.
    """
    from market_sim.data import campd

    states = campd.states_for_iso(ISO)
    pools: dict[int, dict[str, list[np.ndarray]]] = {}
    for year in YEARS:
        df = campd.load_campd_hourly(states, [year])
        net = campd.plant_hourly_net(df, {p: CC_NET_OF_GROSS for p in codes}, year)
        is_summer = summer_by_year[year]
        for pid, arr in net.items():
            if pid not in codes:
                continue
            a = np.asarray(arr, dtype=float)
            n = min(len(a), len(is_summer))
            rec = pools.setdefault(pid, {"summer": [], "offsummer": []})
            rec["summer"].append(a[:n][is_summer[:n]])
            rec["offsummer"].append(a[:n][~is_summer[:n]])
    out: dict[int, dict[str, float]] = {}
    for pid, rec in pools.items():
        r: dict[str, float] = {}
        for label, arrs in rec.items():
            pooled = np.concatenate(arrs) if arrs else np.array([])
            if pooled.size:
                r[f"cems_{label}_p999_mw"] = float(np.quantile(pooled, 0.999))
        if r:
            out[pid] = r
    return out


def _published() -> pd.DataFrame:
    """EIA-860 published nameplate / net-summer / winter, summed per CC plant."""
    from market_sim.config.paths import EIA_860_DIR

    df = pd.read_parquet(EIA_860_DIR / "eia860_generator_operable.parquet")
    cc = df[df["Technology"] == "Natural Gas Fired Combined Cycle"].copy()
    cc["plant_code"] = pd.to_numeric(cc["Plant Code"], errors="coerce")
    cc = cc[cc["plant_code"].notna()]
    for src, dst in (
        ("Nameplate Capacity (MW)", "nameplate_mw"),
        ("Summer Capacity (MW)", "net_summer_mw"),
        ("Winter Capacity (MW)", "winter_mw"),
    ):
        cc[dst] = pd.to_numeric(cc[src], errors="coerce")
    return cc.groupby(cc["plant_code"].astype(int))[
        ["nameplate_mw", "net_summer_mw", "winter_mw"]
    ].sum()


def _denominator_identity() -> dict:
    """G-DENOM: ``_iso_plant_capacity`` is untouched by this flag.

    The map takes no ``cc_winter_capability_basis`` argument at all — the flag
    cannot reach it — so the check is that the caiso-184 raised denominator is
    still exactly the EIA-860 NAMEPLATE the extract's ``unit_capacity_mw``
    numerator is written on.
    """
    from market_sim.data.fleet.campd_bins import cc_summer_derate_ratio
    from market_sim.data.outages import _iso_plant_capacity

    raised = _iso_plant_capacity(ISO, False, True)
    plain = _iso_plant_capacity(ISO, False, False)
    pub = _published()
    rows = []
    for (code, group), mw in sorted(raised.items()):
        if group not in CC_GROUPS or code not in pub.index:
            continue
        np_mw = float(pub.loc[code, "nameplate_mw"])
        if np_mw <= 0:
            continue
        rows.append(
            {
                "plant_code": code,
                "group": group,
                "raised_denominator_mw": round(mw, 3),
                "unraised_denominator_mw": round(plain[(code, group)], 3),
                "eia860_nameplate_mw": round(np_mw, 3),
                "raised_over_nameplate": round(mw / np_mw, 5),
            }
        )
    return {
        "flag_cannot_reach_map": True,
        "cc_bins": len(rows),
        "median_raised_over_nameplate": (
            round(float(np.median([r["raised_over_nameplate"] for r in rows])), 5)
            if rows
            else None
        ),
        "median_unraised_over_nameplate": (
            round(
                float(
                    np.median(
                        [
                            r["unraised_denominator_mw"] / r["eia860_nameplate_mw"]
                            for r in rows
                        ]
                    )
                ),
                5,
            )
            if rows
            else None
        ),
        "_unused_ratio_fn": cc_summer_derate_ratio is not None,
        "rows": rows,
    }


def main() -> None:
    """Size the arm, score the pre-solve gates, and write the record."""
    from market_sim.data.fleet.arrays import _SUMMER_MONTHS

    pub = _published()
    summer_by_year = {
        y: np.isin(
            pd.date_range(f"{y}-01-01", periods=8760, freq="h").month.to_numpy(),
            list(_SUMMER_MONTHS),
        )
        for y in YEARS
    }

    per_year: dict[str, dict] = {}
    all_codes: set[int] = set()
    keep_cap: dict[int, dict[int, dict[str, float]]] = {}
    arm_cap: dict[int, dict[int, dict[str, float]]] = {}
    bin_delta: dict[int, list[dict]] = {}
    hourly: dict[int, tuple[dict, dict]] = {}
    pure_play = _pure_play_cc_plants()

    for year in YEARS:
        off_cfg, on_cfg = _config(False, year), _config(True, year)
        bins_off, gens_off, fa_off = _bins_and_fleet(off_cfg, year)
        bins_on, gens_on, fa_on = _bins_and_fleet(on_cfg, year)
        key_cols = ["Plant_Code", "Plant_Group"]
        a = bins_off.set_index(key_cols)["capacity_mw"]
        b = bins_on.set_index(key_cols)["capacity_mw"]
        assert list(a.index) == list(b.index), "bin membership moved"
        moved = [
            {
                "plant_code": int(k[0]),
                "plant_group": str(k[1]),
                "capacity_keeper_mw": round(float(a.loc[k]), 3),
                "capacity_arm_mw": round(float(b.loc[k]), 3),
            }
            for k in a.index
            if abs(float(b.loc[k]) - float(a.loc[k])) > 1e-6
        ]
        bin_delta[year] = moved
        keep_cap[year], keep_hr = _capability(gens_off, fa_off, summer_by_year[year])
        arm_cap[year], arm_hr = _capability(gens_on, fa_on, summer_by_year[year])
        hourly[year] = (keep_hr, arm_hr)
        all_codes |= set(keep_cap[year]) | set(arm_cap[year])
        noncc = [m for m in moved if m["plant_group"] not in CC_GROUPS]
        per_year[str(year)] = {
            "cache_key_keeper": off_cfg.cache_key(),
            "cache_key_arm": on_cfg.cache_key(),
            "bins_total": int(len(a)),
            "bins_moved": len(moved),
            "noncc_bins_moved": noncc,
            "net_bin_capacity_delta_mw": round(
                sum(m["capacity_arm_mw"] - m["capacity_keeper_mw"] for m in moved), 1
            ),
        }
        for season in ("summer", "offsummer"):
            k_mwh = sum(v[f"{season}_mwh"] for v in keep_cap[year].values())
            a_mwh = sum(v[f"{season}_mwh"] for v in arm_cap[year].values())
            per_year[str(year)][f"{season}_capability_keeper_gwh"] = round(
                k_mwh / 1000.0, 1
            )
            per_year[str(year)][f"{season}_capability_arm_gwh"] = round(
                a_mwh / 1000.0, 1
            )
            per_year[str(year)][f"{season}_capability_moved_gwh"] = round(
                (a_mwh - k_mwh) / 1000.0, 1
            )
            per_year[str(year)][f"{season}_capability_moved_frac"] = (
                round((a_mwh - k_mwh) / k_mwh, 6) if k_mwh else None
            )

    cems = _cems_seasonal(all_codes, summer_by_year)

    rows: list[dict] = []
    noncomm_rows: list[dict] = []
    contra_new: list[dict] = []
    contra_deepened: list[dict] = []
    contra_improved: list[dict] = []
    mono_cap: list[dict] = []
    mono_summer: list[dict] = []
    mono_offsummer: list[dict] = []
    for code in sorted(all_codes):
        p = pub.loc[code] if code in pub.index else None
        nameplate = float(p.nameplate_mw) if p is not None else None
        net_summer = float(p.net_summer_mw) if p is not None else None
        winter = float(p.winter_mw) if p is not None else None
        basis = (
            max(min(net_summer, nameplate), winter)
            if None not in (nameplate, net_summer, winter)
            else None
        )
        rec: dict = {
            "plant_code": code,
            "eia860_nameplate_mw": None if nameplate is None else round(nameplate, 1),
            "eia860_net_summer_mw": (
                None if net_summer is None else round(net_summer, 1)
            ),
            "eia860_winter_mw": None if winter is None else round(winter, 1),
            "published_basis_B_mw": None if basis is None else round(basis, 1),
            "winter_over_nameplate": (
                None
                if not nameplate
                else round(winter / nameplate, 4)  # type: ignore[operator]
            ),
            "commensurable": bool(code in pure_play),
            **{k: round(v, 1) for k, v in cems.get(code, {}).items()},
        }
        for year in YEARS:
            k, a = keep_cap[year].get(code), arm_cap[year].get(code)
            if k is None or a is None:
                continue
            for season in ("summer", "offsummer"):
                for stat in ("max", "mean"):
                    rec[f"{season}_{stat}_keeper_{year}"] = round(
                        k[f"{season}_{stat}_mw"], 1
                    )
                    rec[f"{season}_{stat}_arm_{year}"] = round(
                        a[f"{season}_{stat}_mw"], 1
                    )
                cp = cems.get(code, {}).get(f"cems_{season}_p999_mw")
                if cp and cp > 0:
                    kk, aa = k[f"{season}_max_mw"], a[f"{season}_max_mw"]
                    rec[f"{season}_keeper_over_cems_{year}"] = round(kk / cp, 4)
                    rec[f"{season}_arm_over_cems_{year}"] = round(aa / cp, 4)
                    k_bad, a_bad = kk < cp * CONTRA_TOL, aa < cp * CONTRA_TOL
                    item = {
                        "plant_code": code,
                        "year": year,
                        "season": season,
                        "cems_p999_mw": round(cp, 1),
                        "keeper_max_mw": round(kk, 1),
                        "arm_max_mw": round(aa, 1),
                    }
                    # Scored ONLY where the CAMPD plant total and the model's CC
                    # bins are the same object (see _pure_play_cc_plants); the
                    # rest are reported in full but not scored against a total
                    # that includes machines the model number does not cover.
                    if code not in pure_play:
                        pass
                    elif a_bad and not k_bad:
                        contra_new.append(item)
                    elif a_bad and k_bad and aa < kk - 1e-6:
                        contra_deepened.append(item)
                    elif k_bad and aa > kk + 1e-6:
                        contra_improved.append(item)
            # G-MONO, three exact legs (PRECHECK §5). The flag changes only the
            # pmax basis and the per-season rating multipliers, both of which are
            # CONSTANT within a season, so capability_arm(t) / capability_keeper(t)
            # must be constant within each season up to the two declared clips.
            k_hr, a_hr = hourly[year]
            kv, av = k_hr.get(code), a_hr.get(code)
            if kv is None or av is None or basis is None or not nameplate:
                rows_ok = False
            else:
                rows_ok = True
            if rows_ok:
                sm = summer_by_year[year]
                for season, mask in (("summer", sm), ("offsummer", ~sm)):
                    good = kv[mask] > 1e-9
                    if not good.any():
                        continue
                    ratio = av[mask][good] / kv[mask][good]
                    lo, hi = float(ratio.min()), float(ratio.max())
                    rec[f"{season}_ratio_lo_{year}"] = round(lo, 5)
                    rec[f"{season}_ratio_hi_{year}"] = round(hi, 5)
                    # G-MONO-B: the SUMMER MEAN is invariant by construction —
                    # B x (ns/B) == nameplate x (ns/nameplate) — so the anchored
                    # statistic must not move. The per-hour PEAK does move, in
                    # both directions, because availability is clipped at 1 so
                    # the peak is bounded by pmax: that is the declared H-SUMMER
                    # consequence (PRECHECK §3a) and is reported, not gated. A
                    # summer MEAN that moves is stop-the-line.
                    if season == "summer":
                        mr = float(av[mask].mean() / kv[mask].mean())
                        rec[f"summer_mean_ratio_{year}"] = round(mr, 5)
                        if abs(mr - 1.0) > 2e-3:
                            mono_summer.append(
                                {
                                    "plant_code": code,
                                    "year": year,
                                    "summer_mean_ratio": round(mr, 5),
                                    "peak_ratio_hi": round(hi, 5),
                                }
                            )
                    # G-MONO-C: off-summer ratio constant within the season, i.e.
                    # a single rating swap, not an hour-shaped adjustment. The
                    # declared H-CLIP is the only admissible spread.
                    if season == "offsummer" and (hi - lo) > 1e-4:
                        mono_offsummer.append(
                            {
                                "plant_code": code,
                                "year": year,
                                "ratio_lo": round(lo, 5),
                                "ratio_hi": round(hi, 5),
                            }
                        )
        # G-MONO-A: the capacity sign rule, exact and availability-free. The
        # keeper divides the fleet's summed net-summer capacity by min(1, ns/np)
        # and the arm by ns_clamped/B, so whatever the fleet-vs-EIA membership
        # the ratio is exactly B / nameplate — machine precision, and its
        # direction is fixed by the plant's own published pair.
        if basis and nameplate:
            for m in bin_delta[YEARS[0]]:
                if m["plant_code"] != code:
                    continue
                got = m["capacity_arm_mw"] / m["capacity_keeper_mw"]
                want = basis / nameplate
                rec["capacity_ratio_arm_over_keeper"] = round(got, 5)
                rec["capacity_ratio_predicted"] = round(want, 5)
                if abs(got - want) > 1e-4:
                    mono_cap.append(
                        {
                            "plant_code": code,
                            "group": m["plant_group"],
                            "got": round(got, 5),
                            "predicted": round(want, 5),
                        }
                    )
        (rows if code in pure_play else noncomm_rows).append(rec)

    materiality = max(
        abs(per_year[str(y)][f"{s}_capability_moved_frac"] or 0.0)
        for y in YEARS
        for s in ("summer", "offsummer")
    )
    out = {
        "iso": ISO,
        "years": YEARS,
        "keeper": KEEPER.name,
        "summer_months": sorted(_SUMMER_MONTHS),
        "cc_net_of_gross_check_only": CC_NET_OF_GROSS,
        "per_year": per_year,
        "bin_capacity_delta": {str(y): bin_delta[y] for y in YEARS},
        "g_nocontra_new": contra_new,
        "g_nocontra_deepened": contra_deepened,
        "g_nocontra_improved": contra_improved,
        "g_nocontra_pass": not contra_new and not contra_deepened,
        "g_nocontra_scored_plants": sorted(pure_play & all_codes),
        "g_nocontra_unscored_plants": sorted(all_codes - pure_play),
        "g_mono_capacity_violations": mono_cap,
        "g_mono_summer_violations": mono_summer,
        "g_mono_offsummer_spread": mono_offsummer,
        "g_mono_pass": not mono_cap and not mono_summer,
        "g_denom": _denominator_identity(),
        "max_abs_capability_moved_frac": round(materiality, 6),
        "branch_c_inert": bool(materiality < INERT_FRAC),
        "rows": rows,
        "noncommensurable_rows": noncomm_rows,
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(
        json.dumps(
            {
                k: v
                for k, v in out.items()
                if k not in ("rows", "noncommensurable_rows", "bin_capacity_delta")
            },
            indent=1,
        )[:6000]
    )
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
