# caiso-116 calibration-log entry (append to docs/calibration-log/caiso.md)

> Delivered as a handoff doc: `docs/calibration-log/caiso.md` is 44 KB and parallel
> CAISO sessions append to it, so a full-file API push would risk clobbering their
> entries (the caiso-114/115 precedent). This entry IS committed to caiso.md in this
> branch's local history; merge it into caiso.md on integration. On main the log
> runs 111 → 115 (caiso-112/113/114 live on their own branches, not main).

## caiso-116 (2026-07-23) — EXECUTE-THE-BELLY-LANE, DERIVE-GATED: candidate (a) (the endogenous WECC-West node) CANNOT be evening-scoped to keep C3a while fixing C5a — the modeled West (EIA-930 NW+SW) net-exports only ~19 TWh/yr but CAISO imports 29-36, and L1b matched CA's import VOLUME only by over-generating that ~9-17 TWh/yr gap as gas exported at the intertie hub (the marginal unit that breaks C3a); C5a-fix and C3a-guard are COUPLED through that proxy over-export, so BOTH scopings fail by derivation; the fleet-bound delta was built + tested then reverted (over-corrects C5a + infeasible); keeper UNCHANGED

**Derive-first gate, mechanism built-then-refuted, NO SOLVE, nothing registered.**
Keeper `2026-07-19-caiso-102-hourfix` UNCHANGED (NOT-YET, fail {C3c, C4, C5a}).
The caiso-115 handoff chartered this session to EXECUTE the belly (C5a) lane by
building one pre-registered single delta — candidate (a), the caiso-114
endogenous WECC-West node, evening-scoped so the West does not set CA's evening
LMP. A derive-first pass (rule #1, before committing a mechanism) uncovered a
DATA-SCOPE gap the caiso-114/115 handoffs did not anticipate. Full record +
reproduction: `results/calibration/FINDING-caiso116-endogenous-datascope-2026-07-23.md`
/ `scripts/probes/_caiso116_endogenous_datascope_derive.py` (no LP).

**Inv 1 — the data-scope gap (load-bearing).** Modeled West net-export capability
(`wecc-west-supply` net_export_mw = EIA-930 NW+SW net gen − demand) vs CAISO net
import (raw EIA-930 CISO): **19.4/18.9/19.2 TWh** West vs **28.8/31.9/36.0 TWh**
CA → GAP **9.3/13.0/16.9 TWh**, WIDENING as CA's import demand grows. L1b
(`caiso110_endog_B`) matched CA's volume (32/32/37 TWh) ONLY by having the West
over-generate that gap as gas exported at the measured intertie hub — LOW in the
belly (the C5a fix worked) but HIGH in the evening where it is the marginal unit
and SETS CA's import-zone LMP (+$4-18, the C3a break). The over-export is a proxy
for CA's true out-of-region imports; pricing it at the hub (marginal) breaks C3a.

**Inv 2 — the West cannot supply CA in any block.** West exportable-gas surplus
(gas_mw − own-load gas need) vs CA net import, GW: belly 0.5-1.2 vs 0.7-1.9;
evening 0.7-1.8 vs 3.3-3.9; night 3.3-3.5 vs 5.3-6.2. The West's surplus is
almost all gas, tracks the tie shape (~0 belly / +2 evening / +4 night) but is
far below CA's actual import everywhere.

**Inv 3 — bounding the West is INFEASIBLE.** The modeled West itself net-imports
**22/23/24 % of hours** (net_gen < demand, worst shortfall ~7.3 GW) from WECC
regions outside the modeled NW+SW aggregate and the single CA tie. So the
fleet-bound scoping (cap West thermal at measured output — which WOULD force CA
gas marginal and preserve C3a) cannot be solved cleanly: no CA-connected backstop
represents the West's real (eastern) imports without either under-pricing (cheap
export) or over-inflating CA gas (CA→West in the West's own peak). The gap bites
both directions.

**Inv 4 — empirical anchor.** Committed `caiso110_endog_B/metrics.json`: C5a
**PASS**, C3c **PASS**, C3a **FAIL** (C3b PASS, C4 FAIL) — the coupling, measured.

**Inv 5 — min-hub under-fixes C3a.** The price-temper scoping (offer West gas at
min(MALIN,PALOVRDE) vs the tie-weighted blend; caiso-114 note c) shaves only
**$7.1/$2.5/$1.2** off the evening offer vs the +$4-18 break — the break is the
West gas BECOMING MARGINAL at the hub, not the hub's level. Refuted.

**Determination.** C5a-fix and C3a-guard are **coupled** through the West's
~13-18 TWh proxy over-export; candidate (a) is **NOT viable for the belly lane**
as built. This SHARPENS caiso-115: the belly-volume (hod 10-15) and evening-price
(hod 17-21) lanes separate in HOURS, but the endogenous node re-couples them
through the volume gap (L1b broke C3a because it HAD to over-export gas at the
hub to hit CA's volume, not merely because it re-priced the evening).

**Mechanism built then reverted.** `caiso_wecc_west_thermal_shaped` (cap West
coal/gas availability at measured `coal_mw`/`gas_mw` — the fleet-bound scoping,
the cleanest rule-13-admissible knob, same measured-availability class as the
node's VRE/hydro shaping) was implemented in `wecc_west_fleet.py` + wired +
unit-tested (2 tests), then **reverted**: the derive shows it over-corrects C5a
(bounding the West to 19 TWh under-supplies CA's 29-36 → +9-17 TWh more CA gas,
past the +7 % gate) and is infeasible (Inv 3). Rule #1 forbids solving through a
mechanism that isn't real; the design is preserved in the FINDING (re-buildable
in minutes once the scope is reconciled). Keeper stays `2026-07-19-caiso-102-hourfix`.

**Next (caiso-117), redirect — reconcile the West import scope, or hand the
evening to CA's own scarcity (in preference order):**
1. **Close the data-scope gap:** broaden the modeled West beyond NW+SW (or add
   the West's own eastern/Baja import as an inframarginal price-taker to
   `wecc-west-supply`) so its net-export capability matches CA's 29-36 TWh. Then
   L1b's over-export becomes REAL and inframarginal → CA gas sets the evening →
   `_thermal_shaped` becomes feasible and C3a-preserving.
2. **Do the EVENING lane first/jointly** (the caiso-115-named lane): tighten CA's
   OWN evening scarcity (`hydro_dispatch_envelope` lower percentile / daily
   budget; arm `caiso_firm_import_shape`) so CA's domestic peakers set the evening
   price and the West import becomes inframarginal by comparison. The belly and
   evening lanes are COUPLED — work them together, not separately.
3. **Fall back to candidate (b), belly-HOUR-scoped and West-physically grounded:**
   a belly-only cap at the West's measured belly deliverability (~1-2 GW, a
   West-side physical quantity — Inv 2 — NOT CA's residual flow) fixes the belly
   over-import while leaving the evening untouched (C3a preserved). Must be
   belly-scoped (an all-hours net-export cap hits the same gap → over-corrects
   C5a) and level-tied to physical capability, not the residual (rule 13 /
   caiso-107/109).

**DO-NOT-REDO (added):** endogenous-node fleet-bound scoping (thermal-shaping) on
the NW+SW frame — over-corrects C5a + infeasible until scope reconciled;
min-hub / MALIN-PALOVRDE re-weight — under-fixes C3a (marginality, not level).
Carried: fixed-hub West fallback (caiso-114 KILL); belly-depth on CA-price /
west-surplus-quantity observables (caiso-107/109); firm-rung reprice (pinned,
caiso-104/109).

Next number: caiso-117.
