# PRECHECK — caiso-166: five MEASURED CAISO loss zones (Arm A)

**Session** caiso-166 · **Date** 2026-08-04 · **Branch**
`claude/caiso166-measured-loss-zones-uwsq1n` · **Base** `3bc37ce2`

**Incumbent CAISO keeper** `2026-08-04-caiso164-zonal-loss-surface`
(CALIBRATED-WITH-CAVEATS; 2 owner-ledgered caveats, 0 FAILs). CAISO has **no
failing criterion**. This session does **not** chase a residual — it executes
the rule-14 `[R-ACCURATE]` measured-over-reconciled upgrade chartered by
`PRECHECK-caiso165-dlap-intake-intra-sp15-2026-08-04.md` §5.1, closing
`FINDING-caiso164-zonal-loss-surface-2026-08-04.md` §7 caveat 2.

**Matrix row touched** `zonal_loss_surface` (CAISO cell `K`).

> **This document is pushed BEFORE any solve.** Its §5 homogeneity declaration,
> §6 verdict rule and §7 rule-14 disposition are stated ahead of the LP numbers
> precisely so none of them can be chosen after them. The §4 acceptance figures
> are a **pre-solve DATA gate on measured inputs** — no model output, residual
> or scoring target is read anywhere in this document.

---

## 1. What changes, and what does not

`scripts/data/derive_caiso_loss_surface.py` re-derives
`data/raw/iso-specific-transmission/CAISO_loss_surface.csv` so that `LA_BASIN`
and `SDGE` carry their **own measured** `dev_z` from CAISO's day-ahead
`DLAP_*-APND` load aggregation points, instead of inheriting the SP15
*generation* hub's. Source data: the caiso-165 intake (2024 and 2025 complete
at 8,784 / 8,760 seven-node hours; 2023 partial by construction — `PRC_LMP`
retention begins ~2023-04-24 and moves).

| model zone | source node | disposition |
|---|---|---|
| `NP15` | `TH_NP15_GEN-APND` | **unchanged** — its own hub |
| `ZP26` | `TH_ZP26_GEN-APND` | **unchanged** — its own hub |
| `SP15_rest` | `TH_SP15_GEN-APND` | **unchanged** — the SP15 generation hub *is* the desert/Kern generation belt this zone represents |
| `LA_BASIN` | `DLAP_SCE-APND` | **RECONCILIATION, not identity** (§7) |
| `SDGE` | `DLAP_SDGE-APND` | **near-identity** (§7) |

`DLAP_PGAE-APND` is **deliberately not** substituted for `NP15` or `ZP26`: PG&E
straddles both, so it would replace two measured values with one blended one —
a downgrade. `DLAP_VEA-APND` has no model zone.

**Zero free parameters.** Same frozen estimator `dev_z,m = Σ MCL_z,t / Σ MCE_t`,
same schema, same thresholds. The rule-23 `[R-FROZEN-DERIVE]` re-derive licence
is the **source-data change** (the caiso-165 DLAP intake), cited in the derive's
docstring — not a residual.

**The `ScenarioConfig` flag is unchanged and stays `True` in BOTH arms.** The
A/B delta is the **CSV**, not a config field. The attestation asserts this
explicitly (§8) — an arm whose config differs from the control in any field
fails.

---

## 2. The per-(zone, year, month) coverage rule (carried from caiso-165 §2.2)

> A `(zone, year, month)` cell takes its **own measured DLAP** deviation iff
> that DLAP printed in at least `MIN_HOURS_PER_YEAR / 8760` (= 0.9132) of that
> month's **usable** hours. Otherwise the zone falls back to `TH_SP15_GEN-APND`
> for that month with `interpolated=True`, exactly as before caiso-166.

The threshold is the **existing frozen annual guard expressed as a ratio**, not
a new number (rule 5 `[R-NO-MAGIC]`, rule 23). A **usable hour** is one in
which all three `TH_*_GEN` hubs print — the pre-caiso-166 completeness rule
verbatim, so the `MCE` denominator and the three hub zones are bit-identical.
DLAP presence deliberately does **not** enter the usable-hour test: requiring it
would discard ~96 % of 2023 and destroy the three measured hub zones the
incumbent keeper rests on. Each zone-month's numerator and denominator are taken
over the **same** hour set (the hours its own resolved node printed), so a
partially-covered month is still the measured ratio.

---

## 3. Acceptance gate, strengthened so it can see the change

