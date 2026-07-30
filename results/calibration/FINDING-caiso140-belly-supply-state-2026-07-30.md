# FINDING — caiso-140: the C3a-2025 "belly over-price" is a **Sep–Dec ALL-LOW-PRICE-HOURS** residual whose supply state is now EXACTLY led­gered — gas ride-through loading (74 % of the belly wedge) plus a **+793 MW water wedge the caiso-130 basis missed 10×** (the model's unrestrained PS pumps ~700 MW in the belly) — and the D-gates **KILL the solve**: the only admissible floor instrument delivers **less than half** the −$0.31 the gate needs, because the belly λ is pinned by a 2.7–3.0 GW economic-import plateau at the measured hub parity. NO SOLVE, nothing armed (2026-07-30)

**Keeper `2026-07-29-caiso139-dump-guard-offer` UNCHANGED.** No mechanism armed,
no `ScenarioConfig` field added, **no LP built and no solver called**. This is
the charter's own D-gate discipline executing: D1/D2 landed the diagnosis, D3
priced the counterfactual analytically, and D4's kill-check fired **before**
any arm solved — the caiso-129 pattern ("the one deliverable of a failed
kill-before-solve gate is the measurement that killed it").

Instruments (committed, no LP, no solver):

* `scripts/probes/_caiso140_belly_supply_state.py` — §A (D1) the residual per
  (month × hod) on the rubric's rt_lw weights; §B (D2) the **exact** supply-
  state ledger; §C the drill-down. Every number reproduces from the keeper's
  committed `hourly/` sidecars, the committed actual-LMP reference, the
  committed supply-consistent-demand artifact and the EIA-930 CISO frame.
* `scripts/probes/_caiso140_d3_walkdown.py` — §D3: counterfactual λ(S) for
  S MW of added price-taking CA supply, on the committed sidecars plus the
  `run_year(fleet_only=True)` offer reconstruction (the caiso-131/134
  machinery).

---

## §A — D1: where the +$2.90 actually lives. The "belly" shorthand is corrected

Per (month × hod-band) contributions to the C3a gap, rt_lw common weights
(caiso-131 §2 convention — cells sum exactly to the printed annual gap):

| 2025 | belly 10–15 | eve 17–21 | night 0–6 | other hods | total |
|---|---|---|---|---|---|
| Sep | +0.223 | +0.082 | +0.109 | +0.182 | +0.596 |
| Oct | +0.290 | +0.166 | +0.118 | +0.233 | **+0.807** |
| Nov | +0.069 | +0.080 | +0.057 | +0.145 | +0.351 |
| Dec | +0.167 | +0.112 | +0.167 | +0.152 | +0.598 |
| **year** | **+1.095** | +0.138 | **+0.721** | **+0.950** | **+2.904** |

Sep–Dec carries +2.35 of +2.90 (81 %, reproducing caiso-131 §2), but inside
Sep–Dec the belly band is only **+0.75 (26 % of the gap)**. The overnight
(+0.72 year-round) and the shoulder hods 7–9/16/22–23 (+0.95) carry as much as
the belly. **Any candidate scoped to the midday belly alone can reach at most
~38 % of the residual** — the phenomenon is "all Sep–Dec hours whose measured
price is low", not a midday artifact. (2023/2024 controls print the same
belly-positive pattern at C3a-passing totals +0.97/+2.24.)

## §B — D2: the EXACT ledger. The import wedge decomposes one-for-one into named CA supply states

The keeper's demand input is *built* from measured supply
(`demand = NetGen − NG_cell + CEMS_gas + flats − TI`, the caiso-80 artifact),
and the model's own hourly balance closes on that same demand to <0.01 MW. So,
per hour, **(model import − measured import) = Σ per-fuel (measured − model)
wedges, exactly** — closure residual 0.0 in every set, no coverage gap. The
probes verify the sidecar demand reproduces the committed artifact to 4e-11.

2025, mean MW over the hour set (share of the import wedge):

