# FINDING — caiso-132: **ASK A1 is KILLED at the derive gate.** The DSW→CA corridor congestion that carries C3a-2025 is **import-direction** rent: across all 26,280 hours of 2023–2025 the corridor's export-direction bound is the active one in **2 of 52,560 corridor-hours (0.0038 %)**, and in the Sep–Dec 2025 surplus belly that carries the +$3.87 term it is active in **0.000** of hours on **both** legs. A1's first limb — the corridor export-direction deliverability envelope — is **not a new mechanism at all: it is already armed on the keeper** and is provably inert. Its second limb, a surplus-scoped export floor, has the **wrong sign**: forcing export out of an import-bound zone widens the very spread A1 must close. Cost: one derive, no solve.

**Keeper `2026-07-27-caiso-130-nameplate-aware` UNCHANGED. Derive-gate-only
session — NO LP was built or solved, no mechanism was armed, no bundle was
produced and nothing was registered on the dashboard.** Per the charter's step 1,
"ANY of D1–D3 failing KILLS A1 for the cost of a derive — that outcome is a
complete, publishable session." All three fail, plus a scope gate (D0) added
here that subsumes them. Step 2 (prereg) and step 3 (A/B) are therefore **not
reached**: no solve is authorized, and none was run.

Instrument (committed): `scripts/probes/_caiso132_corridor_export_gates.py`,
sections D0/D1/D2/D3/E. Every number below is reproducible from the keeper's
**committed hourly sidecars** (`hourly/system_<y>.parquet`,
`class_hourly_<y>.parquet` — never a replay), the committed actual-LMP
reference, and the committed EIA-930 BA-to-BA interchange parquet that
`measured_corridor_flow_envelope` already reads.

**Verification against the prior finding.** The instrument reproduces
`FINDING-caiso131` §7's Sep–Dec table **digit-for-digit** — 2025 CA λ **46.19**,
WECC_DSW **42.33**, CA − DSW **+3.87**, WECC_PNW **4.97** — before any new
measurement is taken, so the rows below are on the memo's own basis.

---

## §1 — the four gates, and what killed A1

| gate | what it asked | result | verdict |
|---|---|---|---|
| **D0** (scope, added here) | is the export-direction bound EVER the active one? | **2 of 52,560** corridor-hours, 0.0038 % | **FAIL — family-wide** |
| **D1** | export envelope hour-of-day shape, pairwise cross-year `r ≥ 0.99` | DSW worst **0.9577**, PNW worst **0.9879** | **FAIL** (but non-discriminating — see §4) |
| **D2** | export bound binding in ≥ 50 % of the Sep–Dec 2025 surplus hours | **0.000** on both legs | **FAIL** |
| **D3** | mechanism must *reduce* CA λ − WECC_DSW λ | 100 % of the defect rent is import-bound | **FAIL** |

**D0 is the load-bearing one, and it is the strongest form of the caiso-129
§3(a) kill.** D2 and D3 ask where the mechanism binds and which way it pushes;
D0 answers a prior question — the export-direction bound is essentially never
the active constraint anywhere in the scored record, so *no* export-direction
mechanism can change this LP in *any* hour of *any* of the three years,
independent of scoping, threshold or window.

## §2 — the method: binding direction read off the LP's own duals, with no solve

The keeper's slim bundle carries no flow sidecar, so "does the corridor bind, and
in which direction" looks like a question needing a replay. It is not. For a
corridor link bounded

```
    -export_cap  ≤  f  ≤  +import_cap
```

LP optimality gives `λ_terminus − λ_corridor = μ_import − μ_export` with
`μ_import, μ_export ≥ 0` and complementary — at most one is positive. So **the
sign of the measured zonal spread IS the binding direction**, exactly:

* `> +tol` → an import-direction limit binds; the export bound is **strictly
  slack**;
* `< −tol` → the export bound binds;
* `|·| ≤ tol` → neither binds (the import rung is marginal, corridor slack).

`tol = $0.50/MWh`, the caiso-105 intertie equalisation tolerance. Both zonal λ
series are in the committed `system_<y>.parquet`, so the census is a read, not a
solve. The corridor terminus pairing is the LP's own
(`model/interchange/caiso.py::_CAISO_CORRIDOR_LINK_TO`): **WECC_PNW → NP15**,
**WECC_DSW → SP15_rest**.

One honest qualifier: "import-bound" means *some* import-direction limit binds —
the corridor deliverability group, the link's own TTC, or the
`WECC_import_simultaneous` interface. Which of the three is not separable from
the duals alone. It does not matter for A1: whichever it is, the export bound is
slack in the same hour by complementarity, and that is the whole of D2/D3.

## §3 — D0: the export bound is globally inert (§D0)

All 8,760 hours × 3 years × 2 legs = 52,560 corridor-hours:

