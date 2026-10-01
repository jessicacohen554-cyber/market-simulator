# PRE-REGISTRATION — caiso-151 `caiso_firm_import_selfsched_clip` (single delta)

**Written and committed BEFORE either arm was solved.** No arm result existed
when this document was frozen. Gates below are final — a gate this document does
not contain cannot be quoted as a pass. Format mirrors
`PREREG-caiso148-nuclear-availability-2026-07-31.md` and
`PREREG-caiso138-…`, not copied.

Lever: mechanism-matrix §5.2 CAISO queue **item 2**, whose only live
prerequisite (`caiso-138 §C` firm-block elasticity) was **ANSWERED** at
caiso-150 — the defect is proved direction-free, the mechanism is specified
(FINDING-caiso150 §F), and the BUILD is what this session does. New matrix row
`caiso_firm_selfsched_clip`, CAISO cell `O` at the time of writing.

Base keeper: `2026-07-31-caiso148-nuclear-availability`, determination
CALIBRATED-WITH-CAVEATS, 0 FAILs, C1 12/12 · free 8/8, 2 ledgered non-protective
caveats from the owner's caiso-145 disposition (C3a-2025 on the caiso-141 A2
water wall, C3c-2023/24 on caiso-131 A4), 1 of 3 slots free, protective 0/1.
CAISO holds **no** rule-22 calibration-complete marker (re-verified this
session) — so this session solves **2023 2024 2025 only** and writes no marker.

**Promotion is NOT pre-granted** and is not requested in advance by this
document.

---

## §1 — the delta, exactly

`ScenarioConfig.caiso_firm_import_selfsched_clip: False → True`. **One new
field, one flag, one mechanism** (rule 19 `[R-ONE-MECH]`). Both arms are replays
of the caiso-148 keeper config at the same HEAD; the control is a **zero-delta
replay solved in this session**, *not* the keeper's committed bytes (caiso-146
measured the caiso-139 keeper drifting up to 3.2 GW on a class-hour at HEAD, so
committed bytes are not a clean baseline).

The mechanism, in `inject_caiso_firm_import_selfschedule`:

```
min_gen[t] = min( pmax × availability[t] , ceiling[t] )
```

the system ceiling allocated across the two firm tranches pro rata by their own
shaped capability in that hour — which is the pointwise min at the system level
and introduces **no allocation parameter**.

Three properties that are part of the registration, not commentary:

1. **It clips the FLOOR, never the CAPABILITY.** Above the measured
   price-insensitive ceiling the import is still *available*; it is simply
   price-ELASTIC, so it is handed to the LP as economic capability instead of
   being forced. Clipping availability (what caiso-138 does, correctly, for a
   *deliverability* limit) would delete real import capability and is the wrong
   object here.
2. **It COMPOSES with `caiso_firm_import_envelope_clip` as a second pointwise
   min, on its own flag.** The two reconcile different objects — caiso-138
   against the corridor's measured deliverability, this one against measured bid
   conduct. Arming it on caiso-138's flag is explicitly forbidden
   (FINDING-caiso150 §H).
3. **Zero new DOF** — a pointwise min of two measured series, the accepted
   caiso-138 pattern. It *reconciles* the caiso-73 shape rather than stacking a
   mechanism on top of it.

Also in this delta, and **not** a tuning channel: `MECH_FIRM_IMPORT` gets its
first `D4_WINDOWS` entry, `(0, 24)` all-hours **by driver** (a standing RA/LTC
contract obligation that names no hour at which it lapses). Until now a
19–28 TWh/yr must-flow floor sat outside every legitimacy gate the repo runs —
`NON_THERMAL_MECHS` (D-2 exempt) *and* `MECH_ABLATION_KEPT` *and* no D-4 row
(FINDING-caiso150 §A). With an all-hours window an off-window FAIL is
structurally impossible, so **this row is visibility, not an escalation path**,
and no pass of it may be quoted as evidence for the mechanism.

---

## §2 — the parameter series, and the gates that must clear BEFORE any arm

`scripts/data/derive_caiso_intertie_selfsched.py` →
`data/raw/_processed-legacy/caiso_intertie_selfsched_ceiling.csv`, a pooled
(month × hod) table, loaded by
`data.caiso_intertie_bids.measured_intertie_selfsched_ceiling`.

```
ceiling[month, hod] = ( ALL intertie self-schedule MW, both directions, unsigned )
                    + ( import-classified economic MW offered at or below $0/MWh )
```

Both limbs together are the floor's **own** definition of price-taking conduct
("self-scheduled **or** bid at/below $0/MWh", CPUC D.20-06-028, quoted in the
caiso-77 docstring), and both are taken generously, so
`ceiling[t] ≥ (true price-insensitive IMPORT position)[t]` in every hour. That
one-sidedness is what makes the mechanism survive the caiso-150 §B
identification wall: **direction is not identifiable** (a self-scheduling
resource submits no economic curve; the masked feed carries no direction field;
94.91 % of self-scheduled MW is on unclassifiable resources), and a clip at an
upper bound can only ever REMOVE forcing the measured record cannot support,
never add any.

