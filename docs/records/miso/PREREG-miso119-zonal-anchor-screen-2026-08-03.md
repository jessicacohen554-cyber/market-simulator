# PREREG — miso-119: the `gas_offer_margin_zonal_anchor` EX-ANTE SCREEN at MISO (Phase 0, no LP), with the conditional A/B (Phase 1) pre-registered behind it

**Written, committed and pushed BEFORE the screen probe runs.** Everything
below — the two ex-ante inertness routes and their bands, the construction
gates, the conditional Phase-1 arm spec with its kills and promotion rule —
is fixed in advance. Session miso-119, branch
`claude/miso-119-backcast-calibration-m3srg7`, off `origin/main` at `bfeddc6`.

**Scope item.** The `gas_offer_margin_zonal_anchor` MISO cell (`U`), the head
of the miso-119 handoff's queue. The matrix row's own note charters this
exact construction: *"MISO's cell stays U (spread 0.332, coupled topology,
inertness prior strengthened twice — its own lane may adjudicate I ex-ante on
the no-LP bar with ZERO solves)."* Rule 25 `[R-ISO-SCOPE]`: PJM's `I`
(pjm-144) and ERCOT's `K` (ercot-150) transfer **nothing** — every quantity
below is measured on MISO's own data, MISO's own keeper fleet, MISO's own
committed sidecars. What the siblings DO supply is the row's established
**gate definitions** (the pjm-144 K3 liveness gate and its pre-declared
ex-ante anchor bar), reused here as bars, with MISO's own numbers put to them.

**Keeper under test:** `2026-08-03-miso-117b-ct-heat` (bundle
`results/calibration/miso117_ctheatrate_B`, determination NOT-YET, sole FAIL
C7 `COAL_PRB` ×3y, ledgered caveats 2/3 `{C3a, C3c}`).

---

## §1 — The grain question, restated at MISO (no-LP admissibility)

`apply_gas_offer_margin` adds `markup_hr × (anchor − fuel)` and states its own
identity: *at `fuel == anchor` the reformed offer reduces exactly to the
registered band multiplier* — a statement about a unit's OWN delivered fuel.
The MISO keeper arms BOTH `gas_offer_net_revenue_margin=True` (ISO anchor
3.0492, `constants.GAS_OFFER_MARGIN_ANCHOR_BY_ISO["MISO"]`) AND
`miso_zonal_gas_basis=True` (run_config.json, recorded), so marked-up gas
tranches price their markup at the ISO-level identification point while their
delivered fuel afterwards carries a per-zone spread. The grain mismatch the
row names is therefore genuinely PRESENT at MISO; the question this screen
answers is whether correcting it can move anything the rubric scores.

**MISO's applier convention (code identity, verified in the probe):**
`apply_miso_zonal_gas_basis` delegates to `_apply_meanzero_zonal_gas_basis`
(`src/market_sim/data/fuel/basis/meanzero.py`) — the SAME capacity-weighted
mean-zero core as PJM, no level term. This is the decisive convention fact:
ERCOT's `K` came from the flat measured LEVEL half its convention carries
(the mean-zero spread half was price-inert there too, measured directly);
MISO, like PJM, has **no level half by construction** — the gas-capacity-
weighted mean of the applied spread is exactly zero, so the fleet-aggregate
offer level cannot move and the ONLY channels are (a) cross-zonal price
separation and (b) intra-stack dispatch re-ranking.

**The A−B arithmetic is exact and hour-invariant.** For every tranche with
`offer_markup_hr > 0`, arming the zonal anchor changes its offer by

```
Δoffer_g = offer_markup_hr_g × (anchor_zone(g) − 3.0492)      [$/MWh]
```

— constant across all 8760 hours, independent of the fuel term (which
cancels), and therefore computable EXACTLY with no LP from (i) the derived
zone anchors and (ii) the keeper's own reconstructed fleet. MISO's per-plant
gas pricing (`gas_plant_monthly_fuel_pricing=True`) does not perturb this:
per-plant deviations live in `fuel(t)`, which the margin tracks hour-by-hour
in both arms identically. The winter Chicago citygate overlay
(`miso_winter_citygate_daily=True`) is mean-preserving within month by
construction, so it moves no annual mean and no anchor.

## §2 — The derivation (standing tooling, extended to MISO)

