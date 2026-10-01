# PRECHECK — caiso-165: CAISO DLAP component intake + intra-SP15 measurement

**Session** caiso-165 · **Date** 2026-08-04 · **Branch**
`claude/caiso-dlap-intake-sp15-9yvs1v` · **Base** `d7363b0e`

**Incumbent CAISO keeper** `2026-08-04-caiso164-zonal-loss-surface`
(CALIBRATED-WITH-CAVEATS; 2 owner-ledgered caveats, 0 FAILs). CAISO has **no
failing criterion**, so this session does not chase a residual — it attacks a
**data blocker**.

**Matrix rows touched** `zonal_loss_surface` (CAISO cell `K`, unchanged unless
Phase 3 Arm A promotes) and, if armed, a new intra-SP15 row.

> **This document is pushed BEFORE the Phase 2 probe is run on the intaken data
> and BEFORE any solve.** Its §4 verdict rule and §5 rule-14 disposition are
> stated ahead of the numbers precisely so neither can be chosen after them.

---

## 1. Why this lane

caiso-164 §6 filed a data blocker on an **inference**. It measured that
80–87 % of the NP15−ZP26 basis is CONGESTION, that the model's miss is
frequency-and-direction rather than magnitude (0 separated hours in the top
decile of measured |dMCC|, across the whole lag sweep), and it *attributed*
that to an **intra-SP15** corridor: `LA_BASIN` carries 77–83 TWh of load at a
0.11–0.12 belly renewable/load ratio and absorbs the entire `ZP26 + SP15_rest`
belly surplus through a 12,008 MW one-way link that never binds, so no surplus
reaches Path 15.

That attribution was assembled from **prices and energy balances**. It has
never been measured directly, and it *could not* have been: the committed CAISO
LMP record carries only the three `TH_*_GEN-APND` **generation** hubs, and an
intra-SP15 corridor is structurally invisible in a hub basis with only one
southern hub in it.

CAISO's own feed carries the missing object. `DLAP_PGAE-APND`, `DLAP_SCE-APND`,
`DLAP_SDGE-APND` and `DLAP_VEA-APND` — **load** aggregation points, priced
where load is withdrawn — are confirmed present in the committed nodal
`DAM_LMP_GRP` zips and are served by `PRC_LMP` for every in-retention trade
date.

**This session does not assume caiso-164 was right.** §4 pre-registers a
falsification rule with the same standing as its confirmation rule. A
falsified attribution is a valuable outcome and will be written back into the
finding, the queue and the matrix cell.

---

## 2. Phase 1 — intake (additive; rule 22 in-window)

Extend `scripts/data/fetch_caiso_oasis.py` with the four DLAPs and fetch
`PRC_LMP` DAM (version 12) for **2023, 2024, 2025 only**. The holdout spend
freeze is ACTIVE; no year outside the train window is fetched, read, scored or
registered.

### 2.1 The retention boundary, re-measured

`PRC_LMP` retention moves forward with the calendar. The fetcher's docstring
recorded **2023-04-19** (binary-searched 2026-07-31). Re-binary-searched
**2026-08-04**: the boundary has moved to **~2023-04-22**, and a follow-up
day-level check showed 2023-04-22 and 2023-04-23 themselves already gone, i.e.
**~2023-04-24** in practice — it slid measurably *during this session*.

The boundary is a property of the **report, not the node**:
`TH_SP15_GEN-APND` and `DLAP_SCE-APND` both fail at 2023-04-19 and both succeed
after it. So this is not a DLAP limitation and it is not worked around.

### 2.2 Partial-year policy — declared here, not after the fact

**2023 will be PARTIAL** (~8.3 of 12 months). This is not silently accepted and
it is not backfilled by fetching an out-of-window year. The route to aged-out
history is a hand-downloaded GRP bulk zip (`fold_caiso_oasis_grp_zips.py`),
which is an owner action, not a fetch task; the 22 `DAM_LMP_GRP` zips already
in `data/raw` cover 22 individual days of Jan-2023 only, not a scoreable span.

