# PREREG — nyiso-125: NYISO's per-neighbour seam deliverability envelope

**Date:** 2026-08-04 · **ISO:** NYISO · **Years:** 2023–2025 (training only, rule 22) ·
**Branch:** `claude/nyiso-125-seam-envelope-gi109j` ·
**Keeper at dispatch:** `2026-08-04-nyiso-120-c119-scope` (verified at this session's HEAD).

**This file is committed and pushed BEFORE any solve runs.** It names the
construction, the DOF entries, the blast radius, the kill gates and — in §4 —
the adverse case, in advance.

---

## §0 — verification at this session's own HEAD

Re-derived here, committed artifacts only, no solve:

* `origin/main` at rebase: **`3a25b7d6`** (dispatch line said `2c412668`; main
  moved, this session rebased onto the current head and re-read everything).
* `frontend/data/backcast/keepers/NYISO.json` → keeper
  **`2026-08-04-nyiso-120-c119-scope`**. Confirmed by reading the file.
* nyiso-124's commit **`cf15bb54` IS ON MAIN** (`git merge-base --is-ancestor`
  returns true). The evidence base this session builds on is merged.
* NYISO holds a **`complete`** (validation-tier) marker; **`final` is EMPTY**.
  The **holdout spend freeze is ACTIVE** and outranks the marker. Nothing
  outside 2023–2025 is solved, scored, read or registered.

`scripts/calibration_verdict.py --run-id` and `scripts/audit_keepers.py --iso
NYISO` are re-run and their output recorded in the FINDING, not here — this
file is the pre-commitment, and it is written before the solve, not before the
verification.

---

## §1 — the object, and why this lane

nyiso-124 §6.1 diagnosed the successor object with no solve: **the model's
external seam delivers the right NET and the wrong DISTRIBUTION.** The three
downstate border links sit at their bound in 98–100 % of *all* hours of all
three years (a flat 3,800 MW against a measured downstate median of 1,870 /
1,772 / 2,040 MW) while `NYISO_external>Upstate_West` runs net EXPORT
(−1,003 / −1,520 / −1,689 MW) against a measured IMPORT (+668 / +454 / +148 MW).
The four-link net still reconciles to 2–11 %. ~1.8–2.0 GW of surplus import
lands EAST of the Central-East cutset, so the east never draws on the west and
the model's CE link carries 722.8 MW at the median (util **0.253**) where the
real interface carries util **0.591**.

The matrix row is `seam_flow_envelopes`, NYISO cell **`U`**. Rule 25
`[R-ISO-SCOPE]` is binding both ways: PJM's `pjm_seam_envelope_by_neighbor`
verdict does not fill it. Every parameter below is derived from **NYISO's own
market** — the MIS P-32 "Interface Limits and Flows" posting, committed for all
three training years at `data/raw/NYISO/interface-flows/`.

---

## §2 — Phase 0: what is identified, and what is refused

Probe: `scripts/probes/_nyiso125_seam_envelope.py` (no LP).
Record: `results/calibration/_nyiso125_seam_envelope.json`.

### 2.1 One row is excluded as an accounting duplicate

`SCH - HQ_IMPORT_EXPORT` is not an independent tie. It equals `SCH - HQ - NY`
to within 0.5 MW in **40.7 / 77.9 / 90.9 %** of hours (corr 0.977 / 0.989 /
0.993) and is the only SCH row carrying the ±9,999 "unbounded" sentinel on its
negative limit — the signature of a proxy schedule, not a rated path. Counting
it would double the HQ seam. **EXCLUDED.**

### 2.2 The POSTED-limit envelope is identified — and REFUTED as the repair

NYISO posts an hourly directional limit per external schedule. On the three AC
seams that land on the two links carrying the defect, the measured flow reaches
95 % of the posted positive limit in **0.0–0.1 % of hours in every year**
(NE - NY 0.000/0.000/0.000; OH - NY 0.000/0.000/0.000; PJ - NY
0.000/0.001/0.001). The posted rating is not what allocates this seam. Worse,
a posted-limit envelope would **LOOSEN** exactly the links that over-deliver
(Upstate_West ≥3,650 MW against the incumbent 3,000; Capital_Hudson 1,400 + the
PJ share against 1,600) while moving the downstate links by ~25 MW and ~10 MW.
**Measured refutation, zero-DOF, recorded — not armed.** (This is distinct from
and consistent with the nyiso-122 Tier-3 refutation, which concerned the
*internal* `NYISO_INTERFACE_TTC_BY_*` limits and is not re-opened here.)

### 2.3 The flow envelope is IDENTIFIED on NYC and Long_Island, and REFUSED on the eastern pair