`scripts/data/derive_gas_offer_margin_anchor.py --iso MISO --by-zone
--weights-bundle results/calibration/miso117_ctheatrate_B`, after the minimal
registry extension the PJM lane already modelled: MISO joins
`ZONAL_BASIS_ISOS` + `CAPWEIGHTED_ZONAL_ISOS` (its applier IS the meanzero
core), `GAS_SERIES_FLAGS["MISO"]` gains `miso_zonal_gas_basis: True` (the
flag does not touch `_gas_series` — PJM's own comment pattern — so the ISO
anchor is unchanged by it; gate S2 checks that instead of assuming it), and
`ZONAL_KEEPER_REQUIRED_FLAGS["MISO"] = ("miso_zonal_gas_basis",)`. MISO does
NOT join `SOLVE_FUEL_ARRAY_ISOS`: its per-plant fuel levels would make the
zone-median row mix per-plant idiosyncrasies into a zone anchor (and the
within-zone ptp guard would correctly hard-fail); the synthetic-series
construction measures exactly the zone-spread term the mechanism's zonal
resolution corrects, per the row's own definition. The keeper's per-year
fleet is rebuilt no-LP via `scripts.lib.bundle_fleet.reconstruct_bundle_fleet`
(the sanctioned reconstruction), and the RUNTIME applier is called on that
real fleet — the transform depends on the solve's own per-zone gas capacity,
so a synthetic unweighted mean is not acceptable (pjm-144 §1.3's measured
error class).

**Zero fitted parameters.** The zone anchors are the same measurement as the
ISO anchor evaluated per zone, over the same 2023–2025 training window, by
the same rule-23-frozen derive. They are what the script prints; they are not
swept, whatever the verdict.

## §3 — Phase 0 decision rule (fixed in advance)

Two ex-ante routes to `I`. **EITHER suffices**; both are the row's own
pre-existing bars, not numbers chosen against an expected result:

* **Route A — anchor-grain inertness** (pjm-144 §1.3's own pre-declared
  ex-ante bar, applied unchanged): if `max_z |anchor_z − 3.0492| < 0.10`
  $/MMBtu, the zonal correction is smaller than the identification's own
  noise floor and the cell is `I` ex-ante, no solve spent.
* **Route B — price-side unreachability of the row's liveness gate**: the
  row's established K3 rule (pjm-144, reused at ercot-150) requires, for a
  LIVE verdict, `max over zones |Δ zonal mean λ| > 0.10 $/MWh` in EVERY
  year. Per hour, a zonal energy dual in this LP is set within the span of
  the perturbed offers — absent a degenerate congestion-state flip, an
  offer-cost perturbation bounded by `δ = max_g |Δoffer_g|` cannot move any
  zonal price, hence any zonal ANNUAL MEAN, by more than `δ`. So if
  `max_g,y |Δoffer_g(y)| < 0.10 $/MWh`, the K3 price leg is unreachable ex
  ante, K3 fails by construction, and the row's own rule stamps `I` (the
  pjm-144 disposition: dispatch-live-but-price-inert IS `I`). The
  congestion-flip caveat is stated, not hidden: it is second-order at these
  magnitudes, and gate S5's coupling census from the keeper's own committed
  sidecars is the empirical support REPORTED alongside (share of hours the
  keeper's zones decouple at all, at > $0.01 / $0.10 / $1 / $5 cross-zone
  range). It supports; it does not gate.

**If NEITHER route fires → the screen returns LIVE and Phase 1 (§5) runs.**
No intermediate judgment call: the bands above are the whole rule.

**Reported, never gating (Phase 0):** the capacity-weighted Δoffer
distribution (p50/p95/max, signed and absolute, per year); the marked-up
tranche census (count, MW, classes) and the band-scoped
(`offer_margin_anchor` override) census, expected 0; the per-year
capacity-weighted means the applier removes; C3c tail-flip proximity (keeper
hours with any zone price within `max|Δoffer|` of the $200 threshold, from
the committed `hourly/system_<year>.parquet`); the zone-anchor table itself.

## §4 — Phase 0 construction gates (invalidate the SCREEN, never adjudicate)