`derive_caiso_loss_surface.py`'s `MIN_HOURS_PER_YEAR = 8000` guard exists
exactly to reject a partial year, and it stays. The declared policy is a
**per-(zone, year, month) coverage rule**, which the surface schema already
supports because it carries `interpolated` per row:

> A `(zone, year, month)` cell takes its **own measured DLAP** deviation iff
> that DLAP printed in at least `MIN_HOURS_PER_YEAR / 8760` (= 0.9132) of that
> month's hours. Otherwise the zone falls back to the `TH_SP15_GEN-APND`
> deviation for that month with `interpolated=True`, exactly as today.

**Zero new free parameters**: the monthly threshold is the *existing frozen*
annual guard expressed as a ratio, not a new number (rule 5 `[R-NO-MAGIC]`,
rule 23 `[R-FROZEN-DERIVE]`). It regenerates automatically as retention moves,
and it degrades to today's behaviour where data is absent. Expected outcome:
2023 months Jan–Apr interpolated, May–Dec measured; 2024 and 2025 fully
measured.

The three zones carrying caiso-164's quantity under test — NP15, ZP26,
SP15_rest — are **unaffected**: they keep their own measured `TH_*_GEN` hubs
for all 36 month-cells in every arm.

---

## 3. Phase 2 — measure, no LP. **This is the deliverable even if Phase 3
never runs.**

`scripts/probes/caiso165_intra_sp15_decomp.py`, reading committed artifacts
only. Answers, from CAISO's own `MCE / MCC / MCL / MGHG` decomposition:

* **(a)** the measured `DLAP_SCE − TH_SP15_GEN` basis, split into CONGESTION
  (`dMCC`) and LOSS (`dMCL`);
* **(b)** in the solar-belly hours (Pacific 09–16 — caiso-164's own window,
  carried over unchanged) does the real SCE load pocket separate from the SP15
  generation hub, by how much, in how many hours, in which direction;
* **(c)** the same for `DLAP_SDGE − TH_SP15_GEN`, the post-SONGS Path-44
  pocket.

