# FINDING — capx D35: the FC-6 P2 gas leg re-scoped from a class label to the model's gas partition; neiso-t3's P2 row re-scored on committed artifacts

**Session:** D35 (capacity-expansion / Forecast Finalization track), branch
`claude/capx-d35-p2-scope-b5x2by`. **Date:** 2026-09-02. **HEAD at launch:** `07472e7c`
(origin/main). **Charter:** adjudicate what the gas-up driver leg (P2) SHOULD measure on a
25-year evolution pair whose combined-cycle class migrates to CCS, repair the checker so the
leg measures the model rather than its own construction, and re-score `neiso-t3`'s FC-6 P2
row artifact-only (zero solves), control-first, touching nothing beyond that row and the
FC-6 rollup it feeds.

---

## 0. PRE-STATEMENT — written and committed BEFORE the repaired checker ran

This section is frozen at its commit. §5 grades it.

### 0.1 The scope decision

**The P2 gas leg is re-scoped to TOTAL GAS-FIRED GENERATION — the sum over every class that
burns natural gas in the model's own fuel partition (`gas_cc`, `gas_ct`, `gas_cc_ccs`,
`gas_st`; `data/fuel/_shared.py::_GAS_FUEL_IDX`, the set of classes that pay the gas price).**
The per-class `gas_cc↓` key is retired from the gating list and kept only as a reported
control inside the row's evidence block. Reasons, in order of weight:

1. **It is the only candidate with a theorem behind it — even on the same-fleet pairs the
   leg was written for.** For a fixed feasible set, LP optimality of `x` under cost `c` and
   of `x'` under `c' = c + Δ` gives `Δ·(x' − x) ≤ 0`. A gas-price increase sets
   `Δ_g = hr_g × Δp_g ≥ 0` exactly on the gas-burning units and 0 elsewhere, so the
   heat-rate-weighted gas generation (gas fuel burn) weakly falls. Nothing in that inequality
   says anything about `gas_cc` alone: coal or imports displace the dearest gas MWh first
   (steam, CTs), and a per-class reading can move either way while the theorem holds.
   Total gas-fired MWh is the summary-visible proxy for burn (heat rates within the gas
   classes are close enough that a CT→CC reshuffle cannot invert it at the magnitudes the
   pair produces).
2. **The driver is a fuel-level input, so the response the leg is entitled to expect is
   fuel-level.** `gas_price_factor` scales the delivered gas price for every gas-burning
   unit. A CCS-retrofitted CC burns the same gas as its unabated host at a higher heat rate;
   labelling it a different "fuel" is a taxonomy convenience for the capacity ledger, not an
   economic boundary the gas price respects.
3. **On an evolution pair the class label is itself a response variable.** The CCS screen's
   fuel-cost penalty scales with the gas price, so the split of the CC family between
   `gas_cc` and `gas_cc_ccs` MOVES with the very driver the leg perturbs. Gating on one side
   of that split measures the retrofit screen's composition response — a legitimate model
   behaviour with no pre-registered sign — and reports it as a merit-order failure. That is
   the D23 family exactly: the instrument measuring its own construction.

**Candidates rejected, and why** (the charter's list, adjudicated rather than assumed):

- *The whole `gas_cc` family including CCS-converted units.* A label fix, not a claim fix:
  it still omits `gas_ct`/`gas_st`, it has no theorem behind it, and it inherits the same
  confound the moment a CT or steam unit's share moves. Subsumed by the all-gas scope.
- *The last year both worlds hold unabated CC.* A year search keyed on the outcome of the
  confound. On this pair that year is 2039, where the arm holds 4,000 MW of unabated CC to
  the base's 3,000 and the per-class key STILL reads a violation — so it rescues nothing,
  and as an instrument it lets the comparison year drift with the fleet rather than being
  fixed by the pair. Rejected.
- *A capacity-migration-aware construction* (per-MW utilisation of the unabated class, or a
  class-capacity-normalised comparison). Undefined whenever a class is absent in one world
  (this pair at 2050), and it compares the utilisation of DIFFERENT marginal units across
  worlds, which has no sign expectation. Migration-awareness belongs in the EVIDENCE — the
  row now reports the class split in both worlds and whether the legacy key would have been
  confounded — not in the gate.

**What stays exactly as it was:** the comparison year (the last common solved year), the
`coal↑` sub-check (scored only where the base holds coal at that year, as before), `price↑`,
`objective↑` (where the objective is available), the FAIL-on-sign rule, and the row's
ident/name (`P2` / `merit-order sign`).

**Meaningfulness on fleets that do NOT migrate (charter criterion b):** on a same-fleet pair
the all-gas sum is `gas_cc + gas_ct + gas_st`, the theorem above applies verbatim, and the
sign is BETTER founded than the old per-class key was. Nothing is lost; a class-level
response is still visible in the evidence block.

### 0.2 The artifact-only path

The committed golden-2 FC-6 arms carry `full_horizon_summary.json` + `run_config.json` only
(no per-year parquets, no caches — session-local, gitignored). The summary's
`generation_by_fuel_mwh` (D29 grain) is computed by `run_full_horizon.py` calling the
checker's OWN `_fuel_gen_mwh` and rounding to 0.1 MWh, so a summary-backed P2 is the
cache-backed P2 by construction for generation and load-weighted price. The one sub-check
the summary cannot carry is `objective↑` (no objective in the summary). In summary mode the
row reports it as not available at that grain and excludes it from the gating list — it is
NOT carried as a PASS from the committed row. (The committed row's own detail lists every
failing sub-check and names only `gas_cc↓`, so the committed cache-scored objective↑ was a
PASS; that is recorded here as a fact about the committed row, not scored.)

### 0.3 The pre-stated expectation

- **Control 1 (unmodified scorer, committed inputs):** reproduces the committed
  `forecast_verdict.json` with zero non-provenance diffs. Expected: exact.
- **Control 2 (legacy per-class key computed on the committed summaries):** reproduces the
  committed P2 detail `year 2050: wrong: gas_cc↓` exactly. Expected: exact (same function,
  same rounding).
- **The repaired leg on the committed pair, expected verdict: P2 PASS.** From the numbers
  already in golden-2 §7.1: total gas-fired generation at 2050 is 36.53 TWh (base) vs
  35.36 TWh (gas ×1.5) — falls; load-weighted price 79.16 → 93.95 $/MWh — rises; the base
  holds no coal at 2050 so `coal↑` auto-skips; `objective↑` is not available at summary
  grain. The class-migration evidence is expected to show the base at 0 MW / 0 TWh of
  unabated CC against the arm's 6,000 MW / 23.2 TWh, i.e. the legacy key flagged
  confounded.
- **Consequence for FC-6, expected:** the P2 row FAIL → PASS; the FC-6 category
  FAIL → CAVEAT (the surviving CAVEAT is T16-A's battery row, all-constant series
  [1.0, 1.0], untouched); `reasons` drops `FC-6 driver response FAIL`; `caveats` gains
  `FC-6 driver response`; determination stays **HOLD** on FC-1/2/3/4. Nothing else moves;
  if the recursive diff shows anything beyond those leaves the lane STOPS and routes.

Honesty note on the pre-statement: the charter itself quoted the all-gas 2050 numbers, and
this lane printed the arms' per-year class table while establishing the artifact-only path
(§0.2) before writing this section. The pre-statement's value is therefore NOT that the
outcome was unknown — it is that the scope was chosen on the theorem in §0.1, which would
have been the choice whatever the numbers said. Either outcome of the repaired leg was and
is valid: a surviving FAIL would have measured the model.