* **S1 keeper-config fidelity.** The probe reads
  `miso117_ctheatrate_B/run_config.json → scenario_config`, drops ONLY keys
  present in `scenarios._CACHE_KEY_RETIRED_FIELDS` (pre-verified: exactly
  `ct_committed_hr_override` / `ct_econ_hr_override` / `ct_peak_hr_override`,
  the three retired CT_CHP overrides nyiso-114 deleted), and HARD-FAILS on
  any other unknown key. It asserts `miso_zonal_gas_basis == True`,
  `gas_offer_net_revenue_margin == True`, `gas_offer_margin_anchor == 3.0492`,
  `gas_offer_margin_zonal_anchor == False`,
  `gas_offer_margin_anchor_by_zone == None`, `measured_chp_heat_rates ==
  True`, `measured_ct_heat_rates == True` (keeper-match tokens). The
  weights-bundle reconstruction path additionally carries the derive's own
  GAS_SERIES_FLAGS / ZONAL_KEEPER_REQUIRED_FLAGS hard-checks.
* **S2 ISO-anchor invariance.** After the registry edit,
  `derive_anchor("MISO")` returns 3.0492 to ≤ 1e-4 — the recipe extension
  moved nothing (the zonal flag never touches `_gas_series`).
* **S3 mean-zero invariant.** Per year, the gas-capacity-weighted mean of
  the per-zone transformed series equals that year's ISO series mean to
  ≤ 1e-6 $/MMBtu (exact by the applier's construction); the window-mean-
  weights residual of the anchor table vs 3.0492 is REPORTED (year-to-year
  weight drift only, pjm-144 precedent).
* **S4 domain census.** The count of tranches with `offer_markup_hr > 0` in
  each year's reconstruction is nonzero (if it is ZERO the mechanism has no
  domain at MISO and the verdict is `I` trivially — reported loudly as such,
  distinct from Routes A/B).
* **S5 sidecar census readable.** `hourly/system_{2023,2024,2025}.parquet`
  load and carry per-zone `price`; the coupling census (§3 Route B support)
  computes.
* **S6 hub-table coverage.** `miso_zonal_gas_hub.csv` carries all six MISO
  zones × 2023/2024/2025 with no SPARSE-flagged in-window row.

An S-gate failure is INDETERMINATE — fix the construction or stop; it never
stamps the cell.

## §5 — Phase 1 (CONDITIONAL A/B; runs ONLY if §3 returns LIVE)

Mirrors pjm-144's design with MISO's own expectations; nothing here runs if
Phase 0 adjudicates `I`.

* **Registration.** `constants.GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["MISO"] =`
  the §2 table (zero fitted parameters, rule 23 citation to the derive run).
  Matrix duty (c) is already satisfied — the mechanism row exists.
* **Arms.** Same-HEAD, sequential (rule 12; ~15 GB peak/year — 8 GB swapfile
  enabled first), each `[2023, 2024, 2025]` in one invocation (rule 16):
  * control: `scripts/replay_keeper.py results/calibration/miso117_ctheatrate_B
    --out-dir results/calibration/miso119_control_A --note "miso-119 same-HEAD
    zero-delta control"`
  * arm: `... --out-dir results/calibration/miso119_zonalanchor_B --set
    gas_offer_margin_zonal_anchor=true --note "miso-119 single delta:
    gas_offer_margin_zonal_anchor=true on the miso-117b keeper"`
* **Post-solve order per arm** (the caiso-158/miso-117 discipline): solve →
  register → `legitimacy_diagnostics.py` → `calibration_verdict.py
  --write-metrics` → A/B scorer; both arms registered whatever the verdict
  (rule 15, top-15 MISO retention honoured).
* **Construction gates.** K1 flag fidelity (arm records the zonal gate True +
  the full resolved 6-zone map equal to the registered constant; control
  False/None; both record `gas_offer_net_revenue_margin=True`, anchor
  3.0492). K2 control integrity on the SCORECARD basis (control reproduces
  the keeper's determination + all nine criterion statuses; strict-byte drift
  vs the committed miso-117b sidecars REPORTED, not a gate — miso-117 §6
  precedent). K3 liveness, BOTH legs in EVERY year: `max |Δ class MW|` on a
  class-hour > 50 MW AND `max over zones |Δ zonal mean λ| > 0.10 $/MWh`;
  system load-weighted Δλ reported, no threshold. K4 single delta (the two
  run_config scenario blocks differ in exactly the two zonal-anchor keys).
  K5 both bundles `[2023, 2024, 2025]`.