Context corridors (`SCE−ZP26`, `SCE−NP15`, `PGAE−NP15`, `SDGE−SCE`, plus
caiso-164's `NP15−ZP26` recomputed on the same code path) are measured too, so
that a **null** result LOCATES the congestion rather than only ruling this
corridor out.

Identity guards run first and are reported: MCE must be one system reference
across **all** nodes including the DLAPs, and LMP must reconstruct from its
components. If MCE is not uniform once DLAPs are included, the decomposition is
not usable as published and that is reported rather than averaged over.

---

## 4. THE PRE-REGISTERED VERDICT RULE — stated before the numbers

Evaluated on the **belly window** for the two attribution corridors
(`SCE_pocket−SP15_gen`, `SDGE_pocket−SP15_gen`), on the **congestion component
only** (`dMCC`), per year. `TOL = $0.01` separation threshold, the caiso-164
value, so both probes read on one scale.

| verdict | rule |
|---|---|
| **CONFIRMED** | belly `|dMCC|` separation ≥ **50 %** of hours **AND** mean belly `|dMCC|` ≥ **$1.00/MWh** **AND** ≥ **60 %** of separated belly hours run **pocket-dearer** |
| **FALSIFIED** | belly separation < **20 %** of hours **OR** mean belly `|dMCC|` < **$0.25/MWh** |
| **PARTIAL** | anything between — reported as inconclusive, **never rounded up** |

**Why these thresholds.** The attribution requires the intra-SP15 corridor to
*bind* in the belly. A binding corridor in a nodal market shows a nonzero
congestion component in the hours it binds, and an import-constrained load
pocket must price **above** the generation hub feeding it — hence the direction
clause, which is the part a magnitude-only test would miss (the caiso-164 §9
standing lesson 2: "too small" and "never, in the wrong direction" are
different diagnoses). The $1.00 confirm floor is set against the measured
NP15−ZP26 `dMCC` of $4.7–7.5/MWh that this corridor is alleged to be diverting:
a corridor carrying less than ~20 % of that is not where that basis went.

**Consequences, both directions, committed now:**

* **CONFIRMED** → caiso-164 §6's attribution stands, the blocker becomes a
  chartered lane, and Phase 3 may proceed.
* **FALSIFIED** → caiso-164 §6 is **corrected** in
  `FINDING-caiso164-zonal-loss-surface-2026-08-04.md`, in the CAISO lever queue
  (§5.2) and in the `zonal_loss_surface` matrix cell's note. Arm B is not armed
  under any circumstance. Arm A is judged **on its own rule-14 merits**, which
  do not depend on this verdict (§5).
* **PARTIAL** → recorded as inconclusive; Arm B is not armed; Arm A proceeds on
  its own merits.

---

## 5. Phase 3 — the two arms, and the rule-14 disposition **stated before the
result**

### 5.1 ARM A — five measured zones (recommended, rule-13-clean)

Re-derive `CAISO_loss_surface.csv` with `LA_BASIN` and `SDGE` carrying their
**own measured** `dev_z` instead of inheriting the SP15 generation hub's. Same
frozen estimator (`dev_z,m = Σ MCL_z,t / Σ MCE_t`), same schema, **zero free
parameters**, no residual consulted. Closes `FINDING-caiso164` §7 caveat 2.

**The crosswalk, and whether it is an identity or a reconciliation — declared
now:**

| model zone | DLAP | disposition |
|---|---|---|
| `SDGE` | `DLAP_SDGE-APND` | **near-identity.** SDG&E's service territory *is* the model's San Diego pocket behind Path 44 / SWPL. |
| `LA_BASIN` | `DLAP_SCE-APND` | **RECONCILIATION, not identity.** SCE's territory covers the LA basin *and* much of the desert/Kern belt the model assigns to `SP15_rest`, so `DLAP_SCE` is a load-weighted mix dominated by — but not coincident with — the model zone. |
| `NP15`, `ZP26`, `SP15_rest` | *unchanged* | keep their own measured `TH_*_GEN` hubs. `DLAP_PGAE` is **deliberately not** substituted for NP15 or ZP26: it straddles both, so using it would replace two measured values with one blended one — a downgrade, not an upgrade. |

**Rule 14 `[R-ACCURATE]` disposition, committed before the result:** both
substitutions are **measured-over-reconciled upgrades and are kept regardless
of what they do to the backcast.** The status quo for these two zones is not a
rival measurement — it is the *generation* hub's deviation, weighted to where
power injects (the desert belt), standing in for a *load* pocket at the other
end of the corridor. A DLAP is the right kind of object for a load zone even
where its boundary is imperfect, and rule 14's misalignment clause explicitly
prefers a **reconciled version of the real data** over a stand-in. If the
re-derived surface makes the backcast worse, that is a **discovered bug
elsewhere**, not grounds to revert (rules 1 / 14). It will be reported as such.

**Acceptance gate, strengthened rather than left blind.** The derive's
`--acceptance` mode currently benchmarks only `NP15↔ZP26` and
`NP15↔SP15_rest` — neither of which Arm A changes, so as written the gate could
not see the new zones at all. Arm A therefore **adds** `NP15↔LA_BASIN` and
`NP15↔SDGE` to `ACCEPTANCE_PAIRS`. Every pair-year must stay in the
`[0.5×, 1.5×]` miso-76 B1 band. **A new zone failing the band is a
stop-the-line**, not a caveat.

### 5.2 ARM B — an intra-SP15 transfer limit. **Not armed in this session
unless a published identification is found.**

A limit whose value is chosen so the model reproduces the observed congestion
frequency or basis is an **OUTCOME PIN** and is forbidden (rule 13
`[R-MEASURED]`, rules 5 / 21 / 24). Arm B is admissible **only** from a
published physical limit — a CAISO LCT / LCR local-area import capability, a
published path rating, or an ATC-style construction off measured directed flows
— and **never** from the price residual.

**Declared now:** if no such published limit is found in `data/raw` or in
CAISO's published record, Arm B is **not approximated**. The remaining blocker
is filed with the measurement attached and the session stops there. This is
pre-committed so that a CONFIRMED Phase 2 cannot be used to justify reaching
for a fitted limit.

---

## 6. If a solve happens — discipline

* **No tuning clause.** No parameter is swept, blended or fitted. The only
  input that changes between arms is the loss-surface CSV's `LA_BASIN` /
  `SDGE` rows, produced by the frozen estimator from newly-intaken measured
  data.
* **Pre-solve liveness on a PHYSICAL observable, never prices** — the standing
  caiso-162/163/164 lesson. Liveness is asserted on **flows** on the
  `SP15_rest ↔ LA_BASIN` and `SP15_rest ↔ SDGE` links, plus the link-count
  split check; a `run_config.json` recording a flag as armed is not evidence
  the LP saw it.
* **A/B against a same-HEAD flag-off control** via
  `scripts/replay_keeper.py --set <field>=<bool> --out-dir <arm>`.
* **Rule 16:** `--year 2023 2024 2025` in ONE invocation, ONE bundle per arm.
  **Rule 12:** years sequential within a run.
* **Arms run SEQUENTIALLY, never concurrently** — caiso-164 §5.1 lost a control
  arm to an OOM kill (anon-rss 8.85 GB) with two per-plant CAISO replays
  resident on a 15 GB box. In-session only, never a GitHub Actions runner.
* **Attestation** modelled on `scripts/gen_caiso164_attestation.py`, carrying
  its shape verbatim: assert the intended delta against **both** the incumbent
  and the same-HEAD control; assert every `ScenarioConfig` field new since the
  incumbent holds its default (closing the inherited-schema-drift hole); check
  `mode == "backcast"`; assert the holdout window on both bundles **and** the
  derived surface; verify liveness on flows; FAIL if the control never
  exercised the mechanism; and enforce an **adversarial ceiling** that fails the
  arm for OVER-performing.
* **Inherited owner default flips** (`retirement_rule=pipeline` D-1,
  `entry_rate_limits` + `entry_commissioning_lag` D-2,
  `net_cone_forward_escalation=reindex_gross` D-3a) are **merged owner
  decisions, not this session's choices and not tuning**. Disclosed, and
  asserted on both admissibility grounds: forecast-gated and unreachable at
  `mode="backcast"`, and identical across both arms.
* **Rule 15 / 28b:** every completed run registered (keeper *or* rejected
  probe), with `legitimacy_diagnostics.json` generated into each bundle
  **before** registration so C7/C8 score rather than SKIP. Matrix cell +
  evidence citation updated in this same session. Top-15 CAISO retention
  honoured.
* **Rule 22:** CAISO holds no `complete` marker → no `calibration-complete`
  re-key and no marker written. `complete` is an owner act and is not declared
  here.

---

## 7. DO-NOT-REDO honoured

Not re-tested without new evidence: `energy_reserve_coopt` (I, caiso-144,
explicit DO-NOT-SOLVE), `cc_mustrun_per_plant` (R), `wecc_endogenous_node` (R,
caiso-110), `caiso_corridor_export_path` (R, caiso-132),
`caiso_p1_export_sink_seam` (R), `netload_drag_floors` (R). Not re-tested as
keepers: `caiso_zonal_loss_surface` (caiso-164),
`caiso_asymmetric_path_ratings` (caiso-163), `caiso_per_year_import_caps`
(caiso-162). Not reopened: the caiso-141 A2 pumped-storage wall, the
caiso-131/144 C3c routes, the caiso-104 charge-allocation family, the CAISO
matrix census (closed at caiso-161).

**No N–S TOPOLOGY lever is chartered against the congestion residual** —
caiso-164 §0 measured that topology is not where the recoverable component was.
The corridor under test here is **INTRA-SP15**, a different object.
`td_loss_factor` is **not** armed on top of the keeper's loss surface (rule 19
`[R-ONE-MECH]`).

**Standing blockers not touched by this lane:** C3a-2025 (non-public hourly
pumped-storage data) and C3c-2023/24 (the SoCalGas OFO declaration record).
Neither is closable by an adder, haircut or residual-tuned value (rules 1 / 13).
`caiso_gas_floor_frac = 0.80` and the four other armed-but-inert keeper scalars
remain **owner** decisions and are not removed here.
