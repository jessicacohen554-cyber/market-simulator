# FINDING — caiso-166: five measured CAISO loss zones (Arm A)

**Session** caiso-166 · **Date** 2026-08-04 · **Branch**
`claude/caiso166-measured-loss-zones-uwsq1n` · **Base** `3bc37ce2`
**Prereg** `results/calibration/PRECHECK-caiso166-measured-loss-zones-2026-08-04.md`
(pushed at `6c2dbfd5`, **before either arm solved**)

**Runs** `2026-08-04-caiso-166-measured-dlap` (Arm A) ·
`2026-08-04-caiso-166-control-hubsurface` (same-HEAD control)

---

## 0. VERDICT — Arm A is **NOT PROMOTED**. The CAISO keeper is UNCHANGED at `2026-08-04-caiso164-zonal-loss-surface`.

Two **pre-registered** gates block promotion. Neither was relaxed after it
fired, and neither is a reason to revert the measured data (§3).

1. **Gate S3 (adversarial ceiling) BREACHED**, 2025 `LA_BASIN−SP15_rest`: the
   arm moved the basis `+1.0205 $/MWh` against a measured `dMCL` ceiling of
   `+0.9686` — **105.4 % of ceiling**. PRECHECK §6 pre-committed the
   consequence: *"a defect to investigate, not a result to promote."*
2. **C3a mean LMP regresses 2024 PASS → FAIL** (+9.5 % → +11.5 % against a
   ±10 % band). The incumbent's ledgered `price_mean` exception covers **2025
   only**, so the 2024 FAIL is undocumented and the determination is
   **NOT-YET**.

**The re-derived surface is KEPT regardless** (rule 14 `[R-ACCURATE]`,
pre-committed in PRECHECK-caiso165 §5.1 and restated in PRECHECK-caiso166 §7).
What is withheld is the *promotion*, not the *measurement*.

---

## 1. What was built

`LA_BASIN` → `DLAP_SCE-APND` and `SDGE` → `DLAP_SDGE-APND`, replacing the
`TH_SP15_GEN-APND` **generation**-hub deviation both load pockets had been
inheriting. Same frozen estimator, same schema, same thresholds; the rule-23
`[R-FROZEN-DERIVE]` licence is the **source-data change** (the caiso-165 DLAP
intake), not a residual.

**The A/B delta is a DATA FILE, not a config field.** `caiso_zonal_loss_surface`
is `True` in **both** arms. Config drift against the same-HEAD control is
`{arm_only: [], other_only: [], value_diffs: {}}` — **zero, of any kind**
(asserted; the attestation fails on any config difference).

Pre-solve data gates, all measured inputs:

* derive acceptance **12/12** pair-years in the `[0.5×, 1.5×]` band; the four
  pre-existing pair-years reproduce caiso-164's 1.04–1.06× **exactly**;
* `NP15` / `ZP26` / `SP15_rest` **bit-identical**, 0 diffs across all 96 rows
  each;
* exactly **48 of 240** rows change (2 zones × 12 months × {2024, 2025}).

---

## 2. The gates that PASSED, and they are not weak

**S1 · Placebo year — the strongest single piece of evidence in this session.**
2023's surface rows are identical in both arms (the DLAP record clears the
coverage rule in no 2023 month). The two 2023 solves are therefore identical,
and they are — to **exactly zero**:

| observable | max abs difference, 2023 |
|---|---|
| zonal price | **0.0** |
| class dispatch | **0.0** |
| link flow | **0.0** |

That is a falsifiable check that the loss-surface CSV is the *only* object
differing between the arms, and it held.

**S2 · Liveness on FLOWS, never prices.** The control carries real energy on
both corridors the re-derived surface makes lossy — `SP15_rest→LA_BASIN`
**48.2 / 56.4 / 59.4 TWh** in 8,760 of 8,760 hours, `SP15_rest→SDGE`
**7.6 / 7.4 / 6.9 TWh** in 8,726 / 7,868 / 7,655 hours. The mechanism is
emphatically **not inert**. Link counts are identical (8 = 8) in every year,
and **zero** arm hours exceed any caiso-163 published directional cap.

**S4 · Single-object delta.** Zero config drift vs the control (above);
`mode == "backcast"` both arms; every field new since the incumbent at its
`ScenarioConfig` default. One field the incumbent carries is absent from both
arms — `pjm_seam_envelope_by_neighbor`, **deleted upstream by pjm-152 under
rule 26 `[R-DELETE]`**; the attestation admits it only after asserting against
the live dataclass that it is no longer a `ScenarioConfig` field *at all*, and
that it is absent from **both** arms.

