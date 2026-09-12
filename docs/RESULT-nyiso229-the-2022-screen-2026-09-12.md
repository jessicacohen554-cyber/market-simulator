# RESULT — nyiso-229: the 2022 screen. **The spurious VOLL event is GONE. One of my four gates was mis-specified, and it was the only one that failed.**

**Session:** nyiso-229 · **ISO:** NYISO · **Date:** 2026-09-12
**Pre-registration:** `results/calibration/PRECOMMIT-nyiso229-outage-window-hour-grain.md`, pushed
before any LP, plus ADDENDUM 1 (G-DRIFT / control-in-shard), ADDENDUM 2 (pre-solve threading
verification), ADDENDUM 3 (the OOM and the per-container split).
**Keeper `2026-09-09-nyiso-221-fuelvintage-span` UNCHANGED. Nothing promoted. Nothing registered.**
**Rule 32 `[R-SHARD]`: the parent ran ZERO LP.** Five shard containers; two produced the two legs.
Gate JSON: `results/calibration/_nyiso229_screen_gates_2022.json`.

---

## 0. Headline

| gate | pre-registered test | measured | verdict |
|---|---|---|---|
| **G-CONF** | exactly one field moves; each leg reads its own extract | `unit_outage_window_hour_grain` F→T and nothing else; control resolved `-perunitmerit-` sha `58799099…`, arm resolved `-perunitmerithour-` sha `ee778a87…` | **PASS** |
| **G-DIR** | 2022 firm-load slack must FALL | **360.472 → 0.000 MWh** | **PASS** |
| **G-MAG** | slack → 0.0 **and** hours 3616/3617 clear | slack **0.000**; VOLL hours **124.894 → 0.000** and **235.577 → 0.000** | **PASS** |
| **G-DEMAND** | served demand identical to 4 dp, dump 0 | **152.6817 TWh both legs**, dump **0.000** both | **PASS** |
| **G-CONF-2** | no class-hour outside the restored set moves > 1.0 MW | 5,409 class-hours, worst 1,471.7 MW | **STOP — and the gate is wrong, §3** |

**The 31-May-2022 VOLL event is gone.** Firm load is no longer shed anywhere in 2022, and the
reserve picture collapses with it: shortfall **50,902.6 → 14,657.5 MWh** (−71 %) over **88 → 41**
hours, with `li_10min_total` and `li_30min_total` going to **zero** and `east_10min_total`
5,036.1 → 632.0 MWh. That is the ADDENDUM-1 §3 arithmetic landing: 3,657 MW restored against
360.5 MWh shed.

---

## 1. THE CONTROL VALIDATES THE G-DRIFT AUDIT — and I got back the evidence the split cost me

ADDENDUM 3 §3 said the per-container split would leave this screen unable to speak to
`d4f97391 → HEAD` drift. It does speak to it, because the control leg is the keeper's own 2022
recipe re-solved at HEAD and the committed touchpoint `nyiso_fuelvintage_H2` is the same recipe at
`c430970e`:

| | committed H2 | my control leg | Δ |
|---|---|---|---|
| firm-load slack, MWh | 360.472 | **360.472** | **0.000** |
| served demand, TWh | 152.6817 | **152.6817** | **0.0000** |
| load-weighted mean, $/MWh | 69.9170 | 69.9525 | **+0.0355** |
| load-weighted max, $/MWh | 1,429.99 | **1,429.99** | **0.00** |
| hours > $300 | 8 | **8** | **0** |

Slack, served demand, the annual maximum and the tail count are **identical**. The single
+0.0355 $/MWh is the one LIVE hunk the audit named (`reliability_floor_coeffs_NYISO.csv`, nyiso-227's
NYC ST_GAS re-basing), and it sits in the same range nyiso-228 measured for that hunk on the other
three years (+0.025…+0.028). **So the `solve_container` OMP-pin concern and the unpinned-dependency
drift are both immaterial at this resolution** — measured, not assumed, and the honest correction to
my own ADDENDUM-3 worry.

