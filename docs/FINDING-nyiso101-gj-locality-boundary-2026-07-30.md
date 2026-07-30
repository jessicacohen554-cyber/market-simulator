# FINDING — nyiso-101: the G-J locality Bulk Power Transmission Limit has no
# representable boundary in the five-zone NYISO topology (EX-ANTE REFUSAL)

**Date:** 2026-07-30
**ISO:** NYISO
**Keeper at session start and at session end:** `2026-07-30-nyiso-100-silretire`
(`results/calibration/nyiso100_silretire`) — **UNCHANGED**
**Matrix row:** `nyiso_gj_lcr_tsl` → **G** (governance/identification-refused)
**Instrument:** `scripts/probes/nyiso101_gj_locality_boundary.py` (**no LP**;
build-time identification only)
**Runs produced:** **NONE.** This is an ex-ante refusal — the boundary could not
be identified, so no mechanism was armed and no solve was launched. There is no
bundle to register (rule 15 is satisfied vacuously: no run completed).

---

## 0. Verdict

**The published NYISO G-J locality Bulk Power Transmission Limit cannot be
placed on any link of the five-zone NYISO topology, and the placement is
refused.** Two of the four legs of the real G-J boundary are not expressible as
LP quantities — one because the cutset is *interior to a model zone*, one
because the repo's own source note says the required allocation is a modelling
choice rather than a measured fact — and those two legs carry the overwhelming
majority of the real boundary flow. The two legs that *are* representable are
already governed at their own boundaries by their own published limits
(`nyiso_nyc_lcr_tsl`, `nyiso_li_lcr_tsl`), so putting G-J on them would be a
second mechanism on the same links in the same window (rule 19 `[R-ONE-MECH]`)
— and on the one uncontested representable edge a G-J cap is **provably inert
with no solve**.

This refusal is made **against** the direction the open gate wants. A binding
G-J limit tightens downstate supply and would RAISE downstate peak prices,
which is the direction C3c — the sole NYISO determination blocker — needs. That
was pre-registered as a reason for *extra* scrutiny, not encouragement (rule 1
`[R-STRUCT]`, both directions). The boundary could not be identified, so the
limit does not go in, whatever it would have done to C3c.

**The limit is real and it stays unrepresented.** That is recorded here as a
known, bounded structural limitation of the five-zone aggregation — not as a
resolved item — with an explicit and *satisfiable* re-open condition (§6).

---

## 1. What was chartered

nyiso-100 proved the retired 4,350 MW `NYISO_simultaneous_import` scalar was
*exactly* the G-J locality Bulk Power Transmission Limit for capability year
2024/25, mis-installed on the EXTERNAL NYCA seam
(`docs/FINDING-nyiso100-simultaneous-import-misattribution-2026-07-30.md`).
Retiring it from the external seam left the limit itself represented **nowhere**.
The limit is published every capability year
(`data/raw/capacity-deliverability/nyiso/nyiso.csv`, area `G-J`):

| solve year | delivery year | G-J | NYC | Long Island |
|---|---|---|---|---|
| 2023 | 2023/2024 | **3,425** | 2,875 | 325 |
| 2024 | 2024/2025 | **4,350** | 2,875 | 275 |
| 2025 | 2025/2026 | **4,500** | 2,875 | 275 |

The house pattern for such a limit is `nyiso_nyc_lcr_tsl` / `nyiso_li_lcr_tsl`
(`src/market_sim/model/interchange/nyiso.py`): replace the host link's physical
TTC with the published limit inside the design-condition window
(`NYISO_SELFSUPPLY_FLOOR_HOURS`, local HB14-21). The edit is three lines. **The
task was never the edit — it was the boundary**, and the boundary is where it
fails.

---

## 2. The G-J locality straddles a model zone (mechanical result)

The G-J locality is NYISO load zones **G, H, I, J**
(`data/raw/capacity-deliverability/nyiso/README.md`). The five-zone aggregation
(`config/iso_configs.py::_nyiso_config`) is A–E / F+G / H+I / J / K. Testing
each model zone against the G-J membership set:

