# PREREG miso-177 — the measured-rho A/B: control/arm with kills fixed BEFORE any solve

**Session miso-177, 2026-08-22.** Keeper `2026-08-22-miso-175-hourkey`
(bundle `miso175_hourkey`; determination NOT-YET on C3a-2025 (−11.80 %)
alone, C3c the single ledgered caveat, C6 PASS, C8 PASS all years, zero D-4
conduct failures). This document pre-registers, with thresholds fixed BEFORE
any LP is solved, the single-delta A/B for the RHO_CLIP escalation's MISO
re-solve (`miso_online_rho_no_floor`, default off — implementation commit
`6fd4947`, pushed before this document).

Order of operations, auditable in the commit history: the identification
FINDING (`FINDING-miso177-rho-clip-floor-identification-2026-08-22.md`,
pushed at `95050c9` — the 0.5 floor REFUTED on the repo record and on MISO's
primary record) → the gated implementation (`6fd4947`; OFF path proven
inert: 67/67 cache-key pin tests, pinned default key unmoved; 8 seam unit
tests; model suite 1191 green) → the ENGINE-FROZEN instrument
(`scripts/probes/_miso177_rho_instrument.py` →
`_miso177_rho_instrument.json`, this commit) → the A/B scorer
(`scripts/probes/_miso177_rho_ab.py`, this commit, BEFORE any result
exists) → **this document, committed** → control solve → arm solve → the
gates (§4) → the adjudication (§5) → owner presentation (§6).

---

## 1. The object

The keeper's armed `miso_reserve_online_gated` draws the nested market-wide
Reg+Spin family on gated per-pool columns carrying
`R − online_rho·ΣP(members) ≤ 0` **in addition to** the pool's joint P+R
headroom row and the pool-shared 10-minute ramp row. The solved coefficient
is the RHO_CLIP 0.5 floor; the committed CAMPD measurement is
**0.17644175978069962** (5,276,357 online unit-hours, 93.07 % coverage).
The floor is REFUTED as a citable parameter (the FINDING); the arm consumes
the measurement (cited 4.0 ceiling kept), a **2.834× tightening of every
pool's coupling row**.

## 2. The mechanism, and its DOF answer

`ScenarioConfig.miso_online_rho_no_floor` (default off; registered
drop-at-default per the nyiso-119 discipline; armed key hashes distinctly).
Armed, `_identified_online_rho` returns
`OnlineReserveRho.rho_used_no_floor = min(rho_measured, 4.0)` for the MISO
gated branch only; hard-errors if the artifact is absent. **Zero new numeric
parameters** — a boolean selector between two treatments of one committed
measured input; the DOF ledger gains a selector entry with `n_scalars 0`,
`n_residual` unchanged. The shared `RHO_CLIP` band, the legacy `pmin` path,
and every NYISO call site are byte-untouched at any polarity (rule 25); the
band ruling itself remains the owner's nyiso-145 decision card.

## 3. The engine-frozen instrument (committed WITH this prereg, before any solve)

`_miso177_rho_instrument.json` freezes from the production seam and the
keeper's own committed sidecars:

* **I-1 coefficients**: control consumes **0.5** (the floor), arm consumes
  **0.17644175978069962** (the measurement); artifact sha256
  fixed in the record; tightening factor 2.8338.
* **I-2 static binding surface**: hours where `rho·ΣP_elig < requirement`
  on the keeper's committed dispatch — **0 / 0 / 0 at BOTH rho values in
  all three years** (ΣP_elig min 24.6/25.6/23.7 GW vs requirement max
  2.11/2.43/2.58 GW). The market-wide AGGREGATE coupling ceiling is slack
  everywhere even at the measured value.

**The honest expected-magnitude reading, declared before the solve:** the
keeper's regspin family binds 5 / 6 / 10 hours (duals to $98/$84/$84) through
POOL-GRAIN interactions (per-pool coupling × joint headroom × ramp ×
synchronisation economics), never through the aggregate ceiling. The arm
tightens every pool's coupling row 2.834× but adds no aggregate-forced
shortage, so its reach is pool-grain re-shuffling and opportunity-cost
re-pricing in and near those 5/6/10 hours. **Expected effect: SMALL and
concentrated; near-inertness is a live outcome** and maps to verdict `I`
(§5), not to failure. Direction is EXPECTED toward more regspin binding and
higher DA-foreseen scarce-hour prices, but the miso-169 record documents a
REAL negative-sign interaction (the 2023 Midwest sub-regional $200 family
relieved by regspin-driven re-dispatch, foreseen-hour mean −$49), so **price
direction is disclosed and reported in full, NOT gated** — a kill on
surprising-but-real economics would violate rule 1.

## 4. The A/B and the gates, with kills fixed NOW

Control and arm are `replay_keeper` replays of the keeper at HEAD, run
SEQUENTIALLY (rule 12 — one plant-level MISO LP at a time on this 15 GB
container), each the FULL span 2023 2024 2025 in ONE invocation (rule 16),
under the miso-169 memory recipe (pinned stack matching the bundle's
recorded environment; `MARKET_SIM_HIGHS_THREADS=4`; 8 GB swapfile):

```
python3 scripts/replay_keeper.py results/calibration/miso175_hourkey \
  --out-dir results/calibration/miso177_rho_A \
  --note "miso-177 CONTROL: byte-faithful keeper replay at HEAD (miso_online_rho_no_floor at default off)"
python3 scripts/replay_keeper.py results/calibration/miso175_hourkey \
  --out-dir results/calibration/miso177_rho_B \
  --set miso_online_rho_no_floor=true \
  --note "miso-177 ARM: measured online_rho 0.17644175978069962 consumed without the refuted 0.5 floor (single delta)"
```

