# FINDING — caiso-253: the hod 22–23 charter answers HALF its question and REFUSES the arm. **G-WINDOW is decisive: 22–23 are OVERNIGHT-construction hours** (caiso-87 trigger ON in 0.3–1.9 % of them, against 66.7–84.7 % in the belly) — so the window question is settled and closed. But **G-WEDGE FAILS on its raw-hub leg in 2023, on DA, at both hours**, and the reason is measured and physical: **the DSW hub's own diurnal shape peaks LATER than CAISO's** (Arizona keeps no DST), so at 22–23 Palo Verde is still in its evening peak while CAISO has rolled off, and CAISO clears BELOW the raw hub — caiso-94 §3's "no import, even no-wheel, can set that price" branch. There is **NO carbon wedge** at 22–23 (0.0–4.7 % wedge-consistent): the caiso-93 question answers YES and the caiso-94 question answers NO, at the same hours. **The refused arm was NOT inert** — the model's λ exceeds the raw hub in 54–59 % of these hours — so the gate killed a live arm, one block past where caiso-252 landed. **ZERO LP, ZERO fleet rebuilds, NOTHING ARMED, KEEPER UNCHANGED.** 2 of 8 predictions hold, 2 falsified, 4 never reached.

**Session caiso-253, 2026-09-06.** Branch
`claude/caiso-backcast-calibration-253-9dgorn` off `main` `82f79693`.
Keeper **`2026-09-05-caiso-252-b1-notrim`** (`caiso252_b1_notrim`)
**UNCHANGED**, DETERMINATION **CALIBRATED**. Pre-registration
`PRECOMMIT-caiso253-hod2223-window-charter-2026-09-06.md`, pushed to `origin`
(`2bae8600`) **before any cell of the object was
computed and before any arm was coded**. Rule 22 `[R-HOLDOUT]`: 2023–2025
only; no `complete`/`final` marker; freeze ACTIVE. Instruments:
`scripts/probes/_caiso253_hod2223_gates.py` (the four registered gates) →
`_caiso253_hod2223_gates.json`; `scripts/probes/_caiso253_hod2223_diagnostics.py`
(post-registration, labelled) → `_caiso253_hod2223_diagnostics.json`.

---

## §1 — G-REPRO: the instrument reproduces THREE published quantities

Before any new cell was read, the probe was checked against the committed
record on three independent quantities it did not fit:

| quantity | published | this probe |
|---|---|---|
| CC_REGULAR error at hod 22 / 23, 2025, keeper basis | **+1.55 / +1.56 GW** (caiso-252 handoff; §2.2's +1,619/+1,617 on the PRIOR keeper, less that arm's −66 MW) | **+1,547 / +1,558 MW** |
| caiso-87 surplus-trigger ON share over hod 0–5, 2023/24/25 | **26.4 % / 1.2 % / 3.6 %** (FINDING-caiso93 §2–3) | **26.37 % / 1.23 % / 3.56 %** |
| unconditional overnight (0–5) DA delivered-basis median spread | **−4.7 / −4.5 / −5.1** $/MWh (FINDING-caiso93 §3) | **−4.66 / −4.51 / −5.13** |

**G-REPRO PASSES.** Everything below is read on the same construction that
produced the caiso-93 admissibility record and the caiso-252 anatomy.

---

## §2 — THE REGISTERED GATES

### §2.1 — G-WINDOW: **STARVED**, decisively. The window question is ANSWERED

