# PJM CC over-generation — ranked tuning recommendation (research, no solves)

**Companion to** `docs/handoffs/pjm-cc-level-tuning-2026-06.md` (the brief) and
`docs/cc-high-cf-investigation.md` §"PJM and the net-summer ISOs". This is the
analysis deliverable that brief asked for: a ranked, evidence-backed tuning
direction. **No calibration solves were run.** ERCOT/CAISO/MISO/SPP stay
byte-identical (every lever below is PJM-gated, like the structural fix already
shipped).

## The exposed miss (re-derived from the docs, not from the gone scratchpad)

The `cc_nameplate_summer_derate` structural fix removed the false ~75 %-of-nameplate
CC wall. With it gone, PJM 2024 diagnostic `CC_REGULAR`: **73 % annual CF vs CAMPD
61 %**, **+64.7 TWh** over CAMPD net (model 394.9 vs 330.2), online 87.5 % of hours
vs real 78 % (offline 12.5 % vs 22 %), **135 600 h at 95–100 % CF vs CAMPD 34 500**.
Model gas ≈ 437 TWh vs ~370; coal ≈ 92 vs ~120. Model peak ≈ CAMPD peak (ratio
1.00) → genuine over-generation. This is the rule-11 signal: the wall was masking a
CC that is **structurally too willing to run, and too cheap when it does**. The fix
is the real mechanism, never a new wall (CLAUDE.md #1/#11).

### Decompose the 12 pp CF gap into the two misses (sizes the levers)

Online-fraction arithmetic separates them. If the model ran *only* the real
when-online level but stayed online 87.5 % instead of 78 % of hours, CF would be
61 % × (87.5/78) ≈ **68.4 %**. So:

- **Miss #1 — too many ON hours** explains ~61→68.4 %, i.e. **~7.4 pp ≈ ~60 % of
  the gap / the bulk of the +65 TWh.** Overnight cheap committed block never
  shuts. → commitment / offer-floor.
- **Miss #2 — too high when ON** (the 95–100 % pile) explains ~68.4→73 %, i.e.
  **~4.6 pp ≈ ~40 %.** No reserve headroom held; duct band clears in cheap-gas
  peaks. → reserve co-optimization / capacity headroom / duct pricing.

A single lever fixes neither cleanly; rank by structural correctness first
(CLAUDE.md #1), then tractability and measured-vs-fitted (CLAUDE.md #12).

---

## Public-data anchor: is "real CCs run 61 %, not 73 %" right?

Yes. EIA-860/923 (Electricity Data Browser) NGCC fleet capacity factors run
**~55–60 %** nationally in 2023–24; PJM's gas-CC fleet sits in that band. CAMPD's
61 % is consistent and is *not* a coverage artifact (CAMPD covers essentially all
grid CCs >25 MW). So 73 % is a genuine model over-run, and the target is ~60–62 %.
PJM/Monitoring Analytics **State of the Market** confirms CCs are frequently the
**marginal** unit (set price a large share of hours) rather than pinned
inframarginal at full load — i.e. they cycle and part-load, the opposite of a
95–100 % pile. PJM Manuals **11** (Energy & Ancillary Services, §4.3.3 reserve
requirements/ORDC) and **15** (Cost Development — min-load cost, no-load cost,
start cost) are the *published, measured* basis for both a realistic min-load
offer floor (miss #1) and reserve headroom (miss #2).

**Modeling-best-practice axis.** Every production dispatch model that reproduces
realistic CC cycling does it with **unit commitment** (start-up + min-load +
min-up/min-down) **and operating-reserve co-optimization**: PLEXOS, GE-MAPS,
PROMOD, Dayzer, EPA IPM, EIA NEMS, NREL ReEDS→PLEXOS. A pure economic-dispatch LP
with a cheap committed block **over-runs cheap units** — this is the documented,
well-known limitation of dispatch-only LPs. The two repo levers that map onto the
standard fixes are the **P2 commitment screen** (miss #1) and **in-LP reserve
co-optimization** (miss #2). That is exactly the repo's own settled campaign
(`pjm-reserve-ordc.md` "Phase 1 commitment posture → Phase 2 co-opt → Phase 3
retune offers").

---

## Ranked recommendation

### Rank 1 — TEST FIRST: turn on the P2 commitment screen for PJM
**Lever:** `commitment_enabled=True` (PJM). `model/commitment.py` +
`runner.py`/`run_calibration.py` P2 (the screen is generic, not ISO-gated:
`run_calibration.py:2593` `if config.commitment_enabled:`). It already works on
PJM's per-plant fleet — non-CAMPD gens route through `COMMITMENT_PARAMS_BY_FUEL`
(`commitment.py:120`), keyed by `gas_cc`/`gas_ct` × heat rate.
**Why first:** it is the **most direct structural lever on miss #1** (the larger
~60 % volume share), it is the repo's designated Phase-1 prerequisite
(`pjm-reserve-ordc.md`), and — unlike reserve co-opt — **it already exists**; the
only cost is the third LP solve, not new structure. It is the textbook fix for the
documented dispatch-only over-run.
**Measured vs fitted:** **measured / published.** Startup, min-run, min-down come
from `CC_COMMITMENT_PARAMS` (`constants.py:53`, NREL SR-5500-55433 Kumar 2012:
f-class CC 8 h min-run / 6 h min-down / $48.6/MW-start; h-class 10/8/$63.8). The
IRR-hurdle screen (P1 price vs *base* MC) is a market-design mechanism, not a knob
tuned to the residual.
**Predicted sign:** (a) CC volume **↓** (decommits unprofitable overnight runs →
moves offline toward the real 22 %); (b) 95–100 % mass **↓ modest / neutral**
(commitment is ON/OFF, not when-on level — it trims the pile only via the units it
fully shuts); (c) gas↔coal **gas ↓, coal ↑ slightly** — coal stays committed and
backfills decommitted overnight CC; **wanted direction** (coal is under) and
**bounded**: coal is only ~15 % of PJM 2024, under by ~28 TWh, so do not let the
shift push coal past ~120 TWh / ~20 % share.
**Risk / cost:** compute + memory of the 3rd solve at PJM plant scale (the brief's
stated reason it is off). Tractable (no new columns), but profile memory; solve
years serially if needed (CLAUDE.md #45 caps concurrent PJM plant-level solves).
**Coupling caveat (important):** the screen uses margin = P1 price − **base** MC.
If overnight LMP still exceeds CC base MC (gas-CC ~$20–25 vs PJM overnight
~$20–30), long continuous runs clear the startup hurdle and **stay committed** —
so commitment alone may under-shut. Its power is gated by the offer floor in
Rank 3. Expect commitment to make a real dent but not fully reach 22 % offline
without the Rank-3 floor re-grounding; that is the coupling to test next, not a
reason to delay turning it on first.

### Rank 2 — STRUCTURAL but BLOCKED: zonal/aggregated reserve co-optimization (miss #2)
**Lever:** `energy_reserve_coopt` PJM branch (`run_calibration.py:2401`;
`scarcity.pjm_reserve_coopt_inputs`; `dispatch._build_reserve_rows`). The correct
fix for the 95–100 % pile: hold deliverable (10-min / synchronized) reserve so CC
energy CF tops out below nameplate, with the requirement's dual as the reserve
price — priced *inside* the solve, no wall, no overlay.
**Why not first — it cannot bite as built.** Two hard blocks, both already proven
in-repo (`pjm-reserve-ordc.md`):
1. The as-built reserve rows reuse the **zone-aggregate** `_build_reserve_rows`,
   which caps reserve at a zone's *total* eligible thermal headroom (~38 GW) — far
   above the ~3.3 GW step. The bind-gate probe (`_pjm_coopt_bindgate.py`, no
   re-solve) shows it **clears at $0 every hour** (min 7.3 GW, p50 50.5 GW; 0 h <
   req). A ramp/deliverable cap thins it enough to cross the requirement in only
   ~49 h/yr, and those bind at the **penalty** step ($300–850) — the *shortage*
   regime that **overshoots** the $75–200 opportunity-cost band, while the broad
   afternoon band still floats on free deliverable headroom.
2. The measure that *would* bite — **per-gen `R[g] ≤ ramp10[g]`** so reserve
   competes with energy on the *marginal* unit — is **memory-infeasible on the
   15 GB box** (the zone-aggregate co-opt already OOMs at ~16 GB; per-gen reserve
   columns at PJM plant scale are heavier) **and blocked on ramp-rate data absent
   from `FleetArrays`**.
**Note the shipped ORDC overlay does NOT help here:** it is **post-solve,
price-only — it reserves no MW** (`pjm-reserve-ordc.md`, `scarcity.py`), so it
cannot cap CC energy CF. Do not mistake it for a reserve-headroom lever.
**Measured vs fitted:** the requirement is **measured** (PJM RT Primary Reserve
`as_req_mw`) and the curve is **published** (Manual 11 §4.3.3 / §4.4.1) — fully
admissible (CLAUDE.md #12). The blocker is engineering (memory + ramp data), not
honesty.
**Predicted sign (if/when built per-gen):** (a) CC volume **↓ small** (reserve
displaces ~3 GW of marginal energy); (b) 95–100 % mass **↓↓ — this is the lever
that structurally empties the pile**; (c) gas↔coal **near-neutral / slight gas↓**.
**Recommendation:** keep `as_reserve_withholding` on as the structural pre-condition
(already in `pjm_27_aswh`), and treat the per-gen ramp-limited reserve build as the
real fix for miss #2 — but **scope it as a separate engineering task** (add `ramp10`
to `FleetArrays`; profile/solve serially or shard) rather than the next dial. Until
then, miss #2 is attacked by Ranks 3–5, which are tractable now.

### Rank 3 — LEVEL (cheapest, measured): raise PJM `committed`/`econ_high` toward ERCOT SRMC
**Lever:** PJM `CC_REGULAR` offer curve `committed 0.6624 → ~0.85`, `econ_high
1.1428 → ~1.21` (`results/calibration/_configs/pjm_run20/pjm_keeper_offer_curve.json`). ERCOT's
structurally-validated keeper (`run124`/`run_config.json`) holds its CCs at the
right level **with commitment and reserves OFF** using exactly the richer curve:
`committed 0.87, econ_low 0.92, econ_high 1.21`. PJM's 0.66 committed is ~24 %
below ERCOT's — that cheap must-take floor is what clears overnight (miss #1) and
the low `econ_high` lets the upper ramp clear too readily (miss #2).
**Why Rank 3 not Rank 1:** CLAUDE.md #1 puts structure before offer-level tuning,
and the offer floor's effect on overnight clearing is **coupled to** (and
amplifies) the Rank-1 commitment screen — it should be set *with/after* commitment,
not instead of it. But it is by far the **cheapest and lowest-risk** change (a JSON
edit, zero memory cost) and is the lever that makes commitment actually shut units
overnight (see Rank-1 coupling caveat).
**Measured vs fitted:** **measured-grounded, NOT a residual fit.** The target is a
published-cost / cross-ISO-validated SRMC level: PJM Manual 15 min-load + no-load
cost makes a CC's *effective min-load* $/MWh sit at-or-above full-load SRMC (so a
0.85–0.87 committed multiplier is the physically right floor, and 0.66 is the
anomaly the old wall left behind). Anchor the move to ERCOT's keeper + Manual 15,
**not** to the PJM price/volume residual (that would violate #11). Do **not** chase
the residual past the SRMC-justified level.
**Predicted sign:** (a) CC volume **↓** (higher floor → unit doesn't clear in the
cheapest overnight hours; higher `econ_high` → upper ramp clears less); (b) 95–100 %
mass **↓** (econ_high lift prices the top of the ramp out of marginal hours); (c)
gas↔coal **gas ↓, coal ↑** — a richer CC SRMC lets coal undercut more overnight
hours → **wanted** (coal under) but **bound the move so coal stays ≤ ~120 TWh /
~20 %**; watch the C1 balance, since coal is only ~15 % a too-aggressive committed
raise over-rotates to coal.
**Guardrail:** check delivered-gas level first (`data/fuel.py`,
`GAS_BASIS_DIFFERENTIAL`, per-plant EIA-923) — the repo's design does the gas
*level* correction via basis, not the offer curve. Confirm PJM delivered gas
isn't too cheap vs EIA-923 before attributing the whole miss to offers; otherwise a
committed raise would paper over a fuel-basis miss (#11).

### Rank 4 — MEASURED DATA: demonstrated-peak cap on the 12 over-nameplate CC plants
**Lever:** `cc_capacity_reconcile` with a **demonstrated-peak CAP** (lower model
nameplate to CAMPD p99.9 where nameplate exceeds it). The brief notes **12/69 PJM
CC plants have model nameplate >1.1× their CAMPD demonstrated peak** — they over-run
the top purely on capacity. `scripts/data/derive_cc_capacity_reconcile.py` is currently
**raise-only** (`reconciled = max(cur, p999)`, `_MIN_DELTA`), so it does nothing for
PJM's over-capacity plants; it needs a `min(...)`/cap mode (or a PJM variant
writing `cc_capacity_reconcile_PJM.csv`).
**Measured vs fitted:** **measured (CLAUDE.md #12).** Capping at the demonstrated
CAMPD p99.9 peak is "prefer accurate/measured data over estimates" — a plant that
*never* produced above X MW in the CEMS record should not be modeled with headroom
above X. This is the *opposite-direction* twin of the ERCOT raise-only reconcile
and is the right measured complement to the seasonal derate. (ERCOT stays raise-only
and byte-identical.)
**Predicted sign:** (a) CC volume **↓ (targeted)**; (b) 95–100 % mass **↓↓ on
exactly the offending plants** — directly removes the headroom feeding the pile;
(c) gas↔coal **gas ↓, coal ↑ slight**. Cleanest *measured* attack on miss #2 that
is **tractable today** (no LP-structure change, no memory cost).
**Caution:** cap only where nameplate clearly exceeds the demonstrated peak by a
margin (the >1.1× set), and use p99.9 (not the max) to stay robust to single-hour
CEMS glitches, mirroring the existing script. Do not cap a plant that simply didn't
dispatch high in a low-gas year for economic reasons — use the *demonstrated
capability* peak, not the realized dispatch peak.

### Rank 5 — DUCT BAND: re-ground the 8 % / ~2.25× supplementary-firing band
**Lever:** PJM `CC_REGULAR` `pct_peaking 8`, `peak 2.77×` config (effective duct
~2.25× ≈ $45/MWh on 2024 gas, after `cc_duct_peaking_cap_pct=8`,
`run_calibration.py:784`). If the duct band clears in ordinary cheap-gas high-demand
hours it feeds the 95–100 % pile; real F-class duct firing is a smaller, pricier
slice rarely dispatched.
**Measured vs fitted:** **physically grounded** — F-class supplementary firing is
~4–5 % of nameplate at ~1.3–1.5× incremental (per `cc-high-cf-investigation.md`),
so 8 % at ~2.25× is on the generous side. Re-grounding to the physical
duct-firing increment is measured, not residual-fitted.
**Predicted sign:** (a) CC volume **↓ small** (only the very top); (b) 95–100 %
mass **↓ (the top slice specifically)**; (c) gas↔coal **~neutral**.
**Caution (from the ERCOT sweep):** a blanket peak cut is **not** a keeper —
`cc-high-cf-investigation.md` shows it pushes already-over-running plants further
off and breaches the class gate in some years. Treat this as a **minor, last** trim
after Ranks 1/3/4, and validate per-plant with the 5 %-band `[7b]` / `cf_emd`, not
as a primary lever.

---

## The single change to test first

**Turn on the P2 commitment screen for PJM (`commitment_enabled=True`).** It is the
largest-volume structural lever on the dominant miss (#1, ~60 % of the +65 TWh), it
is the repo's designated Phase-1 prerequisite, its parameters are measured (NREL),
and it already exists — the only cost is the third solve. Test it **alone** first to
isolate its effect on the offline-hours fraction and the gas↔coal balance.

**Then, as the immediate follow-up (one combined re-solve), pair it with the Rank-3
committed-floor raise (0.66→~0.85, econ_high→~1.21)** — the offer floor is what lets
commitment actually shut units overnight (the base-MC coupling caveat). Hold Rank-2
(per-gen reserve co-opt) as a separate engineering task (ramp data + memory), and
fold in Rank-4 (demonstrated-peak cap) as the tractable measured attack on the
95–100 % pile. Validate every step on the 5 %-band `[7b]` / `plant_cf_bands` /
`cf_emd` and the C1 gas↔coal balance, bounding coal at ≤ ~120 TWh / ~20 % share.

## NYISO / NEISO notes (focus stays PJM)

The same `cc_nameplate_summer_derate` fix is wired for NYISO/NEISO, so they will
have shown the same wall-removal → over-run flip. The **structure** (commitment,
reserve co-opt) generalizes, but the **level** must be re-derived per ISO:

- **Offer floors differ** — do not copy PJM's `committed`/`econ_high` to NYISO/NEISO;
  re-anchor each to its own SRMC (their gas basis differs — NYISO uses Transco
  Z6-NY / Iroquois, NEISO Algonquin, both far above Henry Hub, so the *fuel level*
  carries more of their CC offer than in PJM; check `data/fuel.py` basis first).
- **Reserve markets differ** — NYISO is **locational nested** reserves (the
  `energy_reserve_coopt` NYISO branch at `run_calibration.py:2463`, FERC ER21-502);
  NEISO has its own TMSR/TMNSR/TMOR products. The reserve-headroom lever (miss #2)
  is real for both but each needs its own measured requirement series.
- The commitment params (NREL) are fleet-physics, not ISO-specific, so Rank-1
  transfers directly; Ranks 3–5 are per-ISO level work.

## Guardrails honored

- ERCOT, CAISO, MISO, SPP **byte-identical** — every lever above is PJM-gated
  (NYISO/NEISO get their own per-ISO level work). The ERCOT `cc_capacity_reconcile`
  stays raise-only; the PJM demonstrated-peak cap is a separate PJM path.
- No wall restored; no parameter fitted to the price/volume residual (CLAUDE.md
  #1/#11). Every lever is measured/published or a market-design mechanism, with the
  measured-vs-fitted call stated per lever (CLAUDE.md #12).