Attribution is by the NYCA load zone each tie physically lands in (NYISO Gold
Book external interconnections — the same tie geography already cited in
`interchange/spec.IMPORT_NODE_LINKS["NYISO"]`):

| landing zone | ties | attribution |
|---|---|---|
| **NYC** (Zone J) | `SCH - PJM_HTP`, `SCH - PJM_VFT` | **unambiguous** |
| **Long_Island** (Zone K) | `SCH - PJM_NEPTUNE`, `SCH - NPX_CSC`, `SCH - NPX_1385` | **unambiguous** |
| Capital_Hudson (F+G) | `SCH - NE - NY` + part of `SCH - PJ - NY` | **ambiguous** |
| Upstate_West (A–E) | `SCH - HQ - NY`, `SCH - HQ_CEDARS`, `SCH - OH - NY` + part of `SCH - PJ - NY` | **ambiguous** |

`SCH - PJ - NY` is the only row that spans the Central-East cutset: the PJM AC
interface carries the Ramapo 345 kV PARs and the Waldwick 230 kV ties into
Zone G (**east**) *and* the Homer City–Stolle Road / Falconer ties into Zone A
(**west**). **No public source separates them** — not NYISO's P-32, and not
PJM's own tie-line file, which buckets all four NYISO-facing ties as
`NYIS`/`NEPT`/`HUDS`/`LIND` with the AC ties as ONE row
(`data.eia930.envelopes._PJM_TIE_ZONE`).

Measured consequence — the bracket on the split alone:

| year | Capital_Hudson import env p50 | Upstate_West import env p50 |
|---|---|---|
| 2023 | **45 – 955 MW** (width 910) | 1,204 – 2,199 MW (width 995) |
| 2024 | **0 – 916 MW** (width 916) | 1,285 – 2,429 MW (width 1,144) |
| 2025 | **0 – 1,134 MW** (width 1,134) | 708 – 1,891 MW (width 1,183) |

Capital_Hudson is *the link carrying the defect*, and its envelope is
unidentified across the entire range that matters. **Choosing inside that
bracket is choosing a number so the Central-East link starts binding — the
exact failure the charter forbade.** `REFUSED ON IDENTIFICATION` (rule 20
`[R-DOF]`). It is not armed, not approximated, and not carried as a
default-off knob (rule 26 `[R-DELETE]`: an unidentified parameter that still
parses is a re-armable answer key).

### 2.4 The split-invariant JOINT cap is identified — and provably inert

The (Upstate_West + Capital_Hudson) envelope needs no split. It is identified,
and it constrains nothing: the model's joint AC-seam net import (**+597 / +80 /
−89 MW** p50) already sits far **below** the measured envelope (1,818 / 1,706 /
1,243 MW p50). The defect is the *within-pair* allocation, which a joint cap
cannot see. **Identified, measured, INERT — not armed.**

---

## §3 — what IS armed: `nyiso_seam_deliverability_envelope`

**One mechanism, one flag, one delta, default OFF.**

The two border links whose external ties land unambiguously in a single NYISO
load zone — `NYISO_external>NYC` (Zone J) and `NYISO_external>Long_Island`
(Zone K) — have their flat, symmetric, time-invariant static TTC replaced by
NYISO's own measured **directional hourly deliverability envelope**:

```
net[t]        = Σ over that zone's ties of the P-32 hourly net schedule
                (NYISO sign: + = import into NY), keyed onto the model's fixed
                non-leap 8760 clock by LOCAL (month, day, hour)
import_cap[t] = p90 of clip(net, 0, ·) within t's (month × hour-of-day) bin
export_cap[t] = p90 of clip(−net, 0, ·) within t's (month × hour-of-day) bin
ttc[t, i]        = min(import_cap[t], incumbent_ttc[i])      # upper bound
ttc_import[t, i] = min(export_cap[t], incumbent_ttc[i])      # lower bound = −this
```

`Upstate_West` and `Capital_Hudson` keep their incumbent statics **untouched**
(§2.3). No LP change is required: `model/lp/bounds.py` already accepts a
`(T, n_links)` `ttc` and an asymmetric `ttc_import`.

The `min(·, incumbent)` guard is a documented monotonicity property, not a
tuning step — the envelope is a *deliverability* envelope and cannot exceed the
*rating*. **It is a no-op in all three years** (NYC envelope max 975 < 1,000;
Long_Island max 1,190 / 1,190 / 1,125 < 1,200) and this is stated in advance so
a later reader cannot mistake it for a fitted clip.

Measured effect at the seam, computed with no LP:

| year | binds below the static | mean MW removed, NYC | mean MW removed, Long_Island | total |
|---|---|--:|--:|--:|
| 2023 | 100.0 % of hours | 94.7 | 212.5 | **307.2** |
| 2024 | 100.0 % of hours | 177.9 | 228.5 | **406.4** |
| 2025 | 100.0 % of hours | 97.5 | 271.5 | **369.0** |

