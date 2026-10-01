# PREREG — miso-144: attributing the 19.3 GW IN-MERIT IDLE BLOCK (§5.4 queue item 5, Phase 0, diagnosis-first)

**Session:** miso-144, 2026-08-08. **Lane:** §5.4 queue **item 5 (NEW)** — the
in-merit idle block measured (not attributed) at miso-143. **Keeper:**
`2026-08-05-miso-132b-cc-committed` (bundle `results/calibration/miso132_ccmin_B`).
**Posture:** NO SOLVE at G-A/G-B; a solve is licensed only at G-C, for at most
ONE mechanism, after every kill gate passes. Expectation stated in advance: the
miso-131…143 no-solve precedent likely continues.

**Owner directive honoured:** the target is the 2024/2025 mean-LMP level miss;
the 2026-08-08 addition (*close the 2025 −14 % underrun WITHOUT disturbing the
other metrics*) is enforced by the kill gates in §7. No C7 lane, no C7 ledger.

This PREREG is pushed BEFORE any adjudicating statistic. §10 lists exactly what
was read before registration and why none of it is the decomposition.

---

## 0. §0 re-verified from committed artifacts (this session, before this PREREG)

`calibration_verdict.py --run-id 2026-08-05-miso-132b-cc-committed`, no
re-solve, all three years in one invocation (rule 16). Rule 22: MISO holds no
marker in either block, so 2023–2025 only.

**`NOT-YET`, rubric v3.1. SOLE FAIL C3a `price_mean`** (2025 −14.1 %, MODEL
MISS; determination basis lists `price_mean` as the only undocumented
out-of-tolerance criterion). Sole ledgered caveat **C3c, 1 of 1** (all three
years CAVEAT, ACCEPTED MEASURED-INPUT LIMITATION). C1 / C2 / C4 / C6 / C8 PASS
— C1 SKIPPED for all eight classes in 2025 and C2 SKIPPED for both families
(gas −11.2 %, coal +4.2 %) on preliminary EIA-923 vintage; C8 notes ST_GAS
**grounded above budget** at 31.9 / 33.1 / **45.1 %** forced with all binding
mechanisms clearing D-4. Identical to the charter §0 in every observed cell.
The bundle `metrics.json` stale `price_mean: CAVEAT` is noted and ignored — the
scorer is authoritative (charter; not re-discovered).

---

## 1. The object, and what this session must NOT assume

miso-143 measured (committed `_miso143_ladder.json`,
`footing_failure_diagnostic`): in 2025 JJA h12–17 the model has **85,170.6 MW**
(`lo` offer basis; **84,050.8** at `hi`) of capability offered at or below its
own load-weighted clearing price while the sidecar's THERMAL_COLS classes serve
**65,840.6 MW** — excess **19,330.1 MW** (`lo`) / **18,210.2** (`hi`). 2024:
20,001.0 / 19,031.5. 2023: 21,951.2 / 20,966.2. Congestion is REFUTED as the
cause (r = −0.113; the copperplate under-price is LARGEST at zero zonal
spread) — that test is NOT re-run (TRAP 2 / DO-NOT-REDO).

**The floors are a hypothesis, not a finding** (charter). The attribution must
close arithmetically BEFORE any mechanism is named.

## 2. A construction analysis, stated before any number is computed

Reading the committed instrument (`scripts/probes/_miso143_ladder.py` L185,
L325, L413–421; `_miso143_stack.py` L76–78) and the committed miso-143 JSON
shows the subtraction crosses two universes:

- `below` sums `pmax × availability` over **EVERY fleet row** returned by
  `run_year(fleet_only=True)` with offer ≤ anchor. The committed
  `class_idle_frac` table iterates the FLEET's own classes and lists
  **`hydro`, `import`, `nuclear`, `oil`, `biomass`** alongside the thermal
  classes — so the fleet universe includes them.
- `thermal` sums sidecar dispatch over **`THERMAL_COLS` only** =
  COAL + gas classes + (`OTHER`, `oil`, `biomass`) — **no `nuclear`, no
  `hydro`, no `import`**.