The charter's question — *which of the two windows owns 22–23* — has a
measured answer the two constructions themselves name (PRECOMMIT §0.2):
the caiso-93 overnight leg is UNCONDITIONAL *because* the caiso-87 surplus
trigger is coverage-starved there; the caiso-94 daytime leg is trigger-OFF
scoped *because* it is coverage-rich there. Trigger ON share, measured with
the injector's own predicate (`PALOVRDE < 6.97 × SoCal citygate weekly +
$2.5`, measured-hub hours only):

| year | **hod 22** | **hod 23** | 0–5 control | belly 10–14 control |
|---|--:|--:|--:|--:|
| 2023 | 5.0 % | 13.6 % | 26.4 % | 78.8 % |
| **2024** | **0.3 %** | **0.8 %** | 1.2 % | 66.7 % |
| **2025** | **1.6 %** | **1.9 %** | 3.6 % | 84.7 % |

Decided on 2024/2025 (2023's elevated shares are the same documented rule-14
SoCal-citygate misalignment that lifts its 0–5 control to 26.4 %; **22–23
still sits BELOW that control in 2023 too**, i.e. the same regime). **Max ON
share over the decision years and both hours: 1.92 %**, against the
registered STARVED threshold of ≤ 10 % and RICH threshold of ≥ 30 %. The
belly control, 35–44× larger, shows the instrument can see "rich".

**⇒ Hours 22–23 are OVERNIGHT-construction hours.** This half of the charter
is **CLOSED**: no future session needs to re-measure it, and the caiso-252
§12.3 prohibition ("never reach 22–23 by silently extending either window")
now has a measured answer to point at.

### §2.2 — G-WEDGE: legs 1–2 PASS (there is NO wedge). Leg 3 FAILS, and that is the verdict

| year | basis | block | delivered median | wedge-consistent | **raw-hub median** |
|---|---|---|--:|--:|--:|
| 2023 | DA | hod 22 / 23 | −9.74 / −7.85 | 0.0 % / 0.0 % | **−3.98 / −2.56** |
| 2023 | DA | 0–5 control | −4.66 | 2.2 % | +0.75 |
| 2024 | DA | hod 22 / 23 | −5.75 / −5.19 | 0.0 % / 0.0 % | **−0.73 / +0.11** |
| 2024 | DA | 0–5 control | −4.51 | 0.1 % | +0.74 |
| 2025 | DA | hod 22 / 23 | −5.40 / −5.25 | 0.3 % / 0.3 % | **−0.19 / +0.06** |
| 2025 | DA | 0–5 control | −5.13 | 0.1 % | +0.10 |
| 2023 | RT | hod 22 / 23 | −14.24 / −11.07 | 1.1 % / 2.1 % | −8.74 / −5.54 |
| 2024 | RT | hod 22 / 23 | −9.23 / −7.53 | 1.9 % / 2.7 % | −3.84 / −2.42 |
| 2025 | RT | hod 22 / 23 | −7.48 / −6.97 | 4.7 % / 3.3 % | −2.17 / −1.66 |

* **Leg 1 (delivered median ≤ +$4): PASSES everywhere**, by $9–18.
* **Leg 2 (wedge-consistent ≤ 6 %): PASSES everywhere** — max 4.7 %, against
  a border wedge of $14.14 / $15.08 / $12.01. **There is no carbon wedge at
  22–23.** The caiso-93 question — *is the marginal import there
  carbon-paying?* — answers **NO** at these hours, exactly as it does at 0–5.
* **Leg 3 (raw-hub median in [−2, +4]): FAILS.** On **DA**, the basis
  caiso-93 gated and caiso-94 §4A tabulated: **2023 fails at BOTH hours**
  (−3.98, −2.56) while 2024 and 2025 PASS. On RT it also fails in 2024 and at
  hod 22 in 2025 — **but the verdict does not rest on RT** (§5.3): 2023 fails
  on DA alone.

**⇒ G-WEDGE FAILS. Under the registered stop rule (§6.1–§6.2 of the
PRECOMMIT), NOTHING IS ARMED.**

### §2.3 — G-DEPTH: NOT REACHED, and deliberately NOT RUN

The stop rule fires at G-WEDGE. Re-deriving the depth over a window the
charter has refused would be assembling the arm's inputs after refusing the
arm; the frozen derive stays un-run and P-4 is unscored.

### §2.4 — P-5: the model IS short at 22–23 — by MORE than registered, and it is the worst block of the day

Keeper `import` klass minus EIA-930 CISO net interchange, mean MW at hod
22–23: **−984 (2023) / −1,405 (2024) / −1,662 (2025)** — i.e. −0.71 / −0.99 /
−1.20 TWh. Registered band for 2025 was 0.3–1.2 GW: **P-5's magnitude is
FALSIFIED HIGH.** And by hour-of-day, 22 and 23 are the model's **two worst
import-deficit hours of the entire day in every year** (2025: −1,571 / −1,752
MW at 22 / 23; the next worst is −1,304 at hod 06). The hours with no at-hub
clean row are exactly the hours with the largest import deficit. **The object
is real; it is the arm that is refused.**

---

## §3 — POST-REGISTRATION (labelled; scored nowhere)

### §3.1 — WHY leg 3 fails: the DSW hub peaks LATER than CAISO

(`_caiso253_hod2223_diagnostics.json` leg **e**.)

Each series normalised to its own annual mean, so this is SHAPE, not level:

| year | series | hod 22 | hod 23 | hod 00 | hod 04 | hod 05 |
|---|---|--:|--:|--:|--:|--:|
| 2023 | CAISO DA | 1.119 | 1.030 | 0.979 | 1.048 | 1.165 |
| 2023 | PALOVRDE | **1.244** | **1.127** | 1.025 | 0.963 | 1.071 |
| 2024 | CAISO DA | 1.233 | 1.171 | 1.118 | 1.159 | 1.224 |
| 2024 | PALOVRDE | **1.381** | **1.282** | 1.214 | 1.164 | 1.276 |
| 2025 | CAISO DA | 1.284 | 1.246 | 1.207 | 1.226 | 1.302 |
| 2025 | PALOVRDE | **1.388** | **1.344** | 1.323 | 1.262 | 1.338 |

At 22–23 Palo Verde runs 0.10–0.15 of its own mean ABOVE CAISO; by hod 04–05
the ordering has **reversed** (CAISO above PV). The DSW is still inside its
evening peak at 22–23 while CAISO has rolled off its own. **Arizona keeps no
DST**, so the offset is persistent market structure that regenerates for a
forward year — not a 2023–2025 accident. That is the mechanism behind the
negative raw-hub discriminator, and it is the reason 22–23 is *not* simply
"more night".

### §3.2 — It is a SOLAR-SEASON phenomenon, and it has been closing

DA raw-hub median at hod 22–23, by month:

| year | J | F | M | A | M | J | J | A | S | O | N | D | block | 0–5 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 2023 | – | – | −2.6 | −7.9 | −5.5 | −3.1 | **−10.2** | −6.4 | −2.5 | −4.0 | +0.8 | +1.2 | **−3.21** | +0.75 |
| 2024 | +1.0 | +0.3 | −1.3 | −1.5 | −1.3 | −1.4 | **−6.1** | −4.1 | −1.9 | −1.1 | +1.5 | +1.2 | **−0.36** | +0.74 |
| 2025 | +1.0 | +1.3 | −0.1 | −1.8 | −1.3 | −1.4 | −1.3 | **−3.0** | −2.1 | +0.4 | +0.8 | +0.6 | **−0.03** | +0.10 |

(2023 Jan–Feb are the known OASIS retention gap.) In **winter** 22–23 clears
at or above the raw hub in all three years — it behaves exactly like 0–5. The
sub-hub clearing lives in the high-solar months, and the block median has
closed monotonically **−3.21 → −0.36 → −0.03**, consistent with the DMM's
reported WEIM dynamic-transfer growth. **A calendar gate is forbidden as
residual-fitting** (FINDING-caiso94 §8 do-not-redo), so this is reported as
structure, never as a scoping proposal.

### §3.3 — The refused arm was NOT inert. That is the point

Share of measured hours in which the model's own P1 dual exceeds the raw Palo
Verde hub — i.e. in which an at-hub row would CLEAR:

| block | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| **hod 22–23 (this charter)** | **54.3 %** | **59.0 %** | **57.4 %** |
| hod 0–5 (the armed overnight row) | 69.7 % | 77.0 % | 67.4 % |
| hod 18–21 (where caiso-252 landed) | 14.9 % | 22.6 % | 32.3 % |

The row would have cleared in a **majority** of the hours — more often than
in the block caiso-252 successfully armed — pushing λ down and import up in
hours the measured market says the hub is not in merit. That is the caiso-97
overshoot failure mode one block over. **The gate stopped a live arm, not a
dead one**, and it stopped it on admissibility rather than on a residual.

### §3.4 — Neither existing construction can represent these hours

This is the structural result, and it is new:

* the **overnight** construction is **unconditional** — and 22–23 is not
  unconditionally at-hub (§3.2);
* the **daytime** construction's only state variable is the caiso-87 trigger
  — and G-WINDOW measures it **inert** at 22–23 (0.3–1.9 % ON), so a
  trigger-OFF-scoped row there would arm in ~98 % of hours, i.e. be
  unconditional too;
* a calendar/season gate is forbidden (caiso-94 §8).

So the gap is not a clerical omission that either window can absorb. Closing
it needs a state variable neither construction carries — and any state chosen
because it makes the parity hours pass is gate-shopping. **The identification
requirement, not the mechanism, is the open item.**

### §3.5 — Malin is not the alternative carrier

(`_caiso253_hod2223_diagnostics.json` leg **f**.)

Raw-hub discriminator at 22–23 against MALIN instead of PALOVRDE: DA −2.34 /
−0.74 / −0.71 (2023/24/25) against PV's −3.21 / −0.36 / −0.03 — **no better,
and slightly worse in 2024 and 2025**. The north corridor offers no new
evidence, so the caiso-88 north-corridor closure is undisturbed and is not
re-opened here.

### §3.6 — Where the 22–23 energy may actually be (a hypothesis, not a claim)

EIA-930 CISO `NG: OTH` at hod 22–23 rises **274 → 2,112 → 3,342 MW** across
2023–2025, against the keeper's own storage discharge at those hours of
**≈ 680 → 1,683 → 2,769 MW**. EIA-930 carries no battery fuel category, so
CAISO's battery discharge reports into `OTH` — but `OTH` also carries other
and unknown generation, so this is a **hypothesis with a named check**
(compare against CAISO's published battery fleet output), not a result. It is
also consistent with caiso-252's own P-A2 falsification, where evening
storage discharge absorbed 0.47 TWh of the displacement. **The 22–23 CC
over-run is more likely a storage discharge-tail object than an import
object** — which is exactly what caiso-94 §3's raw-hub branch predicts when
actual clears below even the no-wheel hub.

---

## §4 — PREDICTIONS, SCORED

| # | registered | measured | verdict |
|---|---|---|---|
| P-1 | G-REPRO within 25 MW | exact on three published quantities | **HOLDS** |
| P-2 | G-WINDOW reads STARVED (≤ 10 %) | 0.3–1.9 % | **HOLDS** |
| **P-3** | G-WEDGE passes both hours, all three years | fails leg 3, 2023 on DA at both hours | **FALSIFIED** |
| P-4 | depth within ±8 % of the 0–5 depth | — | **NOT REACHED** (§2.3) |
| **P-5** | keeper under-imports 22–23 by 0.3–1.2 GW (2025) | direction yes; **1.66 GW** | **direction HOLDS, magnitude FALSIFIED HIGH** |
| P-6 | phase-0 footprint 1.5–4.0 GW/h, largest year 2025 | — | **NOT REACHED** (no rebuild spent) |
| P-7 | CC 22–23 falls ≥ 0.25 TWh on the screen | — | **NOT REACHED** (no solve) |
| P-8 | G-OVERSHOOT passes | — | **NOT REACHED** (no solve) |

**2 hold, 2 falsified, 4 never reached.** P-3 is the falsification that
closed the arm — **and its registered "uncomfortable reading" was WRONG about
the mechanism.** I registered that a G-WEDGE failure would mean "reality's
marginal import there IS carbon-paying and the model's wedge is CORRECT". It
is not: legs 1–2 show **no wedge at all**. The failure is caiso-94 §3's
*other* branch — actual clears BELOW even the raw hub, so no import of any
basis can set that price. The prediction bound; my stated reason for it did
not, and §3.1 supplies the one that does.

---

## §5 — DISCLOSURES AGAINST INTEREST

1. **INSTRUMENT BUG, disclosed and corrected.** The probe's first execution
   computed legs 1–2 against `CAISO_IMPORT_DELIVERY_BASIS["DSW_overnight_
   clean"]`, which is `(0.0, 0.0)` — raw hub **by design** — so those legs
   were measured on the raw-hub spread rather than on delivered parity. The
   registered construction is the scheduled-import basis at the same hub,
   `DSW_CCGT = (0.03, 4.0)`; it was corrected and re-run. **The correction
   makes legs 1–2 EASIER** (it moved 2024/RT-hod22 and 2025/RT-hod22–23 from
   apparent wedge failures to passes) **and leaves leg 3 — the leg that
   fails — untouched**, since leg 3 was always `actual − PALOVRDE`. It cannot
   be read as gate-shopping: it removed failures from a gate whose verdict is
   FAIL. (caiso-93 §1 disclosed the mirror-image bug in the same arithmetic.)
2. **The PRECOMMIT's G-REPRO target was mis-cited.** It quoted caiso-252
   §2.2's +1,619 / +1,617 MW, which are **prior-keeper** numbers; the
   keeper-basis comparator is the handoff's +1.55 / +1.56 GW. The two are
   consistent through caiso-252's own −66 MW delta, and the measured
   +1,547 / +1,558 matches the correct one.
3. **Gating RT was my own tightening**, beyond the precedent: caiso-93 gated
   **DA** and reported RT. The verdict does not rest on it — 2023 fails on DA
   alone, at both hours — but a reader restoring the precedent exactly should
   know that 2024 and 2025 would then have PASSED leg 3, and the refusal
   would rest on **2023 only**.
4. **A year-scoped arm was never considered admissible**, and that is why the
   2024/2025 DA passes do not become an arm: rule 1's amendment condition (b)
   requires ONE config across every scored year, and the PRECOMMIT's own stop
   rule refuses a partial-year or partial-hour arm. This is stated because the
   temptation was real — the object passes cleanly in the two most recent
   years and its 2023 failure is the largest.
5. **The measured LMP is the CAISO SYSTEM series, not zonal** (caiso-252
   §5.4's disclosure carries here): a zonal SP15 measured series would sharpen
   every spread in §2.2. The model side was read on the load-weighted λ and on
   the NP15 / SP15_rest duals, which agree within $0.9 at 22–23.
6. **The demand-basis confound** (caiso-247 §4.5) applies to §3.6's absolute
   who-serves rows. It does not touch the CEMS-basis CC error (§1) or the
   EIA-930 net-interchange comparison (§2.4), both measured on their own terms.
7. **§3 is post-registration in full** and is scored nowhere; the
   falsifications in §4 are on the registered legs only.
8. **ZERO LP and ZERO fleet rebuilds were spent.** The stop rule fired before
   phase 0's two-rebuild footprint, so P-6 was never measured.
9. **The eighth consecutive favourable C3a direction was declared in advance
   (PRECOMMIT §0.4) and never spent** — no arm was solved, so there is no
   direction to report.
10. **G-DRIFT's one open item is now CLOSED.** The PRECOMMIT §4 audit left
    `_band_categorical` (the `run_calibration_full.py` class-band sidecar
    rewrite) as the only claim not independently verified. It was verified
    exhaustively over every branch of `_tranche_band` — all six exact bands,
    all three prefix families, non-band ids, ids with no underscore, NaN, and
    the one structural risk (a categorical column carrying **unused**
    categories): **values AND categories identical in every case.** Every hunk
    in the fa23c1f7 → 82f79693 audit is therefore INERT for a CAISO backcast,
    verified rather than asserted.

---

## §6 — THE QUEUE AFTER THIS SESSION

1. **The hod 22–23 gap is RE-NAMED and DEMOTED as an import object.** It is
   not an at-hub clean-transfer object across the training window (§2.2,
   §3.1). Re-opening it needs a **state variable neither construction
   carries** (§3.4), identified from market structure and never from the
   parity hours it would admit — or the DA-only, 2024–2025 reading of §5.3
   plus a rule-1-admissible answer to why 2023 differs. Its **window**
   question is closed: 22–23 are overnight-construction hours.
2. **The 22–23 CC over-run is re-pointed at STORAGE** (§3.6) — the discharge
   tail, with caiso-252's P-A2 as the corroborating falsification. First step
   is the named check on `NG: OTH`, and it is a measurement question, not a
   lever.
3. **Panoche** (56803), 39/68/86 % of the CT volume miss — unchanged: an
   obligation instrument or closure (caiso-252 §3.3).
4. **The `complete` marker** — CAISO holds none; the determination is
   CALIBRATED. Declaring it is an owner act (rule 22). **Raised, not
   granted**, and nothing this session did bears on it: the keeper is
   untouched.
5. Carried unchanged: the DMM 2025 RA-import basis, the C3a weight-basis ask,
   the per-zone storage/class sidecar instrument, and the stale
   `program-status.json` top-level CAISO keeper stamp.

---

## §7 — DO-NOT-REDO ADDS

1. **Never re-charter hod 22–23 as an at-hub clean-transfer window on the
   overnight construction.** G-WINDOW is settled (STARVED, §2.1) and does not
   need re-measuring; G-WEDGE's raw-hub leg fails in 2023 on DA at both
   hours, and §3.1 gives the persistent, forward-regenerating reason (the DSW
   hub's later diurnal peak; Arizona keeps no DST). New evidence means a new
   **state variable**, not a re-run of these gates.
2. **Never scope a CAISO import row by calendar or season.** The 22–23
   sub-hub clearing is a solar-season phenomenon (§3.2) and a season gate is
   residual-fitting (caiso-94 §8).
3. **Never take the 2024/2025 DA passes as a year-scoped arm** (§5.4): one
   config across every scored year (rule 1 amendment (b)).
4. **Never read the 22–23 CC over-run as an import-volume miss.** The model
   IS short of import there (§2.4) but the measured price says no at-hub
   import can set that price; the counterpart is more likely the storage
   discharge tail (§3.6).
5. **Never propose MALIN/the north corridor as the 22–23 carrier** on this
   evidence — its discriminator is no better than Palo Verde's (§3.5), and
   caiso-88's closure stands.
6. **Never treat "the arm would have been inert" as the reason this closed.**
   It would have cleared in 54–59 % of the hours (§3.3); the refusal is on
   admissibility.
7. caiso-252 §7 and §12, caiso-251 §8, caiso-250 §7, caiso-249 §7, caiso-248
   §8, caiso-247 §8, caiso-246 §8, caiso-245 §7, caiso-244 §7, caiso-243 §10,
   caiso-242 §9, caiso-241 §10, caiso-240 §7, caiso-239 §8, caiso-230 §9,
   caiso-169, caiso-168 §8 stand in full.

---

## §8 — DELIVERABLES

`PRECOMMIT-caiso253-hod2223-window-charter-2026-09-06.md` (pushed first);
`scripts/probes/_caiso253_hod2223_gates.py` +
`results/calibration/_caiso253_hod2223_gates.json`;
`scripts/probes/_caiso253_hod2223_diagnostics.py` +
`_caiso253_hod2223_diagnostics.json`; this finding; the
`docs/calibration-log/caiso.md` entry; the rule-28 CAISO matrix-shard
evidence append on `import_hub_pricing` (verdict UNMOVED at `K` — no
mechanism was tested, an extension of one was refused before coding) and the
CAISO lever-queue refresh in `docs/mechanism-testing-matrix.md` §5.2.

**No run registered (none produced — no solve was spent), no keeper change,
no `ScenarioConfig` field, no new matrix row, no matrix verdict move, no
`complete` declaration.** Rule 15 `[R-DASHBOARD]` is not engaged: it registers
completed calibration *runs*, and this session produced none.
