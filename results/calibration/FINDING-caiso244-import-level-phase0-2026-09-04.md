# FINDING — caiso-244: the CAISO over-import is a NORTH-CORRIDOR phenomenon carried by the firm block's MIC-share split, not by the spot ladder; the scored pass has NO export outlet; imports set the CAISO price in one hour of five; and the lane's recipe instrument is repaired — caiso-242's voided ratios re-measure at a third of their size. ZERO SOLVES.

**Session caiso-244, 2026-09-04. Branch `claude/caiso-244-backcast-calibration-jag23e`.**
Pre-registered in `PRECOMMIT-caiso244-import-level-phase0-2026-09-04.md`
(pushed `873b1afe`, BEFORE the object's probe was written). **No LP built, no
solver called, nothing armed, no `ScenarioConfig` field, no run registered, no
verdict moved.** Keeper **`2026-09-04-caiso-243-b1-f923` UNCHANGED**,
determination **NOT-YET**, C3a the sole load-bearing FAIL (+3.9 / +12.3 /
+14.4 %). CAISO holds no `complete`/`final` marker; the holdout spend freeze is
ACTIVE; every read and rebuild stayed inside 2023–2025 (one incidental raw
print of 2019–2022 / H1-2026 annual DIBA sums is disclosed in the PRECOMMIT
§0.2 and used nowhere).

---

## §1 — HEADLINE

1. **The two owed instrument repairs are done, structurally.**
   `scripts/replay_keeper.run_year_kwargs` is the ONE sanctioned fleet-only
   recipe reconstruction; `scripts/lib/bundle_fleet.full_run_year_kwargs`
   delegates to it; a regression test confines the retired by-name pattern to
   a frozen allowlist of nine pre-caiso-244 probes. Measured on all six
   designated keepers: the by-name filter drops `prb_overrides` on EVERY ISO
   (36 / 50 / 18 / 42 / 35 / 5 structural flags).
2. **caiso-242's four probes re-measured on-recipe: the gas-basis identity
   ratio is 1.078 / 1.223 / 1.192**, not 1.298 / 1.310 / 1.327 — a third of
   the voided size, and the residual (+0.41 / +0.55 / +0.59 $/MMBtu) is the
   size of the $0.46 `CAISO_CITYGATE_TRANSPORT_ADDER`. CT_PEAKER's econ offer
   sits **0.91× / 1.12× / 1.08×** the measured bid (was 1.10 / 1.28 / 1.26);
   its cheapest-offer-above-price median gap is **$3.74 / $1.38 / $3.66** (was
   $15.57 / $12.63 / $12.96). The fuel-invariant-margin FLATNESS survives and
   is LARGER on-recipe (measured range 0.013 vs armed-implied **0.345**).
3. **THE IMPORT LEVEL OBJECT IS LOCATED.** With the import-side reconstruction
   exact (G-RECON: 0.000 % annual, 1e-4 MW on 3,000+ determined hours), the
   model's **+8.43 / +8.69 / +5.31 TWh** net over-import decomposes as **PNW
   +11.30 / +10.65 / +8.76** and **DSW −2.87 / −1.96 / −3.45 TWh**: the whole
   excess is the NORTH corridor, and the south is UNDER-imported. The
   `PNW_hydro_base` FLOOR alone (7.70 / 9.74 / 9.99 TWh) exceeds the entire
   measured PNW net import (−0.55 / 2.06 / 4.73) by **+8.25 / +7.68 / +5.26**
   and even the measured GROSS PNW import (4.65 / 5.76 / 7.05) by **+3.05 /
   +3.97 / +2.94 TWh**. The model puts **29–33 %** of its net import on COI;
   the measured record puts **−2 / 7 / 13 %** there.
4. **The four fitted spot capacities are NOT where the level sits**: 23.5 /
   3.5 / 2.9 % of model import energy (P-5 holds), with `WECC_scarcity` live
   only in 2023 (2.68 TWh, marginal in 1,647 h — P-5's second leg FALSIFIED
   there).
5. **The scored P1 pass has NO export outlet.** The export legs are lifted to a
   zero lower bound by the RA-bridge floor composition (`caiso_p1_export_sink_seam`
   OFF, cell `R`, caiso-142; caiso-138 §D), so the `import` klass is GROSS and
   the model's net = gross. The committed energy balance bounds P1 exports +
   losses at **0.58 / 2.21 / 2.31 TWh**; at the P1 duals the legs WOULD carry
   **58.6 / 72.4 / 63.9 TWh** if open. Measured gross exports: 5.6 / 4.1 / 2.7.
6. **Imports set the CAISO landing-zone price in 19.9 / 17.7 / 23.0 % of
   hours** (an import row marginal at its WECC node with the corridor link
   unbound) — P-6 FALSIFIED against the < 5 % caiso-202 §C reading.
7. **December is not an import-volume excess**: model net import 4,243 /
   6,427 / 7,042 MW vs measured 3,826 / 6,232 / 7,302 MW in Dec 2023/24/25.
   caiso-232's defect-2 attribution "landing on the IMPORT_TRANCHES residual"
   is not supported on volume.

**Five predictions hold, four fall** (§6). The instrument's own gate held
exactly; the object's largest surprises are P-6 and the P1 export closure.

---

## §2 — THE INSTRUMENT REPAIRS (handoff items 1–2)

### §2.1 — One reconstruction, measured against the two it replaces

| reconstruction | `prb_overrides` | `bit_overrides` / `coal_bit_sigmoid` | `commitment_screen_coal` | strict on unmapped key |
|---|---|---|---|---|
| by-name filter (caiso-202 → -243 probes) | **DROPPED** on all six keepers | DROPPED | carried | no |
| `bundle_fleet.full_run_year_kwargs` (pjm-124) | carried | carried (`None` for `{}`) | carried | no |
| **`replay_keeper.run_year_kwargs` (caiso-244)** | carried | carried | carried (via `screen_coal`) | **yes** (`build_kwargs`) |

`run_year_unreachable` discloses the recorded non-default solve kwargs a
fleet-only rebuild cannot carry: **CAISO none**; ERCOT its four post-LP ORDC /
RTORDPA overlays; PJM `btm_backfill_year=2024`. Nothing on the fleet / offer /
fuel path is unreachable for any ISO.

### §2.2 — caiso-242 §3 re-measured on-recipe (`_caiso244_*_onrecipe.json`)

| quantity | caiso-242 (VOID, lookalike) | **caiso-244 on-recipe** |
|---|---|---|
| model gas ÷ derive citygate, carbon-incl. | 1.298 / 1.310 / 1.327 | **1.078 / 1.223 / 1.192** |
| difference $/MMBtu | +2.13 / +1.38 / +1.52 | **+0.41 / +0.55 / +0.59** |
| CC_REGULAR econ offer ÷ measured bid | 1.22 / 1.28 / 1.49 | **1.021 / 1.130 / 1.140** |
| CT_PEAKER econ offer ÷ measured bid | 1.10 / 1.28 / 1.26 | **0.912 / 1.116 / 1.081** |
| CT_PEAKER reconciled ÷ armed (`rho`, econ_low) | 0.769 / 0.776 / 0.760 | **0.981** (pooled A/B; L1 0.913 / 0.806 / 0.833) |
| CC_REGULAR `rho` | 0.729 / 0.700 / 0.553 | **0.895** |
| CT cheapest offer > system price, hours | 80.7 / 89.5 / 90.7 % | **69.6 / 60.9 / 77.6 %** |
| CT median gap, cheapest − price | +15.57 / +12.63 / +12.96 | **+3.74 / +1.38 / +3.66 $/MWh** |
| CT_PEAKER availability route | 0 h below 1 % headroom | **0 h** (unchanged — CLOSED stays closed) |
| CT econ_low measured mult range vs armed-implied | 0.013 vs 0.2775 (21×) | **0.013 vs 0.3449 (26.5×)** |

**What changes:** the "domestic gas priced ~30 % above the market's own bids"
reading is mostly the instrument's artifact — on-recipe the CC econ rungs sit
2–14 % above the bid and the CT rungs within ±12 %, with 2023 CT_PEAKER *below*
its bid. The residual gas-basis gap is ≈ the transport adder, whose
admissibility on a spot-indexed marginal offer is a new question for the lane
(not taken here). **What does not change:** caiso-242 §5's D1/D2/D3 defect
(confirmed on-recipe at caiso-243), the CT_PEAKER volume miss (dispatch 1.63 /
0.74 / 0.35 TWh against a ~6.2 GW available envelope), and the FLATNESS object,
which is sharper on-recipe. ST_GAS's 1.6–2.0× stays excluded (caiso-230's
base-HR misalignment).