The derive's `--acceptance` mode benchmarked only `NP15↔ZP26` and
`NP15↔SP15_rest` — **neither of which Arm A changes**, so as written it was
blind to exactly the two new zones. caiso-166 **adds** `NP15↔LA_BASIN` and
`NP15↔SDGE` to `ACCEPTANCE_PAIRS`.

The measured benchmark is taken at **the node the surface actually used for that
month**, so an interpolated month is benchmarked against the node it
interpolated from and a measured month against its own DLAP — like for like,
never a measured benchmark against an interpolated surface.

**Every pair-year must stay in the `[0.5×, 1.5×]` miso-76 B1 band. A new zone
failing the band is a STOP-THE-LINE**, not a caveat (caiso-165 §5.1).

---

## 4. Pre-solve DATA gates — RUN, and reported here before any LP

Measured inputs only. No model output is read.

**(a) Acceptance — 12/12 pair-years in band.**

| year | pair | measured dMCL | implied | ratio |
|---|---|---|---|---|
| 2023 | NP15 vs ZP26 | +1.176 | +1.232 | 1.05× |
| 2023 | NP15 vs SP15_rest | +0.235 | +0.251 | 1.06× |
| 2023 | NP15 vs LA_BASIN | +0.235 | +0.251 | 1.06× *(12/12 interpolated)* |
| 2023 | NP15 vs SDGE | +0.235 | +0.251 | 1.06× *(12/12 interpolated)* |
| 2024 | NP15 vs ZP26 | +1.102 | +1.154 | 1.05× |
| 2024 | NP15 vs SP15_rest | +0.844 | +0.881 | 1.04× |
| 2024 | NP15 vs LA_BASIN | −0.080 | −0.076 | 0.94× |
| 2024 | NP15 vs SDGE | −0.367 | −0.359 | 0.98× |
| 2025 | NP15 vs ZP26 | +1.049 | +1.095 | 1.04× |
| 2025 | NP15 vs SP15_rest | +1.018 | +1.063 | 1.04× |
| 2025 | NP15 vs LA_BASIN | +0.049 | +0.052 | 1.06× |
| 2025 | NP15 vs SDGE | −0.292 | −0.290 | 0.99× |

The four pre-existing pair-years reproduce the caiso-164 acceptance
(1.04–1.06×) **exactly**, which is the independent check that the restructure
did not disturb the frozen estimator.

**(b) Unchanged-zone byte identity — 0 diffs.** All 96 `NP15` / `ZP26` /
`SP15_rest` rows are identical to the incumbent surface in `df_deviation`,
`n_hours` and `interpolated`. Exactly **48 of 240** rows change: 2 zones × 12
months × year-labels {2024, 2025}.

**(c) Holdout window.** The surface carries year labels {0, 2023, 2024, 2025}
only. Rule 22 `[R-HOLDOUT]`: the spend freeze is ACTIVE; no out-of-window year
is fetched, read, scored or registered.

**(d) 2023 is unchanged by construction** (12/12 months interpolated for both
zones — see §5), which makes 2023 an internal **placebo year**. Registered as a
gate in §6.

---

## 5. DECLARED BEFORE THE SOLVE — source homogeneity within a year label

Applying §2 mechanically produced a **pooled (`year = 0`) row set whose January
is measured at `DLAP_SCE` and whose February–December fall back to
`TH_SP15_GEN`** (pooled January clears coverage at 2,016 / 2,160 = 0.933
because two of the three pooled years are complete; no other pooled month
does).

That is not one zone's seasonal shape — it is two different locations stitched
into one 12-month vector, and the LP would read the **source switch as a real
seasonal loss signal**: a corridor lossy in January and lossless for the other
eleven months, driven by the report's retention boundary rather than by physics.

**Declared rule (a caiso-166 addition to caiso-165 §2.2, stated here before any
LP result):** a zone's 12 months within one year label must all come from the
same node; if any month fails the coverage rule, every month of that
zone-label falls back. This is rule 14's **misalignment clause** — the January
value is genuine, but used *literally* alongside eleven months of another node
it makes the result less reflective of reality, so the coherent reconciled
vector is preferred. It **self-heals** (once retention covers every month the
whole label becomes measured with no edit) and consults no model output.

**It binds on the pooled forecast-analogue rows ONLY.** The per-year backcast
rows are already homogeneous — 2023 fully interpolated, 2024 and 2025 fully
measured — so **the backcast A/B sees exactly zero bytes of this clause.**
Stated plainly because it is a judgement the caiso-165 charter did not cover.

---

## 6. THE PRE-REGISTERED GATES — stated before the numbers