| set | import wedge | gas | hydro+PS | other | solar | battery | wind |
|---|---|---|---|---|---|---|---|
| annual | +705 | +714 (101 %) | +83 (12 %) | +217 (31 %) | **−319** | +30 | −32 |
| Sep–Dec belly (732 h) | **+1,989** | **+1,477 (74 %)** | **+793 (40 %)** | +332 (17 %) | **−453** | −131 | −36 |
| defect (RT≤$20, 229 h) | **+2,457** | +831 (34 %) | **+1,626 (66 %)** | +385 | **−936** | +636 | −77 |
| Sep–Dec night 0–6 | +1,133 | +886 (78 %) | −54 | — | −41 | +13 | — |

(2023/2024 print the same structure; the Sep–Dec-belly water wedge is
**+769/+803/+793 MW — near-constant across all three years**.)

Readings, each load-bearing:

1. **Gas ride-through loading is the dominant term in every band** — belly
   +1,477 (74 %) and overnight +886 (78 %) in 2025 — and it is the caiso-135
   LOADING defect (same plant count online, 0.74–0.80× the MW), now measured
   as the largest single fuel of the corridor over-import.
2. **The water wedge is 10× what the keeper's disclosure said, and the
   caiso-130 basis is why.** The keeper's "belly hydro gap −92/−58/−83 MW"
   compared model *conventional* hydro (belly 942 MW, 2025) against EIA-930
   `NG: WAT` (1,033) — but WAT **includes the real PS net**, while the model's
   own PS was left out of the model side. Like-for-like (both sides net of
   PS): model water position = 942 − **703 MW of model PS belly pumping** =
   239 vs measured 1,033 → **+793 MW**. The model's 2,078 MW pumped-storage
   fleet — caiso-127 §B2's "one entirely unrestrained arbitrageur" — pumps
   ~700 MW through the Sep–Dec belly in all three years.
3. **The solar wedge is measured curtailment the model refuses.** Model solar
   *exceeds* the measured print by 453 (belly) / 936 (defect) MW — reality
   curtails in exactly these hours and the model, still importing at the
   margin, does not (caiso-134 §6 re-stated from the supply side).
4. **Reality's import state:** in the 2025 defect hours the real market took
   2,804 MW against the model's 5,262 (2023: **+50 vs 3,226** — reality at the
   import/export boundary while the model imports 3.2 GW).

## §C — D3: the reachability map. The belly λ is PINNED by a 2.7–3.0 GW import plateau, and the gate needs the WHOLE wedge at once

`_caiso140_d3_walkdown.py` prices λ(S) for S MW of added price-taking CA
supply per hour, from the committed sidecars + the LP's own reconstructed
offers. Two measured regimes (2025 defect hours):

* **corridor-priced (~45 %)** — the DSW group is cap-bound (dual mean −$18.4
  in bound hours); added supply walks the CA stack down and releases the
  congestion rent, floored at the node parity;
* **parity-priced (~55 %)** — CA λ equals the WECC_DSW node λ **exactly**
  (spread p50 0.00): the marginal economic import backs out at **constant λ**
  until the hour's whole tranche is displaced. Economic (non-firm) import in
  the defect hours: mean 2,705 MW, p50 3,038 — and at S = 3 GW, **51–61 % of
  hours are still on the plateau**.

λ(S) and the implied C3a-2025 move (rt_lw weights; **UPPER bounds** — belly
battery charging is interior vs its caiso-99 cap and PS holds 1.4 GW of pump
headroom, so elastic absorption shrinks every printed drop):

| S (MW) | Sep–Dec belly Δλ | C3a move (belly) | night Δλ | C3a (night) |
|---|---|---|---|---|
| 500 | −0.54 | −0.048 | −0.47 | −0.041 |
| 1,000 | −1.72 | −0.157 | −0.77 | −0.067 |
| **1,500** | −3.45 | **−0.313** | −1.01 | −0.089 |
| 2,000 | −5.64 | −0.511 | −1.29 | −0.114 |
| 3,000 | −8.11 | −0.731 | −1.93 | −0.170 |