**Gates, frozen ex ante** (thresholds are the caiso-81/86/87/88 standard; rule
23 `[R-FROZEN-DERIVE]`). A FAIL files a FINDING and the lane **STOPS** — nothing
is iterated against them:

| gate | statistic | threshold |
|---|---|---|
| **G1** | year-stability CV of the three per-year annual mean levels | ≤ 0.20 |
| **G2** | LOYO **level** — held-out year vs mean-of-other-two | ≤ 25 % |
| **G3** | LOYO **shape** — median relative error over the 288 (month × hod) buckets | ≤ 25 % |
| **G4** | **coverage floor** — (month × hod) buckets sampled in ALL three years | **288 of 288** |

G3 exists because a scalar level gate alone is too weak for a series whose
SHAPE is what the mechanism consumes. G4 is the coverage floor this document
registers: anything less than full three-year bucket coverage is a FAIL, not a
partial application — the loader refuses an incomplete table rather than
applying it to the covered buckets only.

**Corpus balance is load-bearing and is registered, not left to judgment**
(caiso-150 §B: a winter-only corpus reads 2,291 MW nearly flat vs the balanced
3,449 MW peaking in the evening — a ~50 % headline overstatement and a
mislocated peak). The sampler is balanced by construction: days
2, 5, 8, 11, 14, 17, 20, 23, 26, 29 of every month of every train year (spacing
3 walks the weekday through all seven within each month), Feb 29 dropped for the
non-leap model calendar. The pooled table is the **equal-weight** mean of the
three per-year tables, never a raw pooled mean, which would weight years by
their surviving day count.

Two construction details that are correctness conditions, not preferences:
OASIS rows are **run-length encoded** (`TIMEINTERVALSTART_GMT` ..
`TIMEINTERVALEND_GMT`, spans 1–24 h) and are expanded to hour slots **before**
any hourly statistic — skipping this yields a flat ~2.3 GW artifact of range
start-times clustering; and the clock is **exact UTC → US/Pacific**, *not*
`envelopes._caiso_interchange_model_clock` (that lag undoes an EIA-930
publication artifact this source does not carry).

---

## §3 — expected direction and magnitude, stated so it cannot be spun later

**E1-ADVERSE. The fit is expected to get WORSE, and that is not a rejection
ground.** The clip removes forced *cheap overnight* import, so overnight λ
**RISES** and **C5a moves against the gas gap**. This was stated at
caiso-150 §D/§F before any solve and is restated here before any arm.

Rule 1 `[R-STRUCT]` governs: a structurally-correct mechanism stays in even if
the backcast fit worsens, and the response to a worse fit is to find the root
cause, **not** to revert. Equally, rule 1 forbids adopting it *because* it moves
a residual — it is adopted, if at all, because the floor it clips forces more
price-insensitive import than CAISO's own bid record can support.

**Magnitude expected ex ante**, from FINDING-caiso150 §C (measured on the
caiso-148 keeper fleet against a 374-day balanced corpus):

| year | forced energy removed | share of the forced block | hours the clip binds |
|---|---|---|---|
| 2023 | ~0.97 TWh | ~5 % | ~2,100 h (23.9 %) |
| 2024 | ~4.63 TWh | ~17 % | ~4,130 h (47.2 %) |
| 2025 | ~5.71 TWh | ~20 % | ~4,280 h (48.9 %) |

concentrated **overnight, h22–h05**. This session's corpus is an independent
358-day re-fetch on the same balanced design (the caiso-150 corpus was
gitignored and its container is gone), so these are *predictions*, not
carried-forward measurements. **A large departure from them is itself a
finding** and is reported: see §4(c).

**What may NOT be quoted, in either direction** (FINDING-caiso150 §H): the
midday ratio 0.26–0.34 must not be read as *under*-forcing. Midday is exactly
where CAISO export self-schedules peak (oversupply), so the unsigned ceiling is
at its **most** generous there and the true import-only ceiling is unknown. The
model may not under-force midday at all. Observed-and-unresolved, not a result.

---

## §4 — what makes this a REJECT

The mechanism is rejected if **any** of:

- **(a) A derive gate fails.** G1–G4 above. The lane stops at the derive; no arm
  is solved, nothing is registered (the caiso-136/143/144/149/150 pattern).
- **(b) The clip is inert.** If the armed arm's firm-import floored energy is
  within 0.5 % of the control's in all three years, the mechanism is `I`, not
  `K` — a mechanism that changes nothing is not promoted for being harmless.
- **(c) The measured exposure contradicts caiso-150 by more than a factor of
  two** in removed energy in 2024 or 2025 (i.e. outside ~2.3–9.3 TWh for 2024,
  ~2.9–11.4 TWh for 2025). That would mean the two independent corpora disagree
  about the object being measured, which is a measurement problem to file, not a
  mechanism to arm.
