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

## 4. The run, as executed

Relaunched as **S-6-R** (director refresh #20, ledger §0q.2; the original session was lost
after landing §§0–3 and before the solve). Branch fresh off `main` @ `54ca19ae0782`; the old
`claude/capx-s6-pjm-ledger-uihbbp` carried 0 unique commits and is gone from the remote.

Command, byte-for-byte the §3 pre-declaration:

```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  python scripts/run_full_horizon.py --iso PJM --start-year 2026 --end-year 2030 \
  --golden-posture --out-dir results/ff-t1f-s6-pjm/ledger
```

| | |
|---|---|
| run id | **`pjm-2026-2030-s6-ledger`** |
| cache key | `31a19d815fa319a7` |
| bundle | `results/ff-t1f-s6-pjm/ledger/PJM/31a19d815fa319a7` |
| years | 2026–2030, **5/5 solved**, sequential (rule 12) |
| wall | 20.9 min (1,251.9 s); median year 203.6 s |
| peak RSS | **8.845 GB**, solo — the FC-8 CAVEAT, within 0.5 % of FFR-3A-2's recorded 8.8 GB |
| scored at | `54ca19ae0782`, 2026-08-31 |

**One environment step, disclosed because the first launch aborted on it:** `data/clean` is
derived and gitignored, so a fresh checkout has no `confirmed-retirements` partition and
`load_confirmed_exits` refuses to silently degrade to the economic screen. Regenerated with
`scripts/data/curate_confirmed_retirements.py` exactly as its error instructs (PJM: 14 rows,
8 live), then relaunched. **No config change, no flag change, no code change** — the guard is
working as designed and the regeneration is a data-derivation step, not a tuning channel.

**§1.1 reproduced at this HEAD before the solve**, 27 days past the FFR-3A-2 epoch: FPR
0.9170 / 0.9260 / 0.9401 / 0.9401 (held) / 0.9401 (held) → factors 0.880629 / 0.889272 /
0.902813 / 0.902813 / 0.902813; year-less composite 0.871017. Back-solved peak₂₀₃₀
172,733.7, restated requirement 155,946.2, static miss 5,858.2 MW. The pre-declaration's
arithmetic is unmoved.

## 5. The measured ledger — I7 and I12, per year

Read exactly as `check_forecast_invariants` reads them: `accredited firm = peak × (1 + rm)`
from each committed `evolution_<year>.json`, against `resolve_adequacy_requirement_mw` at the
ledger year.

| year | gross peak | rm | accredited firm | requirement | factor | **I7** | I12 floor | I12 |
|---|---:|---:|---:|---:|---:|---:|---:|:--:|
| 2026 | 161,027.2 | −9.41 % | 145,867.6 | 141,805.2 | 0.880629 | **+4,062.4** | −11.94 % | in |
| 2027 | 163,626.6 | −10.85 % | 145,867.7 | 145,508.5 | 0.889272 | **+359.2** | −11.07 % | in |
| 2028 | 166,439.0 | −11.68 % | 147,003.1 | 150,263.2 | 0.902813 | **−3,260.1** | −9.72 % | **out** |
| 2029 | 169,472.0 | −12.57 % | 148,169.4 | 153,001.5 | 0.902813 | **−4,832.1** | −9.72 % | **out** |
| 2030 | 172,733.7 | −12.99 % | 150,291.4 | 155,946.1 | 0.902813 | **−5,654.7** | −9.72 % | **out** |

Misses as a share of gross peak: 2028 **1.96 %**, 2029 **2.85 %**, 2030 **3.27 %**.

### 5.1 The two answers the run was built to give

1. **Does 2029 join the fail set? YES.** S-5's flagged inference is confirmed at
   **−4,832.1 MW**. The caps bind in 2029 (§7), which §2.2 named as the exact condition.
2. **What is the true 2030 magnitude? −5,654.7 MW** (3.27 % of gross peak) — against the
   §2.1 static prediction of −5,858 MW. The live machinery did better than the static floor,
   by 203 MW, and §2.1's "measured miss larger than ~5.9 GW would itself be a drift finding"
   trip-wire did **not** fire.

### 5.2 The answer nobody asked for: **2028 fails too**

