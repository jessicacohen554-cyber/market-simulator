# PRECOMMIT — caiso-261: the hod 22–23 price-taking import volume — DATA-INTAKE ADJUDICATION, rule-13 admissibility fixed BEFORE any wiring. ZERO LP by construction: there is no branch of this document that solves.

**Session caiso-261, 2026-09-06.** Branch
`claude/caiso-backcast-calibration-261-2hrovn` off `origin/main` `8dc64272`.
Keeper **`2026-09-06-caiso-260-b1-demand`** (bundle
`caiso260_demand_vintage`, `meta.json` `git_sha` **`e162147b`**),
DETERMINATION **CALIBRATED** (rubric v3.6): C1 12/12 free 8/8; C2 PASS; C3a
+4.37 / +8.89 / +8.25 %; C3b 0.083 / 0.142 / 0.111; C4 gas r/NRMSE
0.881/0.287, 0.912/0.260, **0.877/0.298**; C3c 23 / 0 / 0 h vs 47 / 35 / 8
(2023 and 2024 CAVEAT, 2025 PASS); C6 attested; C8 PASS; DOF 9 entries /
6 residual, no `authorized_price_tuning` block. Rule 22 `[R-HOLDOUT]`:
2023–2025 only; no `complete` / `final` marker (raised at caiso-257, -259,
-260; not granted); holdout freeze ACTIVE. **G-CTRL form 4** (rule 29(b)):
the keeper's committed bundle and `hourly/` sidecars are the control; **no
control solve**. Pushed before the instrument is run.

---

## §0 — Standing declarations, first