| year | leg | import-bound | **export-bound** | neither | min spread |
|---|---|---|---|---|---|
| 2023 | WECC_PNW | 0.5281 | **0.0000** | 0.4719 | 0.00 |
| 2023 | WECC_DSW | 0.3765 | **0.0002** | 0.6233 | −20.00 |
| 2024 | WECC_PNW | 0.5401 | **0.0000** | 0.4599 | 0.00 |
| 2024 | WECC_DSW | 0.3420 | **0.0000** | 0.6580 | 0.00 |
| 2025 | WECC_PNW | 0.3920 | **0.0000** | 0.6080 | 0.00 |
| 2025 | WECC_DSW | 0.3497 | **0.0000** | 0.6503 | 0.00 |

**Total: 2 export-bound hours in 52,560.** Both are 2023 WECC_DSW, model hours
**2361 and 2697** (both hod 09, mid-April), both at exactly −$20.00 — the
negative-price floor, not a deliverability event. **Neither is in the Sep–Dec
window, neither is in 2025, and neither is in the surplus belly.**

## §4 — D1: the shape gate fails, but it fails *non-discriminatingly* (§D1)

Filed gate: pairwise cross-year `r ≥ 0.99` on the hour-of-day shape, the
caiso-106/107/129 standard. Construction verified equivalent to caiso-129's
(normalised annual hod share) — the two agree to six decimals, because every hod
carries exactly 365 days on the fixed 8,760 calendar, so the share vector is a
positive scalar multiple of the mean profile and Pearson `r` is unchanged.

| direction | leg | 2023/24 | 2023/25 | 2024/25 | worst | gate |
|---|---|---|---|---|---|---|
| **export** | WECC_DSW | 0.9919 | **0.9577** | 0.9766 | **0.9577** | FAIL |
| **export** | WECC_PNW | 0.9926 | 0.9907 | **0.9879** | **0.9879** | FAIL |
| *import (control)* | WECC_DSW | 0.9867 | **0.9802** | 0.9955 | **0.9802** | *FAIL* |
| *import (control)* | WECC_PNW | 0.9897 | 0.9905 | **0.9797** | **0.9797** | *FAIL* |

**Stated plainly, because it matters: the control limb fails too.** The
import-direction envelope — which *is* armed on the keeper, load-bearing, and
never challenged — would not clear `r ≥ 0.99` either. So unlike caiso-129, where
the accepted charge side cleared 0.9919 against a failing discharge side at
0.9726 and the gate genuinely discriminated, here the gate rejects the armed
control as readily as the candidate. **D1 as filed does not distinguish A1 from
the status quo, and no weight is placed on it.** The kill rests entirely on
D0/D2/D3, which are exact and direction-specific.

This is worth carrying forward as a caution about the `r ≥ 0.99` standard: it
was identified on a *storage allocation share* and does not transfer unexamined
to a corridor ATC envelope, whose hour-of-day shape legitimately moves with the
neighbours' own annual solar build (rule 25 `[R-ISO-SCOPE]` in spirit — a gate
threshold fitted on one object is that object's).

## §5 — D2: the export bound binds in **zero** of the defect hours (§D2)

