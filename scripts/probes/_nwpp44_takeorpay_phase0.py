"""nwpp-44 phase 0 (ZERO LP): the exact offer delta of the measured take-or-pay arm.

Rebuilds NWPP's designated keeper (``nwpp42_coalhr_span``) on its OWN recipe via
the sanctioned ``replay_keeper.run_year_kwargs`` + ``derived_run_year_inputs``
path (``run_year(..., fleet_only=True)``, whose ``mc_base`` is the assembled P0
objective the LP is actually handed), once as the CONTROL and once with the two
NWPP-44 gates armed:

* ``coal_takeorpay_from_data`` — each plant's MEASURED EIA-923 Schedule-5
  contracted share (``coal_takeorpay_NWPP.csv``, derived by nwpp-43 from the
  committed ``data/raw/coal-receipts/`` corpus), in place of the uniform assumed
  100%-sunk first tranche;
* ``coal_committed_takeorpay_regulated`` — the committed-band limb, scoped by
  the plant's published EIA-860 ``Regulatory Status`` (``RE``).

Owner ruling 2026-09-20 (PRECOMMIT-nwpp-43 §7) took **Option B, all regulated
coal**, so ``coal_prb_committed_dispatchable`` is NOT armed and no rank carve-out
is applied. This probe ASSERTS that, so a later drift cannot silently re-scope
the arm.

What it answers before any LP is spent (rule 29 ``[R-SCREEN]`` clause 0, which
survives as practice):

* which LP rows move, and by how much — the per-(class, band) offer delta;
* that the move is CONFINED to coal (non-coal rows moved must be 0);
* that the arm is TWO-SIDED — the spot-heavy plants' ``_mustrun`` band gets
  DEARER while the contracted regulated ``_committed`` band gets cheaper, which
  is what distinguishes a measured contract share from a subsidy;
* that ``pmax`` is conserved (an offer re-pricing must never move capacity).

Run: ``python3 scripts/probes/_nwpp44_takeorpay_phase0.py [<year> ...]``
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

BUNDLE = Path("results/calibration/nwpp42_coalhr_span")
ISO = "NWPP"

#: The two gates this lane arms, and the one it deliberately does NOT.
ARMED = ("coal_takeorpay_from_data", "coal_committed_takeorpay_regulated")
REFUSED = ("coal_prb_committed_dispatchable",)


def build(year: int, arm: bool):
    """Rebuild the keeper fleet for ``year``; ``arm`` selects the NWPP-44 gates.

    The CONTROL leg forces the two armed fields back OFF at the point the
    ScenarioConfig is constructed, so both legs run the SAME code at the SAME
    SHA and the only difference is the two booleans (rule 29(b) form 4: the
    keeper's committed bundle is the control, and this is its offer-side image).
    """
    import scripts.run_calibration as RC
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(BUNDLE, year))

    real = RC.backcast_config

    def patched(*a, **k):
        cfg = real(*a, **k)
        if not arm:
            cfg = cfg.with_overrides(**{f: False for f in ARMED})
        return cfg

    RC.backcast_config = patched
    try:
        return RC.run_year(
            year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
        )
    finally:
        RC.backcast_config = real


def _band(unit_id: str) -> str:
    suffix = str(unit_id).rpartition("_")[2]
    known = ("mustrun", "sync", "committed", "econlo", "econhi", "econ", "peak")
    return suffix if suffix in known or suffix.startswith("econc") else "<none>"


def _klass(g) -> str:
    """The SCORED class key (COAL_BIT / COAL_PRB / ...), not the raw fuel type.

    The kill condition (PRECOMMIT-nwpp-43 §6) is denominated in **COAL_BIT**
    TWh, so the delta has to be reported in that currency or it cannot be
    checked against it. Coal rows resolve through the same
    ``COAL_SUPPLY_TO_CLASS`` map the offer curve and the C1 scorer use.
    """
    from market_sim.config.plant_taxonomy import COAL_SUPPLY_TO_CLASS

    if str(g.fuel_type).lower() == "coal":
        supply = str(getattr(g, "coal_supply", "") or "").lower()
        return COAL_SUPPLY_TO_CLASS.get(supply, f"COAL_?({supply or 'untagged'})")
    return str(getattr(g, "plant_group", "") or g.fuel_type)


def _rows(out):
    """One (key, pmax, mc) row per LP generator, keyed by unit id."""
    fleet = out["fleet"]
    mc = np.asarray(out["mc_base"], dtype=float)
    # mc_base is (n_gen,) or (n_gen, T); an offer delta is a per-unit scalar, so
    # collapse the hour axis by its mean (every coal row here is hour-flat, and
    # a non-flat row would show up as a changed mean either way).
    if mc.ndim == 2:
        mc = mc.mean(axis=1)
    return {
        str(g.unit_id): (_klass(g), _band(g.unit_id), float(g.pmax_mw), float(mc[i]))
        for i, g in enumerate(fleet)
    }


def main() -> None:
    years = [int(a) for a in sys.argv[1:]] or [2023, 2024, 2025]
    for year in years:
        print(f"\n{'=' * 78}\nYEAR {year}\n{'=' * 78}")

        arm_out = build(year, arm=True)
        cfg = arm_out["config"]
        for f in ARMED:
            assert getattr(cfg, f) is True, f"{f} did not arm"
        for f in REFUSED:
            assert getattr(cfg, f) is False, f"{f} must NOT be armed (owner Option B)"
        print(f"  gates: {', '.join(ARMED)} = True; {REFUSED[0]} = False (Option B)")

        ctl = _rows(build(year, arm=False))
        arm = _rows(arm_out)
        assert set(ctl) == set(arm), "the arm changed the LP row set; it must not"

        agg: dict[tuple, list] = defaultdict(list)
        noncoal = 0
        dmw = 0.0
        for uid, (klass, band, mw, mc_c) in ctl.items():
            _, _, mw_a, mc_a = arm[uid]
            dmw += abs(mw_a - mw)
            if abs(mc_a - mc_c) < 1e-9:
                continue
            if "COAL" not in klass.upper():
                noncoal += 1
            agg[(klass, band)].append((mw, mc_c, mc_a))

        print(f"  rows moved: {sum(len(v) for v in agg.values())} of {len(ctl)}")
        print(f"  NON-COAL rows moved: {noncoal}")
        print(f"  total |delta pmax|: {dmw:.6f} MW")
        print(
            f"\n  {'class · band':<34}{'n':>4}{'MW':>11}{'ctl $/MWh':>12}{'arm $/MWh':>12}"
        )
        moved_mw = 0.0
        for (klass, band), rows in sorted(agg.items()):
            mw = sum(r[0] for r in rows)
            moved_mw += mw
            wc = sum(r[0] * r[1] for r in rows) / mw if mw else 0.0
            wa = sum(r[0] * r[2] for r in rows) / mw if mw else 0.0
            print(
                f"  {klass + ' ' + band:<34}{len(rows):>4}{mw:>11,.1f}{wc:>12.2f}{wa:>12.2f}"
            )
        print(f"  {'MOVED CAPACITY':<34}{'':>4}{moved_mw:>11,.1f}")


if __name__ == "__main__":
    main()