The fail set is **three years, not one and not two**. S-5 had 2026–2028 reverting from
"graded PASS against the wrong bar" to "ungraded pending S-6"; graded, **2028 fails by
3,260.1 MW**.

**This is not a hold-last effect, and that is the point.** Per S-5 §1.1 the *model-side* bar
moved only in 2029–2030; the model always built to the published FPR in 2026–2028, where the
D-1 defect was checker-only. So in 2028 the model was already targeting 0.902813 — and this
run proves it was: the 2028 backstop built **842.8 MW, its entire ladder budget**, which it
would have had no reason to build at all against the old composite bar (§7.2 shows the
counterfactual need there is zero). **The model was already failing its own 2028 bar, at
full 3.3 GW, and the year-less checker never asked.** The D-1 repair did not mis-grade a
passing year into a failing one; it revealed a shortfall that was there all along.

### 5.3 I12 newly FAILS, and takes FC-2 with it

The requirement-implied floor rises with the FPR series (−11.94 % → −9.72 %) while the
reserve margin falls monotonically (−9.41 % → −12.99 %). The two cross in 2028 and never
re-cross: **three consecutive excursions**, which is the chain length at which I12 stops
being a WARN. I12 is therefore **FAIL**, not WARN — so PJM's live FC-1 fail set is
**{I7, I12}**, and **FC-2 moves CAVEAT → FAIL** on its row 1.

This directly supersedes the D13-era board reading that FC-2 "stays CAVEAT, not FAIL" and
that the 2030 excursion "remains a single recorded excursion (WARN-class) **until 2029's
margin is measured**." 2029's margin is now measured, and it is out of band.

### 5.4 2027 clears by 359.2 MW — and the fleet behind it is identical to 2026's