**S1 · Placebo year (falsifiable).** 2023 carries an identical surface in both
arms, so the arm's 2023 P1 prices and dispatch must be **identical** to the
control's. A 2023 difference means something other than the CSV changed between
the arms, and the A/B is void — **stop-the-line**, not a result.

**S2 · Liveness on a PHYSICAL observable, never prices** (the standing
caiso-162/163/164/165 lesson). Asserted on **flows**, plus the link-count
split:

* the control must carry real energy on `SP15_rest → LA_BASIN` and
  `SP15_rest → SDGE` — the two corridors the re-derived surface makes lossy
  (`eps` 0.000 → 0.025/0.034 in 2024 and 0.027/0.036 in 2025). A corridor that
  never runs means the mechanism is **INERT**, registered as such on flow
  evidence, and promotion is forbidden;
* every CAISO-internal bidirectional link is split into a one-way pair in both
  arms (the split is the incumbent keeper's, not this arm's), so the link count
  must match between arms;
* no treatment hour may exceed a caiso-163 published directional cap.

**S3 · ADVERSARIAL CEILING — the arm FAILS for OVER-performing.** A loss
mechanism may not move a zonal basis by more than the measured `dMCL` it
represents. Per year, `|Δ mean(pocket − SP15_rest)|` must not exceed the
measured `dMCL` for that pair-year, computed from the committed DAM component
record:

| pair | 2024 | 2025 |
|---|---|---|
| `LA_BASIN − SP15_rest` | 0.9242 | 0.9686 |
| `SDGE − SP15_rest` | 1.2107 | 1.3101 |
| `NP15 − ZP26` (non-regression) | 1.1016 | 1.0494 |

A larger movement means the mechanism is doing something other than
representing losses: a defect to investigate, **not a result to promote**.

**S4 · Single-object delta.** Zero `ScenarioConfig` value diffs against the
same-HEAD control (§1), `caiso_zonal_loss_surface == True` in **both** arms,
every field new since the incumbent at its `ScenarioConfig` default, and
`mode == "backcast"`.

**Verdict rule.** Arm A is **KEPT REGARDLESS of what it does to the backcast**
(§7). The gates above are integrity gates, not fit gates. Promotion to
designated keeper follows the owner clause — *"if structural integrity improves
but gates regress that may still be a keeper"* — i.e. Arm A is promoted iff S1–S4
pass and structural integrity improves; a scoring regression is disclosed in
full and does not by itself block promotion, and a scoring **improvement is not
the reason** for it either (rule 1 `[R-STRUCT]`).

---

## 7. RULE 14 `[R-ACCURATE]` DISPOSITION — restated before the result

Carried from `PRECHECK-caiso165` §5.1, which pre-committed it. **Not
re-litigated here.**

* `DLAP_SDGE → SDGE` is a **near-identity**: SDG&E's service territory *is* the
  model's San Diego pocket behind Path 44 / SWPL.
* `DLAP_SCE → LA_BASIN` is a **RECONCILIATION, not an identity**: SCE's
  territory spans both the LA basin and much of the desert/Kern belt the model
  assigns to `SP15_rest`, so the DLAP is a load-weighted mix dominated by — but
  not coincident with — the model zone.

**Both are kept regardless of what they do to the backcast.** The status quo is
**not a rival measurement**: it is the *generation* hub's deviation, weighted to
where power injects, standing in for a *load* pocket at the other end of the
corridor. A DLAP is the right KIND of object for a load zone even where its
boundary is imperfect, and rule 14's misalignment clause explicitly prefers a
**reconciled version of the real data** over a stand-in. **If the re-derived
surface makes the backcast worse, that is a discovered bug elsewhere (rules 1 /
14), reported as such — never grounds to revert.**

The size of what the two zones were missing is already quantified from measured
data: `+0.924 / +0.969` $/MWh (SCE) and `+1.211 / +1.310` $/MWh (SDGE) in
2024 / 2025. For SDGE that is **larger than the entire `NP15−ZP26` loss
component** (`+1.102 / +1.049`) the incumbent keeper was promoted for
representing.

---

## 8. Solve discipline

* **No tuning clause.** No parameter is swept, blended or fitted. The only input
  that changes between arms is the loss-surface CSV's `LA_BASIN` / `SDGE` rows.
  The control arm's input is the incumbent surface **as already committed at
  this branch's base `3bc37ce2`** —
  `git show 3bc37ce2:data/raw/iso-specific-transmission/CAISO_loss_surface.csv`
  — so it is auditable from the repository's own history rather than from a
  copy this session asserts is faithful. The attestation reads that blob
  directly and FAILS if it cannot resolve it.