- The keeper sidecar (committed) shows `nuclear` mean dispatch ≈ 10.3 GW
  annual (11 distinct hourly values), `hydro` ≈ 1.0 GW (4,254 values, LP
  dispatched), `import` ≈ 2.0 GW (2,748 values, LP dispatched), and
  `OTHER`/`biomass` are 12-distinct-value injected profiles (miso-142 §O4)
  with no LP-dispatch relationship to the fleet's biomass capability rows.

So the measured "excess" algebraically contains the **capability of every
in-merit non-thermal fleet row** (nuclear, hydro, import, biomass) whose
dispatch is excluded from the served side, **minus** the injected OTHER/biomass
dispatch that is counted as served with no fleet capability behind it. Whether
that accounts for most of the block or only a corner of it is **exactly what
this session measures** — the prior is two-sided in §5, and the charter's
mechanism terms (forced-elsewhere, ramp, zonal, reserve) are measured alongside
the instrument terms, not instead of them.

Machinery facts fixed from the keeper's meta.json (full ScenarioConfig dump)
before registration:

- `energy_reserve_coopt=True`, `miso_reserve_pergen=True`,
  `miso_zonal_reserves=True`, `miso_measured_reserve_requirements=True` — the
  LP holds real reserve MW on assets (`P + R ≤ cap` joint-headroom rows).
  Committed `reserve_family_2025.parquet`: three families, ALL reserve_class 0;
  annual-mean held = requirement in every family (rbdc 2,642.2 MW =
  midwest 2,165.1 + south 477.2 — an exact partition, so **rbdc held IS the
  physical withheld total**; TRAP 9); family duals nonzero in only 5
  hours (south).
- `ramp_limits=None`, `measured_ramp_capability=False` — the `_build_ramp_rows`
  machinery exists but is NOT armed: **zero ramp rows in this keeper's LP**, so
  the charter's "ramp/min-up binding" term is structurally zero on the
  hold-OUT side. Min-run/commitment floors are LOWER bounds — they force MW
  IN (the forced-elsewhere term), they cannot hold capability OUT.
- `scarcity_price_overlay=None` — no post-LP price overlay; `system.price` is
  the zonal energy-balance dual (R-DUALS).
- `reliability_floor=True` (overrides null) — the registry limbs are live; C8's
  D-2/D-4 already attributes their forced energy (ST_GAS grounded above
  budget).

## 3. The ledger — pre-registered identities

All quantities are **window means over 2025 JJA h12–17** (2023/2024 as
year-generality legs; W1 reported as sensitivity), load-weighted on C3a's own
model-demand weight — ONE weight throughout (TRAP 7) — at BOTH offer brackets
`lo`/`hi`, anchored on the keeper's committed load-weighted P1 price
(`sidecar_price`, miso-143's own anchor, reused not re-derived).

Definitions (per hour, then window-averaged):

- `A0` = Σ_{all fleet rows: o ≤ a} cap − Σ_{THERMAL_COLS} disp — **the
  replication of miso-143's excess, byte-for-byte the same construction.**
- `T_universe` = Σ_{non-thermal fleet rows (nuclear, hydro, import, biomass,
  any class ∉ THERMAL_COLS): o ≤ a} cap — reported **per class**.
- `T_injected` = sidecar `OTHER` + `biomass` dispatch (12-value injections
  served with no fleet capability behind them; biomass fleet capability sits in
  `T_universe`, its sidecar dispatch here — TRAP 10).
- `thermal_gap` = A0 − T_universe + T_injected  **(identity — arithmetic, must
  hold to float precision; construction check CC-1).**
- Per thermal class c (cheapest-first within-class allocation, class grain —
  `class_hourly` has no zone column, disclosed):
  `idle_sys_LB_c` = max(0, capbelow_sys_c − disp_c), `oom_sys_LB_c` =
  max(0, disp_c − capbelow_sys_c). **Identity CC-2:** Σ_c (idle_sys_LB_c −
  oom_sys_LB_c) = thermal_gap exactly.
- `T_zonal` = Σ_c idle_sys_LB_c − Σ_c idle_zonal_LB_c, where the zonal variant
  prices each fleet row against its OWN zone's committed P1 price. (This is an
  INSTRUMENT-BASIS term — the anchor is a demand-weighted mean — and is NOT a
  re-run of the refuted congestion test, which was about the copperplate
  under-price growing with spread; TRAP 2.)
