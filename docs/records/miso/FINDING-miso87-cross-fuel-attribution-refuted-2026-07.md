# FINDING (miso-87, 2026-07-24) — the cross-fuel outage-attribution split is refuted at charter: there is no measured level discrepancy to re-attribute, and no admissible key

**Context.** miso-85 and miso-86 both closed with the same named open lever: a
**cross-fuel attribution split** of MISO's published outage record — the ISO's
own Multiday Operating Margin `OUTAGE` sheet setting *how much* capacity is
offline, a measured key setting *where* — so that neither instrument has to work
outside its competent domain. This finding runs the charter arithmetic the
handoff required to be settled "with data not preference", **before** any solve
was spent. Reproduce with
`python scripts/probes/_miso87_outage_attribution_feasibility.py`.

Result: **refuted at charter, on two independent grounds.** No run was solved,
so nothing is registered (rule 15 is not engaged — there is no completed run).

## 1. The "residual" that motivated the split was a category mismatch

The lever's premise, carried forward from miso-85, was a gap between the two
measured records: CAMPD accounts **27.9 GW** mean thermal offline in 2023
against the published record's **21.8 GW** unplanned total, and the split would
re-attribute the difference.

Those two numbers are not on the same basis. CAMPD's 27.9 GW is **all-cause**
(forced + maintenance windows, undifferentiated — a CEMS gap does not say which)
and **thermal-only**. The published 21.8 GW is **unplanned-only** and covers the
**whole registered fleet**. Put both on an all-cause footing and scale by MISO's
actual thermal share:

| year | published all-cause | implied thermal (61.0–64.4 % share) | CAMPD thermal | share required to reconcile |
|---|---|---|---|---|
| 2023 | 42.4 GW | 25.8–27.3 GW | 27.7 GW | 0.655 |
| 2024 | 41.8 GW | 25.5–26.9 GW | 27.2 GW | 0.650 |
| 2025 | 48.7 GW | 29.7–31.3 GW | 25.2 GW | 0.518 |

MISO's registered capacity is **212.6 GW** (EIA-860 operable, BA = `MISO`), of
which fossil-thermal is **129.7 GW core / 136.8 GW** including the small
oil / reciprocating / process-gas fleet — a **0.610–0.644** share.

* **2023 and 2024**: the required share (0.655, 0.650) sits just above that
  range. The two independent records agree on thermal offline to **~1–2 GW**.
  There is nothing to redistribute.
* **2025**: the required share (0.518) sits *below* it — the published total
  implies **4.5–6 GW more** thermal offline than CAMPD measures. The discrepancy
  **flips sign** inside the three-year training window.

A quantity that is ~zero in two years and reverses in the third is not a
forward-reproducible physical signal a mechanism can carry (rule 13's
admissibility test: would it regenerate for a forward year and respond to changed
conditions?). It is the resolution limit of an aggregate record, and building a
mechanism on it would encode that noise as structure.

## 2. There is no admissible per-fuel key

MISO publishes **region × cause daily MW only**. No unit identity, no fuel
identity, and — decisively — **no thermal share**. Any split must therefore
import a key from outside the record.

The only per-fuel key in evidence is the **CAMPD per-unit record itself** (COAL
0.332/0.325/0.264, ST_GAS 0.589/0.529/0.508, CC_REGULAR 0.200/0.210/0.251,
CC_CHP 0.073/0.093/0.075, CT 0.000 — CTs are outside CAMPD coverage by
construction). Using CAMPD as the key while MISO's record sets the total makes
the mechanism reduce algebraically to

```
derate = CAMPD_class_shape × (assumed thermal share ÷ actual thermal share)
```

— a **scalar level knob** applied to the derate the keeper already solves on,
whose value is an **unmeasured assumption** (MISO publishes no thermal share, so
the numerator cannot be read off any record). That is a fitted level parameter
wearing a measured record's clothes, which rule 10 forbids and rule 20 would
require to appear in `ScenarioConfig` as exactly what it is.

The alternative — a **non-CAMPD** key (GADS / EIA-860 class outage rates) —
resolves the key problem but does not need MISO's published total at all, since
class rates already carry both level and attribution. That is a **different
mechanism** with its own charter, and its motivating gap is narrower than the one
proposed here: it would address `CT_PEAKER`/`CT_CHP` (25.0 GW carrying CAMPD
unavailability of exactly 0.000, covered today only by the statistical WEFOR/POF
layer), not the cross-fuel split.

## 3. Status of the lever

**Closed.** With both the residual (§1) and the key (§2) refuted, the cross-fuel
split as specified in the miso-85/86 handoffs has no admissible construction.
The `miso_native_outage_source` gate stays **wired and default-off** with its
cause set settled at the UNPLANNED components and the all-cause form still
refuted on physical feasibility (miso-85; `_miso85_outage_composition.py`) —
nothing in this finding changes that posture.

What remains genuinely open, and is *not* this mechanism, is the CT coverage hole
in §2: 25.0 GW of MISO peaking capacity whose only availability model is
statistical. That is worth its own charter, on its own evidence, with no
dependence on the published aggregate record.
