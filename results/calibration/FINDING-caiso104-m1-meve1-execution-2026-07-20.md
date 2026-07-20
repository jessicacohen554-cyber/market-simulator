# FINDING (caiso-104): M1 + M-EVE-1 owner rulings executed — M1 (DA charge-allocation schedule) built with gates PRE-REGISTERED below; the M-EVE-1 premise is CONTRADICTED by the keeper's own config record (the caiso-77 must-flow floor is LIVE), pin-check adjudication on the fresh A-leg before any evening leg; negative-hub conduct measured (bid constant = $0); DAM-outage intake opened

**Session 2026-07-20 (CAISO-104 — executing the caiso-103 asks per the owner
rulings obtained this session): M1 (belly DA-allocation-profile charge
schedule) GRANTED; M-EVE-1 (price-taking firm import blocks) GRANTED with the
pre-measurement mandate; da_frac forward semantics = latest-year carry (the
envelope precedent); issue #2546 delegated to the session's recommendation
(→ defer as-is this session, delete + re-gate as a dedicated follow-up — the
A-leg baseline must stay byte-comparable to the keeper). Additionally
owner-directed (2026-07-19): the CAISO DAM-published outage/derate intake
with DAM-before-CAMPD precedence. Keeper: `2026-07-19-caiso-102-hourfix`
(NOT-YET, fail {C3c, C4, C5a(2024 CAVEAT)}; belly +6.0/+6.6/+4.3, evening
−5.8/−4.9/−1.1, overnight +0.8/−0.0/+1.4).**

Everything in §1–§4 was written BEFORE any mechanism leg solved (charter
discipline; the B-leg gates below are the pre-registration).

## 1. M-EVE-1 pre-measurement: firm-flow conduct in negative-hub hours → bid constant $0

`scripts/probes/_caiso104_firm_negative_hub.py` (NEW, committed; decision
rule fixed a priori in its docstring — pooled same-(month × hod)-cell
relative depression ≥ 10 % AND ≥ 2/3 of populated cells depressed ⇒
curtailment conduct ⇒ $0; else −ε). Basis: the caiso-73 shape's own series
(EIA-930 CISO corridor net imports, model clock) stratified within
(month × hod) cells against the corridor's own measured hub (MALIN /
PALOVRDE):

| corridor-year | neg-hub hrs | strata | cells depressed | med flow neg vs pos (MW) | verdict |
|---|---|---|---|---|---|
| PNW 2023 | 136 (2.0 %) | 9 | 0.89 | −652 vs +60 | CURTAILMENT |
| PNW 2024 | 307 (3.5 %) | 26 | 0.88 | −1542 vs −935 | CURTAILMENT |
| PNW 2025 | 295 (3.4 %) | 21 | 1.00 | −1251 vs −584 | CURTAILMENT |
| DSW 2023 | 291 (4.3 %) | 22 | 0.73 | +59 vs +598 | CURTAILMENT |
| DSW 2024 | 939 (10.8 %) | 37 | 0.97 | +629 vs +1579 | CURTAILMENT |
| DSW 2025 | 849 (9.7 %) | 38 | 0.76 | +1684 vs +2221 | flows persist |

**5/6 corridor-years show curtailment conduct** (the PNW corridor flips to
net EXPORT in negative-hub hours). Per the a priori rule the M-EVE-1 bid
constant is fixed at **$0 + the existing intertie tie-break ε** — the block
must not flow through prices reality curtails through. This measurement also
bears on the LIVE caiso-77 floor (§2): a must-flow floor forces firm flow
through negative-λ hours, the opposite of the measured conduct.

## 2. The M-EVE-1 premise is contradicted by the keeper's own config record

