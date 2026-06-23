# CAISO per-hub intertie residuals — over-import + inverted diurnal: root cause and the per-hub-signed-legs fix (2026-06-23)

Branch: `claude/caiso-backcast-residuals-0sy40s`. Picks up the keeper
`2026-06-23-caiso-per-hub-intertie` (bundle `caiso_perhub_intertie_3yr`), which
landed the FULL measured nodal LMP per scheduling point (MALIN != PALOVRDE) on
the priced-import node. Two residuals surfaced/grew with that faithful input:

| metric (2024 / 2025) | keeper repro | actual |
|---|---|---|
| mean LMP | 39.24 / 43.03 | 35.8 (2024) |
| neg-hours | 873 / 407 | ~800 (2024) |
| net interchange (TWh) | −36.04 / −44.17 | −32.4 / −36.2 |
| diurnal interchange corr | **−0.35 / −0.60** | (should be +) |

(Repro `results/calibration/caiso_residuals_repro`, byte-identical to the keeper
command; 2023 is the static-ladder fallback, corr +0.89, not informative.)

## The smoking gun: the measured hubs have the RIGHT diurnal shape; the model imports at the WRONG hours

Hour-of-day, 2024 (EIA-930 CISO net import vs the measured intertie hubs):

| hour block | actual net import | MALIN (PNW) | PALOVRDE (DSW) |
|---|---|---|---|
| overnight h00–05 | **5.2–5.6 GW** | $38–43 | $38–43 |
| midday h10–14 | **0.9–1.4 GW** | $26–30 | **$8–11** |
| evening h18–21 | 4.3–5.4 GW | $50–65 | $51–67 |

The measured hubs already carry the duck curve: PALOVRDE **crashes to $8–11
midday** (the desert-SW solar glut, 949 neg-hrs in 2024) and peaks ~$67 in the
evening; the actual tie deep-imports overnight (5.5 GW) and **backs off midday**
(1 GW) because CAISO is long off its own solar. So the price signal is correct
and faithful — the model's failure is structural, not an input problem.

## Root cause — the pooled single-node topology breaks two ways

The keeper holds **every** import tranche (MALIN-priced PNW + PALOVRDE-priced
DSW) **plus one AVERAGED-hub export sink** on a **single** `WECC_import` external
bubble, capped at 8.3 GW (the `WECC_import_simultaneous` interface limit). That
single pooled node fails on both axes:

1. **OVER-IMPORT (priority 1).** The now-correctly-cheap PALOVRDE midday block
   ($8) can fill the *whole* 8.3 GW import budget over *either* corridor link
   (the single zone routes any tranche over both `WECC_import→NP15` and
   `→SP15`), so the LP imports cheap desert-SW power midday even though CAISO is
   long. Net interchange overshoots actual in both years (−36.0 vs −32.4;
   −44.2 vs −36.2).
2. **INVERTED DIURNAL (priority 2).** The import tranches and the export sink are
   **independent legs on the same bubble** — they never net — so the LP imports
   the cheap midday hub *and* stays long, the exact anti-correlation the bidir
   node was built to fix. corr −0.35 / −0.60.

The standalone **bidir** node (`caiso-20`) DID fix the netting (corr flipped
positive) by collapsing both legs onto ONE signed flow — but it had to **average
MALIN and PALOVRDE into one price**, throwing away the per-hub basis the keeper
just won. Per `NEXT-caiso-roadmap`, every attempt to stack a delivery basis onto
the single averaged bidir node was mutually exclusive with the diurnal fix on the
capped node. The two mechanisms were thought irreconcilable.

## The topology already separates the hubs — it's just pooled

CAISO's config ALREADY models the two physically distinct WECC corridors as
separate links: `WECC_import→NP15` (ttc 4,800 = COI/Path 66, north, ~Malin) and
`WECC_import→SP15` (ttc 10,623 = Path 46/WOR, south, ~Palo Verde), with the
8.3 GW simultaneous cap as a bidirectional interface limit on the SIGNED SUM of
the two flows. The keeper just *pools* both hubs' tranches onto one bubble that
feeds both links. The fix is to stop pooling.

## The fix — per-hub signed legs (`--caiso-per-hub-intertie`)

Split the single `WECC_import` bubble into the two REAL corridors, each a SINGLE
signed flow priced at its OWN measured hub:

* **`WECC_PNW`** — COI/Path-66, MALIN hub, → NP15 (north): the PNW_* import
  tranches + one PNW export leg.
* **`WECC_DSW`** — Path-46/WOR, PALOVRDE hub, → SP15 (south): the DSW_* /
  WECC_scarcity import tranches + one DSW export leg.

Per corridor, every import leg (`hub + wheel + border_carbon`, all ≥ 0) is priced
at/above its export leg (`hub − ε`), so the two are arbitrage-free **per
corridor** → one net direction per hour per corridor (pure LP, no MIP). This
recovers BOTH properties at once:

* **per-hub basis** — each corridor is priced at its own measured hub (MALIN !=
  PALOVRDE), the keeper's win, kept; and
* **per-hub netting** — each corridor carries one signed flow, so the PALOVRDE
  corridor *reverses to EXPORT* in the midday solar glut instead of
  over-importing (the over-import + inverted-diurnal fix), the bidir win, kept.

The 8.3 GW simultaneous-import cap is preserved exactly: the
`WECC_import_simultaneous` interface limit is re-homed onto the two corridor
links (`split_caiso_import_node_per_hub`), still capping the signed sum at
±8.3 GW. Tranche capacities stay at their natural `IMPORT_TRANCHES` values (the
cap is the interface limit, not a per-tranche rescale — matching the keeper).
Export legs carry **no fitted cap**: the export volume is endogenous (how long
CAISO is), bounded by the same physical corridor link TTCs + the bidirectional
interface limit the imports use (rule #12 — a physical limit, not the measured
export peak fitted as a constant).