That is **17–22 %** of the ~1.8–2.0 GW misallocation. It is **stated in advance
that this mechanism cannot close the defect** — the half that could is refused
in §2.3. It is armed because it is structurally right and measured (rule 1
`[R-STRUCT]`, rule 14 `[R-ACCURATE]`), not because it is sufficient.

### 3.1 Rule 19 `[R-ONE-MECH]`

This **replaces** the incumbent flat symmetric TTC on those two links. It does
not stack on it, and no other mechanism caps those links: `nyiso_import_sil_retire`
(on in the keeper) already dropped the mis-attributed 4,350 MW
`NYISO_simultaneous_import` scalar, leaving the per-link TTCs as the sole seam
bound. **nyiso-100's retirement is NOT re-opened and the retired scalar's
number is never re-installed** — this mechanism introduces no aggregate cap of
any kind. The `nyiso_li_tsl` / `nyiso_nyc_lcr_tsl` caps act on the *internal*
`Lower_Hudson→NYC` and `NYC→Long_Island` links, a different boundary.

---

## §4 — the DOF ledger, and the adverse case, pre-registered

### 4.1 Degrees of freedom

| parameter | value | identification source | swept? |
|---|---|---|---|
| tie → landing-zone map | 5 ties → 2 zones | NYISO Gold Book tie geography; already cited in `IMPORT_NODE_LINKS["NYISO"]`. Every tie lands in ONE NYISO load zone. **Attribution-invariant — zero freedom.** | n/a |
| envelope percentile | **90.0** | The repo-wide deliverability-envelope convention: `constants.MISO_SEAM_FLOW_PERCENTILE == PJM_SEAM_FLOW_PERCENTILE == 90.0` and `eia930.envelopes.measured_interchange_envelope`'s default, each carrying the same "headroom above the median, minus the top ~10 % transient/loop-flow hours" rationale and each explicitly *not* tuned to a residual. A **definitional** constant, fixed ex ante. | **NEVER.** Pre-registered here: this session will not sweep it, and a value chosen because a score moved would be a rule 1 / rule 11 violation. |
| binning | month × hour-of-day | Same as MISO/PJM. Definitional. | never |

**New free parameters: ZERO.** One declared definitional constant
(`NYISO_SEAM_FLOW_PERCENTILE = 90.0`) enters `constants.py` and the flag enters
`ScenarioConfig`, so both appear in `run_config.json` (rule 24 `[R-REGISTRY]`).
The keeper's DOF ledger `n_residual` is expected to stay **6**.

**Stated weakness, not hidden:** a p90 of *realized schedules* on a merchant
HVDC tie embeds firm-transmission-service scheduling behaviour, not only
physical capability. It passes rule 13's test the same way MISO's and PJM's do
— the construction regenerates for a forward year from the forward tie set and
responds to changed conditions (it moved 974 → 828 → 975 MW on NYC and 1,012 →
986 → 990 MW on Long_Island across 2023–25 purely from measured behaviour, and
CHPE's 2026 entry is picked up automatically) — no more strongly and no more
weakly than the two cells the repo has already adjudicated.

### 4.2 The numeric prediction (falsifiable, made before the solve)

`Capital_Hudson` is **already at its bound in 100 % of hours**, so it cannot
absorb the displaced MW. Under the monthly EIA-930 reconciliation band the
total net import is pinned. The 307 / 406 / 369 MW removed from downstate
landing must therefore arrive at `Upstate_West` (as reduced export) and reach
load through Central East. **Prediction: the model's `Upstate_West>Capital_Hudson`
flow rises from 722.8 MW p50 (util 0.253) toward ~1,050–1,120 MW (util
~0.37–0.39), closing ~30–40 % of the gap to the measured 0.591.**

If instead the CE flow is unchanged, the displaced MW was met by domestic
generation rather than upstate import — a **different** finding, and it will be
reported as such, not retuned around.

### 4.3 The adverse case — stated honestly, in advance

Cutting downstate over-import **raises downstate prices and lowers upstate
prices**. Against the keeper's C3a (`price_mean`, ±10 % band, `rt_lw` bench —
the ONLY C3a basis, and the only basis levels are quoted from):

| year | keeper C3a | direction this arm pushes | risk |
|---|--:|---|---|
| 2023 | **+7.2 % PASS** | further **UP** | **crosses +10 % and FAILS** |
| 2024 | −0.9 % PASS | up | likely stays in band |
| 2025 | **−10.1 % FAIL** | **UP — toward the band** | this is the year it should help |