- `T_tie(δ)` = in-merit idle within δ of the zonal price (δ = $0.10 primary;
  0.01 / 0.50 / 1.00 reported) — the partially-loaded marginal rung,
  legitimate LP behaviour, not a defect.
- `T_offerbasis` = strict-zonal idle at `lo` − same at `hi` (gas rows whose
  P0-basis offer is below the anchor but whose true P1 offer is not; the true
  P1 block is ≤ the `hi` reading for measured-horizon rows).
- `T_reserve` = window-mean rbdc `held_mw` (the physical total; an UPPER bound
  on the part sitting on in-merit thermal rows — storage-backed RS and any
  non-thermal holding over-subtract, disclosed, bounded by the storage/hydro
  share).
- `T_resid` = Σ_c strict-zonal-`hi` idle − T_reserve. By LP complementary
  slackness (no ramp rows, lower-bound floors only), capability strictly
  in-merit at its own zone's dual and not reserve-held **cannot be idle at the
  optimum** — T_resid measures instrument error (availability reconstruction
  drift, price-sidecar-vs-dual gap, within-class allocation slack) plus any
  genuine anomaly.
- `OOM_LB` = Σ_c oom_sys_LB_c — the charter's **forced-elsewhere displacement**
  term (every out-of-merit MW dispatched displaces one in-merit MW at fixed
  served quantity). Cross-checked against C8/D-2's forced attribution
  qualitatively (annual grain), never re-derived.

**The charter identity maps as:** forced-elsewhere = OOM_LB; ramp/min-up = 0
(structural, §2); transmission/zonal = T_zonal; reserve = T_reserve; residual =
T_resid — **extended** with the pre-registered instrument terms T_universe,
T_injected, T_tie, T_offerbasis because the replication target's construction
crosses universes (§2). If the instrument terms dominate, the honest verdict is
an instrument correction, not a mechanism finding.

## 4. Gates

- **G-A0 (replication):** reproduce A0 = the six committed excess values
  (three years × lo/hi) to |Δ| ≤ 5 MW each, and the committed
  anchor/actual/thermal window values. FAIL ⇒ construction stop: diagnose HEAD
  drift vs probe defect; if unresolved, report and STOP (arm nothing).
- **G-A1 (universe):** measure T_universe (per class) + T_injected; CC-1.
- **G-A2 (thermal gap):** idle/oom LBs (CC-2), T_zonal, T_tie, T_offerbasis,
  T_reserve.
- **G-A3 (closure):** T_resid with the STOP in §6.
- **G-B (only if a single NON-instrument term ≥ 50 % of Σ_c idle_sys_LB_c):**
  name it; adjudicate real-driver-vs-bug. For floors: rule 17 — a floor binding
  in hours its own driver evidence says the class is offline is a bug by
  definition; enumerate what already floors the class (D-2) per rule 19; note
  C8's D-4 says the live limbs bind in-window, so a floor-release arm is
  licensed ONLY by off-window evidence this gate would newly produce, never by
  the price residual. For reserves: MISO really holds ~2.4–2.8 GW of operating
  reserve (measured requirements armed since miso-56/71) — a REAL market
  mechanism; being part of the block is not a defect. For zonal: an instrument
  basis note, not a congestion re-open.
- **G-C (only if G-B resolves to ONE mechanism with measured identification AND
  every §7 gate passes):** same-HEAD zero-delta control first, then
  `replay_keeper --set`, `--years 2023 2024 2025` in a SINGLE invocation, arms
  sequential (rules 12/16), swap enabled first. Expected: NOT reached.

## 5. Predictions — fixed before any window statistic is computed

2025 JJA h12–17, `lo` bracket unless stated; two-sided bands; GW.