| model zone | NYISO zones | vs G-J |
|---|---|---|
| `Upstate_West` | A+B+C+D+E | wholly OUTSIDE |
| `Capital_Hudson` | F+G | **STRADDLES** (in: G / out: F) |
| `Lower_Hudson` | H+I | wholly INSIDE |
| `NYC` | J | wholly INSIDE |
| `Long_Island` | K | wholly OUTSIDE |

Because exactly one zone straddles, the per-link cutset test has no valid
import-direction answer:

| model link | from side | to side | verdict |
|---|---|---|---|
| `Upstate_West->Capital_Hudson` | outside | MIXED | **not a cutset edge** — destination straddles |
| `Capital_Hudson->Lower_Hudson` | MIXED | inside | **not a cutset edge** — origin straddles |
| `Lower_Hudson->NYC` | inside | inside | **interior to G-J** |
| `NYC->Long_Island` | inside | outside | G-J boundary edge, **reversed** |

`Lower_Hudson->NYC` being *interior* to G-J is the important one: it is the link
whose in-window TTC the keeper already replaces with the **NYC** published limit
(2,875 MW). A G-J cap there is not merely a rule-19 stack, it is
category-wrong — it would cap a flow that never crosses the G-J boundary.

---

## 3. Leg-by-leg: two of four legs are not LP quantities

The real G-J boundary is the union of four legs. Their model status:

| leg | real quantity | model status |
|---|---|---|
| **1. F→G AC cutset** | the dominant leg; Zone G carries 4,688 / 4,759 / 4,704 MW of summer capability (2023/24/25 Gold Book) | **UNREPRESENTABLE** — interior to `Capital_Hudson`; no LP column crosses it |
| **2. external ties landing in Zone G** | PJM Ramapo 345 kV ~1,000 MW + ISO-NE New Scotland / Pleasant Valley ~600 MW | **UNREPRESENTABLE** — lumped into the 1,600 MW `import_node->Capital_Hudson` link, whose F-vs-G split `interchange/spec.py` itself calls *"a modelling choice inside the topology"*, not a measured allocation |
| **3. K→J ties** | measured peak-window LI→NYC export ≈ 0 MW | representable (`NYC->Long_Island` reversed) but **already capped in-window** by `nyiso_li_lcr_tsl` at LI's own published limit — rule 19 |
| **4. external HVDC into Zone J** | HTP 660 + Linden VFT 315 = 975 MW posted | representable (`import_node->NYC`, 1,000 MW) but is ~1.0 GW against a 4,350 MW limit whose other legs are missing |

Leg 2 is what closes the door. It is tempting to think leg 1 can be worked
around (see §5), but leg 2 cannot: the model would have to know how much of the
1,600 MW eastern-seam node link lands inside Zone G, and the repo's own
provenance note records that the F/G allocation was never determined from
data — it "re-homes part of the same lumped seam capability" as a topology
choice. There is no measured quantity to recover it from.

### Inertness of the one uncontested representable edge

| year | `NYC->Long_Island` TTC | LI cap in-window | G-J cap | effective `min()` | G-J binds? |
|---|---|---|---|---|---|
| 2023 | 1,650 | 325 | 3,425 | 325 | **NO** |
| 2024 | 1,650 | 275 | 4,350 | 275 | **NO** |
| 2025 | 1,650 | 275 | 4,500 | 275 | **NO** |

Provably inert by arithmetic, no solve required.

---

## 4. NYISO publishes no series that could validate a placement

The NYISO MIS P-32 posting carries seven internal transfer interfaces —
`CENTRAL EAST - VC`, `DYSINGER EAST`, `MOSES SOUTH`, `SPR/DUN-SOUTH`,
`TOTAL EAST`, `UPNY CONED`, `WEST CENTRAL` — and **none is G-J**. The G-J limit
exists only as a capacity-market (ICAP/LCR) transmission-security limit with no
metered hourly counterpart anywhere in repo.

That is a *structural* difference from its two accepted siblings, and it shows
up when the house pattern's own admissibility test is run on all three. The test:
a published locality limit placed on a host link in-window is admissible only if
measured flow on that link's own posted interface respects it in-window — a
limit sitting deep inside the measured distribution is over-tight on that
boundary, which is precisely the nyiso-100 failure mode.

**Accepted analog (control) — NYC 2,875 MW on `SPR/DUN-SOUTH`:**