---

## §3 — THE IMPORT LEVEL, MEASURED (`_caiso244_import_level_anatomy.json`)

### §3.1 — The instrument passed its own gate

Row-level import dispatch reconstructed from LP complementarity on the keeper's
committed P1 zonal duals (PRECOMMIT §2). **G-RECON PASS on the GROSS basis in
all three years**: annual energy **0.000 %** off the committed `import` klass,
hourly RMSE **0.0 MW**, and — the non-tautological leg — **1e-4 MW RMSE on the
3,000+ hours with no marginal import row**. The NET basis fails by 92–110 %,
which is how the instrument itself discovered §3.2.

### §3.2 — The scored pass has no export outlet

`pipeline/commitment._bridge_floored_fleet` maximum-composes the RA-bridge
floor onto `min_gen`; for the `pmin < 0` export legs that lifts the lower bound
to 0 unless `caiso_p1_export_sink_seam` preserves them — and that flag is OFF
on the keeper (cell `R`, caiso-142; caiso-138 §D measured "zero exports in all
26,280 corridor-hours"). Verified here from committed bytes: the ISO energy
balance `Σ class_hourly + discharge − charge + slack − dump − demand` leaves
**0.58 / 2.21 / 2.31 TWh** (66 / 252 / 264 MW mean, ≤ 509 MW in any hour) —
losses plus at most that much export — against the **58.6 / 72.4 / 63.9 TWh**
the legs would carry at the P1 duals (Malin above the WECC_PNW dual in
4,006 / 4,477 / 3,965 h; Palo Verde above WECC_DSW in 2,348 / 2,362 / 2,100 h).
Consequence for every import number this lane has quoted: **model "import" is
gross and net at once**, while the measured comparator is NET of 5.6 / 4.1 /
2.7 TWh of real CAISO exports. The adjudicated cell is not re-opened; the
measured consequence is recorded.

### §3.3 — Corridor decomposition, model (P1) vs measured (EIA-930 on the model clock)

| year | corridor | model net | measured net | measured gross import | **excess** | firm floor | floor − meas. net | floor − meas. gross |
|---|---|--:|--:|--:|--:|--:|--:|--:|
| 2023 | WECC_PNW | 10.75 | **−0.55** | 4.65 | **+11.30** | 7.70 | +8.25 | +3.05 |
| 2023 | WECC_DSW | 26.52 | 29.39 | 29.77 | **−2.87** | 10.24 | −19.15 | −19.53 |
| 2024 | WECC_PNW | 12.71 | 2.06 | 5.76 | **+10.65** | 9.74 | +7.68 | +3.97 |
| 2024 | WECC_DSW | 27.31 | 29.27 | 29.70 | **−1.96** | 12.95 | −16.32 | −16.76 |
| 2025 | WECC_PNW | 13.49 | 4.73 | 7.05 | **+8.76** | 9.99 | +5.26 | +2.94 |
| 2025 | WECC_DSW | 27.75 | 31.20 | 31.54 | **−3.45** | 12.50 | −18.70 | −19.04 |

(TWh. Totals: model 37.27 / 40.02 / 41.24; measured 28.84 / 31.33 / 35.93;
excess **+8.43 / +8.69 / +5.31**. PNW share of net import: model 28.8 / 31.8 /
32.7 %, measured **−1.9 / 6.6 / 13.2 %**.)

### §3.4 — Row attribution, 2023 / 2024 / 2025 (TWh)

| row | limb | energy | of which floor | economic above floor | dispatched share of capability-hours |
|---|---|--:|--:|--:|--:|
| `PNW_hydro_base` | firm | 8.07 / 11.62 / 12.42 | 7.70 / 9.74 / 9.99 | 0.37 / 1.88 / 2.43 | 1.00 |
| `PNW_midC` | spot | 2.68 / 1.09 / 1.07 | — | all | 0.35 / 0.19 / 0.20 |
| `DSW_solar_PV` | firm | 10.58 / 13.47 / 13.39 | 10.24 / 12.95 / 12.50 | 0.34 / 0.52 / 0.89 | 1.00 |
| `DSW_CCGT` | spot | 3.40 / 0.31 / 0.12 | — | all | 0.24 / 0.04 / 0.02 |
| `DSW_CT` | spot | 0.00 / 0.00 / 0.00 | — | — | 0.006 / 0 / 0 |
| `WECC_scarcity` | spot | **2.68** / 0.02 / 0.01 | — | all | **0.194** / 0.003 / 0.002 |
| `DSW_surplus_clean` | clean | 4.55 / 4.49 / 6.72 | — | all | 0.75 / 0.91 / 0.93 |
| `DSW_overnight_clean` | clean | 3.07 / 5.04 / 4.84 | — | all | 0.78 / 0.82 / 0.81 |
| `DSW_daytime_clean` | clean | 2.24 / 3.98 / 2.67 | — | all | 0.60 / 0.75 / 0.69 |
| **firm** | | **18.65 / 25.09 / 25.81 (50 / 63 / 63 %)** | 17.94 / 22.68 / 22.49 | 0.71 / 2.41 / 3.32 | |
| **spot (the 8,800 MW)** | | **8.76 / 1.42 / 1.20 (23.5 / 3.5 / 2.9 %)** | 0 | all | |
| **clean depth** | | 9.86 / 13.51 / 14.23 (26.5 / 33.8 / 34.5 %) | 0 | all | |

The firm floor energies reproduce the keeper's committed D-2 `firm_import`
rows (17.9378 / 22.6842 / 22.494) to the fourth decimal — an independent
cross-check of the reconstruction against a second committed artifact.

### §3.5 — What the level sits on

**The north corridor's firm block.** `PNW_hydro_base` is the DMM annual
RA-import capacity (2,323 / 3,371 / 3,371 MW) × the published MIC north share
(46.2 / 46.2 / 46.4 %), shaped by the measured total-system revealed base and
floored (self-schedule) at min(capability, the caiso-151 ceiling). Its FLOOR
alone forces 7.7–10.0 TWh/yr onto COI. The measured COI-side record
(BPAT + PACW + BANC + TIDC) carried −0.55 / 2.06 / 4.73 TWh net and 4.65 /
5.76 / 7.05 TWh gross — BPAT itself only 1.14 / 2.14 / 3.00 TWh net, against
6.9–15.2 TWh in 2019–2022 (the caiso-235 regime break, read here from the
raw table and used only to name the mechanism). **The MIC north share is a
transmission-CAPABILITY allocation key; it is being used as an ENERGY-source
key, and in 2023–2025 the two disagree by ~40 points.** The south corridor,
where the DMM level would have landed under a measured energy split, is
UNDER-imported by 2–3.4 TWh — the same sign caiso-242 §2.4 / caiso-243 P-5
attributed to over-priced domestic gas, so the two readings are not exclusive
and this session does not adjudicate between them.

**Not the spot ladder.** The 8,800 MW carries 3 % of import energy in 2024–25
and 23.5 % in 2023 (gas at $5–7 made hub + adders competitive; `WECC_scarcity`
alone 2.68 TWh, marginal in 1,647 h). Its role is exactly caiso-188 §3's:
filling the band under the measured envelope in the one high-gas year. The
closed depth lane stays closed; nothing here re-opens it.

**The two firm prices are live — as a bound-setter, not a margin.** P-4 as
written (strictly-between hours) is FALSIFIED (≤ 2.5 % of hours), but the
caiso-151 clip leaves the block above its floor in 2,006 / 4,068 / 4,469 h and
in **1,968 / 3,953 / 4,379** of those the $28 offer sits below λ so the block
runs at CAPABILITY, not at the floor: **0.37 / 1.88 / 2.43 TWh** of PNW
dispatch (0.34 / 0.52 / 0.89 DSW) is decided by the fitted price. caiso-229's
"INERT BY CONSTRUCTION" does not hold on this keeper; caiso-188 §2 reading 1
does. I registered the wrong observable and say so.

### §3.6 — Imports set the CAISO price in one hour of five

An import row is marginal at its WECC node in 5,742 / 5,187 / 5,596 h (the
node has no load; something must set its dual), and in **1,745 / 1,546 /
2,016 h (19.9 / 17.7 / 23.0 %)** the corridor link is unbound so that marginal
import offer IS the NP15 / SP15_rest price. The marginal rows are the three
clean-depth tranches at the RAW Palo Verde hub (1,345–2,408 h each) and
`PNW_midC` at Malin + wheel (1,847–3,012 h). caiso-202 §C's "< 5 % direct-
marginal" acquittal was measured on the ISO load-weighted price against import
offers; this is the node-by-node complementarity count and it is four times
larger. **Not a lever — a measured property of the seam** that any C3a
attribution has to carry: when the model's SP15 price equals the raw Palo
Verde hub, the residual in that hour is a hub-basis residual, not a domestic
offer residual.

### §3.7 — December

Model net import in December: 4,243 / 6,427 / 7,042 MW vs measured 3,826 /
6,232 / 7,302 MW. In Dec-2025 forced firm 2.65 TWh + firm-above-floor 1.05 vs
economic spot + clean 1.53 (P-7 FALSIFIED: forced > economic). The model does
not over-import in December; caiso-232's defect-2 slab (+7.4…+13.5 $/MWh in
every hour) needs another carrier — the §3.6 hub-marginal hours are the
natural next place to look, and that is an ask, not a claim.