## 2. WHAT THE ARM DOES, at full magnitude

| | control | arm | |
|---|---|---|---|
| firm-load slack | 360.472 MWh, 2 h | **0.000, 0 h** | |
| reserve shortfall | 50,902.6 MWh, 88 h | **14,657.5 MWh, 41 h** | −71 % |
| load-weighted mean | 69.9525 | **67.6573** | **−2.295 $/MWh** |
| load-weighted max | 1,429.99 | **476.10** | −67 % |
| hours > $150 / 200 / 300 | 197 / 30 / 8 | **148 / 9 / 4** | |
| served demand | 152.6817 TWh | **152.6817** | identical |

Class energy, TWh: `CC_REGULAR` 36.880 → **37.138**, `ST_GAS` 6.485 → **6.631**,
`CT_PEAKER` 4.266 → **3.974**, `CC_CHP` 13.428 → **13.347**, `oil` 0.6255 → **0.6192**,
`import` **27.8487 unchanged**, `nuclear` / `wind` / `solar` / `biomass` unchanged.
The restored steam and CC capacity displaces peakers and oil — the merit-order response the
mechanism's own arithmetic implies.

**C3c, reported as precision and recall and never as a bare count** (the nyiso-228 §4b rule):

| | model h > $300 | actual | overlap | precision | recall |
|---|---|---|---|---|---|
| control | 8 (all 2022-05-31) | 101 | 0 | **0.000** | **0.000** |
| **arm** | **4 (all 2022-05-31)** | 101 | **0** | **0.000** | **0.000** |

**The count halves and the precision does not move.** The residual four hours are still spurious and
still on the same wrong day: 31 May is no longer a load-shed day, but it is still a
scarcity-priced one. **The arm removes most of a false event and creates none of the 101 real
hours** — exactly what the phase-0 finding §6 declared it would do, and it must not be read as
progress on the winter object.

## 3. G-CONF-2 WAS MIS-SPECIFIED BY ME. I am recording it, not stacking it — and this is the part a reader should audit hardest

**The situation is the one where rationalising is most tempting**, and I want it stated before the
argument: unlike nyiso-228 — where G-ENERGY was mis-specified but G-MAG was the kill, so dismissing
it changed nothing — **here G-CONF-2 is the ONLY failing gate, so dismissing it is the whole
difference between STOP and CLEARS.** That is exactly when a session should be least trusted. So the
claim is made by measurement, not by argument, and the measurements are pre-committed forms
(distance decay, net-versus-gross) rather than anything chosen after seeing the failure.

I wrote *"no class-hour outside the restored set moves > 1.0 MW."* **That is physically wrong for
this LP**, and wrong in the same way nyiso-228's G-ENERGY was wrong: I specified confinement on a
quantity that is not confined. The NYISO LP is intertemporally and globally coupled by construction —
cyclic storage SOC, hydro budgets, the monthly import-reconciliation quota, and commitment bridges
whose run patterns are detected from the P0 solve. Any one of those propagates a change in hour *t*
into hours *t±k*. Demanding zero movement outside the changed hours asks the LP not to be an LP.

Three measurements, and they agree:

1. **Every violating hour is LOCAL to the footprint.** Distance from the nearest restored hour:
   209 hours at 0–1 h, 720 at 2–6 h, 925 at 7–24 h, 270 at 25–168 h, and **zero beyond**.
   **Median 8 h, maximum 60 h.** A genuine out-of-footprint defect would not stop at 60 hours.
2. **The coupled classes are a REALLOCATION, not a creation.** Net over gross GWh across the year:
   `import` **0.000 / 251.760 = exactly 0.000** — the reconciliation band holding its monthly quota
   and moving only hours, which is precisely what it is built to do; `hydro` **5.450 / 249.425 =
   0.022** — a budget-constrained variable redistributing under its own budget; `CT_PEAKER`
   **−291.847 / 310.886 = −0.939** and `CT_CHP` **−0.943** — near-pure displacement.
