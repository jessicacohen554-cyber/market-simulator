"""Generic (non-ISO-tuned) base thermal offer-curve bands.

The else-branch values of the former per-band ``if iso == ...`` ternaries in
``backcast_config`` (refactor-consolidation plan §5: per-ISO tuned ternaries
→ per-ISO constant modules selected by dict; rules 23/25 — values
transplanted byte-for-byte, per-ISO fitted values NEVER merged into these
generic defaults). Operator-supplied band multipliers on AHR × fuel_price;
VOM constant across bands. The economic block is a rising ramp from
econ_low to econ_high; the duct-firing peak is a separate band above it.

Every tuned-value provenance comment moved with its value — see the per-ISO
delta modules (``ercot.py``, ``pjm.py``) for the ISO-fitted branches.
"""

from __future__ import annotations

GENERIC_BASE_OFFER_CURVE: dict[str, dict[str, float]] = {
    # CC offer curve fit to Colorado Bend II / Wolf Hollow II observed
    # CAMPD heat-rate curves: marginal HR ~0.95x avg and flat across
    # the operating range, negligible duct-firing. committed/econ are a
    # flat cheap band; peak 2.25 = F-class duct-burner mult (tweakable);
    # pct_peaking 8% = observed duct-fire headroom. committed % per-plant
    # grounded (cc_committed_per_plant).
    # Generic CC_REGULAR min-stable-load committed band. NEISO's
    # ISO-specific committed lift (1.27, anchored to its measured
    # CAMPD CC heat-rate shape — min-load ~1.30x the fleet-average HR,
    # removing the artificially-cheap min-load block the removed
    # net-summer CC "wall" was masking) lives in _NEISO_OFFER_CURVE
    # and is deep-merged on top downstream, so this stays the generic 0.92.
    "CC_REGULAR": {
        "committed": 0.92,
        "econ_low": 1.06,
        "econ_high": 1.27,
        "peak": 2.25,
        "econ_low_share": 0.50,
        "pct_peaking": 8.0,
    },
    # Flatter curve for the measured baseload-duty MISO CC cohort
    # (fleet.cc_intermediate_plants, median CF >= threshold), routed here
    # only when cc_intermediate_split is set (--cc-intermediate-split;
    # default OFF, so every prior keeper / other ISO is byte-identical and
    # the CC_REGULAR curve above is untouched). MISO's entire CC fleet runs
    # intermediate/baseload (median CF 50-150%, mean ~90%), but the
    # CC_REGULAR curve was fit to ERCOT's duct-fire-heavy 2x1 peaker CCs:
    # its rising start-cost-amortized econ ramp (econ_high 1.27) over-prices
    # the upper operating range of an already-committed baseload CC, whose
    # incremental energy is near its flat full-load heat rate (~0.93x its
    # own average, the documented CC measured shape), so the upper econ
    # tranches sit above the clearing price and the model under-runs the CC
    # fleet (the 2023/2024 gas-CC under-run, -24 to -28 TWh vs EIA-923).
    # This flattens the econ ramp to that measured near-baseload
    # incremental cost (econ 0.95->1.08, straddling the full-load 0.93x and
    # average 1.0x) while KEEPING the physically-real F-class duct-burner
    # peak (2.25) — only the operating-range ramp is corrected, never the
    # duct-fire peak (which would be an unphysical fit to volume; rule #11).
    # The committed band stays 0.92 (the cheap min-stable-load base) and
    # the peaking band stays per-plant via cc_peaking_per_plant. Mirrors
    # ST_GAS_INTERMEDIATE / CT_INTERMEDIATE.
    "CC_INTERMEDIATE": {
        "committed": 0.92,
        "econ_low": 0.95,
        "econ_high": 1.08,
        "peak": 2.25,
        "econ_low_share": 0.50,
        "pct_peaking": 8.0,
    },
    "CC_CHP": {
        "committed": 0.92,
        "econ_low": 0.96,
        "econ_high": 1.12,
        "peak": 2.25,
        "econ_low_share": 0.50,
        "pct_peaking": 8.0,
    },
    # CT_CHP cogens: previously driven by the legacy ct_*_hr_override
    # triple (committed 1.10 / econ 1.20 / peak 1.40). Expressed as an
    # offer curve so the econ ramp and peak are tweakable like every
    # other group. econ_low == econ_high keeps the default a flat 1.20
    # economic block (no dispatch change vs the old single econ value);
    # pull them apart to create a slope. Peaking % stays the CSV value
    # (no pct_peaking key).
    # NOTE (CAISO CT_CHP — EOR cogen over-dispatch, FIXED at the fleet
    # heat-rate layer, not here): the CAISO CT_CHP fleet's three big
    # Kern-County enhanced-oil-recovery cogens (Kern River 10496,
    # Sycamore 50134, Midway Sunset 52169) report a steam-credited
    # (artificially efficient ~5-6 MMBtu/MWh) EIA-923 heat rate, so this
    # offer curve's 1.10 committed multiplier priced them as cheap
    # baseload and the LP ran the three flat at ~88% CF (3.7 TWh in 2024)
    # vs ~0.8 measured. The fix is the POWER-ONLY heat-rate correction in
    # chp._correct_chp_steam_credit_hr, which lifts those three units to
    # the simple-cycle band (~9-11) so they clear on price like peakers —
    # CT_CHP 6.95 -> 3.54 TWh (2024), FAIL -> PASS. It is grounded in
    # topping-cycle physics (steam-credit ratio), NOT this
    # residual-tunable offer curve, so the offer curve stays the validated
    # compact-cogen 1.10/1.20/1.40 for the rest of CT_CHP. (The freed
    # energy backfills onto CC_REGULAR via the evening-ramp import-under /
    # domestic-gas-over root cause, the open C1/C3 item — see
    # docs/caiso-eor-power-hr-2026-06.md.)
    "CT_CHP": {
        "committed": 1.10,
        "econ_low": 1.20,
        "econ_high": 1.20,
        "peak": 1.40,
        "econ_low_share": 0.50,
    },
    # CT/ST committed band raised as a P1 startup-cost proxy: the
    # part-load committed slice only clears when price is high, so
    # peakers stop parking at ~20% CF for hundreds of hours. CT hurdle
    # is committed 1.55 (peak HR mult 13.15); ST hurdle committed 0.81
    # with a slightly lower econ-high / peak top. The CT committed
    # hurdle / econ-low / peak are an ERCOT calibration tune (ercot.py);
    # PJM keeps its own validated CT curve (pjm.py).
    "CT_PEAKER": {
        "committed": 1.55,
        "econ_low": 1.27,
        "econ_high": 1.98,
        "peak": 13.15,
        "econ_low_share": 0.526,
        "pct_peaking": 7.0,
    },
    # Intermediate-duty simple-cycle CTs (MISO). EIA-860 confirms these
    # are genuine GT/IC units, not mislabeled CCs — but their measured
    # CAMPD median CF (>= ct_intermediate_cf_threshold) shows they run
    # intermediate/near-baseload, not as true peakers. Routed here only
    # when config.ct_intermediate_split is set (fleet._offer_curve_for_group
    # + fleet.ct_intermediate_plants); the rest of CT_PEAKER keeps the
    # steep true-peaker curve above. The committed-band start-cost hurdle
    # (CT_PEAKER 1.55) is dropped — an always-running unit amortizes its
    # one start over thousands of hours, so its committed energy is priced
    # at its own delivered marginal cost (base_HR x ~1.0-1.2) with a thin
    # rising ramp, overlapping the CC fleet so it clears at intermediate
    # load. A modest scarcity peak (3.0) is kept above the ramp. Inert for
    # every ISO/run with the split off (keepers unchanged).
    "CT_INTERMEDIATE": {
        "committed": 1.00,
        "econ_low": 1.00,
        "econ_high": 1.20,
        "peak": 3.00,
        "econ_low_share": 0.50,
        "pct_peaking": 5.0,
    },
    "ST_GAS": {
        "committed": 0.81,
        "econ_low": 1.05,
        "econ_high": 1.40,
        "peak": 4.20,
        "econ_low_share": 0.500,
        "pct_peaking": 15.0,
    },
    # Flatter curve for the measured intermediate-duty MISO steam cohort
    # (fleet.st_gas_intermediate_plants, median CF >= threshold), routed
    # here only when st_gas_intermediate_split is set (--st-gas-intermediate;
    # default OFF, so every prior keeper / other ISO is byte-identical and
    # the base ST_GAS curve above is untouched). These near-baseload
    # boilers (Harding Street, Ames, Nine Mile Pt, Lewis Creek, Sabine)
    # carry almost no peaking band — their energy is sustained, not
    # scarcity — so the steep peaker-shaped ST_GAS curve mis-prices them
    # above merit and the model under-runs them. Mirrors CT_INTERMEDIATE,
    # including its committed-band pricing rule: an always-running unit
    # amortizes its start over thousands of hours, so its committed
    # energy is priced at its own delivered marginal cost — the
    # cost-based-offer SRMC floor (base_HR x delivered gas + VOM; MISO
    # Tariff Module C / Attachment L, sanity-checked against the MISO
    # IMM / Potomac Economics SOM report). committed re-grounded
    # 0.85 -> 1.00 (2026-07-08, G-21/#1302 follow-on,
    # docs/miso-caiso-srmc-floor-audit-2026-07.md §2): the old 0.85 was
    # an uncited generic default pricing a non-CHP, non-take-or-pay gas
    # tranche below its own average-heat-rate fuel cost — the pjm-83
    # defect pattern. A steam boiler's part-load heat rate is
    # monotonically WORSE than its average, so 1.0x base_HR is a true
    # floor (no CC flat-plateau exception applies).
    "ST_GAS_INTERMEDIATE": {
        "committed": 1.00,
        "econ_low": 1.00,
        "econ_high": 1.15,
        "peak": 2.20,
        "econ_low_share": 0.500,
        "pct_peaking": 6.0,
    },
    # Coal split by supply: lignite (mine-mouth) raised +0.05 across the
    # board; PRB uses a pure offer curve (sigmoid off) -- higher commit,
    # lower econ-low start, slightly higher econ-high.
    # NOTE: MISO no longer inherits these COAL_* entries — its
    # SOM-grounded near-cost coal bands deep-merge on top downstream
    # (_MISO_OFFER_CURVE, 2026-07-10).
    "COAL_LIGNITE": {
        "committed": 0.95,
        "econ_low": 1.14,
        "econ_high": 1.15,
        "peak": 1.55,
        "econ_low_share": 0.556,
    },
    # PRB committed-band tuning is applied per-run as an offer-curve
    # delta (e.g. Run-60 -0.05, Run-61 -0.20), not baked in here, so the
    # baseline stays at run57 and every run's tweak is delta-from-run57.
    # ERCOT's fitted econ bands live in ercot.py.
    "COAL_PRB": {
        "committed": 0.95,
        "econ_low": 0.77,
        "econ_high": 1.19,
        "peak": 1.48,
        "econ_low_share": 0.556,
    },
    # Non-ERCOT coal by EIA-923 fuel rank (scripts/data/derive_coal_supply.py;
    # routes via fleet._COAL_SUPPLY_TO_CURVE). PJM 2024: 25 bituminous,
    # 8 waste, 2 sub-bituminous plants. Per-plant delivered fuel cost
    # already comes from EIA-923, so these shape the dispatch curve:
    #  - COAL_BIT: Appalachian/Illinois-Basin bituminous — the baseload
    #    workhorse; keeps the validated generic-coal curve.
    #  - Sub-bituminous (Powder River by rail) routes to COAL_PRB —
    #    one PRB name across ISOs (plant_taxonomy COAL_SUPPLY_TO_CLASS);
    #    its non-ERCOT band variants live on the COAL_PRB entry above.
    #  - COAL_WC: waste coal/culm (subsidised remediation fluidised-bed)
    #    — runs flat baseload, almost never peaks (low peak band).
    "COAL_BIT": {
        "committed": 0.90,
        "econ_low": 0.95,
        "econ_high": 1.10,
        "peak": 1.45,
        "econ_low_share": 0.55,
    },
    "COAL_WC": {
        "committed": 0.85,
        "econ_low": 0.90,
        "econ_high": 1.02,
        "peak": 1.20,
        "econ_low_share": 0.55,
    },
    # (The generic ``COAL`` fallback curve for plants with no resolved rank is
    # DELETED — COAL-SUB, owner instruction 2026-09-25: every coal unit now
    # resolves to one of the four subclasses above at load, so no unit reads a
    # bare-``COAL`` curve. Rule 26 [R-DELETE]: deleted, not aliased.)
}