---

## §4 — DISCLOSURES AGAINST INTEREST

1. **The probe's first run was wrong on exports and was corrected before any
   result was read off it.** It carried the fleet-only (P0) export bounds
   into P1 and reported 58–72 TWh of exports. The energy-balance check exposed
   it; the correction (§3.2) is in the committed probe, and the wrong number is
   kept as the "would-export-if-open" diagnostic because it measures how far
   the P1 duals sit below the hubs.
2. **P-4 and P-6 were registered on the wrong observable / the wrong prior.**
   P-4 measured marginality when liveness is a bound question; P-6 trusted a
   load-weighted acquittal that does not transfer to node complementarity.
   Both are scored FALSIFIED as written.
3. **FOURTH consecutive favourable direction, stated as a HAZARD.** The
   PRECOMMIT §0.5 called a firm-floor REMOVAL adverse. The attribution that
   actually landed — a north→south RE-SPLIT — is favourable on BOTH zones:
   caiso-215 measured NP15 UNDER-pricing and the south carrying ~100 % of the
   C3a gap, so less forced import in NP15 raises an under-priced zone and more
   in SP15 lowers an over-priced one. Per rule 1 `[R-STRUCT]` this is never an
   argument; any future arm must exclude C3a's verdict from its promotion
   basis, as caiso-241/242/243 did.
