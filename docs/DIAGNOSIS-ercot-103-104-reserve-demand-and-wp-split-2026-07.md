# ERCOT-103/104 — reserve-demand right-sizing and the West/Panhandle split are both bounded by measured data; the 2023 tail is 97% energy-dual

**Session 2026-07-24. Keeper: `2026-07-23-ercot100-netrev-margin-keeper`
(NOT-YET). Owner-authorized follow-ups to ERCOT-102: (2) the rule-26 ORDC-family
"reserve-demand right-sizing" round, and (3) the West/Panhandle topology split
(the ERCOT-101 §3 "own charter" lane).** Both are pursued to a decisive result;
**neither closes the load-bearing 2023 tail, and neither yields a keeper** — each
is bounded/blocked by ERCOT's own measured data, and each reinforces the
ERCOT-101/102 attributed bound from a new angle.

Probes: `scripts/probes/ercot104_west_congestion_nodal.py` (no-LP, SCED
binding-constraint archive); the registered solve probe
`2026-07-24-ercot103-realized-adder-rtorpa` (one-year 2023 diagnostic, REJECTED);
reused `ercot101_price_decomp.py`, `ercot102_reserve_slack.py`,
`ercot99_score_probe.py`.

## 0. Verdict

* **ERCOT-103 (reserve-demand right-sizing) — REFUTED.** ERCOT's own settlement
  data shows the 2023 scarcity tail is **97% energy dual, 3% reserve adder**
  (RTORPA $42 at the >$300 tail). No reserve-side mechanism can close a tail
  that lives in the energy dual: the in-LP envelope **over-fires** (ercot41/43),
  and the faithful realized-room RTORPA **under-fires** (this session's probe
  regressed C3a −16.8→−24.4% and C3c 76→71). The keeper's current reserve-VOLL
  co-opt is the least-bad proxy.
* **ERCOT-104 (West/Panhandle split) — BLOCKED (rule 11).** The §3 West
  congestion is **nodal, not zonal**: the zonal interfaces (WESTEX/PNHNDL/NE_LOB)
  are export limits already modeled at measured MW with tiny shadow prices
  ($5–21), while the congestion rent lives in 60–518 MW station-to-station lines
  ($3,000+ shadow). A 7-zone reduced network structurally cannot form nodal
  congestion, and there is no measured *zonal* import limit because the
  phenomenon is not zonal. Prior art (Far_West REVERTED, WP-A DEFERRED) reached
  the same wall.

Keeper UNCHANGED. The 2023 tail residual is the energy-offer / RT-re-offer-conduct
bound (no 2023 SCED source) — now confirmed a fifth and sixth way.

## 1. ERCOT-103 — reserve-demand right-sizing (Lane 2)

### 1.1 The measured decomposition: the tail is 97% energy dual

ERCOT publishes the settled RT scarcity components directly
(`data/raw/ercot/ercot_2023_ordc_reserves_hourly.parquet`: `system_lambda`,
`rtorpa`, `prc`). Decomposing the settled price (RTSPP = SPP + RTORPA) at the
2023 tail:

| settled band | hrs | settled | system λ (ENERGY) | RTORPA (RESERVE adder) | PRC held |
|---|---|---|---|---|---|
| > $100 | 387 | $604 | $585 (**97%**) | $19.5 (3%) | 5,637 MW |
| > $300 | 146 | $1,349 | $1,307 (**97%**) | $42.1 (3%) | 5,496 MW |
| > $1000 | 62 | $2,406 | $2,340 (**97%**) | $65.8 (3%) | 5,273 MW |

**97% of the 2023 scarcity price is the energy dual (system λ), only 3% is the
reserve adder (RTORPA).** This is the hard ceiling on any reserve-side mechanism:
even a *perfect* RTORPA reproduction adds ~$42 at the >$300 tail, leaving the
~$1,265 energy-dual gap untouched. The real market held only ~5.5 GW of reserve
(PRC) in scarcity and priced it small — it priced scarcity through **energy
offers**, not the reserve adder. (This is why the ercot41/43 on-line-capacity
envelope over-fired: it forced the energy dual up through a reserve-shortage
mechanism reality did not use — a high number reached through an unreal
mechanism, rule 1.)

### 1.2 The faithful vehicle (realized-room RTORPA) under-fires — REJECTED probe