The registered keeper bundle's `run_config.json → scenario_config` records
**`caiso_firm_import_selfschedule = True`** (with `caiso_firm_import_shape =
True`, `caiso_perhub_firm_base = True`): the caiso-77 must-flow floor
(`transmission.inject_caiso_firm_import_selfschedule`, promoted to keeper
2026-07-12 and carried by `_caiso95_repro_A._keeper_overrides` into every
successor recipe including `_caiso102_repro_A`) floors both firm blocks'
`min_gen` at their FULL shaped capability `pmax × availability`. A unit with
`min_gen == pmax × availability` is PINNED — it can never be marginal and
its $28/$48 ladder price is inert bookkeeping (the caiso-77 docstring says
exactly this).

Consequences, if the pin holds on the solved bytes:

- FINDING-caiso103 §3's tranche attribution ("the firm blocks are
  price-setting in 96–100 % of Q1 hours with 1.7–2.5 GW economically
  withheld") is an artifact of its interior-dispatch proxy (`0.02–0.98 ×
  unit-year p99` on month-varying pinned dispatch: a pinned block in a
  low-shape month reads as "interior", and "capability − dispatch" against a
  per-hod p99 proxy reads as "withheld" when it is month-shape variation).
- M-EVE-1 as designed (swap the two blocks' bids to a price-taking constant)
  is **provably byte-inert**: a variable fixed at equal bounds never sets λ,
  and its mc enters the objective only as a constant.
- The variant that WOULD change bytes — replacing the floor with the $0 bid
  (floor OFF + price-taker offer) — can only REDUCE evening firm flow
  relative to the pinned keeper (the floor already forces full shaped flow
  every evening hour), so it cannot produce the ask's predicted effect
  (withheld GW flowing, evening λ climbing). It would instead curtail the
  forced firm flow in negative-λ belly hours — the §1 measured conduct —
  which is a *different* mechanism with a *different* prediction than the
  granted ask.

**Pre-registered adjudication (before any M-EVE-1 leg):** on the fresh
same-machine `caiso102_repro_A` (this session), check per firm block per
year: `share of hours with dispatch == pmax × availability (tol 1e-6 rel)`.
If ≥ 0.999 (the pin), M-EVE-1-as-granted is adjudicated INERT with no B-leg
(the ERCOT-64 provably-inert precedent), FINDING-caiso103 §3's attribution
is corrected, and the floor→$0-bid replacement goes back to the owner as a
NEW ask (it un-promotes a piece of the caiso-77 keeper mechanism and its
belly/evening effect signs differ from the granted ask). If the pin does
NOT hold (something downstream breaks the floor), M-EVE-1 proceeds as
granted with the §4 gates.

**ADJUDICATION RESULT (this session, `_caiso104_firm_pin_check.py` on the
fresh A-leg — which reproduces the keeper ladder DIGIT-FOR-DIGIT: belly
+6.0/+6.6/+4.3, evening −5.8/−4.9/−1.1, overnight +0.8/−0.0/+1.4):
PINNED — `dispatch == min_gen == pmax × availability` in 1.0000 of
positive-capability hours for BOTH blocks in ALL THREE years** (floor > 0 in
0.878/0.913/0.930 of hours; the remainder are shape-zero hours where the
capability itself is 0, so the blocks are fully determined in all 8760
hours; block means 1051–1777 MW). Verdict per the pre-registered criterion:
**M-EVE-1-as-granted is INERT — no B-leg solved.** Owner ruling (in-session,
on this evidence): **adjudicate inert and RE-CHARTER the evening lane** — a
follow-up session re-decomposes the Q1 margin with a PIN-AWARE method
(interior = strictly between the LP's own bounds, `min_gen` from the
bundle's `floors/*.npz` + caps from the `run_year(fleet_only=True)`
reconstruction — never the unit-year p99 proxy that produced the caiso-103
artifact) to find what actually sets Q1 λ one rung below CT entry, and files
a new ask. The floor→$0-bid replacement (motivated by §1's measured
negative-hub curtailment conduct, which the live must-flow floor
contradicts) was offered and NOT taken this session; it remains a candidate
for the re-charter. The evening residual and the hub-separation defect
(model λ 8–40 $ below the measured hubs Q1) remain REAL and OPEN.

## 3. M1 (DA charge-allocation schedule) — built; B-leg gates PRE-REGISTERED

Implementation (committed this session, all default-off):

- Derive: `scripts/data/derive_caiso_charge_allocation.py` →
  `data/raw/reference/caiso-charge-allocation-profile.csv` (per year: 24
  `alloc_share` hod-values + `da_frac`; derived 2023/2024/2025 da_frac =
  0.8399/0.7994/0.7603 — reproduces FINDING-caiso102 §1 exactly; belly
  share 0.699/0.727/0.718). 24+1 measured statistics per year, zero
  residual-fitted values.
- Gate: `ScenarioConfig.caiso_charge_allocation_schedule` (default off,
  CAISO-only; TIER_TAGS tier 1).
- LP: `dispatch._build_storage_alloc_rows` — the ask's per-day
  scheduled-volume variable `S[d]` is eliminated EXACTLY (Fourier–Motzkin:
  `S` is costless and appears only in its 24 floor rows + 1 cap row, so the
  LP always takes the minimal feasible `S[d] = da_frac × Σ_h Chg[h]`),
  leaving `Chg_fleet[h] ≥ alloc_share[hod] × da_frac × Σ_{h'∈d}
  Chg_fleet[h']` — identical feasible region and duals, no layout change.
  One row per day-hour with `alloc_share > 0` (~17 hods × 365 days/yr);
  fleet battery Chg columns only (PS exempt); built as one
  `kron(eye(365), day_block)` (rule 2). Wired
  `run_calibration.run_year → dispatch_kwargs` (the caiso-99 anchor's exact
  seam); `model.storage.caiso_charge_allocation_params` maps year → row
  with latest-year carry (owner sub-ruling).
- Window declaration: `scripts/legitimacy_diagnostics.py` D4_WINDOWS note
  (charge-side rows are not a min_gen floor — the maxgen no-row-by-
  construction precedent); C8 untouched by construction.
- Tests: `tests/test_caiso_charge_allocation.py` (11) — floors hold in a
  trivial 48-h LP, zero-charge day feasible, out-of-support charge bounded
  to `1 − da_frac`, PS excluded, latest-year carry, flag-off byte-identical
  bounds; `tests/test_dispatch.py` + storage suites pass (167).

**Pre-registered B-leg gates (single delta vs the fresh `caiso102_repro_A`,
2023–2025 one bundle, sequential; registered whatever the result — rule 15;
promotion only on no-status-regression, owner call):**

1. **Direction:** demand-weighted belly (hod 10–14) resid falls toward 0 in
   ALL THREE years.
2. **No overshoot:** belly resid does not cross below −1.0 $/MWh in any year
   (the symmetric convention of the overnight band).
3. **Volume-holding (the mechanism's own claim):** annual battery charge
   TWh AND belly-window charge TWh each within ±5 % of the A-leg per year —
   a volume move > 5 % FAILS the mechanism (the caiso-100 volume-gate
   convention).
4. **No collateral regression:** evening resid not deeper (more negative)
   than the A-leg by > 0.5 $/MWh in any year; overnight resid not below
   −1.5 $/MWh in any year.
5. **Rubric:** C1 12/12 holds; C7/C8 PASS; C5a not worse than the A-leg.
6. **Reporting:** allocation-floor binding share (fraction of day-hours at
   the floor) and reallocated MWh (B vs A per-window charge) reported in
   this FINDING from `storage.parquet` — the D-2-equivalent conduct report
   for a charge-side mechanism.

### 3a. B-leg v1 (`caiso104_m1v1_zero_B`): GATE-3 FAIL — total charge collapse to ZERO, root-caused to a composition construction defect; support rule fixed a priori, v2 re-solved

The first B-leg solved with the v1 derived profile and **failed the
pre-registered volume gate catastrophically: battery charge 4.70/8.56/13.02
TWh (A) → 0.000 in ALL THREE years** — the exact caiso-100 volume-collapse
mode the construction claims to exclude. Root cause (adjudicated from the
committed artifacts, no re-solve): the v1 profile carried MEASUREMENT-DUST
shares (1.7e-5 … 2.8e-3) in hods where the caiso-99 envelope's charge cap
is EXACTLY 0 (2023: hod 17/18/21; 2024: hod 18/22; 2025: hod 22/23). A
floor row `Chg_fleet[h] ≥ share_h × da_frac × Σ Chg` with `share_h > 0` in
an `env_cap[h] = 0` hour makes ANY positive daily volume infeasible, so the
LP's only feasible point was zero charge — a **composition defect between
two measured artifacts at their support margins**, not an economic response
(the S-elimination algebra and the volume-holding property are intact; the
trivial-case tests exercise exactly that and pass). The ask's own window
declaration ("evening/late shares are measured ≈ 0, so the floor forces
nothing there BY CONSTRUCTION") presumed a support the v1 artifact did not
literally have.

**Fix (v2 derive, `SUPPORT_MIN_SHARE = 0.005`):** a hod belongs to the
measured DA-allocation support only when it carries ≥ 0.5 % of annual IFM
charge; sub-threshold shares are set to exactly 0 and the profile
renormalized (Σ = 1). Fixed A PRIORI — before any λ effect of a feasible
leg was observed — as a support definition (composition safety), never a
residual response (rule 23/25 posture documented in the derive script).
v2 artifact: 13–14 active hods/yr, zero share>0 ∧ env=0 conflicts, belly
share 0.706/0.730/0.723, da_frac unchanged. Worst-case composition bound:
max feasible daily volume `min_h env_h/(share_h × da_frac)` = 3.3/3.9/4.2
MWh per fleet-MW vs the A-leg's realized mean 2.3/2.6/3.0 — the composed
constraint binds only on extreme days (intended conduct, not a choke). The
v1 bundle is retained (`caiso104_m1v1_zero_B`) and registered as the failed
probe (rule 15); the v2 leg re-solves under the IDENTICAL §3 pre-registered
gates.

### 3b. B-leg v2 (`caiso104_m1_B`): mechanism armed and conduct-faithful, but **REJECTED on the pre-registered gates** — the belly λ does NOT decouple

v2 (support-fixed profile, identical recipe otherwise, same pre-registered
gates), scored vs the same-machine A-leg:

| gate | result |
|---|---|
| 1 — belly resid falls all 3 yrs | **FAIL**: +6.0→+5.9 / +6.6→**+6.6** / +4.3→+4.1 (2024 unchanged; movement ≈ nil everywhere) |
| 2 — no overshoot | PASS (belly resid stays ≥ +4.1) |
| 3 — volume ±5 % | **FAIL 2024**: annual +3.48 % / **+6.10 %** / +3.93 % (belly window +1.8/+2.2/−1.5 % all pass) |
| 4 — evening not >0.5 deeper; overnight ≥ −1.5 | PASS (evening −5.8→−5.8 / −4.9→−5.1 / −1.1→−1.3; overnight +1.0/+0.1/+1.5) |
| 5 — C1/C3c | PASS (C1 grid ~unchanged, CC/CT misses improve ≤0.11 TWh; C3c identical incl. the 2023-01-13 19-day cluster) |
| 6 — conduct report | floors bind in 0.654/0.636/0.504 of charging-day × active-hod slots; reallocation B−A: overnight +0.21/+0.24/+0.29 TWh, pm-shoulder +0.09/+0.12/+0.23, morning −0.20/+0.03/+0.13, belly +0.06/+0.13/−0.14 |

**Verdict: REJECTED probe (both legs registered per rule 15; keeper
`2026-07-19-caiso-102-hourfix` UNCHANGED).** The mechanism did exactly what
it claimed mechanically — the allocation followed the measured DAM bundle
(gate-6 binding shares), volume held within ~4–6 %, nothing collapsed — and
the belly λ still did not move. The decoupling hypothesis fails for a
structural reason visible in the S-elimination algebra: the marginal stored
MWh now prices at the SHAPE-WEIGHTED DAY BUNDLE, but the bundle is itself
~72 % belly, so ~72 % of the battery's arbitrage margin still lands on
belly-hour duals — bundling redistributes the charge-demand pressure only
across the ~28 % non-belly allocation (which is where the small overnight/
pm-shoulder λ effects and the +3.5–6 % volume rise went). A conduct-correct
allocation cannot remove a price effect that comes from the VOLUME being
priced at the margin at all.

**Lane implication (the belly re-charter's starting point):** the belly
+6/+6.6/+4 residual has now survived BOTH structural correction families
the measured conduct supports — the marginal-cost family (caiso-100/101
adder, volume-refuted) and the allocation family (this leg, λ-inert). What
remains is the third term of the identity: the DEMAND-side price the LP
pays for charge — i.e. the belly λ is propped not by WHEN the fleet charges
(allocation) nor by WHAT the charge costs (adder), but by the LP's
requirement that the marginal charged MWh be arbitrage-profitable at all —
reality's DA-cleared charge is a PRICE-TAKING schedule whose day-ahead
clearing price is NOT the RT belly λ the backcast scores against (the
measured DA-vs-RT belly wedge, FINDING-caiso102 §3). The re-charter should
measure that wedge directly (charge-weighted DA λ vs RT λ in model-charge
hours) before proposing any further mechanism.

## 4. M-EVE-1 B-leg gates (CONTINGENT on the §2 pin-check failing)

Only if the firm blocks are NOT pinned on the fresh A-leg: gate
`caiso_firm_import_selfschedule` semantics change to the $0-bid price-taker
(per §1), single delta vs `caiso102_repro_A`, 2023–2025 one bundle, with the
ask's §3 gates: overnight resid ≥ −1.5 every year; evening λ must not cross
above actual (no overshoot); evening import volume must not exceed the
measured aligned evening TWh by more than the current under-shoot magnitude;
C1 12/12, C7/C8 PASS, C3c unchanged-or-toward-actual, C5a no regression.
If the pin holds, NO M-EVE-1 leg solves this session (§2 adjudication) and
the corrected evening diagnosis + the floor→bid re-charter question go to
the owner.

## 5. DAM-outage intake (owner-directed lane) — opened

`scripts/data/fetch_caiso_dam_outages.py` (NEW): CAISO's daily Curtailed and
Non-Operational Generator prior-trade-date reports (unit-level OUTAGE MRID /
RESOURCE ID / FORCED-PLANNED / start-end / CURTAILMENT MW / PMAX / NQC;
sheet `PREV_DAY_OUTAGES`), one xlsx per trade date 2023-01-01..2025-12-31,
fetched to `data/raw/caiso-dam-outages/daily/` (resumable; missing days
recorded — coverage gaps keep the CAMPD fallback per the owner directive;
spot-checked 5/6 probe dates available, 2024-12-31 is a real gap). The
published schedule is the rule-14 measured instrument; the CAMPD windows
(`campd-unit-outages-CAISO.csv`) remain the fallback for uncovered
units/periods. Remaining lane work (curation schema, RESOURCE ID → ORIS
crosswalk, loader precedence, single-delta A/B) proceeds as session capacity
allows; anything unfinished is handed off with the fetched corpus.

## 6. Issue #2546 (the $5 battery_dispatch_adder fallback)

Owner delegated the disposition to this session's recommendation.
**Recommendation (adopted): DEFER as-is this session** — the literal is
honestly recorded since caiso-101, and every leg this session compares
against a baseline that must stay byte-comparable to the keeper (deleting
the fallback would fold an unrelated byte-delta into every A/B). Follow-up
(dedicated session): DELETE the literal (rule 25 — deleted means deleted),
migrating nothing, with a re-gated CAISO baseline solved in the same session
that deletes it.