- **(d) A protective check regresses** — see §5. Protective regressions are
  disqualifying regardless of what the mechanism does to the fit; CAISO's
  protective slot is 0/1 and this session does not spend it.
- **(e) The delta is not single.** Any second flag, any parameter touched to
  make the result land — automatic reject, and the session says so.

**Explicitly NOT reject grounds** (rule 1 / rule 14 `[R-ACCURATE]`): C5a moving
against the gas gap; E1/E2 worsening; overnight λ rising; any criterion moving
from a better number to a worse one *while its verdict stays the same*. Those
are the predicted, registered consequence of removing forcing the measured
record cannot support. If they occur, the mechanism keeps its verdict on
structural grounds and the residual becomes a **named open root cause**, not a
reason to revert.

---

## §5 — protective checks (all must hold)

1. **`caiso_firm_import_selfsched_clip=False` is byte-identical.** Verified
   ex ante at the unit level (`tests/unit/data/test_firm_import_selfschedule.py::
   TestSelfschedClip::test_clip_off_is_byte_identical_to_the_unclipped_floor`)
   and confirmed by the default `ScenarioConfig().cache_key()` being unchanged
   at `8161b094a391de90` — the field is registered in the cache-key
   default-drop list, so no pre-existing cache is orphaned. (The caiso-138 field
   was the SIXTH instance of missing that one line; this is not the seventh.)
2. **Capability untouched.** `pmax × availability` on the firm rows is identical
   between arms; only `min_gen` moves. Unit-tested.
3. **The clip never raises a floor.** `min_gen_armed ≤ min_gen_control` in every
   hour on every firm row. Unit-tested.
4. **`MECH_FIRM_IMPORT` attribution survives** on every remaining floored hour,
   so D-2/D-4 accounting stays truthful. Unit-tested.
5. **No other ISO moves.** The flag is CAISO-gated; ERCOT/PJM/MISO/NYISO/NEISO
   are untouched (rule 25 `[R-ISO-SCOPE]`).
6. **No criterion verdict may flip PASS → FAIL.** CAISO is at 0 FAILs; a new
   FAIL is disqualifying for promotion (it may still be a legitimate finding —
   but then the mechanism is filed, not promoted, and the FAIL's root cause is
   named).
7. **Neither ledgered caveat is re-litigated.** C3a-2025 and C3c-2023/24 stay
   ledgered exactly as the owner dispositioned them at caiso-145. This session
   proposes no lever for either.
8. **Binding gates go on the classes that ABSORB the change** — for an import
   clip that is **CC_REGULAR** and **CT_PEAKER** (C7-gated; C8 peaker cap 0.15),
   plus ST_GAS/COAL (C7-gated). Nuclear, CC_CHP, CT_CHP and ST_CHP are exempt
   from **both** C7 and C8 by **explicit class list**, not by the 2 %
   materiality floor — no exempt class's D-1/D-2 number may be quoted as a
   passed gate. ST_GAS 2024/2025 raw D-1 rows read FAIL on **both** arms and
   have since before caiso-148: pre-existing, below the 2 % materiality floor,
   **not** attributable to this lever.

---

## §6 — C3a materiality trigger

**1.0 pp.** If the armed arm moves the C3a load-weighted miss by **≥ 1.0 pp** in
any year, that is material and is reported in the finding as a first-class
result — in either direction, including if it *helps*. Below 1.0 pp the movement
is reported as noise and no claim is built on it.

C3a-2025 is a **ledgered caveat**, not an open lane. A movement here does
**not** reopen it: reopening requires new evidence against a named
caiso-140/141/142/143/144 DO-NOT-REDO cell, or the owner-funded non-public
hourly pumped-storage intake (caiso-145). If the clip moves C3a-2025
favourably, that is recorded as an incidental consequence and explicitly **not**
claimed as closing the caveat.

---

## §7 — solve mechanics registered in advance

Two arms, both `--year 2023 2024 2025` in a **single invocation each** (rule 16
`[R-ALLYEARS]`), run as separate concurrent invocations (rule 12
`[R-PARALLEL]`, cap 2 for plant-level CAISO):

```
control: replay_keeper.py results/calibration/caiso148_nucavail_B \
             --out-dir results/calibration/caiso151_control_A
arm:     replay_keeper.py results/calibration/caiso148_nucavail_B \
             --out-dir results/calibration/caiso151_clip_B \
             --set caiso_firm_import_selfsched_clip=true
```

`replay_keeper.py` does not emit `legitimacy_diagnostics.json`, so it is
generated for **both** arms (else C7/C8 score SKIPPED and cannot be quoted).
Both arms are registered on the dashboard whatever the verdict (rule 15
`[R-DASHBOARD]`), and the matrix cell is moved in this session whether the
outcome is `K`, `R` or `I` (rule 28b `[R-MECH-MATRIX]`).

Leave-one-year-out scoring within 2023–2025 precedes any promotion (rule 22
`[R-HOLDOUT]`). No out-of-training year is touched: CAISO holds no
calibration-complete marker.