3. **The violations sit in exactly those classes** — `import` (worst 1,471.7 MW) and `hydro` (worst
   1,305.1 MW) are the two largest, and they are the two most globally-constrained variables in the
   model.

**What a correctly-specified confinement gate would have asked, and the arm's answer:** does the
response *decay* with distance from the mechanism's footprint, and is the out-of-footprint part a
reallocation rather than a creation? **Yes and yes**, by (1) and (2) above.

**Two things I am NOT doing.** I am not re-cutting the gate and re-scoring against the new one — that
would be selecting a criterion because the arm fails the old one, which rule 1 `[R-STRUCT]` forbids.
And I am not claiming the screen "cleared". **The screen returns: three gates PASS, one gate withdrawn
as a defect in my own pre-registration.** A reader who declines the withdrawal should read this screen
as a STOP, and they would be reading it correctly against the document as written.

**I also flagged this gate's weakness BEFORE the numbers landed** (commit `20cf07b3`, and the
finding's §10 note): the two extracts disagree in 5,278 of 8,760 hours, so the gate only ever
constrained ~40 % of the year. That was recorded when it could not help me; it is the same defect
seen from the other side.

## 4. WHAT THIS DOES NOT SHOW

* **Nothing about 2023–2025.** The screen is one year. Rule 16 `[R-ALLYEARS]` requires the full span
  for any keeper, and the keeper's scored years are **2023–2025** — none of which is touched here.
* **Nothing about the winter object.** Jan/Feb/Dec 2022 is 77 % of the annual miss and this arm
  creates none of the market's 101 tail hours. Precision stays 0.000.
* **C3a moves DOWN and that is a cost in two of the four years.** 2022's load-weighted mean falls
  2.295 $/MWh against an actual the model already undershoots (C3a-2022 −13.8 %), so **2022's C3a
  gets worse**. On the keeper's own years the declared expectation is that 2023 (+5.7 %) and 2024
  (+6.5 %) improve and **2025 (−6.3 %) degrades**. None of that is measured yet and none of it was
  gated on.
* **Nothing is registered and no determination is computed.** Rule 15 `[R-DASHBOARD]` is not
  discharged because a screen bundle is never registered (rule 29 clause (2)).

## 5. RULES

1 `[R-STRUCT]` — structure decided this; the price fall was declared ex ante and is not a gate, and
the mis-specified gate was withdrawn on measurement rather than replaced with one the arm passes.
13/14 — the detected hour is the same measured input at its own resolution. 16 `[R-ALLYEARS]` — the
span is NOT yet solved and no keeper claim is made. 19 `[R-ONE-MECH]` — `unit_outage_per_unit_clip`
deliberately not co-armed. 21 `[R-DOF]` — zero free parameters, no ledger entry. 24 `[R-REGISTRY]` —
the grain is a registered field and appears in both legs' `run_config.json`. 29 `[R-SCREEN]` — phase 0
first, screen year named on footprint and liveness before any solve, gates structural and stop-only,
G-CTRL earned and spent deliberately. 30(c) — a 2022 result cannot certify or decertify NYISO.
31 `[R-RETAIN]` — **nothing deleted**; both legs are gitignored and on disk, recoverable from their
shard branches with no re-solve, and the promotion question goes to the owner. 32 `[R-SHARD]` — the
parent ran no LP.

## 6. COST, stated rather than buried

**Five shard containers; two bundles.** One OOM-killed (ADDENDUM 3). One died on a `TypeError` that
was **my own plumbing bug** — the field threaded through `run_calibration_full` but not into
`scripts/run_calibration.run_year` — and one I interrupted because it would have hit the same error.
Then the two that worked. Every failed shard **stopped and reported instead of patching
infrastructure**, which is why each diagnosis cost minutes; rule 32(c)(7) earned its place.

The `TypeError` deserves one more line, because it was luck in the right direction: the precedent
field's own comment says *"an override missing here would solve the control twice."* Had I omitted
only the `with_overrides` hunk and not the parameter, the arm would have solved as the control and
returned a clean-looking bundle answering the wrong question. A crash was the good outcome.
