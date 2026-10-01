# nyiso-125 — the NYISO seam envelope is IDENTIFIED on half the seam and REFUSED on the half that carries the defect

**Date:** 2026-08-04 · **ISO:** NYISO · **Years:** 2023–2025 (training only, rule 22) ·
**Keeper at dispatch:** `2026-08-04-nyiso-120-c119-scope`.

Pre-registration: `results/calibration/PREREG-nyiso125-seam-envelope-2026-08-04.md`,
committed and pushed **before** any solve (§8 addendum, recording the owner's
promotion disposition, likewise written before any result existed).

**Verified at this session's own HEAD, committed artifacts only, no solve:**
`scripts/calibration_verdict.py --run-id 2026-08-04-nyiso-120-c119-scope`
returns **NOT-YET** — `price_mean` **FAIL** (2025 **−10.1 %**; 2023 and 2024
PASS), `price_tail` **CAVEAT** (ledgered, budget **1 of 3 UNSPENT**), the other
seven PASS. `scripts/audit_keepers.py --iso NYISO` **PASS, 0 failures /
0 warnings**. nyiso-124's commit `cf15bb54` is **on main**. NYISO holds
`complete`; `final` is EMPTY; the **holdout spend freeze is ACTIVE** and
outranks the marker — nothing outside 2023–2025 was solved, scored or read.

---

## §1 — the headline

The successor object nyiso-124 §6.1 handed this lane is **half identifiable and
half not, and the half that is not is the half that carries the defect.**

* On **NYC** (Zone J) and **Long_Island** (Zone K) every external tie lands in
  exactly one NYISO load zone. The per-neighbour envelope there is
  attribution-invariant, carries **zero identification freedom**, and is armed.
* On **Capital_Hudson** and **Upstate_West** it is not identifiable at all. One
  posting row — `SCH - PJ - NY` — spans the Central-East cutset, no public
  source splits it, and the split brackets Capital_Hudson's import envelope
  across **45–955 / 0–916 / 0–1,134 MW** in 2023 / 2024 / 2025. That is the
  whole range that matters, on the link the model pins at its bound in 100 % of
  hours. **REFUSED ON IDENTIFICATION** (rule 20 `[R-DOF]`).
* The **posted-limit** envelope — the better rule-13 object, and fully
  identified — is **REFUTED as the repair** by measurement.
* The **split-invariant joint** cap is identified and **provably inert**.

So the mechanism this session ships is deliberately partial, was pre-registered
as partial, and **cannot close the defect it was aimed at**. It is armed because
it is measured and structurally right, not because it suffices.

---

## §2 — measurement bases, named up front

Five price/flow bases now exist for NYISO and none is blended:

1. the scorer's `rt_lw` bench — **the ONLY C3a basis**, and the only basis any
   level in this document is quoted from;
2. the NYISO hub hourly series;
3. the per-zone monthly series;
4. nyiso-124's zone-letter basis (MIS RT Zonal LBMP);
5. **this session's basis: the MIS P-32 "Interface Limits and Flows" posting** —
   hourly per-interface *net schedule* and *posted directional limit*, committed
   at `data/raw/NYISO/interface-flows/` for all three training years.

Basis 5 is a **flow/limit** series, not a price series. It is never compared to
a price, and no C3a number is derived from it.

Source hours are keyed onto the model's fixed non-leap 8760 clock by **local
(month, day, hour)**, never positionally — the nyiso-123 §1 correction, since a
per-year `date_range` is one day off for leap-2024 from Mar 1 onward. Feb 29 is
dropped.

---

## §3 — Phase 0, four verdicts

Probe: `scripts/probes/_nyiso125_seam_envelope.py` ·
record: `results/calibration/_nyiso125_seam_envelope.json`. No LP.

### 3.1 One posting row is an accounting duplicate

`SCH - HQ_IMPORT_EXPORT` is not an independent tie. Against `SCH - HQ - NY` it
is equal to within 0.5 MW in **40.7 / 77.9 / 90.9 %** of hours (corr 0.977 /
0.989 / 0.993), and it is the **only** SCH row carrying the ±9,999 "unbounded"
sentinel on its negative limit — the signature of a proxy schedule rather than
a rated path. Counting it would double the HQ seam. **EXCLUDED**, and named in
the code (`NYISO_SEAM_ACCOUNTING_DUPLICATE`) so a future landing-zone entry
cannot silently re-admit it.

