# FINDING — caiso-203: the charter's build object is **ALREADY BUILT, PROMOTED AND ARMED** — the caiso-150 §F reconciliation IS `caiso_firm_import_selfsched_clip`, built at caiso-151 (2026-07-31), keeper-promoted the same day, and live in every keeper since including `2026-08-17-caiso-200-h1-memberpanel`, whose own committed D-2/D-4 rows prove the clip engaged (forced 17.938/22.684/22.494 TWh = caiso-150's unclipped 18.856/27.232/27.989 minus **exactly** the caiso-151 removals 0.919/4.548/5.495). Every deliverable the charter enumerates exists at HEAD: the rule-23 frozen derive with honesty gates (caiso-151), the ScenarioConfig field + matrix row (caiso-151), the `D4_WINDOWS` entry (caiso-151), D-2/D-4 gate visibility (caiso-155). **NO SOLVE SPENT** — kill-before-build; the stale `caiso_firm_selfsched_floor` cell **O → K** as a bookkeeping adjudication on the existing caiso-151 evidence; keeper unchanged (2026-08-19)

**Keeper `2026-08-17-caiso-200-h1-memberpanel` UNCHANGED. No mechanism armed, no
`ScenarioConfig` field added, no derive run, no corpus fetched, no LP built,
nothing registered.** This is the kill-before-solve discipline
(caiso-129/140/150/202 pattern) firing on the charter's own premise: the defect
statement the charter carries describes the **pre-caiso-151** model, and the
mechanism it orders built is the one caiso-151 built, gate-tested, A/B'd and
promoted eighteen days before this charter was written. Executing the charter
literally would have violated rule 28a (re-testing the adjudicated `K` cell
`caiso_firm_selfsched_clip` with no new evidence), rule 19 (a second field
reconciling the same floor against the same measured series), and rule 23
(re-deriving a frozen artifact with no source-data change).

No instrument was needed: every number below reproduces from committed bytes —
`src/market_sim/config/scenarios.py`, `src/market_sim/model/interchange/caiso.py`,
`src/market_sim/data/caiso_intertie_bids.py`,
`data/raw/_processed-legacy/caiso_intertie_selfsched_ceiling.csv`,
`scripts/legitimacy_diagnostics.py`, and the keeper bundle
`results/calibration/caiso200_h1_memberpanel/` (`run_config.json`,
`legitimacy_diagnostics.json`).

---

## §A — the charter vs the record, deliverable by deliverable

The caiso-203 charter ordered: (1) a rule-23 frozen derive of the measured
(month × hod) self-schedule series from the PUB_BID_DAM intertie corpus per
caiso-150 §F; (2) a new `ScenarioConfig` field flooring `min_gen` at the
measured self-schedule instead of full shaped capability, plus a `D4_WINDOWS`
entry and D-2 mechanism id "so the floor is finally gate-visible"; (3) a
PRECHECK pushed before any solve; (4) an A/B vs a same-HEAD zero-delta control
over 2023–2025, both registered. Each already exists:

| charter deliverable | where it already exists | evidence |
|---|---|---|
| frozen derive, honesty gates | **caiso-151** — `scripts/data/derive_caiso_intertie_selfsched.py` → `caiso_intertie_selfsched_ceiling.csv` (288 rows, committed) | G1 CV 0.042 ≤ 0.20; G2 LOYO level 4.6/8.4/4.6 % ≤ 25; G3 LOYO shape 19.3/12.3/18.6 % ≤ 25; G4 288/288 (FINDING-caiso151 §B) |
| balanced corpus, OASIS re-fetch | **caiso-151** — independent 357-day balanced re-fetch (the caiso-150 corpus container was already gone then) | reproduces caiso-150: unclassifiable 94.54 % vs 94.91 %, swing 1.52× vs 1.49× |
| field flooring min_gen at the measured series instead of full shaped capability | **caiso-151** — `caiso_firm_import_selfsched_clip` (scenarios.py): `min_gen[t] = min(pmax × availability[t], ceiling[t])`, system ceiling pro-rata across the firm tranches, zero allocation parameter | the exact caiso-150 §F form ("why this form and no other") |
| `D4_WINDOWS` entry | **caiso-151** — `(MECH_FIRM_IMPORT, None): (0, 24)` in `scripts/legitimacy_diagnostics.py` | line 332 at HEAD, with the caiso-151 provenance comment |
| D-2 id / gate visibility | **caiso-155** — the plant-set defect caiso-151 §F filed (plant_code ≤ 0 rows dropped from the diagnostics matrix) was fixed ISO-generically | `firm_import` rows present in the caiso-200 keeper's committed `legitimacy_diagnostics.json`, D-2 and D-4, all three years |
| PRECHECK before solve | **caiso-151** — `PREREG-caiso151-firm-selfsched-clip-2026-07-31.md`, pushed before either arm solved | in-repo |
| A/B vs same-HEAD control, `--year 2023 2024 2025`, registered | **caiso-151** — single-flag A/B, promoted keeper `2026-07-31-caiso-151-firm-selfsched` | FINDING-caiso151 §C–§E; the runs were later pruned from the site under the 2026-08-15 retention directive — evidence retained, nothing retracted |