| # | quantity | band | point | falsifier that matters |
|---|---|---|---|---|
| P1 | A0 replication, 6 values | \|Δ\| ≤ 5 MW | exact | any miss ⇒ construction stop |
| P2 | T_universe | [13.5, 19.5] | 16.5 (nuc ≈ 11.8, hyd ≈ 1.6, imp ≈ 2.6, bio ≈ 0.5) | < 10 ⇒ universe mismatch NOT dominant; the block is substantially real-thermal and the miso-143 successor framing survives |
| P3 | T_injected | [0.7, 1.4] | 1.0 | — |
| P4 | thermal_gap | [0.8, 6.8] | 3.8 | > 8 ⇒ the thermal side alone is most of the story |
| P5 | OOM_LB | [0.8, 4.5] | 2.0 | > 5 ⇒ forced-in displacement is the dominant object → G-B on floors |
| P6 | CC-2 identity | exact | exact | tautology; coding check only |
| P7 | T_zonal | [0.2, 2.5] | 0.9 | — |
| P8 | T_tie (δ=$0.10) | [0.1, 3.0] | 0.6 | > 3 ⇒ the "block" is substantially the marginal rung itself |
| P9 | T_offerbasis | [0.5, 1.8] | 1.1 | committed system-wide lo−hi is 1.12; a strict-zonal reading far off it would flag the allocation |
| P10 | T_reserve (window rbdc held) | [2.2, 3.2] | 2.65 | partition check: midwest+south = rbdc to ≤ 1 MW (TRAP 9) |
| P11 | T_resid | [−1.0, +1.5] | +0.3 | **STOP if \|T_resid\| > 3.0** (§6) |
| P12 | ramp term | 0 (structural) | 0 | any ramp row found in the builder path ⇒ re-open |
| P13 | year-generality | T_universe within ±25 % of its 2025 share in 2023/2024 | — | a term that exists only in 2025 cannot explain a three-year block |

Branch priors: **BRANCH-INSTRUMENT 65 %** (universe + instrument terms ≥ 60 %
of A0 and T_resid inside the stop) · BRANCH-RESERVE 15 % (strict thermal idle ≈
reserve holding) · BRANCH-OOM 12 % (OOM_LB dominant → G-B floors) ·
BRANCH-REAL-RESIDUAL 8 % (stop fires or an unexplained strict-idle mass).

## 6. Stop rules, pre-committed

1. **G-A0 miss** ⇒ diagnose; unresolved ⇒ report, arm nothing, stop.
2. **\|T_resid\| > 3.0 GW** ⇒ the attribution does not close ⇒ report the full
   decomposition with the residual at magnitude, arm NOTHING, name the
   successor (an availability-reconstruction audit: fleet_only vs the solve's
   own availability — the one leg no committed artifact can verify; disclosed
   instrument limit). An unattributed block licenses nothing (charter G-A).
3. **No single non-instrument term ≥ 50 % of Σ idle_sys_LB** ⇒ no G-B mechanism
   naming; report shares and queue the object per the branch verdict.
4. Kill-gate breach at any G-C consideration ⇒ no arm, report.

## 7. Kill gates — bars fixed now, before any number is seen

- **KG-1 C3b-2025 NRMSE ≤ 0.200** (currently 0.191; headroom 0.009). Any arm
  putting it over converts a PASS to FAIL and is NOT a fix.
- **KG-2 C3a 2023/2024 stay PASS** (−0.4 / −6.0 now; no gated-year flip).
- **KG-3 C1/C2 stay PASS on gated years**; 2025 is UNGATED — any post-arm 2025
  fuel-mix statement is DESCRIPTIVE vs EIA-930 and says so (charter blocker).
- **KG-4 C4 stays PASS.**
- **KG-5 C8:** no material class's forced share RISES; no D-4 window breaks; a
  floor CHANGE regenerates `legitimacy_diagnostics.json` and re-reads the
  grounded-above-budget escalation (ST_GAS 45.1 % grounded; CT_PEAKER 10.7 %
  vs 15 % cap). Releasing a floor may LOWER forced share — the intended
  direction.
- **KG-6 C3c ledger 1 of 1 — SPENT.** No second entry exists.
- **KG-7 fail-set:** the run's fail set must remain ⊆ {C3a}.
- Rule 1 is one-directional: a structurally-correct mechanism stays even if the
  residual worsens; it never licenses breaking a passing criterion to buy C3a.

## 8. Traps, each with its counter-measurement