### 3.2 The posted-limit envelope: identified, and REFUTED as the repair

NYISO posts an hourly **directional** limit per external schedule, which is a
*rating* — a stronger rule-13 object than any flow statistic. It was measured
first for exactly that reason, and it fails on the evidence:

| interface | share of hours at ≥95 % of its posted import limit |
|---|---|
| `SCH - NE - NY` | 0.000 / 0.000 / 0.000 |
| `SCH - OH - NY` | 0.000 / 0.000 / 0.000 |
| `SCH - PJ - NY` | 0.000 / 0.001 / 0.001 |

The posted rating is **never** what allocates the AC seam. And a posted-limit
envelope would **LOOSEN** precisely the two links that over-deliver
(Upstate_West ≥3,650 MW against the incumbent 3,000; Capital_Hudson 1,400 + the
PJ share against 1,600) while moving the two downstate links by ~25 MW and
~10 MW. Arming the most accurate available rating would therefore make the
diagnosed misallocation **worse**.

This is a genuine rule-14 `[R-ACCURATE]` exception case and is recorded as one:
the accurate datum is real, but it is **misaligned to what the model's border
link represents** — the link is doing double duty as a rating *and* as the
seam's scheduling behaviour, and only the rating half is posted. It is
**REFUTED, not armed**, and it does not re-open the nyiso-122 Tier-3 refutation,
which concerned the *internal* `NYISO_INTERFACE_TTC_BY_*` limits.

### 3.3 The flow envelope: IDENTIFIED downstate, REFUSED on the eastern pair

Attribution is by the NYCA load zone each tie physically lands in (NYISO Gold
Book external interconnections — the same tie geography already cited in
`interchange/spec.IMPORT_NODE_LINKS["NYISO"]`):

| landing zone | ties | attribution |
|---|---|---|
| **NYC** (J) | `SCH - PJM_HTP`, `SCH - PJM_VFT` | **unambiguous** |
| **Long_Island** (K) | `SCH - PJM_NEPTUNE`, `SCH - NPX_CSC`, `SCH - NPX_1385` | **unambiguous** |
| Capital_Hudson (F+G) | `SCH - NE - NY` + part of `SCH - PJ - NY` | **ambiguous** |
| Upstate_West (A–E) | `SCH - HQ - NY`, `SCH - HQ_CEDARS`, `SCH - OH - NY` + part of `SCH - PJ - NY` | **ambiguous** |

`SCH - PJ - NY` carries the Ramapo 345 kV PARs and the Waldwick 230 kV ties into
Zone G (**east of Central East**) *and* the Homer City–Stolle Road / Falconer
ties into Zone A (**west**). Neither NYISO's P-32 nor **PJM's own tie-line
file** separates them — `data.eia930.envelopes._PJM_TIE_ZONE` buckets all four
NYISO-facing ties as `NYIS` / `NEPT` / `HUDS` / `LIND`, with every AC tie in the
single `NYIS` row. Checked in both directions before refusing.

The bracket that refusal rests on:

| year | Capital_Hudson import env p50 | Upstate_West import env p50 |
|---|---|---|
| 2023 | **45 – 955 MW** (width 910) | 1,204 – 2,199 MW (width 995) |
| 2024 | **0 – 916 MW** (width 916) | 1,285 – 2,429 MW (width 1,144) |
| 2025 | **0 – 1,134 MW** (width 1,134) | 708 – 1,891 MW (width 1,183) |

**Choosing inside that bracket would be choosing a number so the Central-East
link starts binding** — the exact failure the nyiso-123/124 charter §3 forbade,
and the reason no eastern envelope is armed, approximated, or parked behind a
default-off knob (rule 26 `[R-DELETE]`).

### 3.4 The joint cap: identified without the split, and provably inert

The (Upstate_West + Capital_Hudson) envelope is split-**invariant**, so it needs
no attribution at all. It also constrains nothing: the model's joint AC-seam net
import (**+597 / +80 / −89 MW** p50) already sits far below the measured
envelope (**1,818 / 1,706 / 1,243 MW** p50). The defect is the *within-pair*
allocation, which a joint cap cannot see. **Identified, measured, INERT — not
armed.**

---

## §4 — what is armed