4. **The measured comparator has its own boundary caveats** (rule 14): EIA-930
   BA-to-BA net interchange; BANC and TIDC (California BAs) sit in the
   WECC_PNW corridor by the repo's `CAISO_CORRIDOR_DIBA` geography; the DSW
   corridor includes LDWP and IID. The corridor map is the committed producer's
   and is not re-litigated here — the PNW excess (+8.8…+11.3) is far larger
   than any plausible re-mapping.
5. **The D-2 `class_total_twh` for `firm_import` (35.56 / 40.88 / 39.98) does
   not equal the committed `import` klass (37.27 / 40.02 / 41.24)**; the
   forced energies match exactly, the class totals differ by −1.7 / +0.9 /
   −1.3 TWh. Unexplained here (the D-2 total is keyed by row class, the klass
   by the dispatch label); filed, not load-bearing.
6. **One incidental read outside the window** (PRECOMMIT §0.2): raw annual
   DIBA sums for 2019–2022 and H1-2026 were printed while inspecting the
   interchange parquet. They are quoted once in §3.5 to NAME the regime break
   caiso-235 already published, and for nothing else.

---

## §5 — CANDIDATE FORMS, FOR THE OWNER — NONE CHOSEN, NONE ARMED

The level sits on the corridor SPLIT of the firm block (and secondarily on its
use as an energy floor). Forms, with admissibility stated:

