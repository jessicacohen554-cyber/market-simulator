# FINDING (caiso-86b partial import ladder, 2026-07-16): the PARTIAL four-rung measured ladder ALSO fails the LOYO honesty gate — and so does its gas-indexed (implied-heat-rate) form — because the WECC rung prices ride a gas × hydro regime mix a 3-year sample cannot identify as a stable forward rule; the measured-ladder-PRICE lane is closed and the soft-month lane moves to the caiso-82 §3 clean-depth composition mechanism

**Session:** caiso soft-month lane, 2026-07-16 (handoff Lane A1). **Derive-first,
no LP solved.** Follow-up to
`FINDING-caiso86-import-ladder-gates-2026-07-15.md` §4, which left the partial
(four-rung) ladder as the one admissible-looking variant.

## 1. What was attempted

`scripts/derive_caiso_import_tranches.py --partial` (new mode, this session):
the caiso-86 Q-Q duration-coupling derivation unchanged, with the honesty
gates scored on the four year-stable rungs only (PNW_hydro_base, PNW_midC,
DSW_CCGT, DSW_CT). DSW_solar_PV is still derived and printed but excluded —
in the partial design it would keep its static value as an explicitly-labelled
price-taker floor, so its derived-price stability is not load-bearing.

## 2. Gate results — FAIL

Year-stability (CV ≤ 0.20) PASSES on the four-rung subset (0.18/0.16/0.16/0.17),
but LOYO (worst held-out rung error ≤ 25%) FAILS:

| held-out | PNW_hydro_base | PNW_midC | DSW_CCGT | DSW_CT | worst |
|---|---|---|---|---|---|
| 2023 | 30.5% | 24.1% | 25.6% | 29.1% | **30.5% FAIL** |
| 2024 | 10.7% | 11.9% | 6.5% | 10.7% | 11.9% ok |
| 2025 | 17.3% | 45.5% | 19.6% | 17.7% | **45.5% FAIL** |

The 2023 miss is BROAD-BASED — all four rungs 24–31% high-side (2023 was a
high-West-gas year; every rung's revealed price was elevated), and 2025's is
the PNW_midC drop (90.5/89.1 → 62.0 $/MWh). A pooled static $/MWh ladder
cannot carry a fuel-price regime change; the LOYO gate correctly detects it.

## 3. The gas-indexed form fails harder

The broad-based 2023 elevation suggests the natural repair: derive an implied
HEAT RATE per rung (derived price ÷ year-mean measured gas) and let the
forward ladder ride the year's gas price (forward-reproducible from gas
forwards). Tested against three measured gas series (CA Composite daily
citygate spot — the caiso-84 keeper series; SoCal citygate weekly; PG&E
citygate weekly), same gates:

- CV: PNW_midC 0.34 and DSW_CCGT 0.21–0.34 FAIL on every series
  (PNW_hydro_base/DSW_CT pass on CA-composite and PG&E).
- LOYO: held-out 2023 worst 44.5–71.6% FAIL, held-out 2024 worst 48.1–60.1%
  FAIL (all rungs miss ~35–70%, every series).

The CA gas halving (5.20 → 2.43 $/MMBtu year-mean, 2023→2024) OVER-corrects:
the rung prices only fell ~30%, not ~53%. The WECC hub price level is neither
a static $/MWh curve nor gas-proportional — it rides a gas × hydro/regional
conditions mix that three years cannot identify as a stable forward rule.
Testing further functional forms until one passes would be tuning the method
to the gate (the caiso-86 §3 prohibition); the enumeration stops here.

## 4. Disposition

**Lane A1 is CLOSED without a solve** (derive-first gate failure, both
admissible forms). The static-fitted $/MWh rungs remain labelled
STATIC-FITTED-PENDING-MEASURED (G-26 stays open — it can re-open if the
intertie-LMP source extends to enough years to identify the regime mix,
rule 23). `--partial` stays in the derive script as reusable gate
infrastructure.

The soft-month C3a lane therefore proceeds on the OTHER caiso-82 §3
mechanism — the one whose measured evidence IS year-stable: the import
ladder's carbon-wedge COMPOSITION. Beyond ~5.2 GW of clean-priced supply,
every model import MW pays the +$13–19 unspecified/fossil CARB rung, while
the measured CAISO−hub spread shows the real marginal import carries NO
carbon wedge in surplus-West hours (WEIM/EDAM GHG attribution assigns clean
resources to CAISO transfers), and the measured south-corridor
depth-in-surplus is year-stable (p95 4.7/5.4/5.5 GW, 2023/24/25 — banked in
caiso-82 §3). Clean DEPTH, not rung PRICE, is the measured quantity this
lane can ground on.