Three consequences:

1. **The gate is reachable in principle** — the full measured wedge
   (~2.3–2.6 GW belly incl. water, +0.9 GW night) restores −0.5 to −0.7
   against the −0.31 needed, mostly through the congestion-release channel.
   E1/E2 are structurally favourable: added supply can only move λ down.
2. **Every partial lever is arithmetically insufficient.** At the
   gas-wedge-alone size (1.5 GW belly) the *upper bound* is −0.31 exactly —
   before elastic absorption. This is why caiso-119's ±60 MW and every
   single-component probe to date read as inert: the plateau eats the first
   ~2.7 GW at constant λ in half the hours.
3. **The plateau is the P1 export-sink seam wearing a price.** Reality's
   deep-surplus λ falls *below* import parity because reality's outlet is the
   WEIM export; the scored P1 pass structurally cannot export (caiso-138 §D,
   the owner-chartered seam lane). Until that lane or a full-wedge restoration
   lands, the model's surplus-hour λ has a hard floor at the measured-hub
   delivered-import parity. (Filed as evidence FOR that lane, not a re-arm.)

## §D — D4: the kill. The only admissible instrument delivers less than half the gate

**The instrument space.** A committed-gas loading floor must survive
caiso-135 §3's reality test (a floor is a claim about what CANNOT happen).
Measured on CAMPD CA CC conduct, Sep–Dec, evening-full-configuration days:
**62–74 % ride through the belly at p50 loading 0.67–0.78, but 20–29 % drop
below 0.30** — the mixture is real, so ANY class-flat or fleet-quantile floor
at the level the gate needs (~0.55–0.68) is contradicted on a fat minority of
plant-days. The heterogeneity is **between plants** (across-plant own-p50
spread 0.05–0.92), so the only admissible form is the established per-plant
own-conduct family (`st_gas_mustrun_p25` / `coal_mustrun_per_plant`): each
committed plant floored at **its own** measured p25 loading-when-on, per
window. That statistic is stable (cap-weighted own-p25, belly:
0.356/0.331/0.337; night: 0.579/0.604/0.554 across 2023/24/25).

**The kill-check** (committed keeper state × measured per-plant p25s, CAMPD
plant match 0.68):

| 2025 Sep–Dec | committed CC (model) | per-plant own-p25 floor ADDS |
|---|---|---|
| belly | 2,699 MW | **+757 MW** |
| night | 5,527 MW | **+304 MW** |
| shoulder | 6,043 MW | +347 MW |

Against §C's curve that is a C3a-2025 move of **≈ −0.13** (upper bound;
≈ −0.20 even at a perfect plant crosswalk) — **less than half the −0.31 the
gate needs**, before elastic absorption shrinks it further. The other half of
the wedge — the +793 MW water state — has **no in-repo measured hourly
instrument**: EIA-930 WAT is PS-blind (it nets real PS inside the cell),
EIA-923 is monthly (CAISO PS fleet monthly nets are ±50–80 GWh — no hourly
shape), and the LESR storage report is battery-only.

**Verdict: KILL before solve.** No fitted parameter can be added to bridge the
shortfall (rule 21/D4 — a residual closable only by a tuned value is an open
root-cause issue, not a mechanism), and arming a measured-conduct forcing
family that closes under half its target is a rule-13 adjudication (the
per-plant loading floor is a smoothed form of the forbidden CEMS pin, and its
admissibility as *market conduct* — DA-schedule/cycling-cost ride-through —
is an owner call, as every prior forcing family's was). Nothing is armed.

## §E — the asks (filed, NOT built)

* **A1 — the committed-gas ride-through conduct floor**, per-plant own-p25,
  window-resolved, reconciled INTO the RA bridge's level (rule 19: same
  mechanism, better-identified level — never a second stacked floor). Buildable
  today from committed CAMPD bytes; delivers ~40–60 % of the gate; requires
  the owner's rule-13 adjudication of the forcing family and is only worth a
  solve **jointly** with A2 or A3.