`fleet_by_fuel_after` for 2026 and 2027 are **byte-identical** (no retirements, no
commissioned entries — 2027's decisions all carry COD 2029), and firm capacity differs by
0.1 MW. So 2027's pass is bought **entirely by its lower published FPR**: the same fleet
measured against the 2028 factor would fail by **1,856.5 MW**. 2027 is not a year the supply
side won; it is the last year the bar was low enough.

Rule 21's suspicion clause applies to 2027 and is recorded rather than waved past: a
+359.2 MW clearance on a 145,508.5 MW bar is 0.25 %, and §1.3's un-intaken external-tie
leniency alone (−275.8 MW) would cut it to **+83.4 MW**.

## 6. Decomposition of the 2030 headline — it closes to 0.2 MW

The pre-declared §2.3 method: bar response from this run's own ledgers, residual named as
epoch drift.

```
committed FFR-3A-2 I7 (old bar)      150,088.0 − 150,454.0  =   −366.0 MW
+ epoch drift, accredited firm       150,291.4 − 150,088.0  =   +203.4 MW
− bar step  (0.902813 − 0.871017) × 172,733.7               = −5,492.3 MW
                                                              ───────────
= predicted 2030 I7                                            −5,654.9 MW
  MEASURED 2030 I7                                             −5,654.7 MW
  residual                                                        +0.2 MW
```

* **Peak drift is −0.1 MW** — the 2030 demand path is unchanged from the FFR-3A-2 epoch, so
  the back-solved anchor (172,733.8) and the measured peak (172,733.7) agree to the rounding
  of the committed verdict. There is no demand-side drift to attribute.
* **Epoch drift on the supply side is +203.4 MW of accredited firm** across 27 days and the
  landings §2.3 named (R-NEW default, D11-R entry-volume rule, FF-2A arms, demand/fuel
  re-derives). Independently corroborated: this run graded on the *old* bar gives 2030
  I7 = −162.5 MW against the committed −366.0 MW, a +203.5 MW difference — the same number
  from the other direction.
* **Everything else — 97 % of the move — is the corrected bar**, exactly the quantity S-5
  computed scorer-side and the owner signed as card C-A.

## 7. Why the gap did not close: one cap-bound channel, one that never fired

### 7.1 The reserve-margin backstop is the ONLY responder, and the growth ladder binds at 100 %

| year | ladder budget (gas_ct) | gas_ct decided | of which backstop | of which economic | budget consumed |
|---|---:|---:|---:|---:|:--:|
| 2026 | 842.8 | 0.0 | 0.0 | 0.0 | — |
| 2027 | 842.8 | 0.0 | 0.0 | 0.0 | — |
| 2028 | 842.8 | **842.8** | 842.8 | 0.0 | **100 %** |
| 2029 | 1,685.6 | **1,685.6** | 1,685.6 | 0.0 | **100 %** |
| 2030 | 3,371.2 | **3,371.2** | 1,371.2 | 2,000.0 | **100 %** |

The BLK-10 ladder is `ENTRY_GROWTH_LIMIT_MULTIPLE (2.0) × prior-max annual build`, seeded at
PJM's **measured EIA-860 gas_ct maximum of 421.4 MW/yr** over the trailing
10-year window, and doubling each year a build lands. The arithmetic reproduces the ledger
exactly: 2 × 421.4 = 842.8 → 2 × 842.8 = 1,685.6 → 2 × 1,685.6 = 3,371.2.

**The interconnection-queue caps never bind.** PJM's are 2.0 GW/yr per-tech gas_ct and
10 GW/yr all-tech; the ladder is an order of magnitude tighter in the first failing year.
§2.2 anticipated a cap-bound backstop but named the queue caps as the suspect — the measured
binding constraint is the **growth ladder**, and the reason is structural: the backstop is
wired to build `gas_ct`, the technology with PJM's *smallest* measured historical build rate
(gas_cc's ladder budget is 23,089.6 MW/yr and goes almost entirely unused).

Against gaps of 3.3–5.7 GW, a channel that can deliver 0.8–1.7 GW/yr of nameplate at a
0.94 UCAP credit cannot close them. **The clearance the model does buy is administrative
build and is reported as such** (§2.2): the FC-2 backstop share **rose 23.6 % → 25.3 %**,
exactly the direction pre-declared, still inside the (10 %, 30 %] CAVEAT band.

### 7.2 The backstop counterfactual, per year

| year | firm before backstop | requirement (corrected) | requirement (old composite) | backstop built | backstop *needed* under the old bar | I7 under the old bar |
|---|---:|---:|---:|---:|---:|---:|
| 2026 | 145,867.6 | 141,805.2 | 140,257.3 | 0.0 | 0.0 | +5,610.3 |
| 2027 | 145,867.7 | 145,508.5 | 142,521.5 | 0.0 | 0.0 | +3,346.2 |
| 2028 | 146,210.8 | 150,263.2 | 144,971.1 | 842.8 | **0.0** | +1,239.7 |
| 2029 | 146,584.9 | 153,001.5 | 147,612.9 | 1,685.6 | 1,093.6 | **+0.0** |
| 2030 | 149,002.5 | 155,946.1 | 150,453.9 | 1,371.2 | 1,544.0 (cap-bound) | −162.5 |

Read across: under the old bar, **2029 clears exactly at zero** on a backstop of 1,093.6 MW
that the ladder could afford. Under the corrected bar it needs ~5.1 GW of nameplate and the
ladder allows 1.7 GW. **2029's failure is a bar effect expressed through a cap** — precisely
the mechanism §2.2 said would decide the year. 2030 was cap-bound under *both* bars.

### 7.3 The retirement reliability floor did not fire — at all

§2.2's response #2, the S-4b mirror, **retained 0 MW in every year**: `floor_retained: []` in
all five committed evolution ledgers, and the (gitignored) `year_*_floor_retentions.json` are
all `[]`, which is the affirmative "the floor did not bind" record.

The reason is structural, not marginal. **Every retirement in the horizon is a step-0
`confirmed` exit** — 2029: 3,302.0 MW (Bruce Mansfield-class coal at p6166, 2,600.0 MW across
four tranches, plus 702.0 MW of oil at 1554); 2030: 530.4 MW (p602 coal, three tranches) —
and confirmed exits **bypass the reliability floor by design** (spec §5.1–§5.2; CLAUDE.md
step 0: the only exogenous fossil exit channel, and it bypasses the floor). The economic
screen retired **nothing** in 2026–2030.

So the floor had nothing eligible to retain. **On this PJM leg the corrected bar has exactly
one response channel, and it is the capped one.** The S-4b analogue is not merely small here
— it is structurally inert, and it would stay inert however much higher the bar went. That
is a cleaner negative than §2.2 pre-declared, and it is reported at full strength because it
changes what any future PJM adequacy lane should expect.

*(This also answers, in the negative for 2026–2030, the board's standing "retirement-screen
calibration, PJM's open suspect" hypothesis: the screen retires nothing, so it cannot be
what drives PJM's supply side over this horizon. Named, not acted on — §10.)*

### 7.4 A second structural interaction, measured and reported, not fixed

Economic entry carries a **two-year commissioning lag** (`entry_pipeline`: decided 2027 →
COD 2029; decided 2028 → COD 2030; decided 2029/2030 → COD 2031/2032, outside the horizon).
The backstop's gas_ct, by contrast, lands **same-year**.

In 2030 those two share one ladder budget (rule 19, one physical queue): economic entry took
**2,000.0 MW for a 2032 COD**, leaving the backstop 1,371.2 MW of the 3,371.2 available. Had
the whole budget been available to the same-year channel, 2030 would have gained a further
**+1,880.0 MW** of accredited firm and the miss would read **−3,774.7 MW** — still a FAIL, so
this changes no verdict, but it is a real mechanism observation: **a decision that commissions
outside the horizon consumes budget the in-horizon adequacy channel needs now.**

Recorded as an observation only. Nothing was re-tuned, re-gated or proposed here — rule 1:
this is the structure the model has, and a lane that wants to change it needs its own charter.

## 8. Scorecard against the pre-declaration (§2), item by item

| pre-declared (§2) | measured | verdict |
|---|---|---|
| §2.1 static 2030 ≈ −5,858 MW as an *upper bound*; live machinery "should do strictly better" | −5,654.7 MW, better by 203.4 | **held** |
| §2.1 a measured 2030 miss > ~5.9 GW would be a drift finding | 5.65 GW — trip-wire did not fire | **held** |
| §2.2 #1 backstop is the dominant responder, builds more in 2029–2030, share RISES | sole responder; +842.8 / +1,685.6 / +1,371.2 MW; share 23.6 → 25.3 % | **held** |
| §2.2 #1 "2029 joins iff the caps bind in 2029" | caps bind (100 % of ladder); 2029 joins at −4,832.1 | **held, and the conditional resolved** |
| §2.2 #1 caps suspected = interconnection-queue caps | queue caps never bind; the **BLK-10 growth ladder** binds | **refined** |
| §2.2 #2 floor retains firm MW in 2029–2030 (S-4b mirror) | **0 MW, every year** — all exits are confirmed exits, which bypass the floor | **did NOT materialise; structurally inert** |
| §2.2 #3 2026 is pure intake, becomes the committed base anchor | 2026 I7 +4,062.4 on peak 161,027.2 / firm 145,867.6 — now committed | **held** |
| §2.3 epoch drift decomposed and named | +203.4 MW firm, −0.1 MW peak; residual **+0.2 MW** | **held** |
| §2.4 an honest FAIL is a finding | three failing years, reported at full magnitude; nothing re-tuned | **held** |

**Nothing in the pre-declaration was moved, widened or reinterpreted after the fact.** Two
items came out *worse* than declared (the fail set is three years, and I12 newly fails), one
came out *better* by 203 MW, one suspect was refined (ladder, not queue cap) and one
pre-declared channel proved inert.

### 8.1 The honest headline

**PJM's T1-F adequacy position against the corrected bar is worse than the board has ever
recorded, and the reason is not the bar alone.** The bar accounts for 97 % of the 2030 move,
but the *shape* of the failure is a supply-side finding: a fleet whose only same-year
adequacy response is a backstop rate-limited to PJM's measured historical build of the one
technology it is wired to build, against a requirement that steps up 3.18 pp of peak and
stays there, with the retirement-side verb of the same requirement unable to answer because
every exit in the horizon is contractually confirmed rather than economic.

Per §2.4: **no clearance is claimed as organic adequacy** (there is none to claim — nothing
cleared); the FC-2 backstop-share rise is reported as administrative build; no band was
widened, no input reverted, nothing re-tuned in response. The one result that landed close
to a boundary — 2027 at +359.2 MW — is flagged under rule 21 with the leniency that would
nearly close it (§5.4), rather than quoted as a pass.

## 9. FC re-score

`scripts/forecast_verdict.py --tier t1f --summary … --run-config …`, committed artifacts
only, at `54ca19ae0782` / cache `31a19d815fa319a7`:

| category | before (FFR-3A-2) | **after (this run)** |
|---|---|---|
| FC-1 structural integrity | FAIL (I7 alone) | **FAIL — {I7, I12}** |
| FC-2 adequacy & equilibrium | CAVEAT | **FAIL** (row 1 I12; row 4 backstop 25.3 % CAVEAT) |
| FC-3 / FC-4 | n/a | n/a |
| FC-5 / FC-6 | SKIPPED | SKIPPED |
| FC-7 provenance & DOF | CAVEAT | CAVEAT (the program-wide absent DOF ledger) |
| FC-8 runtime | CAVEAT (8.8 GB) | CAVEAT (8.8 GB, no co-run) |
| **determination** | **HOLD** | **HOLD** |

The determination does not move; **the number of failing required categories does — one to
two.** FC-7's `dof ledger` CAVEAT is left exactly where lane D8 put it: D8's own §6
pre-registered `pjm-t1f` FC-7 as *unchanged* and deferred every verdict/board re-emission
until this lane and its siblings land. This run now commits the PJM bundle D8 said did not
exist, so the D8 follow-up has a `--dof-ledger` target it did not have before. **Not done
here** — it is D8's deferred work, not S-6's.

## 10. Registration + board refresh (rule 15, forecast namespace only)

**Registered:** `pjm-2026-2030-s6-ledger` via the single
`scripts/register_forecast_run.py --summary … --label s6-ledger --kind t1f` path. Committed:
`frontend/data/hindcast/pjm-2026-2030-s6-ledger.json`, `full_horizon_summary.json`,
`run_config.json`, `forecast_verdict.json`, resolved `config.yaml`, and
`evolution_2026..2030.json`. Heavy artifacts (parquet, `year_*_floor_retentions.json`, the
solve log) stay gitignored under the §3 block committed with the pre-declaration. The
generated namespace (`registry/`, `runs/`, `manifest.js`, `program-status.js`) stays
gitignored — the Pages deploy is its writer; `--reindex` was run locally for the `file://`
preview only. **No `VERDICT_MAP` entry was added**, following the S-4V/S-4b precedent
exactly: the run renders score-only in the explorer and the verdict lives on `pjm-t1f`.
**The backcast namespace was not written to.**

**Verdict keys, preserve-then-overwrite:** the FFR-3A-2 measurement is preserved **verbatim**
at **`pjm-t1f-ffr3a2`** (byte-identical apart from the preservation note appended to its
provenance — asserted programmatically before write), and the bare **`pjm-t1f`** now carries
this run's own scorer output with provenance `{scored_at_sha 54ca19ae0782, scored_at_date
2026-08-31T00:43:56Z, cache_epoch 31a19d815fa319a7, session capx-S6-pjm-ledger}`. **One key
added, one key changed, every other key in the file asserted unmoved.**

**Board (`program-status.json`), PJM block only:** `fc.FC-2` CAVEAT → FAIL (the only cell
that moves); the I7 blocking row restated to the measured three-year fail set; a new
I12/FC-2-row-1 blocking row; `gate.b_t1f_verdict.detail` and `gate.note` refreshed. Every
superseded clause — the S-5/D13 restatement provenance included — is preserved **verbatim**
inside its replacement. **The leg status does not move: fail before, fail after**; `open`
stays `false`, `closed_on` stays `['b']`, leg (d) untouched, no authorization created.
Nothing opened and nothing closed. A `s6_pjm_ledger` lane record carries the before/after,
and the block deliberately uses no `forecast-provenance/v1` field names so the staleness
checker can never read a board edit as a scoring event.

**Cross-ISO prose FLAGGED, NOT EDITED** (the S-4V discipline — it is outside this lane's
charter). Four statements are now stale and are routed to the director in
`s6_pjm_ledger.flagged_not_edited`:

1. `gate_reading`'s "LIVE FC-1 FAIL SETS, exactly: … PJM {I7}" and "In PJM and MISO, I7 is
   now the ONLY FC-1 failure left" — PJM's set is **{I7, I12}**.
2. `gate_reading` and `headline` still quote "2029 plausibly joining … an INFERENCE, flagged,
   which lane S-6 measures" and the 2030 miss as 5,858 MW — **measured: 2028+2029+2030, and
   2030 is 5,655 MW**.
3. `gate_reading`'s "The SMALLEST live miss is now MISO 2027 (3,659 MW)" — **PJM 2028 at
   3,260 MW is smaller.**
4. `gate_reading`'s "retirement-screen calibration, PJM's open suspect" — answered in the
   negative for this horizon (§7.3); the live suspect is the ladder-paced backstop.

## 11. Guardrail compliance

* **Rule 22 `[R-HOLDOUT]`:** forecast mode, 2026–2030 only. No out-of-training backcast year
  was solved, scored or registered; no measured actual was read; the tier-scoped holdout
  freeze is not implicated in either direction. The §2.1b window cap is satisfied by
  construction (5 solve-years — no `--full-solve-authorized`, and none was passed).
* **Rule 13 `[R-MEASURED]`:** no measured outcome fed back. Every input is the shipped
  default at golden posture; the §1.3 external-tie leniency was **not** intaken (a registry
  re-vintage is its own lane under rule 23) and is carried as a named one-sided caveat on
  every I7 number above, including the sensitivity in §5.4.
* **Rule 15 `[R-DASHBOARD]`:** registered on the **forecast** namespace via the single
  `register_forecast_run.py` path, in the session that produced it. Backcast surfaces
  untouched — no keeper shard, no `status/*.js`, no `calibration-complete.json`, no backcast
  registry.
* **Rule 28 `[R-MECH-MATRIX]`:** duty (a) discharged — the PJM lever queue
  (`docs/mechanism-testing-matrix.md` §5.3) was read; **no lever taken, this is not a
  mechanism session**. No mechanism proposed or tested, no cell verdict minted, no
  `ScenarioConfig` field added, **no shard edited**. `scripts/check_mechanism_matrix.py`
  passes (integrity OK, anchors OK, keeper stamps OK) — verified unchanged at this diff.
* **Rules 5 / 24 `[R-NO-MAGIC]` / `[R-REGISTRY]`:** no new tunable, no config change, no code
  change. Every number in this finding is read from a committed artifact or computed from a
  registry constant cited in place.
* **Rule 1 `[R-STRUCT]`:** two structural observations (§7.3 floor inertness, §7.4 ladder
  crowd-out) are reported and routed, not acted on. Nothing was adjusted to move a residual.
* **Rule 27 `[R-PUSH]`:** Opus session (per the r#20 model-economy doctrine — this lane is
  pre-declared execution). No source file was rewritten from response content; the two
  ≥300-line JSON surfaces were edited in place by guarded scripts and blob-verified after
  push (§12).
* **Collision care:** `ff-verdicts.json` and `program-status.json` edits are PJM-keyed only,
  asserted programmatically before write; rebased on `origin/main` before pushing. No other
  lane's block was read into or resolved. At session start `git ls-remote` showed only
  `main` and the D12-A orphan branch (ERCOT config/matrix — disjoint surfaces), so no live
  contention existed.
* **No GitHub Actions workflow** was created; the solve ran in-session.

## 12. What this leaves open (named, routed, not built)

1. **The four stale cross-ISO board statements** (§10) — director's, per the S-4V precedent.
2. **The external-tie re-vintage** (1,281.7 → 1,005.9 MW UCAP): a rule-23 intake lane of its
   own. Direction is known and one-sided — it widens every miss by 275.8 MW and cuts 2027's
   pass to +83.4 MW.
3. **The 2029/30 PJM planning parameters**, scheduled for publication with the December 2026
   BRA. On publication the registry row supersedes hold-last for those years automatically
   (S-5 §1, the intake pointer is already in place) and this leg should be re-measured.
4. **D8's deferred FC-7 re-emission** now has a committed PJM bundle to point `--dof-ledger`
   at, which it did not have when D8 pre-registered `pjm-t1f` FC-7 as unchanged.
5. **Two structural questions this run raises and does not answer** — whether the backstop
   should be ladder-paced against a technology PJM barely builds (§7.1), and whether an
   out-of-horizon COD should consume in-horizon adequacy budget (§7.4). Both are mechanism
   questions requiring their own charter, their own pre-declaration and a matrix cell. **This
   lane takes neither.**