| form | what | admissibility | direction |
|---|---|--:|---|
| **(i)** published RA-import CAPABILITY ALLOCATION by branch group (CAISO's annual MIC allocation RESULTS — what LSEs actually took north vs south, not the total capability) | replaces the MIC-share key with a published allocation key, same two sources' cadence | rule 13 ADMISSIBLE by inspection (published, annual, forward-regenerating); a **data-intake ask** — not in `data/raw` | favourable (§4.3) |
| **(ii)** measured corridor ENERGY share of the price-insensitive base (the caiso-151 OASIS intertie-bid record, if per-intertie grain exists; the committed `caiso_intertie_selfsched_ceiling.csv` is system-level) | replaces the key with CAISO's own bid conduct | admissible IF the per-intertie grain exists — a data question first | favourable |
| **(iii)** measured corridor share of EIA-930 net import (the SAME series the firm SHAPE already uses, caiso-73) | extends the admitted revealed-base construction to the corridor dimension | rule-13 TENSION stated plainly: the shape use was admitted as a capability profile; a share key on the same series moves the level onto the outcome — the owner's call, and the weakest of the three | favourable |
| **(iv)** treat the DMM RA "Imports" capacity as a CAPABILITY, not an energy floor (drop the self-schedule floor's level to what a measured energy source supports) | changes the floor's basis, not its split | needs (i) or (ii) as the source; alone it re-opens caiso-77/151's adjudicated floor — NOT recommended without a source | adverse or mixed |

The recommendation, stated and not taken: **(i) first, as a data-intake
session**, then a single-flag re-split arm pre-registered against the
caiso-215 zonal sign. Nothing about the 8,800 MW ladder, the firm prices or
the clean-depth tranches is proposed.

---

## §6 — PREDICTIONS, SCORED

| # | prediction | verdict |
|---|---|---|
| P-1 | G-RECON ≤ 1 % / < 100 MW on one basis | **HOLDS** — exact, gross basis |
| P-2 | PNW excess > DSW excess every year | **HOLDS** — +11.30/+10.65/+8.76 vs −2.87/−1.96/−3.45 |
| P-3 | PNW firm floor − measured PNW net ≥ 4 TWh every year | **HOLDS** — +8.25/+7.68/+5.26 (and +3.05/+3.97/+2.94 vs GROSS) |
| P-4 | firm rows strictly between floor and capability ≥ 10 % of hours (2024, 2025) | **FALSIFIED** — 0.7/0.2 % PNW, 1.3/2.5 % DSW; liveness holds by a different signature (§3.5) |
| P-5 | spot rows < 25 % of import energy; `WECC_scarcity` < 1 % of capability-hours | **HOLDS / FALSIFIED** — 23.5/3.5/2.9 % ✓; scarcity 19.4 % in 2023 ✗ |
| P-6 | import-marginal & link-unbound < 5 % of hours | **FALSIFIED** — 19.9/17.7/23.0 % |
| P-7 | Dec-2025 economic import > forced | **FALSIFIED** — 1.53 vs 2.65 (+1.05) |
| P-8 | export legs < 0.5 TWh | **HOLDS** — P1 export is 0 by construction (§3.2); the balance bound alone (≤ 2.31 TWh incl. losses) would not have settled it |

---

## §7 — DO-NOT-REDO ADDS

1. **Never compare the model's `import` klass to measured NET interchange
   without saying so.** The klass is GROSS and the scored pass exports nothing;
   the comparator nets 2.7–5.6 TWh of real exports.
2. **Never cite caiso-242 §3's voided ratios; cite §2.2 here.** The gas-basis
   identity gap is ≈ the transport adder, and the CT_PEAKER price-gap median is
   $1.4–3.7, not $13–16.
3. **Never attribute the CAISO over-import to the 8,800 MW spot ladder.** It
   is 3 % of import energy in 2024–25; the level is the north firm block.
4. **Never quote caiso-229's "firm prices INERT BY CONSTRUCTION."** Under the
   caiso-151 clip the $28 / $48 offers decide 0.7–3.3 TWh/yr as bound-setters.
5. **Never quote caiso-202 §C's < 5 % as the import-marginal share.** Node
   complementarity puts it at 18–23 %.
6. **Never attribute the December level slab to import VOLUME.** Model and
   measured December net import agree within ±420 MW in all three years.
7. **Never rebuild a recipe by parameter name** (caiso-243 §10.4, now
   CI-enforced by `tests/regression/test_run_year_kwargs_recipe.py`).

---

## §8 — OWNER ASKS

1. **Form of the firm-block corridor re-split** (§5) — recommendation (i), a
   data-intake session for CAISO's published RA-import capability ALLOCATION
   results by branch group.
2. **The transport adder on a spot-indexed marginal offer** (§2.2) — the
   on-recipe gas-basis residual is ≈ `CAISO_CITYGATE_TRANSPORT_ADDER`; whether
   a DEB-style marginal offer carries it is a methodology question, not a
   number to move.
3. **The caiso-232 December slab's carrier** (§3.7) — §3.6's hub-marginal
   hours are the next measurement; not started.
4. **The D-2 class-total basis** (§4.5) — a scorer-side bookkeeping question.
5. Unchanged from caiso-243 §9: D3, the 2025 overlay gap, PJM/MISO exposure,
   the DOF-provenance instrument, caiso-238 objects 3/4, the OFO arm.

---

## §9 — DELIVERABLES

`scripts/replay_keeper.py` (`run_year_kwargs`, `run_year_unreachable`,
`RUN_YEAR_REMAP`, `RUN_YEAR_NON_RECIPE`); `scripts/lib/bundle_fleet.py`
(delegation + `clear_fleet_caches`); `tests/regression/test_run_year_kwargs_recipe.py`;
the four caiso-242 probes rewired + `_caiso244_{gas_basis_identity,passthrough_test,roundtrip,ctpeaker_anatomy}_onrecipe.json`;
`scripts/probes/_caiso244_import_level_anatomy.py` + `_caiso244_import_level_anatomy.json`;
`PRECOMMIT-caiso244-import-level-phase0-2026-09-04.md`; this finding; the
caiso.md entry; evidence appends (no verdict move) on the CAISO shard cells
`import_hub_pricing`, `caiso_firm_selfsched_floor`, `measured_offer_surface`.
**No run registered (none produced), no keeper change, no `ScenarioConfig`
field.**

**Next number: caiso-245.**