1. **Quantity relapse** (family CLOSED): no GW here is a price lever; any
   GW→price sentence states the product on the LADDER slope ($1.496/MWh per GW,
   miso-143) and that the ladder and the block are NOT disjoint — the same MW
   cannot be spent twice.
2. **Congestion re-run** (REFUTED): not re-run. T_zonal is the instrument's
   price-basis term (mean-vs-zonal anchor), explicitly NOT the
   spread-vs-underprice test.
3. **Floor as foregone conclusion**: OOM_LB is measured as a class-grain bound
   BEFORE any floor is named; floors enter only at G-B behind the ≥ 50 % bar.
4. **Instrument crossing**: every dispatch/price number is the keeper sidecar's;
   EIA-930/EIA-923 are not touched in G-A. LEVELS on the scorer's basis only.
5. **Coal sidecar alias**: `_miso143_stack.COAL_COLS` asserted map, reused.
6. **klass ≠ plant_group**: `_miso143_stack.klass_of` reused + non-empty
   assertion per class.
7. **Mixed weights**: ONE weight (C3a's model-demand weight) for every window
   mean; G-A0 re-asserts the committed anchor/actual pairs (the six deficits
   −4.75 / −8.333 / −10.676 / −10.671 / −30.999 / −30.435 are implied by the
   committed anchor/actual values this replication must match).
8. **Fixing the number**: Phase 0 — no parameter is sized at all.
9. **Reserve family double-count** (NEW): the three families share one physical
   R pool; summing held across families triple-counts. Counter: rbdc (all-zone
   family) held is THE total; assert midwest + south = rbdc per hour ≤ 1 MW.
10. **Biomass dual identity** (NEW): biomass is a fleet capability class AND a
    12-value injected sidecar class. Counter: assert the injection's distinct
    count (= 12); capability → T_universe, dispatch → T_injected; never both
    sides of one subtraction.
11. **Import is not silently absorbed** (NEW): import's in-merit idle line is
    reported separately inside T_universe with its existing owners cited
    (`miso_seam_envelope_merit_cap` armed; seam classes SPENT miso-114/123 —
    no new seam work here).

## 9. Data blocker, carried

EIA-923's 2025 vintage is PRELIMINARY: C1 skipped for all eight classes, C2 for
both families in 2025. (a) C1/C2 PASS is not evidence against this charter's
object; (b) post-arm safety in 2025 is never claimed from C1/C2 — descriptive
EIA-930 scoring instead, labelled; (c) a reportable limit on any finding.

## 10. Read before registration (disclosed in full)

Committed artifacts only, no window-decomposition statistic among them:
`_miso143_ladder.json` (the six excess values, anchors, class_idle_frac —
miso-143's published output), `_miso143_footing.json` reference, keeper
`meta.json` flags (§2), `reserve_family_2025.parquet` **annual** family means +
dual counts (2,642.2 / 2,165.1 / 477.2; 0/0/5 nonzero-dual hours),
`system_2025.parquet` schema + zone list (external zones carry zero demand),
`class_hourly_2025.parquet` schema + per-class distinct-value counts and
**annual** means (nuclear 10,341.5 MW / 11 values; hydro 1,034.7 / 4,254;
import 2,016.3 / 2,748; OTHER 665.8 / 12; biomass 334.3 / 12), the scorer's §0
output, and the probe/source files named in §2. The P2/P3/P10 bands are built
from these annual/structural facts; every WINDOW quantity in §5 is unmeasured
at registration.

## 11. Rule duties

Rule 15 (no LP ⇒ no run to register; if G-C arms, the run registers same
session). Rule 28(b) (queue stamp written this session, item 5 into the queue;
cell verdicts only if a mechanism is tested). Rule 22 (2023–2025 only). Rules
13/14/19/21/23/24/25 throughout. Probe hygiene: repo root on sys.path +
`load_zonal_shares` asserted non-None (miso-140b §6), via `_miso143_stack`
reuse. Concurrent-session check at open: zero open MISO PRs, no live MISO
branch (only miso-143's merged leftover). DO-NOT-REDO honoured as listed in the
charter; the trough window untouched; no `*_lw` re-derivation; no seam class
re-open; no `cc_nameplate_summer_derate` re-open; no `miso_cc_coal_rebalance`.
