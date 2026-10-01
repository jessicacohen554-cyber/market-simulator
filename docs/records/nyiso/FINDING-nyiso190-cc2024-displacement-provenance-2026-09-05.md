# FINDING — nyiso-190 (`backcast-calibration` lane): the nyiso-189 keeper's one unmeasured justifying clause is **REFUTED** — the +1.28 TWh it added to the 2024 `CC_REGULAR` cell was NOT taken from steam the model was short of, it was taken from plants the model was ALREADY over-running by 78 % of the displaced volume, and the cell's real neighbour is a ±8–9 TWh plant-grain misallocation inside a pinned gas family

**Session:** nyiso-190, `backcast-calibration` lane
(`claude/nyiso-190-backcast-calibration-n7t2e1`), 2026-09-05.
**SOLVES RUN: ZERO.** Every number below is read from committed artifacts.
**Keeper at entry AND at exit: `2026-09-05-nyiso-189-steam-identity`** —
CALIBRATED, grade 7, fails 0, C3c ledgered. **Nothing is promoted, demoted,
re-scored or re-registered; the dashboard is untouched** (no run was produced,
so rule 15 has nothing to register). **No marker requested** — D56 has NOT
landed (NYISO is still in `calibration-complete.json`'s `withdrawn` block at
`c9f1d26e`), so no rule-22 D-5(b) re-key applies.
**Pre-registration:** `results/calibration/PREREG-nyiso190-cc2024-displacement-provenance.md`,
pushed to `origin` BEFORE the first number of the object was read; every bar
and every branch of §4 is executed verbatim below.
**Machine records:** `results/calibration/_nyiso190_displacement_provenance.json`
(the bars), `_nyiso190_plant_grain_posthoc.json` (labelled post-hoc), probes
`scripts/probes/nyiso190_displacement_provenance.py` /
`nyiso190_plant_grain_posthoc.py`.

---

## 1. The result in one paragraph