So the pre-registered adverse case is explicit: **the arm may fix 2025 and
break 2023.** nyiso-123's identity (a model that closed the basis and changed
nothing else scores its own upstate error +24.74 / +8.60 / +2.45 %) is *not*
this counterfactual — this arm moves upstate DOWN as well — but 2023 is the
year at risk and it is named now, before the numbers exist.

**If that happens it is a RESULT, reported as such.** It is not a reason to
sweep the percentile, scope the mechanism to one year or one zone, unarm the
export leg, or ledger a caveat. C3c remains the SOLE ledgered caveat (budget
**1 of 3, UNSPENT**); C3a-2025 is a criterion FAILURE deliberately NOT ledgered
and this session will not "solve" it by ledgering it. Owner decision D.1 (HOLD
PROMOTION, FIND ROOT CAUSE) stands.

**Leave-one-year-out** within 2023–2025 is scored before any promotion is
proposed. In-sample gain with held-out degradation is overfitting, not skill.

---

## §5 — blast radius

* **Solve-affecting surface:** the column bounds of exactly **2** of the LP's
  flow variables (`NYISO_external>NYC`, `NYISO_external>Long_Island`), NYISO
  only, gated on a default-off flag. No other ISO can reach the code path.
* **No LP change.** `bounds.py` already supports `(T, n_links)` `ttc` +
  asymmetric `ttc_import`; the ERCOT GTC and PJM measured-interface overlays
  use the same seam.
* **Untouched:** `NYISO_INTERFACE_TTC_BY_MONTH` / `_BY_YEAR` (nyiso-122/124
  refutation — not re-opened), `IMPORT_NODE_LINKS` statics, the import tranche
  ladder and its prices, `EXTERNAL_SIMULTANEOUS_LIMITS`, every floor/bridge
  mechanism, every other ISO.
* **Control:** a same-HEAD `--no-…` twin, same recipe, 2023 2024 2025 in ONE
  invocation and ONE bundle each (rule 16). The control must reproduce the
  keeper's C3a; if it does not, the A/B is void and is reported as void.
* **Network layer:** both arms commit `hourly/network_<year>.parquet` with
  `git add -f`. The `unit_network_layer_sidecar` NYISO cell is already `K` —
  nothing to arm — and it removes nyiso-124's one provenance caveat (its
  evidence came from `nyiso116_c3c_unitlayer`, a nyiso-113-recipe replay whose
  G1 FAILED at max |Δp| 10.5 / 10.6 / 9.0, licensed for C3c tail work only).

---

## §6 — kill gates (pre-registered; any fire stops the arm)

| id | gate | action on fire |
|---|---|---|
| **K1** | any zone's annual mean LMP moves > 25 % in any year | KILL — structural blow-up, not a calibration result |
| **K2** | unserved energy (slack) appears in any hour where the control had none | KILL — the envelope removed feasible supply |
| **K3** | C1 (fleet/dispatch construction gates) regresses against the control | KILL |
| **K4** | max zonal \|ΔLMP\| < $0.10 in all three years | **INERT** — report, do not promote |
| **K5** | the monthly EIA-930 net-interchange reconciliation band fails to hold in either arm | VOID the A/B, investigate |
| **K6** | the control fails to reproduce the keeper's C3a (34.77 / 37.99 / 60.22 basis) | VOID the A/B |

Non-gates, stated so they cannot be retro-fitted into gates: C3a moving in
either direction on any year is a **result**, not a kill. C3c is unchanged by
construction (this arm touches no scarcity mechanism) and if it moves, that is
reported.

---

## §7 — deliverables and duties

1. `scripts/probes/_nyiso125_seam_envelope.py` + `_nyiso125_seam_envelope.json`
   — Phase 0, committed with this file, **before** the solve.
2. Both bundles registered on the **backcast** dashboard in this session,
   keeper or rejected (rule 15): bundle + `registry/<id>.json` +
   `runs/<id>.js` + `bench/`, then `build_manifest.py`.
3. Matrix row `seam_flow_envelopes`, NYISO cell **`U` → whatever is measured**
   (rejections included), with citation, in this session (rule 28). The §5.5
   prose header is re-stamped only if the keeper changes
   (`check_mechanism_matrix.py` validates both halves).
4. `FINDING-nyiso125-seam-envelope-2026-08-04.md`.
5. **No promotion** unless LOYO passes and, because NYISO holds `complete`,
   rule 22 D-5(b) is honoured in full: re-key `calibration-complete.json`'s
   `keeper` **and** re-verify `determination` with
   `scripts/calibration_verdict.py --run-id` before the promotion commit lands.
   A worse re-verified determination STOPS the promotion and escalates.

---

*Pre-registered 2026-08-04, before any LP solve for this session.*
