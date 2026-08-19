# DECISION CARD — the `RHO_CLIP` band (owner, rule 22 D-5(b))

Raised by session **nyiso-145**, 2026-08-19, on the standing escalation opened by
nyiso-144. **No solve was spent**; every number below is measured on committed
artifacts (`scripts/probes/_nyiso145_rho_clip_card.py`, record
`results/calibration/_nyiso145_rho_clip_card.json`). Nothing is re-banded here
and neither gated flag is armed — both stay `U` pending this ruling.

---

## 0. THE ASK, in one line

`RHO_CLIP = (0.5, 4.0)` clips **every measured `online_rho` row that exists in
this repository — all three, on two different ISOs' fleets.** Decide whether the
0.5 floor stands, moves, or goes.

---

## 1. WHAT `rho` IS, and why the band is load-bearing

The online-gated class-2 reserve row (`model/lp/reserve_rows.py`) is

    R[c, z]  −  rho · Σ_{g eligible in z} P[g, t]  ≤  0

so `rho` is the MW of 10-minute deliverable headroom that one MW of on-line
output carries with it. **On NYISO that row REPLACES the capability row rather
than joining it** (the branch ends in `continue`; `zone_cap` stays 0), so `rho`
is the class's **only** bound. A wrong `rho` is not a refinement — it is the
whole constraint.

`data.online_reserve_rho.rho_used` returns `clip(rho, 0.5, 4.0)`. All three
measured rows sit below 0.5, so **today the coefficient in the LP is the
guardrail, never the measurement.**

---

## 2. THE MEASUREMENT — every `online_rho` row in the repo

| ISO | family set | measured `rho` (as-operated) | `rho_minload` | value used today | online unit-h | CAMPD coverage |
|---|---|---:|---:|---:|---:|---:|
| MISO | `miso_reg_spin` | **0.1764** | 0.6863 | **0.50 (FLOOR)** | 5,276,357 | 93.1 % |
| NYISO | `incity_obligation` | **0.3014** | 1.2462 | **0.50 (FLOOR)** | 401,361 | 95.5 % |
| NYISO | `nyc_spin` | **0.2011** | 1.1247 | **0.50 (FLOOR)** | 124,850 | 80.5 % |

Two facts fall straight out of that table, and together they are the case.

**(a) No measurement on any fleet reaches the floor.** Three independent family
sets, two ISOs, 5.8 million online unit-hours, 80–96 % metered coverage — every
one clipped. A floor that no measured fleet has ever reached is not bounding
physics; it is overriding data.

**(b) Every `rho_minload` counterpart lands INSIDE the band.** That is the
diagnosis, not a coincidence. `RHO_CLIP` was written for the LEGACY estimand —
the eligible fleet's cap-weighted `(pmax − pmin)/pmin`, evaluated **at minimum
stable load**, where the value genuinely is `(1 − f)/f` and `[0.5, 4.0]` brackets
`f ∈ [0.2, 0.667]`. The measured seam introduced a **different estimand**: the
as-operated aggregate `Σ head / Σ P` over the fleet's real online hours, where
units run well above min load and headroom-per-MW is several times smaller. Same
fleets, same derivation, two estimands — **the min-load one is inside the band in
all three rows and the as-operated one is below it in all three rows.** The band
was inherited across a change of estimand.

---

## 3. IS THERE ANY PHYSICAL BASIS FOR A FLOOR?

* **The 4.0 CEILING has one.** At minimum stable load a unit's headroom is at
  most `(1 − f)/f`; the deepest turn-down in the model's own class tables is
  NYISO ST_GAS at `f = 0.239`, giving ≈ 3.2, and `f = 0.2` gives exactly 4.0. The
  ceiling is a real bound on the min-load estimand and is loose-but-harmless on
  the as-operated one. **Nothing here argues against keeping it.**
* **The 0.5 FLOOR has none.** The physical lower bound on 10-minute headroom per
  MW online is **zero** — a fleet at full load carries no headroom, and that is
  routinely approached at peak. Read as `(1 − f)/f`, a floor of 0.5 asserts
  `f ≤ 0.667`: every online fleet always holds at least half its output as
  10-minute headroom. No measured fleet does.
* **Its stated justification is self-referential.** Both call sites described it
  only as "the same [0.5, 4.0] physical band the path-A family uses". `git log
  -S` finds no earlier primary citation, and the earliest textual appearance
  (`PREREG-nyiso110-spin-online-peak-formation-2026-08-02.md` §2) asserts the band
  without a source.

**The floor's safety direction is not even consistent across ISOs.** In MISO the
gated coupling row **adds** to the pool's joint headroom row, so clipping *up* to
0.5 is conservative — miso-169's own words: *"the floor blunts the refinement in
the CONSERVATIVE direction."* In NYISO the row **replaces** the capability row,
so clipping up to 0.5 makes the class's only bound **looser** than the meter
supports — by **2.49×** (`nyc_spin`) and **1.66×** (`incity_obligation`). One
uncited number, opposite safety directions in two ISOs.

---

## 4. WHAT EACH NYISO FLAG DOES AT THE FLOOR vs AT THE MEASUREMENT

