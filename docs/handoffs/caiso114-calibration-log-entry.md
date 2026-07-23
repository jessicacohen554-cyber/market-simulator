# caiso-114 calibration-log entry (append to docs/calibration-log/caiso.md)

> Delivered as a handoff doc: `docs/calibration-log/caiso.md` is 44 KB and parallel
> CAISO sessions append to it, so a full-file API push would risk clobbering their
> entries. This entry is committed to caiso.md in the branch's local history; merge
> it into caiso.md on integration. (caiso-112 / caiso-113 entries live in PRs
> #2786 / #2792, not on this main — phantom merge.)

## caiso-114 (2026-07-23) — L1b endogenous WECC-West node (Option A), West gas priced at the MEASURED intertie hub (hub-alone): fixes C5a + C3c and the tie clears INTERIOR (caiso-110 flood/degeneracy resolved), but BREAKS the C3a guard via an EVENING over-price → REJECTED probe; keeper 2026-07-19-caiso-102-hourfix UNCHANGED

**The build.** Wired caiso-110 Option A: `WECC_import` becomes a real co-optimized
WECC-West neighbor zone (own measured demand + a reduced import-priced fleet from
the `wecc-west-supply` frame), superseding the static import tranches / per-hub
split / clean-depth injectors (rule 18). Gate `caiso_endogenous_wecc_node`
(default off, byte-identical off). THE caiso-110 fix (`build_wecc_west_thermal_mc`):
the West GAS units (gas_cc/gas_ct) are re-priced hour-varying at the MEASURED
delivered West intertie hub — the tie-capacity-weighted MALIN(4800)+PALOVRDE(10623)
blend — via an `mc_base` override; coal keeps its physical PRB vom. HUB-ALONE, no
CARB adder: hub+CARB over-corrected the 2024 diagnostic (net import -3.1 TWh, gas
96.4 — tie flipped to net export) because the measured intertie LMP is the price
imports actually CLEARED at and CA gas is already CARB-priced, so hub-alone
competes evenly. 0 fitted params (rule 1/13/25); 7 tests.

**A/B (single delta, 3 yr one bundle, same-machine).** A = caiso102_repro_A
(flag off). B = caiso110_endog_B (registered 2026-07-23-caiso-114-endogenous-west).

| year | net import B (actual) | gas A→B (actual) | tie interior |
|------|----------------------|-------------------|--------------|
| 2023 | 32.3 (28.9) | 60.6→64.4 (74.2) | 63.8 % |
| 2024 | 31.7 (32.4) | 54.4→62.6 (61.0) | 73.2 % |
| 2025 | 37.1 (36.2) | 46.2→50.3 (51.6) | 68.3 % |

The tie clears INTERIOR every year (no flood / no tie-pinned degeneracy — the
caiso-110 84-min KILL is RESOLVED; solves ~9-10 min/yr).

**Verdict (NOT-YET, fail {C1, C3a, C4}) vs keeper NOT-YET {C3c, C4, C5a}:**
- FIXES C5a (CO2, the keeper's load-bearing fail → PASS) — the PRIMARY goal.
- FIXES C3c (scarcity tail → PASS).
- still fails C4 (gas hourly NRMSE 0.35-0.45, r 0.78-0.87 — both keeper and B).
- BREAKS C3a (mean LMP +11.0/+15.6/+10.5 %, the must-stay-PASS guard).
- BREAKS C1 (2023 CC_REGULAR -4.7 TWh — the high-hub-year under-gas).

**C3a diagnosis (no re-solve) — the over-price is ENTIRELY EVENING; belly IMPROVES.**
Zonal-mean LMP by hour, A→B: evening (18-21) **+18/+12/+4** $/MWh (2023/24/25);
belly (10-14) **-5/-2/-1** $/MWh. The design's self-limiting belly thesis HELD
(belly not over-imported/over-priced, unlike L1a''s fixed-hub belly over-price).
The regression: the measured intertie hub over-states the marginal EVENING export
price to CA — in interior-tie evening hours the West sets CA's import-zone LMP at
its own internal evening-scarcity hub ($56+), above where West energy actually
cleared to CA on the margin.

**Determination: REJECTED probe** (pre-registered gate: promote iff C3a STAYS PASS
and C5a→0; C3a did not). Keeper stays 2026-07-19-caiso-102-hourfix. But L1b is the
first mechanism to fix C5a via a forward-stable ENDOGENOUS structure (not a fitted
depth — caiso-107/109 killed those) with the tie interior, so the STRUCTURE is
right; only the West-node EVENING clearing is wrong.

**Next (caiso-115): refine the West-node evening clearing, do NOT fall back to a
fixed hub (charter KILL).** The belly/overnight are correct; the evening West offer
is too high as CA's marginal setter. Candidates (derive-first, single delta each):
(a) the evening hub embeds a WECC-wide scarcity CA's own ORDC should price, not the
import — test decoupling the West evening offer from the internal hub scarcity tail;
(b) the tie should BIND in the evening (West at export limit, CA gas marginal)
rather than the West setting an interior price — test an ε flow_cost / evening TTC;
(c) revisit the MALIN/PALOVRDE evening blend. Also close C1 2023 + C4. rule-22 LOYO
before any promotion.