The nyiso-189 promotion took C1-2024 `CC_REGULAR` from +2.05 to +3.33 TWh
(+1.8 → +2.8 pp against a 3.0 pp band) and justified the regression in one
clause that was never measured: *"the NYC steam it displaces is what the market
committed anyway."* **That clause is false as stated, and this session measures
why on the keeper's own registered dispatch.** The market DID have the
displaced units on — **83.9 % of the removed MWh fall in measured-online
hours (B1 SUPPORTED)** — but the model was running them **harder than the
market did**: **78.1 % of the displaced TWh moved those plants TOWARD their
measured annual output (B2 REFUTED, `w_away` 0.219**, and 0.216 on the
scorer's own EIA-923 basis — the two bases agree). The displacement was a
*correction on the displaced side*, not the deepening of a market-committed
deficit. The gas family stays pinned (**B3 HOLDS**: the arm moves the six-class
family total by 0.042 TWh and sits +1.87 TWh from the family actual against a
±3.82 TWh band), so the increment is a genuine within-family reallocation —
but the set it came from is **not** what the clause names: only **0.42** of the
2024 displaced TWh is downstate steam/cogen, below the pre-committed 0.50
naming bar, so **per PREREG §3 B4 this session may not call it "NYC steam /
cogen displacement"** — it is 0.76 TWh `CC_CHP`, 0.46 `CC_REGULAR`, 0.30
`ST_GAS`, split NYC 0.74 / Capital-Hudson 0.71 / Upstate-West 0.21. Under
PREREG §4's pre-committed branch for `B2 < 0.50`, **no cell-G question goes to
the owner**: the premise of the "re-open G vs accept" card is refuted, and what
the measurement surfaced instead is a **larger and un-owned object** — on the
keeper, 72 benched plants carry **+11.25 TWh of over-run against −8.18 TWh of
under-run for a net of +3.07 TWh**, i.e. roughly **±8 TWh of offsetting
plant-grain misallocation** inside a family the class totals say is pinned, and
it repeats at ±7.4 TWh (2023) and ±9.3 TWh (2025). The single largest cell of
it sits in a class an already-`K` mechanism was scoped out of (§4).

---

## 2. The bars, executed verbatim (PREREG §3)

**V1 — the instrument is the runs it claims to be. PASSED.** The registered
`2026-09-04-nyiso-188-combined` payload reproduces the FINDING-nyiso189 §3.1
control column (`CC_REGULAR` 36.1081 vs 36.11; `CC_CHP` 19.5552 vs 19.56) and
`2026-09-05-nyiso-189-steam-identity` reproduces the arm column (37.3915 vs
37.39; 18.8405 vs 18.84), all within the 0.01 TWh tolerance. The nyiso-189
sitting established the nyiso-188 payload IS the control (its same-HEAD replay
was bit-identical, 0 of 52,560 prices differing in every year), so no replay
was needed and none was run.

| bar | 2023 | **2024 (gated)** | 2025 | verdict |
|---|---|---|---|---|
| **B1** `s_online` at the 2 % bar (1 % / 5 %) | 0.750 (0.827 / 0.738) | **0.839** (0.852 / 0.831) | 0.834 (0.834 / 0.826) | **SUPPORTED** every year (bar ≥ 0.50) |
| **B2** `w_away`, CAMPD basis (EIA-923) | 0.139 (0.159) | **0.219** (0.216) | 0.375 (0.199) | **REFUTED** every year (bar ≥ 0.50); bases agree |
| **B3** family arm − actual / arm − control | +1.14 / +0.037 | **+1.87 / +0.042** | −0.68 / +0.043 | **HOLDS** every year (band ±3.82 / tol 0.25) |
| **B4** downstate-steam-cogen share of displaced | 0.597 | **0.420** | 0.418 | naming rule **FAILS** 2024 & 2025 |
| displaced / gained TWh (keys) | 2.454 (50) / 2.502 (2) | **1.749 (47) / 1.800 (2)** | 1.631 (54) / 1.685 (2) | — |

The gainers are only ever the two repriced plants — Bethlehem 2539
(+2.445 / +1.750 / +1.668) and World Generation X 54131 (+0.057 / +0.050 /
+0.017) — so the whole question is who paid, and B1/B2 answer it.

### 2.1 B1 and B2 together — what actually happened

B1 and B2 are not in tension; together they say something sharper than either.
The removed MWh land in hours the market had those units **on** (0.84), so the
model is not committing them in the wrong hours. What it gets wrong is the
**level within the online envelope**: the plants that paid were being run above
their measured output, and taking energy off them moved 78 % of the displaced
volume closer to what they actually generated. The 2024 displaced set, ordered
by volume (model control → arm vs actual, TWh):

| plant | class / zone | control | arm | CAMPD | EIA-923 | moves |
|---|---|---|---|---|---|---|
| Empire Generating 56259 | `CC_CHP` / Capital-Hudson | 4.161 | 3.882 | 2.981 | 2.892 | **toward** |
| Brooklyn Navy Yard 54914 | `CC_CHP` / NYC | 2.881 | 2.658 | 1.801 | 2.170 | **toward** |
| Cricket Valley 57185 | `CC_REGULAR` / Capital-Hudson | 5.114 | 4.946 | 4.241 | 4.161 | **toward** |
| Athens 55405 | `CC_REGULAR` / Capital-Hudson | 3.657 | 3.541 | 4.046 | 3.970 | away |
| East River 2493 `ST_CHP` | NYC | 1.266 | 1.160 | 0.557 | 0.745 | **toward** |
| Ravenswood 2500 `ST_GAS` | NYC | 2.522 | 2.419 | 0.681 | 0.635 | **toward** |
| Arthur Kill 2490 | `ST_GAS` / NYC | 2.230 | 2.128 | 1.353 | 1.272 | **toward** |
| East River 2493 `CT_CHP` | NYC | 1.664 | 1.565 | 1.693 | 2.149 | away |
| Sithe Independence 54547 | `CC_CHP` / Upstate-West | 9.571 | 9.478 | 6.286 | 6.158 | **toward** |

Every one of the five plants the session prompt named as the movers to check —
Ravenswood 2500, Arthur Kill 2490, East River 2493, Empire 56259, Cricket
Valley 57185 — is a plant the model was **over**-running, on both actual bases.
The two `away` rows in the top eight (Athens, East River `CT_CHP`) are plants
the model already under-ran and made slightly worse; they carry 0.219 of the
displaced volume between them and the rest of the `away` set.

### 2.2 What B3 pins, and what it does not

The six-class gas family totals 67.81 TWh model against 65.95 TWh actual in
2024 (+1.87, inside the ±3.82 band), and the arm moves that total by 0.042 TWh
— a real reallocation, exactly as nyiso-186 found on its own keeper. The
internal split, however, is not one object:

| class (2024) | control | arm | actual | arm − actual |
|---|---|---|---|---|
| `CC_REGULAR` | 36.108 | 37.392 | 34.060 | **+3.331** |
| `CC_CHP` | 19.555 | 18.840 | 17.017 | **+1.823** |
| `ST_CHP` | 1.104 | 0.996 | 0.872 | +0.124 |
| `ST_GAS` | 9.591 | 9.293 | 9.913 | −0.620 |
| `CT_CHP` | 1.085 | 0.976 | 2.172 | **−1.196** |
| `CT_PEAKER` | 0.327 | 0.317 | 1.911 | **−1.594** |

The CT deficit (−2.79 TWh across `CT_PEAKER` + `CT_CHP`) is the nyiso-187
out-of-market-commitment object and is untouched by this session. What B2 adds
is that the **+5.28 TWh of combined-cycle over-run is not simply that deficit's
mirror**: it also stands against a `ST_GAS` class that is itself *under* by
0.62 TWh while containing the model's two largest NYC steam over-runs
(Ravenswood +1.74, Arthur Kill +0.78) and its largest steam under-runs
(Northport −1.78, Bowline Point −0.92). Class totals hide that.

---

## 3. POST-HOC, LABELLED — NOT A BAR: the plant-grain misallocation

*(The nyiso-187 precedent for a labelled post-hoc sensitivity is the model.
Nothing here is adopted, rejected or gated on; it characterises B2's result at
full magnitude. Record: `_nyiso190_plant_grain_posthoc.json`.)*

On the keeper, against each plant's own measured annual:

| year | plants | gross over | gross under | net | offsetting misallocation |
|---|---|---|---|---|---|
| 2023 | 73 | +11.86 | −7.38 | +4.48 | **7.4 TWh** |
| 2024 | 72 | +11.25 | −8.18 | +3.07 | **8.2 TWh** |
| 2025 | 71 | +11.22 | −9.29 | +1.93 | **9.3 TWh** |

The over-run set is stable and concentrated. Model annual capacity factor
against measured, and the model's peak against the plant's own demonstrated
CAMPD peak:

| plant | class | model − CAMPD 23 / 24 / 25 | model CF vs CAMPD CF (23/24/25) | model peak vs CAMPD peak MW (2024) | hours ≥ 95 % of nameplate, model vs CAMPD (23/24/25) |
|---|---|---|---|---|---|
| Sithe Independence 54547 | `CC_CHP` | +1.59 / **+3.19** / **+3.48** | 0.56/0.93/0.97 vs 0.40/0.62/0.62 | 1,366 vs 1,193 | 1,639/5,591/6,727 vs 198/922/1,961 |
| Brooklyn Navy Yard 54914 | `CC_CHP` | +1.35 / +0.86 / +1.19 | 1.07/0.94/1.00 vs 0.60/0.64/0.58 | 390 vs 242 | 8,172/6,226/6,714 vs **0/0/0** |
| Empire Generating 56259 | `CC_CHP` | +0.27 / +0.90 / +0.77 | 0.59/0.68/0.68 vs 0.55/0.52/0.54 | 680 vs 648 | 1,989/2,041/3,924 vs 39/65/80 |
| Ravenswood 2500 `ST_GAS` | `ST_GAS` | **+3.13** / +1.74 / +0.84 | 0.25/0.15/0.12 vs 0.05/0.04/0.07 | 1,389 vs 1,243 | 0/0/0 vs 0/0/0 |
| Arthur Kill 2490 | `ST_GAS` | +1.29 / +0.78 / **−0.24** | 0.31/0.28/0.25 vs 0.15/0.18/0.28 | 799 vs 887 | 0/0/0 vs 30 (2024, measured) |

**Not every row is monotone, and the exceptions are stated:** Arthur Kill
*flips* to a 0.24 TWh under-run in 2025 (model CF 0.25 against a measured 0.28),
and Ravenswood's over-run decays 3.13 → 1.74 → 0.84 as its measured output
rises. Only the three `CC_CHP` rows are over in all three years, and Sithe's
grows monotonically. That non-uniformity is itself part of the finding: this is
a **placement** defect that moves with the year, not a fixed offset.

**Honest reading of the instrument.** Brooklyn Navy Yard is a `ct_only` CEMS
reporter (`ct_ratio` 1.172), so its CAMPD series understates its electric
output by ~17 %; correcting for that puts its true peak near 280 MW, still far
under the model's 390 MW, and its zero hours at ≥95 % of nameplate are
unaffected by a uniform ratio. Sithe and Empire are **not** `ct_only` and their
EIA-923 annuals corroborate CAMPD to within 0.13 TWh, so those rows need no
correction. A model peak above bench nameplate is not by itself a defect —
duct firing legitimately exceeds nameplate — which is why the load-bearing
column is the **duty** one: the model holds BNY at ≥95 % of nameplate for
6,200–8,200 hours a year in a record that never once reaches that level.

---

## 4. WHERE THIS LANDS: an already-`K` mechanism, scoped out of the class carrying the largest cell

`cc_capacity_reconcile` (NYISO cell **K**, nyiso-188) bounds per-plant LP
capacity at the plant's own CAMPD demonstrated peak (p99.9) — the exact defect
§3 measures. **Its derive is scoped to `CC_REGULAR` by construction**
(`scripts/data/derive_cc_capacity_reconcile.py`: `g.plant_group ==
"CC_REGULAR"` at the model side, `csv["Plant_Group"] == "CC_REGULAR"` at the
CAMPD side), and its committed 15-row table
(`data/raw/_processed-legacy/cc_capacity_reconcile_NYISO.csv`) contains **no
`CC_CHP` plant** — Sithe 54547, Empire 56259 and Brooklyn Navy Yard 54914 are
all absent. `CC_CHP` is +1.82 TWh over in 2024 and +3.09 in 2025, and Sithe
alone accounts for +3.19 / +3.48 of it.

**This session neither builds nor proposes that extension** — PREREG stops S1
(zero solve) and S3 (no CC lever) bind, and the tension is stated rather than
reinterpreted: S3's "no CC lever" was written against a *volume lever fitted to
this cell*, and a demonstrated-peak bound derived from each plant's own CAMPD
record is a different class of thing (rule 14 `[R-ACCURATE]`, zero parameters,
the identical frozen rule an existing `K` cell already runs) — but the call on
whether that distinction holds is not this session's to make after the fact.
It is handed to the queue as an **untested candidate with its direction
unknown**: capping `CC_CHP` releases energy that may land on `CC_REGULAR` (the
cell gets **worse**) or on the `CT_PEAKER` / `CT_CHP` / `ST_GAS` deficits (the
cell and those cells both improve). **Rule 1 governs either way**: the reason
to test it is that the model demonstrably runs three plants above their
demonstrated capability for thousands of hours a year, not what it does to the
residual.

---

## 5. What this changes, and what it does not

### 5.1 Changed

* **The nyiso-189 keeper's justifying clause is withdrawn as a statement of
  fact.** "The NYC steam it displaces is what the market committed anyway" is
  false in both halves: the displaced set is not majority downstate steam/cogen
  (B4 0.42 in 2024), and the displacement did not deepen a market-committed
  deficit — it relieved a model over-run in 78 % of its volume (B2). **The
  keeper itself is untouched**: no gate moves, no determination changes, and
  the promotion's own license (rules 14 + 13 + 1 on a measured-input repair)
  never rested on this clause. What is withdrawn is a *reason offered in
  prose*, not a result.
* **The C1-2024 `CC_REGULAR` cell is no longer attributed solely to the
  nyiso-187 disposition.** The CT deficit half stands and is untouched. The
  combined-cycle half now has a measured, un-owned neighbour (§3–§4).

### 5.2 NOT changed, and NOT claimed

* **Cell `scuc_load_pocket_commitment` stays `G`.** No re-open is attempted or
  recommended; the nyiso-97 §5 re-open bar and the nyiso-160 access closure
  both stand unchanged. PREREG stop **S2** is the reason this measurement can
  never be used to identify it: this is observed unit conduct, which nyiso-97
  forbids by name as an identification route.
* **No C3a-2025 lever.** `DECISION-CARD-nyiso148` Q1 is confirmed still pending
  and the −8.3 % remainder stays owner-court (stop S5).
* **No claim about the CT deficit's ownership.** nyiso-187 §2 stands verbatim.
* **No solve, no registration, no keeper change, no marker** (stops S1, S6).

## 6. Handed forward

1. **The `CC_CHP` demonstrated-peak scope gap (§4)** — the largest single
   un-owned cell measured here, direction on C1-2024 unknown, needs one A/B.
2. **The `ST_GAS` internal misallocation** — Ravenswood +1.74 / Arthur Kill
   +0.78 over against Northport −1.78 / Bowline Point −0.92 under, on a class
   that is only −0.62 net. A class-total reading cannot see it. (Ravenswood's
   *availability* was adjudicated at nyiso-183; this is its energy placement
   against Long Island and Capital-Hudson steam, which is a different object.)
3. **Bethlehem 2539 has no headroom left, in any year.** The arm puts it
   **above** its measured CAMPD output in all three — 4.880 vs 4.180 (+0.70),
   5.896 vs 5.539 (+0.36), 5.664 vs 5.267 (+0.40) — where the 2024 control was
   1.39 TWh *under*. The nyiso-189 repair did not merely close that gap, it
   crossed it. Any further in-merit repair at that plant now moves away from
   its actual, and the +0.70 in 2023 is worth a look on its own. (Its EIA-923
   rows — 4.358 / 3.639 / 3.432 — sit on the same understated filing basis as
   the heat-rate defect nyiso-189 repaired and are not the instrument for this
   plant; CAMPD is.)
4. **Forecast lane, unchanged from the nyiso-189 handoff:**
   `egrid_steam_collapse_heat_rates` regenerates per eGRID vintage;
   `APPLIED_VINTAGE = 2023` tracks the fleet join's own vintage
   (`egrid2023_data_rev2.xlsx`). **eGRID 2025 has NOT landed** — `data/raw/fleet-egrid`
   holds vintages through `egrid2024_data.xlsx` only. When it does, re-derive
   (`scripts/data/derive_egrid_steam_collapse_heat_rates.py --iso NYISO`) and
   re-check the applied vintage's admissions (rule 23: a source-data change).
   The record-only caution stands: Bethpage 50292 (2022) and Cornell 50368
   (2024) fire the fence with non-physical identities, so a future applied
   vintage admitting such a row needs the class-band check nyiso-189 §5.2
   item 4 names.

## 7. Governance

Rule 1 `[R-STRUCT]`: the bars and every outcome branch were fixed and pushed
before the first number; the branch the evidence selected (`B2 < 0.50` → no G
question) is the one pre-committed, and it is followed even though the session
was opened expecting the other one. Rule 13 `[R-MEASURED]`: nothing measured is
fed back as an input; this session produces documents, not config. Rule 15: no
run was produced, so nothing is registered and the dashboard is untouched.
Rule 19 `[R-ONE-MECH]`: no mechanism added or stacked. Rule 22 `[R-HOLDOUT]`:
2023–2025 only, no marker requested, freeze respected, D56 confirmed not
landed. Rule 24 `[R-REGISTRY]`: no tunable added or changed. Rules 25 / 28: no
mechanism was tested so no cell changes status; the NYISO shard's
`scuc_load_pocket_commitment` evidence line and the §5.5 queue are updated in
this session, and no other ISO's shard is touched. Rule 27 `[R-PUSH]`: on-disk
bytes pushed, every ≥300-line blob verified after each push.

*(nyiso-190, 2026-09-05. Zero solves. Keeper unchanged.)*