| year | cap | in-win p50 | in-win p95 | in-win max | h>cap | %>cap |
|---|---|---|---|---|---|---|
| 2023 | 2,875 | 1,750 | 2,643 | 3,613 | 54 | 1.8% |
| 2024 | 2,875 | 1,907 | 2,870 | 3,614 | 146 | 5.0% |
| 2025 | 2,875 | 1,970 | 2,948 | 3,772 | 201 | 6.9% |

The cap sits essentially **at the p95** of its own interface's in-window flow.
That is the signature of a correctly-boundaried security limit, and it is
available *because* Zone J's boundary has a posted interface.

**Candidate — the G-J limit on each candidate host link:**

| host (posted interface) | year | G-J cap | in-win p95 | in-win max | h>cap | %>cap | cap sits at pctile |
|---|---|---|---|---|---|---|---|
| `Upstate_West->Capital_Hudson` (`TOTAL EAST`) | 2023 | 3,425 | 4,578 | 5,883 | 937 | 32.1% | 67.9% |
| | 2024 | 4,350 | 5,110 | 6,260 | 541 | 18.5% | 81.5% |
| | 2025 | 4,500 | 5,317 | 6,097 | 486 | 16.6% | 83.4% |
| `Capital_Hudson->Lower_Hudson` (`UPNY CONED`) | 2023 | 3,425 | 4,267 | 5,803 | 757 | 25.9% | 74.1% |
| | 2024 | 4,350 | 4,630 | 5,748 | 275 | 9.4% | 90.6% |
| | 2025 | 4,500 | 4,449 | 6,263 | 129 | 4.4% | 95.6% |
| `Lower_Hudson->NYC` (`SPR/DUN-SOUTH`) | 2023 | 3,425 | 2,643 | 3,613 | 3 | 0.1% | 99.9% |
| | 2024 | 4,350 | 2,870 | 3,614 | 0 | 0.0% | 100.0% |
| | 2025 | 4,500 | 2,948 | 3,772 | 0 | 0.0% | 100.0% |

In 2023 the limit would sit at the **68th–74th percentile** of measured
in-window flow on either eastern host — forcing the model below what the real
system actually moved in a quarter to a third of in-window hours. And on
`Lower_Hudson->NYC` it is *inert* (100th percentile, 0 hours) on top of being
category-wrong.

**A necessary honesty note.** This exceedance does **not** falsify the published
limit. Because leg 1 is real, measured `UPNY CONED` flow above the G-J limit is
explained by Zone-G net export, and the required Zone-G generation at the
in-window extremes — 2,010 / 1,487 / 1,180 MW at p95 and 3,545 / 2,605 /
2,994 MW at max — stays **inside** Zone-G capability (76% / 55% / 64% of it) in
every year. The limit is *consistent with* measurement for an unobservable
Zone-G net position. That is exactly why the verdict is **unidentified, not
refuted**: the discrepancy and the missing term are the same size.

---

## 5. Why the obvious workaround does not rescue it

Both legs of the translation are individually measurable, so it is worth showing
precisely where the arithmetic stops.

Zone-G power balance, with `ext_G` the external imports landing in Zone G:

```
F_[F->G] + ext_G  =  load_G + F_[G->H] - gen_G
```

`F_[G->H]` is the `UPNY CONED` cutset the model's `Capital_Hudson->Lower_Hudson`
link carries. The published limit binds the left side; a cap on the model link
binds `F_[G->H]`. So a translated cap is

```
F_[G->H]  <=  GJ_limit + gen_G - load_G - ext_G
```

**A static reconciled cap is unidentified.** `load_G` is measured directly
(`HUD VL` in `data/raw/zone-specific-demand/NYISO/`: in-window mean 1,168 /
1,207 / 1,231 MW). `gen_G` is bounded only by [0, Zone-G capability], which
pins the reconciled cap to an interval whose **width is larger than the limit
itself**:

| year | G-J cap | Zone-G capability | load_G in-win | reconciled cap interval | width | as % of cap |
|---|---|---|---|---|---|---|
| 2023 | 3,425 | 4,688 | 1,168 | [2,257, 6,945] | 4,688 | **137%** |
| 2024 | 4,350 | 4,759 | 1,207 | [3,143, 7,902] | 4,759 | **109%** |
| 2025 | 4,500 | 4,704 | 1,231 | [3,269, 7,973] | 4,704 | **105%** |