Even the charter's pre-registered expected directions are the caiso-151
*measured outcomes*: C3a UP (+0.045/+0.626/+0.494 pp, confirmed E1-adverse,
accepted under rule 1), net imports toward actual (0.042/1.099/0.628 TWh of
import stops flowing), displacement import → CC_REGULAR ~1:1 (the C1
CC_REGULAR heal direction), C8/C6 clean both arms. The charter and caiso-151
are the same session specification, written twice.

## §B — the verification chain run this session (committed bytes only)

1. **Field + injector + artifact.** `caiso_firm_import_selfsched_clip` is a
   documented `ScenarioConfig` field (default off, CAISO-only, requires
   `caiso_firm_import_selfschedule`); `inject_caiso_firm_import_selfschedule`
   takes `selfsched_clip` and applies the pointwise min via
   `measured_intertie_selfsched_ceiling`; the frozen artifact is committed and
   present (3,777 bytes).
2. **Armed in the current keeper.** `caiso200_h1_memberpanel/run_config.json`
   carries `caiso_firm_import_selfsched_clip: true` in BOTH the override
   channel (`coal_prb_sigmoid_overrides`) and the resolved `scenario_config` —
   carried unbroken through the caiso-151 → 153 → 157 → … → 188 → 196 → 197 →
   199 → 200 keeper lineage (every promotion in that chain was G-DELTA /
   recipe-preserving on this flag).
3. **Engaged, not just armed — the arithmetic identity.** The keeper's
   committed `legitimacy_diagnostics.json` D-2 rows show `firm_import` forced
   energy **17.9378 / 22.6842 / 22.4940 TWh** (2023/24/25). caiso-150 §A
   measured the *unclipped* floor at 18.856 / 27.232 / 27.989 TWh; the
   differences — 0.918 / 4.548 / 5.495 TWh — equal the caiso-151 A/B's
   measured clip removals (0.919 / 4.548 / 5.495) to rounding. The D-4 rows
   read `firm_import, h0-23, off-window 0.000, pass` in all three years.
4. **Therefore the charter's defect paragraph is stale.** "Floored min_gen ==
   pmax×availability in ~8,000 h/yr — 27–28 TWh/yr must-flow … over-forces
   4.634/5.705 TWh/yr" and "sits outside every legitimacy gate … no
   D4_WINDOWS entry" both describe the world caiso-150 measured on
   2026-07-31, remediated the same day by caiso-151 and made gate-visible by
   caiso-155 on 2026-08-02.

## §C — why the charter could not be executed literally

- **Rule 28a (DO-NOT-REDO).** `caiso_firm_selfsched_clip` is an adjudicated
  `K` cell; the charter presents no new evidence (its evidence base is
  caiso-150 itself, the evidence the K adjudication consumed). caiso-151's own
  binding list forbids "re-deriving `caiso_intertie_selfsched_ceiling.csv`
  against a residual" and replacing/stacking the clip.
- **Rule 23.** The frozen derive re-runs only on a *source-data* update. None
  is cited; the OASIS corpus would regenerate the same pooled climatology.
  OASIS reachability was therefore **not** tested — the charter's data-blocker
  clause is moot because no fetch is owed.
- **Rule 19.** A "new ScenarioConfig field" flooring min_gen at the measured
  series would be a second mechanism reconciling the same floor against the
  same measured object. Interpreted as the clip, it is a duplicate; the only
  *distinct* reading — using the measured series as the floor **level** (so
  raising the midday floor toward the ~3,600–4,100 MW ceiling where the
  unclipped shape sits at ~1,000 MW) — is exactly what caiso-150 §B/§H
  forbids: the series is a one-sided **both-directions ceiling**, most
  generous midday where CAISO *export* self-schedules peak, and "the midday
  ratio must not be quoted as under-forcing". A floor AT the ceiling has no
  measured lower-bound support in any hour.
- **The A/B is vacuous either way.** With the clip already in the baseline
  recipe, the charter's treated arm is the control (zero delta); the
  inadmissible midday-forcing variant is the only arm that would differ, and
  it fails rule 13 before any solve.

## §D — how the stale premise arose (genealogy, so it is not repeated)