`ScenarioConfig.nyiso_seam_deliverability_envelope`, default **off**,
NYISO-only, one flag, one delta. `data/nyiso_seam_envelope.py`. The two
identified border links trade their flat symmetric static rating for NYISO's own
measured directional hourly envelope — the p90 of the directionally-clipped net
schedule within each (month × hour-of-day) bin. `Upstate_West` and
`Capital_Hudson` keep their statics.

**No LP change:** `model/lp/bounds.py` already accepts a `(T, n_links)` `ttc`
and an asymmetric `ttc_import` — the same seam the ERCOT GTC and PJM
measured-interface overlays use.

Measured effect, with no LP:

| year | binds below the static | MW removed, NYC | MW removed, Long_Island | total |
|---|---|--:|--:|--:|
| 2023 | 100.0 % of hours | 94.6 | 212.3 | **306.9** |
| 2024 | 100.0 % of hours | 177.9 | 228.4 | **406.3** |
| 2025 | 100.0 % of hours | 97.0 | 271.5 | **368.5** |

**17–22 % of the ~1.8–2.0 GW misallocation.** Stated in the pre-registration
before the solve, and repeated here: this **cannot** close the defect.

### 4.1 DOF ledger

| parameter | value | identification | swept? |
|---|---|---|---|
| tie → landing-zone map | 5 ties → 2 zones | NYISO Gold Book tie geography, already cited in `IMPORT_NODE_LINKS`. Every tie lands in ONE load zone — attribution-invariant. | n/a |
| envelope percentile | **90.0** | repo-wide deliverability-envelope convention (`MISO_SEAM_FLOW_PERCENTILE` == `PJM_SEAM_FLOW_PERCENTILE` == 90.0 and `measured_interchange_envelope`'s default), each explicitly not tuned to a residual. Definitional, fixed ex ante. | **NEVER** |
| binning | month × hour-of-day | same as MISO/PJM. Definitional. | never |

**Zero new free parameters.** `NYISO_SEAM_FLOW_PERCENTILE` and the flag both
appear in `run_config.json` (rule 24 `[R-REGISTRY]`).

**Stated weakness, not hidden:** a p90 of *realized schedules* on a merchant
HVDC tie embeds firm-transmission-service scheduling behaviour, not only
physical capability. It clears rule 13's forward-analogue test the same way
MISO's and PJM's do — the construction regenerates from the forward tie set and
responds to changed conditions (974 → 828 → 975 MW on NYC and 1,012 → 986 → 990
on Long_Island across 2023–25, purely from measured behaviour; CHPE enters the
same feed in 2026) — no more strongly and no more weakly than the two cells the
repo has already adjudicated.

### 4.2 Leave-one-year-out

LOYO is **structural here, not statistical**: each year's envelope is built
**only from that year's own postings**, so no year informs another's parameters
and there is nothing for a held-out year to have leaked into. The LOYO test
therefore reduces to reading the three per-year outcomes, which §5 reports
individually. No parameter was identified on any year, so no parameter can be
overfitted to one.

---

## §5 — Phase 1: the A/B, and every pre-registered gate

Control `2026-08-04-nyiso-125-control` (bundle `nyiso125_control`) ·
treatment `2026-08-04-nyiso-125-seam-envelope` (bundle `nyiso125_seam_A`).
Single delta, same HEAD, 2023 2024 2025 in ONE invocation and ONE bundle each
(rule 16). Both registered on the backcast dashboard (rule 15). Gate record:
`results/calibration/_nyiso125_gate_scores.json`.

**The delta is clean.** The treatment logs the envelope on exactly the two
identified links, with the MW removed matching Phase 0 to the decimal; the
control mentions the mechanism **zero** times.

### 5.1 Every kill gate is silent

| gate | threshold | measured | verdict |
|---|---|---|---|
| **K1** zone mean LMP move | > 25 % | largest **+5.76 %** (Long_Island 2023) | **silent** |
| **K2** new unserved energy | any | **0.0 MWh**, every zone, every year | **silent** |
| **K3** C1 regression | any | PASS → PASS | **silent** |
| **K4** inertness | max \|ΔLMP\| < $0.10 | **$265.93 / $106.21 / $104.79** | **silent — LIVE** |
| **K5** seam net | material move | **+31 / −98 / +90 MW** p50 | **silent** |
| **K6** control reproduces keeper | C3a | **+7.2 / −0.9 / −10.1 %**, model $34.64 vs keeper $34.64 | **silent** |

### 5.2 The ex-ante prediction is confirmed in all three years, and overshoots in none

§4.2 reasoned *before solving* that `Capital_Hudson` — already at its bound in
~100 % of hours — cannot absorb the displaced MW, so the 307/406/369 MW removed
downstate must arrive at `Upstate_West` as reduced export and reach load through
Central East, lifting the CE link to ~1,050–1,120 MW p50 / util ~0.37–0.39 and
closing ~30–40 % of the gap.

| year | ext→Upstate_West | ext→Capital_Hudson | CE flow p50 | CE util | measured CE util | **gap closed** |
|---|--:|--:|--:|--:|--:|--:|
| 2023 | −998 → **−754** | 1,600 → **1,600** (at bound) | 850 → **1,183** | 0.467 → **0.668** | 0.807 | **+59.1 %** |
| 2024 | −1,520 → **−1,231** | 1,600 → **1,600** (at bound) | 562 → **963** | 0.197 → **0.335** | 0.616 | **+33.0 %** |
| 2025 | −1,702 → **−1,377** | 1,600 → **1,600** (at bound) | 723 → **1,094** | 0.255 → **0.383** | 0.591 | **+38.0 %** |

2025 lands at **1,093.6 MW / util 0.383** — dead centre of the pre-registered
band. `Capital_Hudson` stays pinned exactly as predicted, so the mechanism runs
through the channel it was reasoned to run through, not a coincidental one.

**A correction this session makes to its own inherited number:** the measured CE
utilisation is read **per year** from NYISO's own posting. nyiso-124 quoted
**0.591**, which is the *2025* value; 2023's posted limit is far lower (1,725 MW
median, pre-NY-Transco) so its measured utilisation is **0.807**. Using one
year's figure for all three would have misstated 2023's gap by ~2.4× — and would
have reported a spurious 162 % "overshoot" where the truth is a 59 % close with
the model still **below** measured. Corrected here, not carried.