* **Kills.** P1: C1 holds 16/16 all-class, 12/12 free-class. P2: the arm's
  FAIL set ⊆ control's — expected exactly `{C7 COAL_PRB ×3y}`; ANY new FAIL
  kills; named fragile cells C3a-2025 (−14.1 % of ±15 % ledger band) and C3c
  (ledgered 1/6/0 h). C7 `COAL_PRB` cv_ratio movement within its standing
  FAIL is REPORTED either way and neither kills nor promotes (this lever is
  NOT a C7 instrument and is not offered as one). P3: C6/C8 stay PASS (C8
  watch: `CT_PEAKER` D-2 share 0.141/0.100/0.104 vs the 0.15 cap; the h14-21
  limb is NOT touched, per the standing bar). P4 on the DELTA (ercot-150's
  P4 lesson): per year, arm slack+dump within max(+10 MWh, +1 %) of the
  control's own value. P5: no fitted follow-up — no parameter moves to
  "finish" the result; the table is not re-derived against it.
* **Promotion rule, pre-committed:** all K-gates pass AND no kill →
  **promoted to keeper** (rule 1: the structurally correct identification
  grain of a mechanism the keeper already arms, at zero fitted parameters).
  K3 fails → **`I`**, registered, keeper unchanged. Any kill (K-gates clean)
  → registered, **`O`**, put to the owner with the numbers (never `R`).

## §6 — Declarations

* **Expected structure (not a gate):** two-sided zonal geometry (mean-zero
  centroid convention) — premium-basis zones (expected: the MidCon/Northern
  Natural West/Plains in 2023–24) under-marked today, discount zones
  over-marked; magnitudes expected FAR smaller than PJM's (raw window spread
  0.332 vs 1.483 $/MMBtu). No magnitude band is declared for any criterion.
* **NOT claimed:** no C7 `COAL_PRB` claim in either direction (the C7
  residual is the miso-113-routed overnight-distribution lane; a cost-side
  lever is pre-declared NOT to reach it — handoff bar). No amplitude claim
  (the spread is annual/zonal, within-day offer σ unchanged by construction;
  miso-89/miso-114 stay where they are). No C3c claim. No seam claim. No
  re-litigation of any armed mechanism; single delta only.
* **Standing bars honoured:** h14-21 `CT_PEAKER` limb untouched;
  `min_stable_pct` not re-derived; `CC_CHP` volume/heat-rate questions stay
  closed; `miso_cc_coal_rebalance` stays unarmed; the regulated-PRB family
  stays SPENT; no derive re-run outside the §2 rule-23-cited extension.
* **Holdout (rule 22):** 2023–2025 ONLY, in every phase. MISO holds no
  `calibration-complete` marker; no out-of-training year is solved, scored
  or read by any part of this session.
* **Contamination, declared:** the session is NOT blind. Before this prereg
  was written it read the miso-117/118 findings, the MISO log, the matrix row
  (including pjm-144 §7's "MISO's raw spread (0.332) is smaller than PJM's
  and MISO is similarly coupled — its prior of inertness just got stronger"),
  and eyeballed `miso_zonal_gas_hub.csv`'s West/Plains and Illinois 2023–2025
  rows (window means ≈ +0.08 / +0.01 $/MMBtu; the sign-flipping 2025 West
  row); MISO-South's rows were NOT read, and its ≈ −0.26 level is an
  INFERENCE from the quoted 0.332 spread, recorded here before verification.
  What this prereg fixes in advance is therefore the decision RULE: both
  Route bands are the row's own pre-existing gates (pjm-144's ex-ante anchor
  bar; the K3 zonal liveness threshold), not values positioned against the
  expected MISO numbers, and the markup-side magnitudes (`offer_markup_hr`
  distribution) that decide Route B were unknown when this was written.
* **Rule 28 duty (b):** the MISO cell is stamped in THIS session with the
  Phase 0 (or Phase 1) verdict and citation, rejections and inert verdicts
  included. Rule 15: if Phase 0 adjudicates `I`, no run is produced and
  nothing registers on the dashboard — stated, not assumed.

## §7 — Probe

`scripts/probes/_miso119_zonal_anchor_screen.py` (no LP; transcript
`results/calibration/PROBE-miso119-zonal-anchor-screen-2026-08-03.txt`):
runs §4's gates, the §2 derivation via the standing derive's own functions,
the §3 statistics, and prints the verdict under the §3 rule. Re-runnable at
zero LP cost.
