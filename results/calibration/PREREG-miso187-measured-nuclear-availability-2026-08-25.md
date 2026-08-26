# PREREG miso-187 — the MEASURED-NUCLEAR AVAILABILITY ARM: the second miso-186 §3 candidate, armed under the existing `nuclear_unit_availability` gate

**Session miso-187 (2026-08-25).** Registered **BEFORE any adjudicating
quantity is computed.** Executes the queue head installed by miso-186
(`FINDING-miso186-direction-decomposition-2026-08-25.md` §3/§6, matrix §5.4
stamp miso-186): the MISO measured-nuclear availability layer — the second
candidate that cleared **every** PREREG-miso186 §4 admissibility clause
((i) the smear deviates from the NRC measured record; (ii) an NRC reactor
power state is a physical availability event, rule-13 forward-regenerable;
(iii) `nuclear_unit_availability` is `U` in MISO's shard, not adjudicated;
(iv) the deriver's scalars are frozen, inherited, never re-tuned; (v) static
reach +0.299 GW ≥ 0.25 GW) — and was left unarmed at miso-186 ONLY by the
single-delta selection rule (the status-scope repair's larger 0.480 GW
reach). Target: the C3a-2025 direction/level rubric failure on the NEW
keeper `2026-08-25-miso-186-statusscope` (bundle `miso186_dir_B`),
determination NOT-YET on {C3a-2025 −12.32 %, C1 fuelmix CC_REGULAR 2024
+8.09 vs ±8.00 TWh}, C3c the single ledgered caveat.