The clean structural right-sizing (ercot43 §7.4's "reserve-demand side") is the
post-solve realized-room RTORPA (`ercot_ordc_only_scarcity` + envelope as a
pricing-only basis, in-LP ORDC total-reserve span OFF): it prices the *realized*
reserve like reality's RTORPA and cannot over-fire/shed load. Probed 2023
(`2026-07-24-ercot103-realized-adder-rtorpa`, replay of the margin keeper with
`ercot_ordc_only_scarcity=true`, `ercot_ordc_total_reserve=false`,
`ercot_online_capacity_envelope_extreme=true`):

| metric (2023) | keeper | realized-adder probe |
|---|---|---|
| C3a (hub-basis, `ercot99_score_probe`) | −16.8% ($40.2) | **−24.4% ($36.6)** |
| C3a (zonal-basis, `ercot101_price_decomp`) | −27.3% ($46.8) | **−35.5% ($41.5)** |
| C3c settle tail (200) | 76/181 | **71/181** |
| model priced > $300 | 42 h | **20 h** |
| realized RTORPA at price>$300 | (in-LP) | **$18** (max $130) |

It **regressed both C3a and C3c.** Root cause: under `ercot_ordc_only_scarcity`
the RegUp/RRS withheld families drop from the VOLL step to the plan-hold epsilon
(`reserves/spec.py:1016-1033`), removing the keeper's *only* tail-formation lever
(the reserve co-opt binding at VOLL — ERCOT-102 §2), and the faithful RTORPA does
not compensate. Worse, the model's realized RTORPA is only **$18** — *below* the
measured $42 — because the model carries phantom headroom (ERCOT-102), leaving a
*larger* realized reserve room than reality, so the ORDC curve prices it lower.
`ercot102_reserve_slack` on the probe: model priced scarcity in 20 h (keeper 42),
reserve binds 14/56 hits (keeper 52/59).

### 1.3 The reserve-side is exhausted

Three mechanisms, three outcomes, one wall:
* **in-LP ORDC span + envelope** (ercot41/43): OVER-fires ($347/$455, C3a +708%).
* **realized-room RTORPA** (this probe): UNDER-fires (C3a −24.4%, 20 tail h).
* **keeper reserve-VOLL co-opt**: least-bad proxy (C3a −16.8%, 42 tail h) but
  still under-fires — it cannot reach an energy-offer tail.

No reserve-demand representation closes a tail that is 97% energy dual. The
right-sizing is real market structure (the realized-room RTORPA is more faithful
than the 10.7 GW over-demand), but faithfulness here means abandoning the only
proxy that forms *any* tail — so it is not adopted (it regresses). The frozen
ORDC-curve constants are untouched (rule 26); no parameter was swept to a price.

## 2. ERCOT-104 — West/Panhandle topology split (Lane 3)

### 2.1 Panhandle is already a zone; the gap is import-direction

ERCOT is already modeled with Panhandle as a distinct (load-free) zone
(`config/iso_configs.py`), and the West/Panhandle wind-corridor **export**
interfaces (WESTEX ~9,800 MW, PNHNDL ~2,680 MW, NE_LOB) are already
`TransferLink`s at measured GTC limits. The ERCOT-101 §3 residual (LZ_WEST
+$64 mean above HB_HUBAVG in 2025) is a *positive/import-direction* congestion
premium — the opposite regime from the export/curtailment case that the
**reverted Far_West split** and the **deferred WP-A** already ruled out (both
copper-plate no-ops behind a non-binding interface).

### 2.2 The congestion is nodal, not zonal — no measured zonal import limit

`ercot104_west_congestion_nodal` on the measured NP6-86 SCED binding-constraint
archive (`data/raw/iso-specific-transmission/SCEDBTCNP686_*2023.parquet`):

| kind | example constraints | shadow price | limit |
|---|---|---|---|
| **ZONAL interfaces** (already modeled) | WESTEX $5.44, PNHNDL $19.10, NE_LOB $20.79 | mean **$15** | 1,100–9,800 MW (export) |
| **NODAL station-to-station** | KINGNW $5251, VERN_69T1 $3294, LYTTON_S $3256, 531T531 $3284 | mean **$3,387** | **60–518 MW** |

The congestion rent is ~200× larger on the nodal 138/345 kV station lines than on
the zonal interfaces. The West scarcity premium is **nodal congestion below zonal
resolution** — a 7-zone reduced network structurally cannot form it, and there is
**no measured zonal import limit** to build a split on because the phenomenon is
not at a zonal boundary (rule 11: prefer measured data — but a split needs a
measured *zonal* limit, which does not exist here). Building a split on an
*estimated* import limit is exactly the copper-plate no-op the prior art proved.

### 2.3 It also would not touch the load-bearing year

The §3 congestion is a 2025 effect (LZ−hub +$64 mean); the load-bearing 2023 tail
has only +$15 congestion (`ercot101_price_decomp`), and 2025's C3a/C3b already
PASS (only the supporting C3c fails). A Tier-0 topology change (every keeper
baseline re-solves) to chase a supporting 2025 gate, via an unrepresentable nodal
phenomenon and an unmeasured import limit, fails the cost/benefit and rule-11
tests. **Blocked; not built.**

## 3. Synthesis — the frontier is closed on the reserve and topology sides

ERCOT-101 attributed the 2023 tail to RT re-offer conduct (no 2023 SCED source)
from the offer side; ERCOT-102 confirmed it from the reserve side (measured AS
already held, non-binding). ERCOT-103 now confirms it from the **settlement
decomposition** (97% energy dual; every reserve-demand form over- or under-fires),
and ERCOT-104 from the **congestion resolution** (the West premium is nodal, not
zonal). Two more candidate explanations — an under-held/over-demanded reserve, and
an unformed zonal congestion — are eliminated. The residual is the energy dual set
by real-time energy offers, for which no 2023 measured source exists; per rule 1
it stays attributed, not tuned. The realistic route off NOT-YET remains the
owner-signed C6 governance attestation (CALIBRATED-WITH-CAVEATS), now backed by
four independent confirmations of the bound.

Next number: ercot-105.