Binding hours of the gated row on the **designated keeper's own committed
per-plant model hourlies** (`2026-08-18-nyiso-144-layup-exclusion`), by year
2023 / 2024 / 2025. The two flags are mutually exclusive (rule 19); only one can
ever be armed.

### `nyiso_synchronised_reserve` — NYC, requirement 250 MW, eligible = quick-start

| rho | 2023 | 2024 | 2025 |
|---|---|---|---|
| **0.2011 (measured)** | 8,739 h (99.8 %) | 8,740 h (99.8 %) | 8,714 h (99.5 %) |
| **0.50 (floor, used today)** | 8,608 h (98.3 %) | 8,572 h (97.9 %) | 7,845 h (89.6 %) |
| 1.0 (legacy fallback) | 7,583 h (86.6 %) | 6,744 h (77.0 %) | 4,436 h (50.6 %) |
| 4.0 (ceiling) | 0 h | 0 h | 0 h |

Binds in essentially every hour at either value: **the band changes how hard,
not whether** — confirming nyiso-144. The floor understates the shortfall.

### `nyiso_incity_commitment_obligation` — NYC 500 MW + Long Island 120 MW, eligible = quick-start ∪ ST_GAS

| zone | rho | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| NYC | **0.3014 (measured)** | 7,117 h (81.2 %) | 7,912 h (90.3 %) | 7,493 h (85.5 %) |
| NYC | **0.50 (floor)** | 4,858 h (55.5 %) | 6,717 h (76.7 %) | 5,596 h (63.9 %) |
| Long Island | **0.3014 (measured)** | 7,471 h (85.3 %) | 6,679 h (76.2 %) | 5,483 h (62.6 %) |
| Long Island | **0.50 (floor)** | 5,346 h (61.0 %) | 4,488 h (51.2 %) | 4,086 h (46.6 %) |

**Here the band is material**: the floor removes ~26 / 14 / 22 pp of NYC binding
hours and ~24 / 25 / 16 pp on Long Island. Arming this flag today would size a
commitment driver from a guardrail.

*(Carried unchanged from nyiso-144 §2.4, so it is not re-litigated here: arming
the obligation also MOVES `nyc_10min_total` and `li_10min_total` out of class 1,
removing the capability row that currently binds 28/28/62 h at $25 — so its
expected effect on the C3c tail is neutral-to-negative regardless of `rho`.)*

---

## 5. THE OPTIONS

| | option | band | what it does | what it costs |
|---|---|---|---|---|
| **A** | **Delete the floor** | `(0.0, 4.0)` | Every measured row solves at its own measurement. Ceiling keeps its min-load derivation. Both NYISO gated flags become admissible on a data-identified coefficient (rule 21 satisfied). | A future fleet measured at ≈ 0 would zero its class's reserve. Real, but see below. |
| **B** | **Lower the floor to fit** | e.g. `(0.15, 4.0)` | Keeps a guardrail; admits all three current rows. | The number is chosen *so the data survives* — a fitted guardrail by another name, and it would need re-choosing the first time a fleet measures lower. Rules 5/21. |
| **C** | **Keep `(0.5, 4.0)`** | unchanged | No code change. | Both NYISO gated flags stay `U` **permanently** — neither can enter a keeper on a guardrail-chosen coefficient. MISO's armed run keeps solving at the floor. The reserve-price-formation gap (nyiso-110 / -124 / -144) stays open with its named instrument unreachable. |

**Session recommendation: A.** It is the only option whose every endpoint is
citable and none of whose endpoints is chosen against a measurement: `0` is the
physical lower bound of headroom-per-MW-online, and `4.0` is `(1 − f)/f` at the
deepest turn-down in the model's own class tables. The guard option B reaches
for is real but is better met **structurally than by a silent clip** — the
artifact already reports `online_unit_hours` and `campd_coverage_frac` per row,
so a degenerate measurement can be refused loudly at derivation time (as
`load_online_rho` already refuses a missing row) instead of being quietly
replaced by a number the LP then treats as measured.

**What A is not.** It is not a licence to arm either flag: arming stays a
separate decision, and `nyiso_incity_commitment_obligation` carries the §4
structural objection independently of the band. It does not touch MISO's lane —
`miso_reg_spin` would begin solving at 0.1764 rather than 0.5, which is a
*tightening* there, and miso-169's arm would need re-solving before any claim
about it is made. **That cross-ISO consequence is why this is an owner ruling and
not a NYISO-lane call** (rules 25 / 28d).

---

## 6. PROVENANCE

* Escalation opened: `results/calibration/FINDING-nyiso144-downstate-scarcity-and-rho-2026-08-18.md` §2.3.
* Independent second hit, same day, different ISO: `results/calibration/RESULT-miso169-online-gated-execution-2026-08-19.md` §2.
* Code: `src/market_sim/data/online_reserve_rho.py` (`RHO_CLIP`, and the honest-status comment nyiso-144 left in place); `src/market_sim/model/reserves/spec.py::_identified_online_rho`.
* Measurement: `scripts/data/derive_campd_online_reserve_rho.py` → `data/raw/_processed-legacy/campd_online_reserve_rho_{NYISO,MISO}.csv`.
* This card's own record: `scripts/probes/_nyiso145_rho_clip_card.py`, `results/calibration/_nyiso145_rho_clip_card.json`.