### 5.3 The scored criteria

| criterion | control (= keeper) | treatment |
|---|---|---|
| C1 fuel-mix | PASS | PASS |
| C2 system volume | PASS | PASS |
| **C3a mean LMP** | +7.2 / −0.9 / **−10.1 % FAIL** | +7.7 / −0.8 / **−10.2 % FAIL** |
| C3b duration/shape | PASS | PASS |
| **C3c price tail** | **3 / 0 / 14 h** → FAIL ×3 | **18 / 2 / 21 h** → **PASS / FAIL / PASS** |
| C4 dispatch corr | PASS | PASS |
| C6 governance | PASS | PASS |
| C7 diurnal (D-1) | PASS | PASS |
| C8 forced share (D-2) | PASS | PASS |
| **determination** | **NOT-YET** | **NOT-YET** |

D-1 / D-2 / D-4 / D-5 / D-9 / D-10 all PASS in both arms.

**C3c — the sole ledgered caveat — improves materially.** Against a measured
10 / 12 / 42 h, the model goes 3 / 0 / 14 h → **18 / 2 / 21 h**. On identical
scoring the tail gate moves from failing **all three years** to failing **2024
alone**. No new caveat slot is spent (budget still **1 of 3**).

### 5.4 Reported against interest

Three things this arm does **not** do, stated plainly:

1. **C3a-2025 gets marginally WORSE** (−10.1 % → −10.2 %). The C3a FAIL is not
   closed, is not ledgered, and is not softened. Owner decision D.1 (HOLD
   PROMOTION, FIND ROOT CAUSE) is addressed only in the sense that a root cause
   was found and partly repaired — the *residual* did not move.
2. **2023's tail now OVERSHOOTS at 1.80×** (18 h against 10 h actual). It clears
   the band, but the model over-produces that year's tail where it previously
   under-produced it. Named as an open item, not explained away.
3. **The defect is not closed.** By construction this arm reaches only the
   identified half of the seam; ~1.5 GW of the misallocation sits behind the
   `Capital_Hudson` link, which stays pinned at its bound in ~100 % of hours in
   both arms. Its envelope is unidentified (§3.3) and was refused.

### 5.5 What this says about the C3c frontier premise

The C3c ledger records C3c as *"a DIAGNOSED, UNCLOSED STRUCTURAL LIMITATION of
the five-zone representation"* with an *exhausted* lever queue — i.e. the
five-zone model **cannot** form NYISO's real scarcity tail.