**C7 / C8 PASS.** `legitimacy_diagnostics.json` was generated into both bundles
**before** registration, so both scored rather than SKIPPED.

---

## 3. THE S3 BREACH IS A GATE-SPECIFICATION DEFECT, NOT A MECHANISM DEFECT — and the gate still stands

The pre-registered ceiling asks whether the arm moved a basis by more than the
**measured `dMCL`**. It did, by 5.4 %, in one pair-year of four. The
decomposition says why, and it exonerates the mechanism:

| year | zone | measured `dMCL` | **surface-implied** | LP delta | LP ÷ implied | LP ÷ measured |
|---|---|---|---|---|---|---|
| 2024 | `LA_BASIN` | +0.9242 | +0.9597 (1.038×) | +0.9213 | **0.960×** | 0.997× |
| 2024 | `SDGE` | +1.2107 | +1.2566 (1.038×) | +1.1483 | **0.914×** | 0.948× |
| 2025 | `LA_BASIN` | +0.9686 | +1.0096 (1.042×) | +1.0205 | **1.011×** | **1.054×** |
| 2025 | `SDGE` | +1.3101 | +1.3656 (1.042×) | +1.2523 | **0.917×** | 0.956× |

*(surface-implied = the derive's own `--acceptance` algebra,
`Σ_m h_m × MCE_m × ((1+dev_to)/(1+dev_from) − 1) / Σ_m h_m`.)*

**The LP tracks the surface it was given to within 1.1 % — never meaningfully
above it.** The 105.4 % decomposes as **1.042 (estimator) × 1.011 (LP
tracking) = 1.054**. The excess is the MCE-weighted estimator's own known
positive bias against measured `dMCL` — the same +4 % the derive's
`--acceptance` gate *accepts* inside its `[0.5×, 1.5×]` band, and the same
1.04–1.06× caiso-164 recorded and passed on.

So the S3 ceiling, set at exactly `1.00×` of measured `dMCL`, holds the LP to a
**tighter standard than the derive's own accepted estimator tolerance** — an
internal inconsistency that only surfaces when the estimator's positive bias
and a near-complete recovery coincide, as they do in 2025 `LA_BASIN`.

