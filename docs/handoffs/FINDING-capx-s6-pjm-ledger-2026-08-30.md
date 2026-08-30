# FINDING — capx-S6: the PJM T1-F ledger run — first supply-side measure against the corrected (hold-last-FPR) bar

**Session:** capx S-6 PJM T1-F LEDGER RUN (capacity-expansion / Forecast Finalization track)
**Date:** 2026-08-30 · **Branch:** `claude/capx-s6-pjm-ledger-uihbbp` (off `main` @ `5cdb55d`)
**Charter:** director ledger `capx-director-ledger-2026-08.md` lane S-6 (§0p.2, r#19 pack
prompt; owner-held at dispatch, hold lifted by the owner's own dispatch of this session —
its release condition, CAISO-224-FIN landing, is satisfied at this HEAD: PR #4415 merged).
Predecessors: `docs/handoffs/FINDING-capx-s5-pjm-horizon-edge-2026-08-30.md` (the corrected
bar; landed PR #4340), `FINDING-capx-d2b-i7-ledger-2026-08-25.md` §5 (the PJM leg's
observability limit), `FINDING-capx-s4b-neiso-ara-2026-08-30.md` §§4–5 (the pre-declaration
discipline and the floor-retention response pattern this finding mirrors).

**Sections §0–§3 were written and committed BEFORE any solve** (the S-4b discipline).
Sections §4+ were written after.

---

## 0. What this is

S-5 restated PJM's T1-F I7 position scorer-side — the 2030 miss 366 MW → **5,858 MW**
(3.39 % of gross peak) under the owner-signed HOLD-LAST-FPR convention (card C-A), with
2029 "plausibly joining" as a second failing year — but it ran **no solve**, so the SUPPLY
side has never been measured against the corrected bar. The standing `pjm-t1f` verdict is
the FFR-3A-2 scorer's output on a bundle that is gitignored by design; the committed record
carries exactly ONE (firm, requirement) pair (2030) plus four summary anchors (§1.2). This
session runs the minimum solve that makes the supply side observable:

* **Does 2029 actually join the fail set?** (S-5's flagged inference — the bar rises
  3.18 pp of peak, but the model's backstop now targets that same bar, same-year.)
* **What is the true 2030 magnitude once the fleet responds?** (The static restatement
  assumed the FFR-3A-2 fleet frozen; the live machinery retains exits and force-builds
  against the corrected requirement.)

**ONE run, no control pair.** Nothing changed since S-5 landed at HEAD — the requirement
delta IS S-5's scorer-side restatement, already quantified to the MW (§1.1), so a
composite-bar control arm would only re-measure arithmetic already committed. What this run
adds is the supply-side response, decomposed against the committed `pjm-t1f` anchors (§2.4);
any epoch drift vs that (2026-08-03-epoch) bundle is decomposed and named per the
S-4V/NYISO-lane discipline.

## 1. The corrected bar, verified live at this HEAD (pre-solve)

### 1.1 Requirement factors — the live resolver's own output, this checkout

`resolve_adequacy_requirement_mw(cfg, "PJM", peak=1.0, year)` at `5cdb55d` reproduces S-5 §3
exactly (published FPR 2026–2028; held-last 0.9401 for 2029–2030 under card C-A):

| year | delivery yr | FPR | req factor (× gross peak) | I12 floor implied |
|---|---|---:|---:|---:|
| 2026 | 2026/27 | 0.9170 (published) | 0.880629 | −11.94 % |
| 2027 | 2027/28 | 0.9260 (published) | 0.889272 | −11.07 % |
| 2028 | 2028/29 | 0.9401 (published) | 0.902813 | −9.72 % |
| 2029 | 2029/30 | 0.9401 (held-last) | 0.902813 | −9.72 % |
| 2030 | 2030/31 | 0.9401 (held-last) | 0.902813 | −9.72 % |

The **model-side** bar moved only in 2029–2030 (composite 0.871017 → 0.902813, +3.18 pp of
peak): the model always built to the published FPR in 2026–2028 — the D-1 defect was
checker-only there. Every supply-side response to S-5's change is therefore expected in
**2029–2030 alone**; a 2026–2028 deviation from the committed anchors is epoch drift by
definition (§2.3).

### 1.2 The committed anchors (everything the record carries for `pjm-t1f`)

From `frontend/data/forecast/ff-verdicts.json` `pjm-t1f` (FFR-3A-2, epoch 2026-08-03,
`scored_at_sha 8ba592814d92`) — the bundle itself is unrecoverable:

1. **I7 2030: firm 150,088 MW vs (composite) requirement 150,454 MW** ⇒ back-solved
   peak₂₀₃₀ = 150,454 / 0.871017 = **172,733.8 MW** (±0.6, verdict rounds to the MW);
   rm₂₀₃₀ = −13.11 %. Restated bar 172,733.8 × 0.902813 = **155,946.2 MW**; static miss
   **5,858 MW**.
2. **I12: only 2030 out of band** at the old year-less floor (−12.9 %) ⇒ rm ≥ −12.9 % in
   2026–2029 in that run (the only committed bound on its 2029: between the old floor and
   the corrected floor is a 3.18 pp window inside which its 2029 sat unobserved).
3. **Backstop share 23.6 %** of additions (FC-2 row 4) over the 2026–2030 trajectory.
4. **Runtime:** peak RSS 8.8 GB (no co-run), the FC-8 CAVEAT; ~19 min cold / 3.8 min per
   solve-year (D2b §5.1).

### 1.3 Supply-side leniency carried on the record, NOT intaken here

The external-tie entry `ADEQUACY_EXTERNAL_TIE_FIRM_MW["PJM"] = 1,281.7` MW UCAP is the
2026/27 BRA cleared import held static; PJM's published 2027/28 figure is 1,005.9 MW
(−275.8 MW). Correcting it would **WIDEN** every year's miss by up to ~276 MW. This session
runs shipped defaults (no config change, no intake — a registry re-vintage is its own lane
under rule 23); the leniency is carried as a named one-sided caveat on every I7 number
reported below.

## 2. PRE-DECLARED expectations (recorded and committed before any solve)

Directions, not targets (rule 21): nothing below is a number the run is steered toward, and
a result landing just clear of a gap is the suspicious one.

### 2.1 Static arithmetic (the no-response floor of the analysis)

If the 2029/2030 supply side were identical to FFR-3A-2's, the corrected bar alone gives:
2030 I7 = **−5,858 MW (FAIL)**; 2029 I7 unknown within (−3.18 pp of peak, +) of its
unobserved margin — S-5's "plausibly joins". The static reading is the *upper bound* of the
2030 miss under zero drift; the live machinery should do strictly better (§2.2), and a
measured 2030 miss LARGER than ~5.9 GW (beyond the ~276 MW leniency and demand drift) would
itself be a drift finding to attribute, not a bar effect.

### 2.2 Known endogenous responses, directions declared in advance

1. **Reserve-margin backstop — the dominant expected responder.** It resolves ON for
   capacity-market PJM under `--golden-posture`, targets the SAME
   `resolve_adequacy_requirement_mw` bar (year threaded — S-5 verified `evolve.py:811`),
   builds **same-year** gas_ct sized nameplate = gap/(1 − EFORd 0.06), and is capped by BOTH
   the PJM interconnection-queue caps (gas_ct 2.0 GW/yr per-tech, 10 GW/yr all-tech) AND the
   BLK-10 growth ladder (2.0 × prior-max annual gas_ct build, net of the year's economic
   gas_ct decisions, deficit carrying forward; the ladder rises as builds land). Direction:
   **more backstop gas_ct in 2029–2030** than the old bar would trigger (the +3.18 pp bar
   step is +5.4–5.5 GW of requirement at those peaks). The old run landed 366 MW short of
   even the composite bar in 2030, i.e. its backstop was cap-bound there; whether the caps
   leave the corrected-bar gap open is exactly what the run measures. **2029 joins the fail
   set iff the caps bind in 2029** (the backstop otherwise closes its own same-year gap by
   construction). **Any clearance bought this way is REPORTED AS SUCH** — I12 and the FC-2
   backstop-share row (23.6 % baseline) are re-read as consequences, never targets; the
   share is expected to RISE.
2. **Retirement reliability floor — the S-4b mirror, tightening direction.** The floor
   tests the same requirement (one requirement, two verbs), so the higher 2029–2030 bar
   blocks marginal economic exits the composite bar would have released; retained units are
   named in the ledger's `floor_retained` rows. Direction: firm MW clawed back in
   2029–2030; magnitude measured, not predicted (NEISO's analogue was 699.3 MW on a far
   smaller system — no transfer of magnitude across ISOs).
3. **2026 is the base year (no evolution):** its I7 reads the input fleet against the
   published-FPR bar — pure intake, no response possible. No committed 2026 pair exists to
   difference against (unlike S-4b's exact isolation check); its value here is forward:
   it becomes the committed base anchor for every later PJM lane.

### 2.3 Epoch drift — expected, bounded to named channels

The committed pair is 27 days of epoch older (2026-08-03 → this HEAD; among the landings:
R-NEW default, D11-R entry-volume rule, FF-2A arms, demand/fuel re-derives). Drift is
measurable at exactly one committed anchor (2030) plus three soft anchors (§1.2 items 2–4).
Discipline: **the bar response is computed from this run's own ledgers** (backstop rows +
floor-retained rows in 2029–2030, re-tested against the composite bar arithmetic — both
channels are need-proportional, so what each would have done under the old bar is exact
scorer-side arithmetic on the same ledger); **the residual** of (measured 2030 firm −
150,088) after removing the bar response is the epoch-drift estimate, decomposed as far as
the ledgers allow (exits by unit/reason, entry by tech, peak drift vs 172,733.8) and named
honestly where attribution ends — never silently absorbed.

### 2.4 The honest-outcome clause (verbatim discipline)

If 2029 joins the fail set, THAT IS THE HONEST OUTCOME, reported at full magnitude. If
2029 clears on backstop build, the clearance is reported as administrative build, never as
organic adequacy. If 2030's miss shrinks, the shrink is decomposed (§2.3) — a miss that
lands just clear of zero triggers the rule-21 suspicion check against the cap arithmetic
before it is believed. Nothing is re-tuned, no band widened, no input reverted in response
to any of it; contradictions beyond the declared channels are the headline and an
attribution question. An honest FAIL is a finding, not a problem.

## 3. Run construction (declared)

```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  python scripts/run_full_horizon.py --iso PJM --start-year 2026 --end-year 2030 \
  --golden-posture --out-dir results/ff-t1f-s6-pjm/ledger
```

* 5 solve-years — inside the §2.1b window cap, no `--full-solve-authorized`; years
  sequential within the run (rule 12); solo in this session's container (rule 12's memory
  cap is per-box; 8.8 GB peak RSS recorded for this leg, no co-run here).
* Forecast-mode 2026–2030 at shipped defaults + golden posture (PJM curve-ON). No
  out-of-training backcast year is solved, scored or registered (freeze tier-scoped; this
  session touches neither tier); no measured-outcome feedback (rule 13); no config change,
  no new mechanism, no matrix duty (rule 28 duty (a) discharged: PJM lever queue read; no
  lever taken — this is not a mechanism session).
* **Scoring:** `scripts/check_forecast_invariants.py` (embedded in the runner) + FC re-score
  via `scripts/forecast_verdict.py --tier t1f --summary … --run-config …` — committed
  artifacts only.
* **Registration (rule 15, FORECAST namespace only):** run id **`pjm-2026-2030-s6-ledger`**
  via `scripts/register_forecast_run.py --summary … --label s6-ledger --kind t1f`.
  Committed: `full_horizon_summary.json`, `run_config.json`, `forecast_verdict.json`,
  `PJM/<cache_key>/config.yaml` + `evolution_<year>.json` ×5, the
  `frontend/data/hindcast/pjm-2026-2030-s6-ledger.json` sidecar. Heavy artifacts
  (parquet/npz/hourly/floor-retention logs) gitignored — the S-4b slim-vs-heavy split, own
  campaign block.
* **Verdict keys (preserve-then-overwrite, the S-4V/S-4b protocol):** the current bare
  `pjm-t1f` (FFR-3A-2) is preserved VERBATIM under **`pjm-t1f-ffr3a2`** (the established
  suffix for that vintage, as NEISO/NYISO already carry) with the preservation note
  appended to its provenance; the bare `pjm-t1f` key then takes this run's scorer output
  with provenance `{scored_at_sha, scored_at_date, cache_epoch=<cache_key>,
  session=capx-S6-pjm-ledger}`. Never the backcast namespace.
* **Board:** `program-status.json` PJM block ONLY — T1-F rows, `fc` map, gate leg (b)
  detail refreshed from the measured verdict, with the S-5 restatement provenance kept
  verbatim; no other ISO's block. Shared-file collision care (r#19 map): ff-verdicts +
  program-status edits are PJM-keyed only; rebase before pushing; never resolve another
  lane's block (T3 NEISO golden and others in flight).
* Exit: this FINDING §§4+; report to the owner; the director stamps the ledger on its
  refresh.

---

*(Sections below were written AFTER the solve.)*