**The endogenous form does not fix it.** One could object that `gen_G` need not
be estimated, because the model computes it: NYISO runs `plant_level_fleet`, so
Zone-G units are individually addressable and the constraint could be written as
a subset-sum row,

```
F_[CH->LH][t]  -  Σ_{g in Zone G} P[g,t]   <=   GJ_limit - load_G[t]
```

which is linear and implementable, and whose non-separable omission is small
(Zone G holds only ~80 MW of hydro and 0 MW of battery against 4,567 MW of
dispatchable thermal, so the un-splittable `Capital_Hudson` renewable/storage
zonal variables barely matter). That objection is fair as far as it goes, and it
is why this refusal rests on **leg 2, not leg 1**: the row still needs `ext_G`,
the Zone-G share of the 1,600 MW eastern-seam node link, and that number does
not exist as a measured quantity — only as an undetermined modelling choice
(§3). Writing the row would require inventing it, which is a fitted parameter on
the residual's own side of the ledger (rules 24 `[R-REGISTRY]`, 5
`[R-NO-MAGIC]`). It would also be the model's only constraint of that class,
introduced for a limit that has no series to validate it against (§4).

---

## 6. Re-open condition (satisfiable, unlike C3c's)

Unlike C3c — a diagnosed structural limitation with an empty lever queue and no
satisfiable re-open condition (`FINDING-nyiso97` §5) — this cell has one clear
gate:

> **Split `Capital_Hudson` into Zone F and Zone G as separate model zones.**

That makes leg 1 a real link and forces leg 2 to be allocated explicitly, at
which point the published G-J limit lands on a genuine cutset and the house
pattern applies unchanged. The F/G county split is already carried, per-county,
in `zone_assignment.NYISO_CAPITAL_HUDSON_COUNTIES` (F: Albany, Columbia, Greene,
Rensselaer, Saratoga, Schenectady, Schoharie, Warren, Washington; G: Dutchess,
Orange, Rockland, Sullivan, Ulster), and the Gold Book Table III-2a carries the
zone letter per unit directly, so the fleet side is ready.

It is nevertheless **out of scope for a mechanism session** and is not queued
here. A zone split is a topology change: load shares, zonal demand shapes,
reliability-floor limb keys (`Capital_Hudson:ST_GAS`), D-2 attribution ids,
reserve/interchange registries and every NYISO keeper's comparability all move
with it. It is the same class of change as the ERCOT West/Panhandle topology
split, which is **CLOSED**
(`docs/DIAGNOSIS-ercot-trough-price-formation-2026-07.md` §§7–10) — so it needs
its own owner-authorized charter, not a lever-queue entry.

---

## 7. What this changes

- **Nothing in the keeper.** `2026-07-30-nyiso-100-silretire` is untouched; no
  flag added, no default changed, no solve run. C1 14/14 · free 10/10, C6 PASS
  (24-entry ledger, n_residual 6), C7/C8 PASS, C3c sole blocker, DETERMINATION
  NOT-YET — all unchanged.
- **The 2023 CC_REGULAR margin is untouched.** The ISO's tightest cell
  (−2.80 of ±2.94, 32.497 TWh) was budgeted ~0.14 TWh for this session and
  **spent 0.00 TWh**. It carries forward in full.
- **`nyiso_gj_lcr_tsl` → G** on the matrix, with this document as the citation
  and the §6 re-open condition recorded. Do not re-test the cell as a
  mechanism-flag lever; it re-opens only behind a zone split.
- **No new `ScenarioConfig` field** was added, so the rule-28(c) CI guard has
  nothing to enforce.

## 8. Reproduce

```
uv sync && PYTHONPATH=.:src python scripts/data/curate_capacity_deliverability.py
PYTHONPATH=.:src python scripts/probes/nyiso101_gj_locality_boundary.py
```

Sections: `provenance`, `cutset`, `legs`, `split`, `falsify`, `reconcile`. No LP;
runs in seconds. Method note carried forward from nyiso-100 and honoured here:
MIS/instrument feeds are aligned on **UTC timestamps**, never positionally (the
probe keeps both clocks — UTC for joins, local for the HB14-21 window, which is
a local-clock definition); 2024 posts 8,784 hours against the model's 8,760.