**The gate is NOT relaxed.** It was pre-registered at `1.00×` and it fired;
re-cutting it now, after seeing the number, is precisely the move the
pre-registration exists to prevent. **A future session may re-charter the
ceiling PROSPECTIVELY** — the defensible form is the *surface-implied*
separation (or measured `dMCL` × the acceptance band's upper edge), declared
before a solve. That re-charter is an owner call, not this session's.

---

## 4. C3a got WORSE, and per rules 1 / 14 that is a DISCOVERED BUG, not a reason to revert

| year | control | arm | band |
|---|---|---|---|
| 2023 | +3.7 % PASS | +3.7 % PASS *(placebo — identical)* | ±10 % |
| 2024 | +9.5 % **PASS** | +11.5 % **FAIL** | ±10 % |
| 2025 | +12.1 % (ledgered CAVEAT) | +14.4 % (ledgered CAVEAT) | ±10 % |

Load-weighted λ moves `+0.688` (2024, +1.82 % of level) and `+0.793` (2025,
+2.06 %). **That direction is physically obligatory**: losses consume MWh, so
representing them must raise the delivered price level. The arm did not
*create* a high bias — CAISO's mean LMP was **already** running +9.5 % / +12.1 %
hot against RT actuals with a control that sat only 0.5 pp inside the band. The
measured losses pushed a pre-existing bias across a threshold it was already
touching.

Worth recording, because the surface is derived on the **day-ahead** basis
while C3a scores against **RT**: against CAISO's own DA prices the control sits
at −0.1 % (2024) and +9.0 % (2025), and the arm at +1.8 % and +11.3 %. The
2024 arm is *closer to DA* than the control is to RT. The DA−RT premium is
+$3.30 (2024) and +$0.98 (2025).

The root cause of CAISO's hot level is **not** in this lane, and no
compensating adder, haircut or offset was added anywhere. The standing C3a
caveat remains the **owner's**, on the caiso-141 A2 non-public hourly
pumped-storage data wall.

---

## 5. ⚠ OPEN ITEM FOR THE OWNER — the keeper and its input surface now disagree

`CAISO_loss_surface.csv` is a **shared LP input**. With the re-derived surface
committed and Arm A not promoted, the designated keeper
(`2026-08-04-caiso164-zonal-loss-surface`, solved on the *old* surface) **no
longer reproduces from the repository.** Arm A *is* that keeper's recipe
re-solved on the corrected data, so the natural resolution is to promote it.

This is stated loudly rather than buried, because it is a real inconsistency
and the alternatives are worse:

* reverting the CSV would leave the **committed derive script and the committed
  artifact disagreeing** — anyone re-running the derive gets a diff; and
* it would mean keeping a **known-wrong** data file so an old keeper
  reproduces, which is exactly the "bury the error back inside an inaccurate
  input" rule 14 forbids.

**The decision is a one-liner and it is the owner's:** re-charter the S3 ceiling
prospectively (§3) and promote Arm A, or direct otherwise. Note that promotion
would also need the 2024 `price_mean` FAIL ledgered or fixed (§4).

---

## 6. Arm B REMAINS BLOCKED — the prohibition binds harder, not softer

No intra-SP15 transfer limit was armed. caiso-165 CONFIRMED the corridor
congests and measured the model at 0.00 % separation on `LA_BASIN−SP15_rest`
in all 8,760 belly hours. **No published physical limit** — CAISO LCT/LCR local
capability, a published path rating, or an ATC construction off measured
directed flows — is in `data/raw`.

A limit chosen to reproduce the now-precisely-known measured numbers is an
**OUTCOME PIN**, forbidden by rule 13 `[R-MEASURED]` and rules 5 / 21 / 24. It
is filed, not approximated.

Note what §2 shows about this: the arm moves `LA_BASIN−SP15_rest` from `0.0000`
to `+0.9213 / +1.0205` — the corridor now separates on **losses**. The measured
separation is dominated by **congestion** (`|dMCC|` 1.04–6.45 $/MWh), which
this lane does not and cannot address. Standing blockers C3a-2025 and
C3c-2023/24 are likewise untouched.

---

## 7. ⚠ DELIVERY GAP — the dashboard payloads could not be pushed

Both runs are registered **locally** (bundles, sidecars and
`runs/<id>.js` payloads all generated, C7/C8 scored). They are **not on the
remote**, for a transport reason outside this lane:

* **`git push` returns HTTP 413 for every push in this container** — including a
  *no-op ref advance whose request body was 4 bytes*. Git sends the receive-pack
  RPC with `Transfer-Encoding: chunked` and the origin rejects any chunked body;
  `http.postBuffer`, `http.version=HTTP/1.1` and `protocol.version=0` all fail
  identically. A direct `POST` of 4 bytes to the same endpoint returns 200, so
  it is the transport, not the pack. `GH_TOKEN` is a 14-character proxy
  placeholder, so pushing to `github.com` directly is not available either.
* `mcp__github__push_files` works and is byte-verified (rule 27) — but it is
  **text-only** with a **~457 KB** cap, and the payloads are **674 KB /
  677 KB**, with the bundle `hourly/*.parquet` sidecars binary.

**Landed via `push_files`, every blob hash-verified against local:** the
pre-registration, the derive, the re-derived surface, this finding, and
`results/calibration/_caiso166_session_artifacts.patch` — a git-generated,
`git apply --check`-verified patch carrying the three artifacts too large or too
risky to retype: `scripts/gen_caiso166_attestation.py` (new, 813 lines), the
`zonal_loss_surface` **mechanism-matrix** cell update (the file is 843 KB, over
the cap) and the `docs/calibration-log/caiso.md` entry (380 KB). Apply with
`git apply results/calibration/_caiso166_session_artifacts.patch`.

**Needs a session with a working `git push`:** `frontend/data/backcast/runs/*.js`
(2 files), the registry sidecars, and the bundle parquet sidecars. Registry
sidecars are deliberately **withheld** rather than pushed alone — a sidecar
without its payload is silently invisible in the Run Explorer
(`docs/handoffs/dashboard-payload-push-gap-2026-07.md`), which is worse than a
clean absence. **Top-15 CAISO retention pruning was also reverted locally** for
the same reason: a half-applied prune on the remote is worse than none.

---

## 8. DO-NOT-REDO honoured

Not re-tested: `energy_reserve_coopt` (I, caiso-144), `cc_mustrun_per_plant`
(R), `wecc_endogenous_node` (R), `caiso_corridor_export_path` (R),
`caiso_p1_export_sink_seam` (R), `netload_drag_floors` (R). Not re-tested as
keepers: `caiso_asymmetric_path_ratings`, `caiso_per_year_import_caps`. The
`caiso_zonal_loss_surface` **mechanism verdict is untouched** — this session
re-derived its *input data* and did not re-test the mechanism. No N–S topology
lever chartered; `td_loss_factor` not armed (rule 19 `[R-ONE-MECH]`). Not
reopened: caiso-141 A2, caiso-131/144 C3c, caiso-104, the caiso-161 census.