### Why this is structurally faithful and forward-reproducible (rules #1, #11, #12)
- The COI/Path-66 (Malin) and Path-46/WOR (Palo Verde) corridors are genuinely
  distinct transmission paths with their own WECC Path Rating Catalog ratings;
  modeling them as two ties at two hubs is MORE faithful than one averaged node.
- Every price is the measured neighbor-hub nodal LMP — a forward-reproducible
  market quantity (regenerates for any year, responds to changed conditions),
  never an outcome pinned to the residual.
- `--caiso-import-solar-shape` is now **redundant**: it was a no-OASIS proxy that
  collapsed the DSW import offer toward −$20 to manufacture the negative midday
  tail; the measured PALOVRDE hub now prints that tail directly, and on a signed
  node a −$20 import offer drives the very over-import we are fixing. The primary
  per-hub keeper drops it (rule #11 — prefer the measured input over the proxy);
  a probe with it ON quantifies the redundancy.

### Implementation
- `config/constants.py`: `CAISO_PER_HUB_IMPORT_ZONES`, `CAISO_IMPORT_TRANCHE_HUB`
  (now the single source of truth, imported by `eia_loader`).
- `model/transmission.py`: `split_caiso_import_node_per_hub`,
  `build_caiso_per_hub_intertie`, `inject_caiso_per_hub_intertie_prices`; the
  gas-coupling / solar-shape injectors made per-hub-zone-aware
  (`_caiso_import_tranche_of`).
- `config/scenarios.py`: `caiso_per_hub_intertie` flag (default off).
- `scripts/run_calibration.py` + `run_calibration_full.py`:
  `--caiso-per-hub-intertie` wiring (build + split + inject).
- `tests/test_caiso_per_hub_intertie.py`: topology split, builder, per-hub-basis
  + per-corridor arbitrage-free injection, dispatch netting/back-off.

## Caveat to watch in the solve (logged honestly)
On a signed corridor, when the PALOVRDE hub goes **deeply** negative (−$20 to
−$30 in the extreme glut hours), the import leg is *paid to inject*; if in-state
dump is cheaper than that payment the LP could import-and-curtail (a money pump).
The CAISO-default `negative_renewable_offers` floor raises `dump_cost` to ~$20,
which blocks it for all but the very deepest hours; the solve metrics below
confirm whether any residual over-import in those hours is material.

## Results (dashboard: `2026-06-23-caiso-per-hub-signed` keeper + `…-per-hub-legs` probe)

| metric (2024 / 2025) | keeper (pooled node) | **per-hub signed legs** | actual |
|---|---|---|---|
| net interchange (TWh) | −36.04 / −44.17 | **−32.39 / −41.11** | −32.38 / −36.16 |
| diurnal interchange corr | −0.35 / −0.60 | **−0.15 / −0.36** | (→ +) |
| mean LMP | 39.24 / 43.03 | 43.82 / 44.86 | 35.8 / — |
| neg-hrs | 873 / 407 | 459 / 193 | ~800 / — |

* **Priority 1 (over-import) — SOLVED.** 2024 net interchange −36.04 → −32.39,
  dead-on actual (−32.38); 2025 −44.17 → −41.11 (still over but much closer).
  The per-corridor netting stops the cheap Palo Verde block flooding the budget.
* **Priority 2 (diurnal) — improved, not solved.** corr −0.35 → −0.15 (2024) and
  −0.60 → −0.36 (2025). The hour-of-day profile shows the residual: the model
  STILL imports ~5 GW midday (h09–14) when actual is ~1 GW, and under-imports the
  evening (h15–20) — a phase shift that integrates to the correct ANNUAL volume.
  Root cause of the remaining miss: **the cheap midday hub price is NOT a
  deliverable midday supply** — the desert-SW is locally long (its own solar) so
  Palo Verde prints $8, but that surplus is not deliverable to a simultaneously-
  long CAISO. The next priority-2 lever is a measured midday-deliverability /
  diurnal corridor-flow limit (a real, forward-reproducible transmission
  quantity), NOT a fitted diurnal multiplier.
* **Body / neg-hrs regressed — and that is the finding (rule #1).** mean
  39.24 → 43.82, neg 873 → 459. The pooled keeper's *better* body was partly an
  **over-import artifact**: cheap midday imports suppressed midday prices and
  manufactured negative hours. With the interchange volume corrected, the honest
  body is higher, and the residual is now an **in-state midday over-pricing**
  problem (the standing `DIAGNOSIS-caiso-body-overprice` item) — to fix at root
  cause, not by reverting to the over-importing pooled node.
* **solar-shape now redundant (probe `…-per-hub-legs`).** Per-hub legs + solar-
  shape is byte-near the keeper (2024 corr −0.17 vs −0.15, neg 535 vs 459, mean
  43.49 vs 43.82): the measured per-hub Palo Verde hub already prints the
  negative midday tail solar-shape proxied, and on a signed node its −$20 import
  offer mildly re-inflates the midday over-import. Dropped from the keeper
  (rule #11 — prefer the measured input over the proxy).

**Keeper decision.** `2026-06-23-caiso-per-hub-signed` supersedes
`2026-06-23-caiso-per-hub-intertie` (keepers.json updated): it is the most
structurally faithful CAISO run — correct interchange volume, the real two-
corridor topology, measured per-hub prices, no proxy — per rule #1, even though
its mean-LMP error grew (the lower-error pooled keeper was missing the real
structure). Open residuals handed off: (1) midday-deliverability diurnal lever
(priority 2 remainder), (2) in-state midday over-pricing body (priority 3-adjacent).