Scorer: `scripts/probes/_miso177_rho_ab.py` →
`results/calibration/_miso177_rho_ab.json` (committed before either result
exists). Registration ids: `2026-08-22-miso-177-control` /
`2026-08-22-miso-177-rho-measured` (BOTH registered whatever the outcome,
rule 15, full span, rule 16).

* **R-0 CONTROL INERTNESS (ABANDON).** Every one of the control's 12 scored
  sidecars (`class_hourly`/`system`/`storage`/`reserve_family` × 3 years)
  is value-identical to the committed keeper's (numeric max|diff| = 0,
  identical row sets). Anything else ⇒ HEAD drift or a non-inert default —
  STOP, report, solve no arm conclusion.
* **R-1 COEFFICIENT EXACTNESS (KILL).** (a) The artifact's sha256 equals the
  instrument's frozen digest; (b) the arm's `run_config.json` records
  `miso_online_rho_no_floor: true` and the control's records it false or
  absent; (c) at scoring time the production seam yields 0.17644175978069962
  under the arm polarity and 0.5 under the control polarity.
* **R-2 LIVENESS (verdict mapping, not a kill).** LIVE iff ≥ 50 P1
  zone-hour price cells with |arm − control| > 0.001 $/MWh summed over the
  three years (of 3 × 61,320). Fewer ⇒ the treatment is measured INERT on
  this keeper: verdict `I`, keeper unchanged, and the owner presentation
  becomes "floor refuted AND its removal is inert here — cite-and-delete is
  a zero-cost cleanup at the MISO seam."
* **R-3 CONDUCT (KILL).** The arm's regenerated
  `legitimacy_diagnostics.json` carries ZERO D-4 conduct failures (the
  miso-173/175 headline preserved) and zero NEW D-4 rows vs the regenerated
  control.
* **R-4 C8 (KILL).** C8 PASS in all three years on the arm
  (grounded-above-budget is an allowed PASS form).
* **R-5 RECORD FLIPS (KILL).** Over the verdict scorer's 67 records, ZERO
  PASS → non-PASS flips, arm vs the committed keeper.
* **R-6 AGAINST-INTEREST (KILL).** C3a-2023 stays within ±3.0 % (keeper
  +1.230 %) AND C3a-2024 stays within ±10 % with an adverse (more-negative)
  move ≤ 1.5 pp (keeper −4.064 %). C3a-2025 is reported at full magnitude
  and NOT gated (§5 honesty clause).
* **R-7 OVER-REACH (KILL).** |annual demand-weighted P1 price Δ| ≤ 2.0 % in
  every year — a reserve-supply coefficient moving annual prices beyond
  that is doing something the §3 instrument says it cannot physically be
  doing, i.e. mis-wired.

Reported in full, gated by nothing: per-year regspin dual-positive hour
counts and dual levels both arms; load-weighted price deltas annual /
summer / control-binding-hours / DA-foreseen vs RT-only (the miso-169 K-5
cut); the Midwest sub-regional family's binding interaction; C3a-2025 at
full magnitude.

## 5. Verdict mapping, fixed now

* **R-0 fires** → ABANDONED-AT-CONTROL: report, register nothing as arm
  evidence, escalate the drift.
* **Any of R-1/R-3/R-4/R-5/R-6/R-7 fires** → arm REJECTED-AS-ARMED with the
  firing gate named; both runs registered; matrix cell evidence appended;
  keeper unchanged. The FINDING's refutation of the floor STANDS regardless
  (identification and arm-viability are separate facts).
* **All kills silent + R-2 LIVE** → the arm is the KEEPER-CANDIDATE on
  rules 5/14/21 (a measured coefficient replacing a refuted guardrail in an
  armed keeper mechanism), **presented to the owner WITHOUT
  self-promotion**: this is the six-cycle-old owner escalation and the
  ruling is theirs (charter clause). No keeper-shard edit, no re-key, no
  promotion this session unless the owner rules.
* **All kills silent + R-2 INERT** → verdict `I` recorded with the record;
  keeper unchanged; owner presented with the zero-cost-cleanup framing.

**Honesty clause (C3a-2025).** C3a-2025 is CLOSED end-to-end as a
model-class limit (miso-163 owner ruling; FINDING-miso171 §6). This A/B is a
rule-5/14/21 coefficient-identification repair and is argued on that ground
ALONE; any C3a-2025 movement in either direction is disclosed, never
claimed, and no number this A/B produces may be quoted as scarcity progress.

## 6. Governance

* Rule 22: 2023–2025 only; MISO holds neither `complete` nor `final`; the
  holdout spend freeze is untouched; no marker re-key owed. LOO is vacuous:
  zero free parameters — the consumed value is the committed pooled
  measurement, and the flag is a selector (miso-172/173/175 precedent).
* Rule 19: no new mechanism, floor, or stacked channel — the treatment
  changes the identified value of the ONE existing coefficient of the ONE
  existing gated mechanism. Rule 26: nothing deleted; the banded default
  remains for replay fidelity of every pre-existing bundle.
* Rule 25: MISO-only by construction (the flag is read solely inside
  `_miso_design`'s gated branch); the NYISO decision card and PJM's path-A
  `needs-citation` row are their own lanes' objects.
* Abandon-before-solve conditions: available RAM < 13 GB at solve start;
  artifact sha256 mismatch vs the instrument; R-0.