**0.1 There is no rubric failure to tune.** The only scored movement at
caiso-260 was C3c-2023 crossing the 0.5× line by ONE hour (24 → 23 of 47).
C3c is the accepted model-class limitation with an EMPTY in-model queue on
every route (caiso-144); rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]` forbid
closing it with any adder, offset or value tuned to the tail. **This session
treats the C3c-2023 caveat as a constraint to be reported, never as a
target; a result that "recovers" that hour is fitting and is not claimed.**

**0.2 The two exposures, stated before any candidate is named** (caiso-257
§10 #3, caiso-260 handoff):

| cell | keeper | bound | margin | direction of an import carrier at 22–23 |
|---|--:|--:|--:|---|
| C4-2025 gas NRMSE | **0.298** | ≤ 0.30 | **0.002** | hod 22–23 carry 9.4 % of the 2025 gas MSE (caiso-258 §6); more import there lowers CC → relaxes the cell (direction only, **excluded** from any basis) |
| C3c-2023 tail | **23 h** vs 47 | ≥ 0.5× = 24 h | **at the line** | unknown a priori; E-4(b) below measures how many of the 23 sit at 22–23; **never a target** |

**0.3 The C3a pattern, declared.** caiso-260 moved C3a favourably in 2023
and 2025 and was flat in 2024, after eight consecutive favourable
promotions. Any carrier that adds import at hod 22–23 has a favourable
first-order C3a direction **by construction** (caiso-258 §8 #8). **C3a is
excluded from every prediction, gate and conclusion below, in both
directions.** So is C4. The evidence this document admits contains no
price.

**0.4 No solve, by construction.** Every leg below is a read of committed
artifacts, a `fleet_only` rebuild, or a published document. The stop rule
(§5) has no branch that reaches a solve, a screen, a `ScenarioConfig`
field, a derive run, a bench regeneration or a corpus re-fetch. Rule 29(a)'s
screen-year clause is therefore stated only for a **future** arm (§5.3).

---

## §1 — THE OBJECT (caiso-258 §5 / §9, caiso-260 §10 #2)

At hod 22–23 the keeper imports **−972 / −1,467 / −1,763 MW** less than
EIA-930 CISO net interchange on the model's clock (2023 / 2024 / 2025;
caiso-258 §1, measured on the caiso-257 keeper). The armed WECC stack is at
one third of its capability there (2025: 4,438 of 13,459 MW; 8,836 MW
priced out $4–20 above node duals of $43.8 / $44.4 that match the measured
night price, caiso-258 §5). The model's own stack says no more import is
worth buying at $44; the market moved ~1.8 GW more at that price. The
counterpart on the plant side is CC_REGULAR (+1,536 / +1,546 MW at hod 22 /
23 in 2025, CEMS basis), 58 % of it on plant-hours where the real plant was
OFF (caiso-258 §4).

**Routes already closed, binding here:** a ladder-price or adder move
(caiso-252 §7 #2; caiso-258 §10 #4); a clean-transfer window extension to
22–23 (caiso-253 §7 #1 — refused on the measured raw-hub discriminator,
2023 fails at both hours); a per-plant pin (rule 13); EIA-930 realised flow
as an input (rule 13 — an outcome); re-keying the firm split on capability
holdings (caiso-245 §7 #1); re-measuring the self-schedule ceiling or
attempting its import/export split (caiso-150 §H).

**What the caiso-258 queue asked for, verbatim:** "a measured,
forward-regenerating source for contracted import volume beyond the DMM RA
showing (DMM §17 native-load-need showings; CPUC RA import showings), rule-13
admissibility adjudicated *before* it is wired — a showing is a contracted
capability, not a realised flow; the realised EIA-930 flow is an outcome and
stays forbidden as an input." **This document is that adjudication.**

---

## §2 — THE HYPOTHESIS, AS A FALSIFIABLE STATEMENT

**H-INTAKE.** *There exists a measured, forward-regenerating source for
contracted or self-scheduled import VOLUME that the keeper's firm block does
NOT already carry, whose quantity at hod 22–23 is of the order of the gap
(≥ 0.5 GW in 2025).*

If H-INTAKE holds, the session names the source, its admissibility class,
and the intake it would need — and stops (wiring is a later PRECOMMIT). If
it is falsified, the object is **closed as a data-intake object** and
re-named by what the residual is then shown to be.

### §2.1 Admissibility classes, fixed ex ante (rule 13 `[R-MEASURED]`)

| class | what | rule-13 test | verdict, fixed now |
|---|---|---|---|
| **A — a showing / contracted capability** | RA import showings; non-RA contract showings; the ISO's "native load need" set-aside; RA import capability allocations | regenerates from forward showings; responds to changed conditions (a market that contracts more imports shows more) | **ADMISSIBLE in class** — but a **capability is not an energy**: it may enter only the way the firm block already enters (a published level × a measured shape, floored, clipped at the measured price-insensitive ceiling), and only if it is a quantity the firm block does **not** already carry |
| **B — as-submitted bids** (OASIS `PUB_DAM_GRP`) | intertie self-schedules and economic curves | publishes continuously at a 90-day lag; regenerates for any forward year (caiso-151) | **ADMISSIBLE as conduct measurement**, already consumed (the selfsched ceiling); subject to the caiso-150 §H wall — no import/export split of self-schedules |
| **C — realised flows** | EIA-930 net interchange; DMM realised WEIM transfers; OASIS settled schedules | an **outcome** — "could this be produced for a forward year from forward drivers?" NO | **FORBIDDEN as an input.** Admissible only as a **diagnostic** for attribution (which limb the residual sits in), never wired |
| **D — a price, adder, window or threshold moved on this residual** | any | — | **FORBIDDEN** (DO-NOT-REDO, §1), whatever source is cited for it |

---

## §3 — THE SOURCES, NAMED — with a disclosure

**DISCLOSURE, first (against interest).** Source scoping for this
PRECOMMIT fetched the DMM 2025 Annual Report (`caiso.com/documents/
2025-annual-report-on-market-issues-and-performance.pdf`, sha256
`7c89fdc4…15ea9`, the same document caiso-252 adjudicated) and **read** its
§17 (pp. 337–342, Figures 17.3–17.5), Figure 16.9 (p. 321), Figure 4.2
(p. 175) and Figures 1.52–1.53 (pp. 77–78) **before this document was
pushed** — reading a published report is data readiness (rule 22, channel
1), but the values seen are transcribed here as **operands** and score **no
prediction**. Nothing from the keeper's bundle, the sidecars, the ceiling
artifact or EIA-930 was computed before the push; those legs carry the
predictions.

**S-1 — DMM 2025 Annual Report §17 "Wheeling rights", the native load
need.** *Definition, verbatim (p. 340):* "this 'native load need' capacity
on interties is the sum of shown import resource adequacy, as well as
non-resource adequacy contracts that load serving entities may show the ISO.
… Before T-30, the ISO estimates how much intertie transmission capacity
native loads will need by identifying the maximum amount of shown import RA
and non-RA contracted imports delivered on that intertie for the same month
over the previous two years." *What is published:* a **monthly transmission
set-aside in MW**, for the **Jun–Sep 2025 months with priority
wheel-through reservations only**, on the **PWT-relevant tie points only**
(NOB, Malin 500, Palo Verde, Adelanto–Victorville), as **bar charts** (no
table). *Values read from Figure 17.3 (all relevant tie points, ±100 MW),
cross-checked against the text's own over-estimate figures (1,500 / 900 /
1,600 / 2,100 MW = 42 / 22 / 39 / 52 %):*

| 2025 | estimate (historic RA + load growth + historic non-RA) | of which historic non-RA | **final = shown RA imports** |
|---|--:|--:|--:|
| Jun | ≈ 5,100 | ≈ 250 | **≈ 3,600** |
| Jul | ≈ 5,200 | ≈ 50 | **≈ 4,300** |
| Aug | ≈ 5,600 | ≈ 600 | **≈ 4,050** |
| Sep | ≈ 6,300 | ≈ 300 | **≈ 4,150** |

Malin (Fig 17.4): final ≈ 1,050 / 980 / 1,010 (Jul–Sep). NOB (Fig 17.5):
final ≈ 900 / 980 / 900 / 820 (Jun–Sep). **The "final value" bar is shown
RA imports alone**; the non-RA component appears only inside the historic
*estimate*.

**S-2 — the on-disk measured price-insensitive intertie ceiling**
(`data/raw/_processed-legacy/caiso_intertie_selfsched_ceiling.csv`,
caiso-151 from `PUB_DAM_GRP`, class B, pooled 2023–2025 climatology,
(month × hod)): at hod 22 / 23 it reads 2,877 / 2,797 (Jan) … 4,398 / 4,133
(Jul) … 3,924 / 3,852 (Dec) MW. This is the quantity the keeper's firm
floor is already clipped to (`caiso_firm_import_selfsched_clip = True`).

**S-3 — RA import capability allocations** (`data/raw/ra-import-allocations/
CAISO`, class A): LSEs hold 11,741 / … MW of import capability (caiso-245),
5.05× the DMM RA-import figure — a **capability**, adjudicated at caiso-245
as not an energy and not a split key.

**S-4 — DMM Figure 16.9, RA imports by price bin** (peak hours HE17–21,
DAM, class B as published): 2025 self-schedule + (−$150, $0] bins ≈ 1.2–2.7
GW by month; the > $0 bins are a thin cap. Corroborates the caiso-252 §3.4
adjudication of Table 16.7; not an hourly series.

**S-5 — DMM Figure 4.2 (net inter-regional dynamic WEIM transfers by hour,
5-minute market) and Figures 1.52–1.53 (California region interchange
before/after dynamic transfers)** — class **C**, diagnostic only. The
"California ISO" bar at hours 22–24 reads a net **import** of roughly
+0.5–1.0 GW in each 2025 quarter; the region's after-transfer line sits
above the before-transfer line by a similar amount in those hours. Text
(p. 77): "after dynamic transfers, California's net imports increased by
approximately 580 MW (26 percent)" on an annual basis.

**S-6 — CPUC RA import showings** (the CPUC annual Resource Adequacy
Report): by construction the **same object as S-1's final value and the DMM
RA-import row** — shown RA imports — on a jurisdictional (CPUC-LSE) rather
than BAA boundary. Not fetched: it cannot contain a "beyond-RA" quantity
because it is the RA showing, and its boundary is the rule-14 misalignment
the firm block's own comment already rejects for CARB/CEC series.

**S-7 — the economic limb of the public-bid corpus** (import-classified
economic bids > $0, by price, (month × hod)) — class B. The corpus is **OFF
DISK** (gitignored payload; re-fetch ≈ 1,096 daily zips at ≥ 6 s each,
0.5–0.9 GB). **Not measured this session.** Named here because it is the
only *measured* source that could size the residual left after S-1/S-2, and
because consuming it would be the gap-register **G-26 / audit C-6** CAISO
closure (the ladder's $/MWh are "static-fitted-pending-measured"), which is
a standing cross-ISO item — **it is NOT proposed on this residual** (class D
if selected here, caiso-252 §7 #2) and is raised to the owner in §7 as a
decision.

---

## §4 — THE ESTIMATOR (zero LP), with falsifiers

Instrument: `scripts/probes/_caiso261_import_intake_adjudication.py` →
`results/calibration/_caiso261_import_intake_adjudication.json`. It reads
the keeper's committed `hourly/` sidecars, EIA-930 CISO through
`eia930.frames._eia_hourly_frame_filled` (the model's clock, caiso-255b §6
#1), the S-2 artifact, the caiso-245 holdings json, the S-1 / S-5 values
transcribed above, and the D-3 leg of the re-pointed caiso-258 closure
probe (an on-recipe `fleet_only` rebuild at HEAD — preconditions:
`data/clean` curated for CAISO; `mic_partition` 16,055 / 16,452 / 16,148
MW; no fallback line). Every number the FINDING will cite lives in the json.

**G-REPRO (the keeper changed identity at caiso-260).**
* **P-1** — the hod 22–23 import deficit on the caiso-260 keeper is within
  **±300 MW** of caiso-258's −972 / −1,467 / −1,763 MW in every year. Basis:
  the caiso-260 arm moved annual import by −0.119 / −0.041 / −0.240 TWh
  (−14 / −5 / −27 MW mean) and demand at 22–23 by +86 / +60 / −64 MW; a
  move beyond ±300 MW would mean the arm re-shaped the hour, which its own
  footprint says it did not.
* **P-1b** — the CC_REGULAR error at hod 22 / 23 in 2025 (CEMS basis) is
  within ±300 MW of +1,536 / +1,546 (the arm took −0.452 TWh off CC in
  2025, −52 MW mean).

**E-1 — the self-scheduled hypothesis, on committed artifacts.** Let
`floor_2223[y, m]` be the keeper's summed firm-tranche `min_gen` at hod
22–23 from the D-3 rebuild, by year and month, and `ceil_2223[m]` the S-2
ceiling.
* **P-2** — **the clip binds**: mean over months of
  `(ceil_2223[m] − floor_2223[y, m])` is **≤ 150 MW in every year** (the
  pro-rata clip and the eford derate leave a small non-negative remainder).
  If it holds, the keeper already floors the WHOLE measured price-insensitive
  intertie position at these hours, and **no self-scheduled or ≤ $0 intertie
  volume remains un-carried** — H-INTAKE's "self-scheduled" limb is
  falsified by CAISO's own bid record.
* **Falsifier / alternative object:** if `ceil − floor ≥ 500 MW` in any
  year, the clip is *not* binding where the shape says it should, and THAT
  is the object — a different one, needing its own PRECOMMIT; this session
  then stops without an arm.

**E-2 — the showing hypothesis (S-1).**
* **P-3** — for each of Jun–Sep 2025, the S-1 final shown-RA value at the
  PWT ties is within **±600 MW of `ceil_2223[m]`** and within ±600 MW of the
  keeper's own summer `floor_2223[2025, m]`: the showing IS the
  price-insensitive intertie position the ceiling measures, on a subset of
  ties — it is **not additive** to the firm block.
* **P-4** — the "historic non-RA imports" component of the S-1 estimate is
  **≤ 700 MW in every month** and appears only in the estimate, never the
  final: the one "beyond-RA" quantity the source names is an order of
  magnitude below the gap and is not a shown value.

**E-3 — attribution of the residual (class C, diagnostic only, never
wired).**
* **P-5** — the dynamic WEIM net transfer into the CAISO BA at hours 22–24
  in 2025 (S-5 chart read, ±150 MW) is between **+0.4 and +1.2 GW**, so the
  remainder of the 1.8 GW (**≥ 0.6 GW**) is **economic intertie import
  cleared at or below λ** — class B conduct that only S-7 could size, and
  class D if any armed rung were moved to reach it.

**E-4 — exposures, measured on the caiso-260 bundle.**
* **P-6** — hod 22–23 carry **8–11 %** of the 2025 gas-fleet MSE (caiso-258
  §6 re-measured; direction only; C4 excluded from every conclusion).
* **P-7** — of the keeper's 23 model hours > $200 in 2023 (system price,
  the sidecar's load-weighted `price`), **≤ 3 fall at hod 22–23**: a carrier
  at these hours cannot move the C3c-2023 count across the 0.5× line, and the
  caveat is not a target. *(Reported whatever it reads; a value > 3 changes
  nothing about what this session does — it is a disclosure of exposure.)*

---

## §5 — STOP RULE (STOP-only; nothing here promotes)

**5.1** If **P-2 holds AND P-3 AND P-4 hold** → **H-INTAKE is FALSIFIED**:
no admissible source carries a contracted or self-scheduled import volume
beyond what the firm block already carries. The object is **CLOSED as a
data-intake object** and **re-named** by E-3's attribution ("economic
intertie import at hub parity, plus dynamic WEIM transfer, at hours no armed
construction may reach without a price, a window or a realised flow"). The
session ends with **no arm, no solve, no screen, no field**; the G-26 route
(S-7) is raised to the owner as a decision (§7), not proposed.

**5.2** If **P-2 is falsified** (the clip not binding by ≥ 500 MW in any
year) → also **STOP**: a different object (the floor under-carrying its own
measured ceiling) — reported, chartered separately, never acted on here.

**5.3** If **P-3 or P-4 is falsified** (a shown non-RA or beyond-ceiling
quantity ≥ 0.5 GW exists in S-1) → **STOP and report the intake** it would
need (class A: a level × the measured shape, floored, clipped), with its
rule-29(a) screen year to be named in THAT PRECOMMIT as the year of the
largest **added floor MW** (the mechanism's own footprint), never the year
of the largest residual. No wiring in this session.

**There is no branch in which this session solves.** G-DRIFT
(`_caiso255_gdrift_identity.py`, re-pointed at `caiso260_demand_vintage`,
keeper sha `e162147b`) is therefore **not run** — it binds at solve time
(PRECOMMIT-caiso255 §6.2) and no solve is at stake; disclosed rather than
spent.

---

## §6 — WHAT THIS SESSION WILL NOT DO

No `ScenarioConfig` field; no derive script invoked
(`derive_caiso_supply_consistent_demand.py` is never run — it takes no
arguments and rewrites the committed artifacts); no bench part regenerated
(so the caiso-260 §8 #7 standing duty is not engaged); no public-bid
re-fetch; no rung re-priced; no window moved; no EIA-930 or DMM realised
flow wired; no run registered (none produced — rule 15 is not engaged); no
bundle written (rule 29(c) not engaged); no matrix verdict moved (evidence
appends only, rule 28(b)); no out-of-training year touched; freeze
untouched.

Housekeeping carried in the same PR (caiso-260 §8 #8): the three probes
that hard-coded the pruned `caiso257_ctonly` path
(`_caiso255_gdrift_identity.py`, `_caiso258_hod2223_closure.py`,
`_caiso260_screen.py`) are re-pointed at `caiso260_demand_vintage`, the
screen probe's keeper baseline updated to the caiso-260 C4 values. Path
edits only.

---

## §7 — OWNER ASKS (raised, not granted)

1. **The `complete` marker** (rule 22) — CAISO is CALIBRATED on a keeper
   whose demand basis matches its scoring basis; raised again.
2. **The 2022 price source** (caiso-259 §7 #2) — volume-only rung /
   alternative hourly archive / leave unspent.
3. **The stale `program-status.json` `isos.CAISO.keeper` stamp** — not
   touched; ask before touching.
4. **The C3a weight basis** (caiso-247 §4.5); **the per-zone storage/class
   sidecar**; **S2 funding**; **the DMM 2025 RA-import basis**.
5. **NEW — the G-26 / audit C-6 CAISO closure**: a measured intertie
   economic offer surface from `PUB_DAM_GRP` (S-7, class B), which would
   replace the ladder's static-fitted $/MWh with CAISO's own as-submitted
   bids the way the NYISO / NEISO / MISO seam ladders were closed. It is the
   only measured source that could size the residual this session expects
   E-3 to leave; it is **not proposed on this residual** (caiso-252 §7 #2)
   and would need (a) the corpus re-fetched, (b) its own PRECOMMIT with
   C3a/C4 excluded and the C4-2025 / C3c-2023 exposures re-stated, (c) the
   caiso-150 §H wall respected (economic curves are classifiable by
   monotonicity, self-schedules are not). Fund, defer, or refuse.

**Next number: caiso-262** (if this session produces a FINDING and nothing
else).