**Mechanism-in-kind boundary (named now so rule 26(b) is decidable):** the
arm is the EXISTING gated `ScenarioConfig.nuclear_unit_availability` field
(scenarios.py:9448, default off) — the same per-reactor NRC-daily overlay
PJM (pjm-nuc-1b, owner-ordered), NYISO (nyiso-98), CAISO (caiso-148) and
NEISO (neiso-71) already carry. **No new `ScenarioConfig` field, no new
matrix row** — duty 26(c) is not triggered; MISO's existing cell
`nuclear_unit_availability: U` is adjudicated to the A/B outcome (rule
26(d): MISO's shard only, the sister-ISO verdicts fill nothing here — the
crosswalk, extract and anchor are derived from MISO's own fleet and data).

## 0. What has been looked at, and what has not (the pre-registration boundary)

Before writing this document the session read only:

* **Committed prior findings/preregs and their committed values** —
  `FINDING-miso186-direction-decomposition-2026-08-25.md`,
  `PREREG-miso186-midwest-stack-direction-2026-08-25.md`,
  `PREREG-miso184-south-export-ladder-tail-2026-08-24.md` (the §6 gates
  carried verbatim below), `_miso186_direction_decomposition.json`,
  `_miso186_ab_gates.json`. Every measured statistic quoted below is a prior
  session's committed number, restated not re-derived.
* **Code (mechanics, no measured statistic):**
  `scripts/data/derive_nuclear_availability.py` (the NRC deriver: frozen
  EVENT_RAW_MAX 0.90 / SCALE_CLIP 1.25 / WEDGE_TOL 0.01, the per-month
  fixed-point that reconciles NRC daily timing to the EIA-923 monthly
  anchor, the dropped-month wedge fallback, the `NRC_TO_EIA` crosswalk
  structure and the four sister-ISO entries);
  `scripts/data/derive_nuclear_monthly_cf.py` (the anchor deriver and its
  `--check` mode); `src/market_sim/data/outages.py`
  `nuclear_unit_availability_series` (extract → per-reactor hourly series,
  NaN = uncovered → smear stands);
  `src/market_sim/data/fleet/arrays.py` `_apply_nuclear_availability` (the
  application order: monthly smear → ISO-generic per-reactor overlay →
  dormant zeroing); `src/market_sim/config/constants.py`
  `NUCLEAR_MONTHLY_CF_BY_YEAR` / `NUCLEAR_MONTHLY_CF` / `NUCLEAR_DORMANT_UNTIL`;
  `scripts/replay_keeper.py` (`--set` semantics);
  `scripts/probes/_miso186_ab_gates.py` (the scorer this session re-keys).
* **Identifier facts (not statistics):** the model's MISO nuclear fleet
  listing — unit_id, plant_code, pmax, zone for the 13 reactors (a fleet
  loader enumeration, the same class as miso-186's F-footing fleet count);
  the NRC report `Unit` name strings for those reactors
  (`data/raw/nrc-reactor-status/*.txt` column values, no Power statistic
  read); the matrix shard cell state (`nuclear_unit_availability: U`).
* **One code-path identification, disclosed** (computed before this
  document; it adjudicates NOTHING and no gate hangs on it): which monthly
  layer the keeper's smear actually consumes. `NUCLEAR_MONTHLY_CF_BY_YEAR`
  **carries a "MISO" entry at HEAD** (constants.py:2286, 2023–2025, with its
  own EIA-923 derivation citation), and `_apply_nuclear_availability`
  prefers it; on the frozen 2025 scarce set (months 21×Jun/13×Jul/5×Aug/
  8×Sep) the anchor smear means **0.8972** — exactly the committed 0.897 —
  where the static-pattern × (1−EFORD) alternative would mean 0.912.
  **CORRECTION to the charter/miso-186 §3 sub-clause, disclosed:** the
  sub-claims "no `NUCLEAR_MONTHLY_CF_BY_YEAR["MISO"]` entry" and "the
  static seasonal pattern × (1−EFORD)" are FALSE at HEAD — the anchor
  exists and is the active smear. The structural claim is UNCHANGED and is
  the charter: the smear is uniform across all 13 reactors (no
  `nuclear-availability-MISO.csv`, MISO absent from `NRC_TO_EIA`), so a
  unit-specific outage inside a scarce hour is invisible. Charter step (1)
  therefore becomes a `--check` VERIFICATION of the committed anchor, not a
  new derivation.
* Environment facts: 15 GB RAM / 4 cores; no swap configured yet (the
  miso-169 recipe is applied before any leg runs).

**No NRC Power statistic, no reach number, no gate quantity has been
computed for this session.** The candidate's evidence quoted below
(South 0.954 vs 0.897 → +0.299 GW; Midwest 0.885 vs 0.897 → −0.075 GW;
Callaway 68.9 % / Clinton 77.2 % / Monticello 86.8 %) is miso-186's
committed record, restated.

## 1. The object and the candidate (committed; restated)

New-keeper baselines (miso-186 committed): 2025 scarce set 47 h; RDT
direction **N→S binding 7/47, S→N 0/47, unconstrained 40/47** vs the
measured record **S→N 32/47 any-row (9/47 majority), N→S 0/47**; scarce-mean
South boundary-complex net inflow **N_S^m = +0.682 GW** vs measured
**−2.441 GW**. The standing falsifiable prediction (miso-183, partially
realized at miso-186): a candidate must move the scarce-hour RDT direction
toward the measured record.

The candidate's committed evidence (miso-186 §3, the A_Nuclear drill): on
the NRC scarce-date record the **South** 5-reactor fleet (Waterford 3,
Grand Gulf, River Bend, ANO 1+2 — 5,258.9 MW) ran capacity-weighted
**0.954** where the smear posts 0.897 (static reach **+0.299 GW** of scarce
South supply, clears the §4(v) 0.25 line), while the **Midwest** 8-reactor
fleet ran **0.885** (−0.075 GW — the smear also hides the real concentrated
outages: Callaway 68.9 %, Clinton 77.2 %, Monticello 86.8 %). **Both sides
move the direction the right way**: more real South supply, less real
Midwest supply → less manufactured southward pressure. Because the deriver
reconciles the NRC daily series to the SAME EIA-923 monthly anchor the
smear already consumes, the arm is (in fully-covered, reconciled months) an
energy-preserving REDISTRIBUTION across reactors and days — the mechanism
is timing/location, not a level lever.

A-priori S-5 expectation, declared now (the charter's own words): C3a-2025
may **worsen slightly again** (added South supply lowers prices the model
already under-prices) while the direction improves; the C1 fuelmix
CC_REGULAR 2024 band exceedance (+8.09 vs ±8.00) may move either way (the
overlay redistributes 2024 nuclear too). Both faces are reported at full
magnitude, never traded.

## 2. The work (data first, then the A/B)

1. **Anchor verification (charter step 1, reduced per §0):**
   `derive_nuclear_monthly_cf.py --isos MISO --years 2023 2024 2025 --check`
   must confirm the committed `NUCLEAR_MONTHLY_CF_BY_YEAR["MISO"]` block
   re-derives from EIA-923 exactly. A mismatch is a STOP-and-report (a data
   defect adjudicated on its own, never silently re-tuned — rule 23).
2. **The crosswalk (charter step 2):** add `NRC_TO_EIA["MISO"]` mapping the
   NRC `Unit` names to the model fleet EXACTLY — Clinton (204, 1), Fermi 2
   (1729, 2), Monticello (1922, 1), Prairie Island 1/2 (1925, 1/2), Point
   Beach 1/2 (4046, 1/2), Waterford 3 (4270, 3), Grand Gulf 1 (6072, 1),
   Callaway (6153, 1), River Bend Station 1 (6462, 1), Arkansas Nuclear 1/2
   (8055, 1/2) — with the sister-ISO comment discipline for reactors that
   report to NRC but carry no fleet unit (Palisades — restart era, non-OP in
   the EIA-860 operable vintages the fleet keeps) or carry neither
   (Duane Arnold, retired 2020; no 2023–2025 NRC rows).
3. **The extract (charter step 3):**
   `derive_nuclear_availability.py --iso MISO` over the in-train years
   (NRC raws 2018–2026 already on disk; no new fetch — rule 22, freeze
   ACTIVE, MISO holds NO marker). Commit the extract + crosswalk. Reported
   verbatim, whatever they are: the per-month pool scales, any partial-
   coverage or OFF-ANCHOR dropped months (where the smear stands and the
   candidate's reach shrinks — reported, never patched).
4. **The A/B (§4):** control + arm `replay_keeper` replays of
   `miso186_dir_B` at HEAD.

## 3. Anti-sweep (binding)

The deriver's scalars (EVENT_RAW_MAX 0.90, SCALE_CLIP 1.25, WEDGE_TOL 0.01)
are inherited FROZEN from the sister-ISO deriver — never re-tuned here, on
any result (rule 23). The crosswalk is an identifier mapping, not a tunable.
The extract is consumed as the deriver writes it; no row is edited, no month
re-included after a wedge drop, no reactor excluded because of what a leg
later shows. The hour sets, the miso-183 spread classifier, the `N_S^m`
construction and every gate line below are frozen by this document; no
alternative statistic or threshold may be quoted after seeing a result.
Reported-only quantities never migrate into a gate. A result against
interest is reported at full magnitude. If an input is missing or deficient
the affected step STOPs with the deficiency disclosed — never patched ad
hoc.

## 4. The A/B (PREREG-miso184 §6 gates VERBATIM, re-keyed to the new keeper's committed baselines)

Control and arm are `replay_keeper` replays of `miso186_dir_B` at HEAD, run
SEQUENTIALLY (rule 12 — one plant-level MISO LP at a time on this 15 GB
container, miso-169 memory recipe: 8 GB swapfile,
`MARKET_SIM_HIGHS_THREADS=4`), each the FULL span 2023 2024 2025 in ONE
invocation (rule 16):

```
python3 scripts/replay_keeper.py results/calibration/miso186_dir_B \
  --out-dir results/calibration/miso187_nuc_A \
  --note "miso-187 CONTROL: byte-faithful keeper replay at HEAD (nuclear_unit_availability default off)"
python3 scripts/replay_keeper.py results/calibration/miso186_dir_B \
  --out-dir results/calibration/miso187_nuc_B \
  --set nuclear_unit_availability=true \
  --note "miso-187 ARM: per-reactor NRC-daily nuclear availability (single delta; PREREG-miso187)"
```

Registration ids `2026-08-25-miso-187-control` /
`2026-08-25-miso-187-nucavail` — **BOTH registered whatever the outcome**
(rule 15, full span, rule 16).

* **S-0 CONTROL INERTNESS (ABANDON).** Every scored sidecar of the control
  (`class_hourly`/`system`/`storage`/`reserve_family` × 3 years)
  value-identical to the committed keeper's (`miso186_dir_B`). Anything
  else ⇒ HEAD drift — STOP, report, no arm conclusion (the miso-177 R-0
  discipline).
* **S-1 EXACTNESS (KILL).** The arm's `run_config.json` records exactly the
  single delta `nuclear_unit_availability=true` (control false/absent);
  every other input byte-identical between legs. The flag demonstrably
  acted, witnessed per-reactor from the legs' own solve outputs (frozen
  now): **Callaway (plant 6153)** — the committed record's deepest scarce
  outage (68.9 % vs the 0.897 smear) — has 2025 scarce-mean dispatch LOWER
  in the arm than the control, and the **South 5-reactor aggregate**
  (plants 4270/6072/6462/8055) has 2025 scarce-mean dispatch HIGHER in the
  arm than the control. (Direction-of-change witnesses only; their
  magnitudes are reported, never gated — the structural gates are S-2/S-3.)
* **S-2 DIRECTION (the charter's structural gate).** On the frozen scarce
  mask (from ACTUALS — identical for both legs), the arm's 2025 scarce-hour
  N→S binding count under the miso-183 spread classifier (verbatim: spread =
  P1 `price(MISO-South) − price(MISO-East)`; N→S ≡ spread > +$1; S→N ≡
  spread < −$1; RPE ±$1 dead band) must **FALL below the control's**
  (committed NEW-keeper baseline: **7/47**). Reported alongside, never
  gated: the S→N count (measured record: 32/47 any, 9/47 majority) and the
  full classifier composition, all years.
* **S-3 OUTFLOW (the charter's structural gate).** The arm's 2025
  scarce-mean model South boundary-complex net inflow `N_S^m` — computed
  EXACTLY from each leg's full solve outputs (link `flows` into MISO-South,
  the seam-band net at `MISO_external_South` included, the zonal storage
  term included), verified against the zonal energy balance (residual
  < 1 MW) — must move from the control's value (committed NEW-keeper
  baseline: **+0.682 GW**) **toward the measured −2.441 GW by ≥ 0.1 GW**.
* **THE CHARTER KILL.** An arm that improves C3a-2025 while BOTH S-2 and
  S-3 fail is a level adder wearing a repair's name → REJECTED regardless
  of every other number (rule 1's enforcement).
* **S-4 CONDUCT (KILL).** Zero D-4 conduct failures on the arm's
  regenerated `legitimacy_diagnostics.json`, zero NEW vs the control; C8
  PASS all years.
* **S-5 FULL-MAGNITUDE SCORING (report + escalation, NOT a kill).** The
  complete verdict scorer on both legs; C3a all years, C1/C2/C3b/C3c, every
  regression reported at full magnitude. Movements outside the commercial
  band (±10 %) in 2023/2024, or any criterion PASS→FAIL flip, fire the
  **owner-escalation path**, never an auto-reject and never an auto-keeper —
  resolved here by the STANDING owner posture directive (twice in writing at
  miso-184/186, re-affirmed in this session's charter: *"if structural
  integrity improves but gates regress that may still be a keeper — expect
  C3a-2025 to WORSEN slightly again (added South supply) while the
  direction improves; report both faces, never trade a fitted level for
  it"*). A promotion additionally requires the standing leave-one-year-out
  note within 2023–2025 (rules 20/22 — the mechanism carries zero fitted
  scalars and its identification, the NRC daily record reconciled to the
  EIA-923 anchor, is year-independent: no parameter is identified against
  any year's outcome) and the rule-21 DOF ledger entry (MEASURED, zero
  lineage solves).

**Promotion rule (fixed now).** The arm is promoted keeper **iff BOTH
structural gates (S-2 AND S-3) pass, S-1/S-4 are clean, and the charter
kill is silent** — the S-5 face is then disclosed at full magnitude under
the standing posture directive, never claimed as improvement. One
structural gate passing and one failing (or any pattern satisfying no row)
is a MIXED outcome: registered, cell adjudicated from the evidence
(`I` if the arm demonstrably acted yet moved neither structural gate, `R`
otherwise), keeper UNCHANGED, owner escalation with both faces. Both
structural gates failing ⇒ NOT promoted, cell `R` (or `I` per the same
line), keeper unchanged. Registration + matrix stamp + calibration-log
entry in-session regardless of outcome; a promotion re-stamps
`keepers/MISO.json`, rebuilds `status/MISO.js`, and fires the
calibration-keeper-auditor. MISO holds no `complete`/`final` marker, so no
rule-22 D-5(b) re-key is owed.

## 5. Instrument

`scripts/probes/_miso187_ab_gates.py` → 
`results/calibration/_miso187_ab_gates.json` — the miso-186 scorer re-keyed
(KEEPER/CONTROL/ARM paths, the S-1 witness above, baselines 7/47 and
+0.682), committed **after this PREREG and before it is run** (the miso-184
order). If promoted, `scripts/gen_miso187_attestation.py` (the miso-186
attestation generator re-keyed) writes the keeper attestation with the new
MEASURED ledger entry; the control stays unattested (a control, never a
keeper candidate — the miso-178 §11 phenomenon, disclosed in advance).

## 6. DO-NOT-REDO and governance

**DO-NOT-REDO (miso-185 §9 + miso-186 carried in full):** the offer family
at BOTH grains (miso-179 `R` / miso-180 `I`; the `miso_offer_spread_anchored`
unspent re-open clause untouched — this session may not be cited as graft
evidence); `miso_south_firm_export_block` `G` (re-open ONLY on
contract-grain term×MW or a by-counterparty contract-path series);
`miso_south_export_ladder_rt_tail` `R`; `miso_seam_coincident_envelope` `R`;
`measured_interface_limits` `R`; `m2m_seam_entitlement_cap` `G`;
`import_shape_lever` `G`; `internal_congestion_split` `G`;
`zonal_loss_surface` `R`; `measured_offer_surface` `R`;
`gas_hub_basis_overlay` `R`; `ramp_envelopes` `I`;
`dam_availability_rebasis` `R`; the ordc/reserve and dispersion families;
reserve-requirement raises (miso-178 §8). The miso-183 basis question is
CLOSED (V-TRADE); `ba_code="SOCO"` stays a forecast-lane rule-14 item; the
import-side ladder tail (miso-184 §4) is NAMED, report-only.
`unit_outage_fleet_status_scope` is the KEEPER (`K`) — not re-tested; its
maxgen/layup scope boundary is a documented boundary, extended only on
adjudicated evidence. Standing report-only items (owner charter needed, not
this session's levers): the C1 fuelmix CC_REGULAR band exceedance; the
MISO-Illinois $8.22/MMBtu scarce delivered-gas observation; the D-4 posture
question with the ~1.3 GW scarce-export model-class concession.

**Governance.** Rule 22 `[R-HOLDOUT]`: 2023/2024/2025 ONLY; freeze ACTIVE;
MISO holds NO marker (fail-closed); no new fetch of out-of-train market
dates (the NRC status raws are availability events, in-train 2023–2025
already on disk). Rule 1 `[R-STRUCT]`: the charter kill enforces it. Rule
12 `[R-PARALLEL]`: years sequential within each leg; legs sequential; the
miso-169 memory recipe. Rules 13/14: the §1 candidate cleared the
PREREG-miso186 §4 admissibility clauses at miso-186 (committed); the arm
prefers the measured per-reactor record over the smear estimate. Rule 23
`[R-FROZEN-DERIVE]`: frozen deriver scalars inherited; the anchor is
verified with `--check`, never re-tuned. Rule 24: the arm is the existing
registered `nuclear_unit_availability` field, recorded in `run_config.json`.
Rule 26: §5.4 queue stamp + calibration-log entry + MISO shard cell U→verdict
in-session, negative outcomes included; `check_mechanism_matrix.py` before
every matrix push. Rule 27 `[R-PUSH]`: exact on-disk bytes; every pushed
blob ≥300 lines verified on both transports; on HTTP 408/500 set
`git config http.version HTTP/1.1` and retry with backoff. No new
`.github/workflows`. THE OWNER MERGES; no PR unless asked.