**That premise is now partly falsified, on measured evidence, and the falsifier
is not a scarcity mechanism.** A seam-side input correction — carrying no
scarcity parameter, no ORDC change, no floor, no reserve mechanism — moved the
tail from 3/0/14 h to 18/2/21 h. A substantial part of the "missing" tail was
never a zonal-resolution limit: it was **surplus import landing downstate and
drowning the scarcity that should have formed there**.

This is stated as a finding, **not** acted on: the C3c ledger text lives in the
keeper attestation and its re-open condition is an owner disposition (nyiso-124
already flagged that the *stated* re-open condition — the F/G topology split —
is falsified as written). What changes here is the evidence available to that
disposition. **No caveat is added, removed or re-worded by this session.**

---

## §6 — governance

* **Promotion.** Keeper → `2026-08-04-nyiso-125-seam-envelope`. The decision
  rule was fixed in PREREG §8 **before any result existed**, under the owner's
  standing disposition that structural gain may outweigh a gate regression: no
  kill gate fired and the arm is live, so §8.1(3) promotes.
* **Rule 22 D-5(b) honoured in full.** NYISO holds `complete`, so the same
  session re-keyed `calibration-complete.json`'s `keeper` **and** re-verified
  `determination` on committed artifacts (no solve) **before** the promotion
  commit. The label is **unchanged at NOT-YET** and the substance is better, so
  the stop-and-escalate branch does not fire — and the one substantively worse
  number (C3a-2025) is written into the marker in those words.
  `scripts/audit_keepers.py --iso NYISO` **PASS, 0 failures / 0 warnings**.
* **Rule 28.** `seam_flow_envelopes` NYISO **`U` → `K`** with citation; the
  matrix keeper header, the §5.5 prose header and the new field's anchor are all
  re-stamped in this session. `check_mechanism_matrix.py` exits 0.
* **Rule 15.** Both runs registered — keeper *and* control — with bundle,
  sidecar, `runs/<id>.js` and `bench/`. Both commit
  `hourly/network_<year>.parquet` via `git add -f`, which **discharges
  nyiso-124's one provenance caveat**: the control independently reproduces its
  seam diagnosis on the CURRENT keeper recipe (`external→Upstate_West` p50
  −998 / −1,520 / −1,702 MW against nyiso-124's −1,003 / −1,520 / −1,689 from
  the nyiso-113-recipe replay `nyiso116_c3c_unitlayer`).
* **Rule 22 holdout.** 2023–2025 only. The spend freeze is active and nothing
  out-of-training was solved, scored, read or registered.
* **No tuning.** The p90 convention was not swept, no band widened, no leg
  unarmed, nothing scoped to a year or zone in response to a score.

## §7 — the named successor

**The eastern half of the seam, and it needs an identification, not a lever.**
`Capital_Hudson` sits at its bound in ~100 % of hours in *both* arms and carries
~1.5 GW of the misallocation. Its envelope cannot be built until the
`SCH - PJ - NY` Zone-A / Zone-G split is identified from a source neither ISO's
tie file provides — a PAR-level or facility-level posting, an OASIS path-level
series, or an owner-authorised data intake. **Until such a source exists, this
lane is data-blocked, and the correct action is to say so rather than to pick a
number inside the 0–1,134 MW bracket.**

Second, unrelated and now better-evidenced: **C3a-2025's remaining −10.2 %**.
nyiso-120 measured ~94 % of that gap as pre-existing; this session shows the
seam repair does not touch it, which narrows where it can live.

## §8 — reproduce

```
uv run python scripts/probes/_nyiso125_seam_envelope.py
uv run python scripts/replay_keeper.py results/calibration/nyiso120_c119_scopegate \
    --out-dir results/calibration/nyiso125_control --note "..."
uv run python scripts/replay_keeper.py results/calibration/nyiso120_c119_scopegate \
    --out-dir results/calibration/nyiso125_seam_A \
    --set nyiso_seam_deliverability_envelope=true --note "..."
uv run python scripts/legitimacy_diagnostics.py --bundle <arm> --iso NYISO \
    --years 2023 2024 2025 --json-out <arm>/legitimacy_diagnostics.json
uv run python scripts/gen_nyiso125_attestation.py
uv run python scripts/probes/_nyiso125_score_gates.py \
    --control results/calibration/nyiso125_control \
    --treatment results/calibration/nyiso125_seam_A \
    --json-out results/calibration/_nyiso125_gate_scores.json
```