* **Rule 16 `[R-ALLYEARS]`:** `--year 2023 2024 2025` in ONE invocation, ONE
  bundle per arm. **Rule 12 `[R-PARALLEL]`:** years sequential within a run.
* **The two arms run SEQUENTIALLY, never concurrently** — caiso-164 §5.1 lost a
  control arm to an OOM kill (anon-rss 8.85 GB) with two per-plant CAISO
  replays resident on a 15 GB box. **In-session only, never a GitHub Actions
  runner** (CLAUDE.md "GitHub Actions — never offload work to CI").
* **A/B against a same-HEAD control** via `scripts/replay_keeper.py`. Control =
  the current surface; arm = the re-derived one; the flag is `True` in both.
* **Attestation** modelled on `scripts/gen_caiso164_attestation.py`, carrying
  its shape: assert the intended delta against **both** the incumbent and the
  same-HEAD control; assert every `ScenarioConfig` field new since the incumbent
  holds its default; check `mode == "backcast"`; assert the holdout window on
  both bundles **and** the surface; verify liveness on flows; FAIL if the
  control never exercised the mechanism; enforce the S3 adversarial ceiling.
* **Inherited owner default flips** (`retirement_rule=pipeline` D-1,
  `entry_rate_limits` + `entry_commissioning_lag` D-2,
  `net_cone_forward_escalation=reindex_gross` D-3a) are **merged owner
  decisions, not this session's choices and not tuning**. Disclosed, and
  asserted on both grounds: forecast-gated and unreachable at
  `mode="backcast"`, and identical across both arms.
* **Rule 15 / 28b:** every completed run registered (keeper *or* rejected
  probe), with `legitimacy_diagnostics.json` generated into each bundle
  **before** registration so C7/C8 score rather than SKIP. Matrix cell +
  evidence citation updated in this same session. Top-15 CAISO retention
  honoured.
* **Rule 22:** CAISO holds no `complete` marker → no `calibration-complete`
  re-key and no marker written. `complete` is an owner act, not declared here.

---

## 9. Arm B remains BLOCKED — and the block binds harder, not softer

An intra-SP15 transfer limit is **not armed**. caiso-165 CONFIRMED the corridor
congests (belly separation 89–99.7 %, mean `|dMCC|` 1.04–6.45 $/MWh,
pocket-dearer up to 99.1 %) and measured the model at **0.00 %** separation on
`LA_BASIN−SP15_rest` in all 8,760 belly hours, with `SDGE−SP15_rest`
**INVERTED** (model −2.63 / −5.32 vs measured +3.92 / +6.42 $/MWh).

No published physical limit — CAISO LCT/LCR local-area import capability, a
published path rating, or an ATC-style construction off measured directed flows
— is in `data/raw`. A limit chosen to reproduce those numbers is an **OUTCOME
PIN** and is FORBIDDEN (rule 13 `[R-MEASURED]`, rules 5 / 21 / 24). **Now that
the target numbers are known precisely, the prohibition binds harder, not
softer.** If no published limit is found, the blocker is filed and the lane
stops — it is not approximated.

Standing CAISO blockers likewise untouched: C3a-2025 (non-public hourly
pumped-storage) and C3c-2023/24 (the SoCalGas OFO declaration record). Neither
is closable by an adder, haircut or residual-tuned value.

---

## 10. DO-NOT-REDO honoured

Authoritative list taken from the matrix, not from prose. Not re-tested without
new evidence: `energy_reserve_coopt` (I, caiso-144, explicit DO-NOT-SOLVE),
`cc_mustrun_per_plant` (R), `wecc_endogenous_node` (R, caiso-110),
`caiso_corridor_export_path` (R, caiso-132), `caiso_p1_export_sink_seam` (R),
`netload_drag_floors` (R). Not re-tested as keepers: `caiso_zonal_loss_surface`
(caiso-164 — this session re-derives its **input data**, it does not re-test the
mechanism's verdict), `caiso_asymmetric_path_ratings` (caiso-163),
`caiso_per_year_import_caps` (caiso-162). Not reopened: the caiso-141 A2
pumped-storage wall, the caiso-131/144 C3c routes, the caiso-104
charge-allocation family, the caiso-161 matrix census.

**No N–S TOPOLOGY lever is chartered** — caiso-164 §0 measured that topology is
not where the recoverable component was. `td_loss_factor` is **not** armed on
top of the loss surface (rule 19 `[R-ONE-MECH]`).