Defect hour set, on caiso-120/121's own conventions so the rows compose with
theirs: belly = hod 10–15, surplus = belly hour with measured RT ≤ $20/MWh,
narrowed to Sep–Dec (`FINDING-caiso131` §7's window, 81 % of the C3a-2025 gap).

| year | n | CA λ | actual RT | leg | λ_leg | spread | import-bd | **export-bd** | neither |
|---|---|---|---|---|---|---|---|---|---|
| 2023 | 192 | 22.09 | 9.36 | WECC_PNW | 5.42 | +16.67 | 0.401 | **0.000** | 0.599 |
| | | | | WECC_DSW | 13.54 | +8.55 | 0.479 | **0.000** | 0.521 |
| 2024 | 239 | 16.55 | 8.75 | WECC_PNW | −5.56 | +22.38 | 0.561 | **0.000** | 0.439 |
| | | | | WECC_DSW | 10.96 | +5.89 | 0.431 | **0.000** | 0.569 |
| **2025** | **229** | **24.88** | **9.06** | **WECC_PNW** | **−10.03** | **+34.90** | **0.764** | **0.000** | 0.236 |
| | | | | **WECC_DSW** | **16.51** | **+8.36** | **0.441** | **0.000** | 0.559 |

Gate: export-bound in ≥ 50 % of hours. Actual: **0.000**. D2 fails by its whole
range on both legs in all three years.

Corroboration from the quantity side (model import from `class_hourly`, ceiling
from the LP's own envelope), Sep–Dec surplus belly:

| year | corridor import ceiling | model import | utilisation | export ceiling |
|---|---|---|---|---|
| 2023 | 4,270 MW | 3,296 MW | 0.760 | 2,452 MW |
| 2024 | 5,901 MW | 4,898 MW | 0.824 | 1,189 MW |
| **2025** | **6,050 MW** | **5,569 MW** | **0.929** | **1,202 MW** |

The import ceiling is at **93 % utilisation** in the 2025 defect hours and
rising year on year, while the export ceiling is non-zero in 100 % of them and
untouched. The model is pressed hard against the import side of the corridor and
nowhere near the export side — the same conclusion the duals give, from
independent data.

## §6 — D3: the sign is wrong, and limb (a) is already in the keeper (§D3)

**Both limbs of the family, checked against the D2 census.**

**Limb (a) — the corridor export-direction deliverability envelope. This is not
a new mechanism. It is already armed on the keeper.** The keeper carries
`caiso_corridor_flow_limit = True` with `caiso_corridor_atc_forward` falsy, so
`scripts/run_calibration.py` takes the measured branch, builds
`corridor_export_env = measured_corridor_flow_envelope(..., direction="export")`
and hands it to `build_caiso_corridor_flow_groups(..., export_envelope=...)`,
which emits the asymmetric group `(idx, import_cap, False, export_cap)`. The
export ceiling has therefore been in every CAISO keeper solve on this path, and
D0 measures what it does: it binds in 2 of 52,560 corridor-hours. **A1's first
limb is an already-armed, provably-inert mechanism, and re-arming it is a no-op**
(the `FINDING-caiso129` §3(a) failure mode, in its strongest form).

**Limb (b) — a surplus-scoped export floor. Wrong sign.** A floor forcing net
export moves energy *out* of CA. In an import-bound hour that is a supply
reduction, so λ_CA weakly **rises** and λ_DSW weakly falls: the spread A1 must
close **widens**. This is the `FINDING-caiso129` §3(c) "a floor can only ADD"
form, mirrored into the export direction — and it is not a prediction, it is the
measured caiso-113 outcome: L1a′ bounded the export legs at this same measured
p95 envelope and **broke the C3a guard with an over-price of +11.5 % (2024) /
+12.7 % (2025)**, for exactly this reason.

The share of the defect-hour congestion rent that sits in import-bound hours —
i.e. the share unreachable by limb (a) and pushed the wrong way by limb (b):

| year | WECC_PNW rent | in import-bound h | WECC_DSW rent | in import-bound h |
|---|---|---|---|---|
| 2023 | $17.16/MWh | **100.0 %** | $8.99/MWh | **100.0 %** |
| 2024 | $21.71/MWh | **100.0 %** | $6.31/MWh | **100.0 %** |
| 2025 | $35.33/MWh | **100.0 %** | $9.02/MWh | **100.0 %** |

100.0 % on both legs in all three years. There is no residue for an
export-direction mechanism to act on.

## §7 — the finding underneath the kill: **the stranding is PNW, not DSW**

`FINDING-caiso131` §7 named CA − WECC_DSW (+$3.87) as the Sep–Dec 2025 term and
noted WECC_PNW "stranded at $4.97". Reproducing both on one basis makes the
ranking explicit:

| year | CA λ | DSW λ | **CA − DSW** | PNW λ | **CA − PNW** |
|---|---|---|---|---|---|
| 2023 | 49.87 | 46.33 | +3.54 | 12.47 | **+37.40** |
| 2024 | 41.00 | 38.64 | +2.36 | −4.58 | **+45.58** |
| **2025** | **46.19** | **42.33** | **+3.87** | **4.97** | **+41.22** |

**The CA − PNW spread is an order of magnitude larger than CA − DSW**, and in
the 2025 defect hours the PNW leg is import-bound in **76.4 %** of hours against
DSW's 44.1 %. The corridor defect C3a-2025 rests on is predominantly the
**northern** leg. Its measured import envelope is also the small one — mean
**1,714 MW** (2025) against DSW's 4,885 MW — on a corridor (COI/Path-66) whose
physical rating is several times that.

## §8 — §E, forward pointer: the single-signed-link NET representation (OBSERVATION ONLY)

Filed as a measurement, **not** as a recommendation and **not** as a rehabilitated
A1. The LP represents each corridor as **one signed link** bounded at the p95 of
measured **net** import. Reality moves power both ways across the corridor's
several DIBAs within the same hour. From the committed EIA-930 parquet:

| year | leg | net import | gross import | gross export | gross/net | hours flowing BOTH ways |
|---|---|---|---|---|---|---|
| 2023 | WECC_PNW | −63 MW | 604 | 667 | −9.55 | **60.7 %** |
| 2024 | WECC_PNW | 236 MW | 721 | 485 | 3.05 | **70.7 %** |
| 2025 | WECC_PNW | 543 MW | 867 | 323 | 1.60 | **72.8 %** |
| 2023 | WECC_DSW | 3,356 MW | 3,710 | 354 | 1.11 | **80.5 %** |
| 2024 | WECC_DSW | 3,372 MW | 3,806 | 434 | 1.13 | **83.3 %** |
| 2025 | WECC_DSW | 3,581 MW | 3,949 | 368 | 1.10 | **83.8 %** |

CAISO's northern corridor is nearly **balanced in net** (−63 / +236 / +543 MW)
while carrying 604–867 MW gross import *and* 323–667 MW gross export, moving
power both ways at once in **61–73 %** of hours (DSW: 81–84 %). A net envelope on
a net link cannot hold that, and it is the net envelope that binds 76 % of the
2025 defect hours.

**Every caveat that applies, applies.** (i) This is a **topology** question
(bidirectional corridor legs), a different family from A1, and it must be
chartered separately — the charter forbids building a mechanism inside a
diagnosis session. (ii) It is *not* a licence to relax the import ceiling: the
model already over-imports the surplus belly by **+2,606 MW** against actual
(caiso-121), so a mechanism that simply buys more import headroom is
rule-1 `[R-STRUCT]` / rule-14 `[R-ACCURATE]` refused on its face. (iii) It must
clear the ask memo §2 envelope, above all **E1 (2025 spillover ≤ +$0.00)** —
2025 has −$0.31 of band room. (iv) It sits squarely in the territory where
caiso-113 (L1a′ export legs) was **rejected** and caiso-114
(`caiso_endogenous_wecc_node`) is **not re-armable**; neither precedent is
disturbed by anything here.

## §9 — what this does and does not change

* **Keeper unchanged**, determination NOT-YET, fail set **{C3a-2025, C3c}**.
  Nothing was solved, scored or registered.
* **C3a-2025 keeps its diagnosis and loses its selected family.**
  `FINDING-caiso131` §7's attribution — Sep–Dec, 81 % of the gap, corridor
  congestion — is **reproduced and unchanged**. What is refuted is caiso-121's
  *family selection* for it: the corridor/export-path family cannot act on
  import-direction rent. C3a-2025 is now a diagnosed defect with **no selected
  mechanism**.
* **The ask memo's ranking is disturbed.** §7 of the ask put A1 first as "the
  tractable one". With A1 killed, the memo's remaining items (A2 the LOLP
  reserve measure, A3 the SoCalGas OFO intake, A4 the C3c ledger) are unchanged
  and unaffected — none of them was contingent on A1 — but the C3a-2025 lane now
  needs a new candidate before it can be worked at all.
* **C3c was not touched**, per the charter's explicit instruction. It remains a
  separate lane (asks A2/A3/A4).

## §10 — DO-NOT-REDO (new, binding)

* **Re-proposing the corridor / export-path family for CAISO C3a in any form** —
  export-direction deliverability envelope, surplus-scoped export floor,
  window-scoped or regime-scoped variants. D0 shows the export bound is the
  active constraint in 2 of 52,560 corridor-hours; D2 shows it is active in 0.000
  of the defect hours; D3 shows the floor limb has the wrong sign and reproduces
  the measured caiso-113 C3a break. Scoping cannot rescue a mechanism whose bound
  is slack everywhere.
* **Re-arming the corridor export-direction envelope as if it were new.** It is
  already armed on the keeper via `caiso_corridor_flow_limit` (§6); any proposal
  to "add" it is a no-op and any A/B against it would produce a byte-identical B.
* **Re-measuring** the corridor binding-direction census (§3/§5), the defect-hour
  congestion rents (§6), the CA−DSW / CA−PNW ladder (§7), or the net-vs-gross
  interchange decomposition (§8). The committed instrument carries all of them
  and needs no solve.
* **Quoting the `r ≥ 0.99` hour-of-day gate against a corridor ATC envelope
  without its control limb.** §4: the armed import envelope fails the same gate
  (0.9797–0.9802). A one-sided application of it would have killed A1 for the
  wrong reason and would equally condemn a load-bearing keeper mechanism.
* **Treating §8's net-vs-gross measurement as a funded candidate.** It is an
  observation with four live objections (§8) and no charter.

Carried forward unchanged: everything in `FINDING-caiso131` §10,
`FINDING-caiso130` §7, `FINDING-caiso129` §6, `FINDING-caiso127` §7 and
`FINDING-caiso128`'s DO-NOT-REDO. Notably still binding: C3c is a supply-surplus
defect and no offer-curve/heat-rate or quantity-side derate work addresses it;
`caiso_endogenous_wecc_node` is not re-armable; the allocation-floor and AS-award
families are CLOSED; the extract basis is frozen and C3a-2025 is a guard, never a
tuning target; rule 20 `[R-HOLDOUT]` — 2023–2025 only, and no year outside it was
solved, scored or probed here.

Next number: caiso-133.