The `caiso_firm_selfsched_floor` cell was created `O` by caiso-150 ("chartered,
in play, verdict not yet reached"). caiso-151 executed the charter but stamped
its result on a **new** row (`caiso_firm_selfsched_clip` O → K) and never
re-adjudicated the floor cell, which stayed `O` with caiso-150-era evidence
text ("mechanism SPECIFIED but deliberately NOT built") still attached to the
base row note. caiso-202 §F.3 (2026-08-18) then read the open cell at face
value — "completing the O-cell `caiso_firm_selfsched_floor` reconciliation
REMOVES forced overnight supply" — even though its own §C acquittal was
measured on the keeper *with the clip armed*, and appended a direction note to
the stale cell. The caiso-203 charter compounded it by quoting caiso-150's
unclipped measurements as the current keeper state. This is the mirror image
of the caiso-167 stale-parenthetical incident (where queue item 2 wrongly read
as *finished* by caiso-151): a matrix bookkeeping omission at caiso-151 let
one mechanism's status be misread for eighteen days — in both directions.

## §E — the adjudication: cell `caiso_firm_selfsched_floor` O → K

A **bookkeeping adjudication on existing evidence** (the caiso-167/169
"bookkeeping repair, not an adjudication of new work" pattern), within this
charter's own deliverable 4 authorization ("update the CAISO matrix shard cell
O→K/R with evidence"). The floor mechanism (`caiso_firm_import_selfschedule`)
is armed in every CAISO keeper since caiso-77; the caiso-150 wrong-object
defect chartered against it was remediated at caiso-151 by the composed
selfsched clip and the caiso-138 envelope clip; it is D-2/D-4-visible since
caiso-155 and D-4-passes on the current keeper. That is a `K` — the verdict
was *reached* on 2026-07-31 and simply never recorded on this cell.

Two standing limitations are carried as annotations on the cell, not as open
build work:

1. **Below the measured ceiling, the floor's shape basis is still EIA-930
   realised net corridor interchange** — the wrong object *in kind* (caiso-150
   §C). No admissible measured replacement exists: the §B identification wall
   means only the one-sided ceiling is measurable, so the clip form is the
   complete reconciliation the public record supports ("why this form and no
   other", caiso-150 §F). Any successor needs a new source that splits
   direction — which caiso-150 §H adjudicated unreachable from the public
   feed.
2. **caiso-202 §F.3 direction note carried:** the reconciliation is
   C3a-adverse and is never a C3a lever (confirmed: caiso-151 paid
   +0.045/+0.626/+0.494 pp on C3a, accepted pre-registered under rule 1).

## §F — record changes

- **Keeper, markers, holdout freeze: UNCHANGED.** No solve, no bundle, no
  dashboard registration due (rule 15 applies to completed runs — the
  caiso-134/140/150/202 disposition).
- **Matrix (rule 28b, CAISO shard only):** `caiso_firm_selfsched_floor`
  cell **O → K** with the full lineage evidence; re-stamp block appended to
  the shard tail; §5.2 caiso-203 block added to
  `docs/mechanism-testing-matrix.md`. No other cell moves.
- **`docs/calibration-log/caiso.md`:** caiso-203 entry.
- **The DOF-ledger stale-text item (caiso-202 §H) stays FILED, not fixed** —
  its trigger is "the next promotion's attestation" and no promotion occurred.
- **The lane RETURNS TO ITS RESTING STATE** (caiso-201 Q1). This charter was
  the owner's second re-opening of the rested lane; like caiso-202 it ends
  with committed diagnosis, no solve, and the resting state intact.

## §G — DO-NOT-REDO (new, binding; carried lists of caiso-151 §, caiso-150 §H, caiso-202 §I, caiso-140 §G unchanged)

- **Re-chartering a build of `caiso_firm_selfsched_floor` / the caiso-150 §F
  reconciliation absent new source evidence.** The build exists
  (`caiso_firm_import_selfsched_clip`, caiso-151, K, armed in the keeper);
  the cell now says so. A future charter against this object must cite
  evidence newer than caiso-151.
- **Re-fetching the OASIS PUB_BID_DAM corpus to regenerate
  `caiso_intertie_selfsched_ceiling.csv` with no source-data change**
  (rule 23; caiso-151's carried clause).
- **Flooring firm-import min_gen AT the measured self-schedule ceiling** (as
  a level, in any hour): the series is a one-sided both-directions upper
  bound; midday it is dominated by export self-schedules (caiso-150 §B/§H).
- **Quoting the caiso-150 §A/§C unclipped-floor measurements
  (18.9/27.2/28.0 TWh forced; 4.6/5.7 TWh over-forced; "no D4_WINDOWS
  entry") as the state of any keeper from caiso-151 onward.** The keeper
  numbers are the D-2 rows: 17.94/22.68/22.49 TWh.

Next number: caiso-204.