* **A2 — data intake, not a mechanism: an hourly PS / conventional-hydro
  split** (CAISO OASIS PS aggregate, CDEC/DWR pumping records) to ground the
  +793 MW water wedge — both the model's unrestrained PS belly pumping and
  the conventional-hydro belly allocation are unadjudicable on the PS-blind
  930 WAT cell.
* **A3 — the P1 export-sink seam** (caiso-138 §D, already owner-chartered,
  cross-ISO): this finding adds its C3a-2025 price: the 2.7–3.0 GW
  import-parity plateau with 51–61 % of defect hours never leaving it, and
  reality at +50 MW measured import (2023 defect hours) against the model's
  3.2 GW.

## §F — what this changes on the record

* **Keeper unchanged**, NOT-YET, fail {C3a-2025, C3c}. No solve, no bundle, no
  dashboard registration due (rule 15 applies to completed runs — the
  caiso-134/135 disposition).
* **Rule 28:** `cc_mustrun_per_plant` CAISO `.` → **R** and
  `netload_drag_floors` CAISO `U` → **R** — both rejected ex ante as the
  C3a-2025 lever on §C/§D arithmetic (any committed-gas floor instrument at
  its measured conduct level delivers < half the gate). Evidence cells cite
  this finding; the CAISO column header is re-stamped.
* **The caiso-131 §7 "57 % congestion" attribution is refined**, not
  contradicted: the congestion component is the ~45 % corridor-priced regime;
  the other ~55 % of defect hours are parity-priced, where congestion relief
  does nothing and only plateau exhaustion moves λ.
* **Rule 22:** 2023–2025 only; no out-of-training year touched.

## §G — DO-NOT-REDO (new, binding)

* **Re-measuring the month×hod residual map, the exact ledger, its closure,
  the water-wedge PS decomposition, the walk-down λ(S) curves, the per-plant
  conduct p25s or the kill-check arithmetic.** The two committed probes carry
  all of them from committed bytes in minutes.
* **Scoping a C3a-2025 candidate to the midday belly alone.** §A: the belly
  band is 26 % of the gap; night + shoulder carry more. Mis-scoped by
  arithmetic.
* **Quoting the caiso-130 "belly hydro gap −92/−58/−83 MW" as the water
  state.** §B: that basis nets real PS out of one side only; the like-for-like
  wedge is +769/+803/+793 MW. Any future hydro/PS claim must state its PS
  treatment on BOTH sides.
* **Using EIA-930 `NG: WAT` as a conventional-hydro anchor without the PS
  caveat**, or claiming the model's PS belly pumping is right/wrong from
  in-repo bytes — §D: no in-repo source separates them hourly (A2 is the
  intake ask).
* **Proposing any class-flat or fleet-quantile committed-CC loading floor**
  (0.45–0.68 band). §D: the measured mixture contradicts it on 20–44 % of
  plant-days — the caiso-135 §3 reality test, re-confirmed at window grain.
* **Re-filing the per-plant own-p25 ride-through floor as a STANDALONE
  C3a-2025 closer.** §D: +757/+304 MW ≈ −0.13 upper bound against −0.31. It
  may return only under an owner grant and only jointly with A2/A3.
* **Re-testing single-component supply additions ≤1.5 GW against C3a-2025**
  (hydro re-allocation, storage shape, CHP, import depth …). §C: the plateau
  absorbs the first ~2.7 GW at constant λ in half the hours — the kill is
  instrument-agnostic arithmetic, not a verdict on any one lever's realism.

Carried forward unchanged: everything in `FINDING-caiso139` §G,
`FINDING-caiso138` §G, `FINDING-caiso137b` §6, caiso-137 §7 first bullet,
`FINDING-caiso136` §5, caiso-135 §10, caiso-134 §9, caiso-133 §9, caiso-132
§10, caiso-131 §10, caiso-130 §7, caiso-129 §6, caiso-127 §7.

Next number: caiso-141.
