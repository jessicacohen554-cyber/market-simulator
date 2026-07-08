# G-31 — staged over-supply thinning + limited-foresight dispatch on the ERCOT capacity hindcast (2021→2025)

_Generated 2026-07-08 · gap-register G-31 (follow-on to G-30) · forecast-side,
NON-KEEPER probe · no quarantine touched (2022/2026 bridged, not solved/read)_

**Question (G-31):** the G-30 `entry_lookahead_reprice` arm cut ERCOT hindcast
over-retire 22.8 → 15.8 GW but left the **13.96 GW coal false-retire
untouched** — that first (largest) coal wave is decided in the quarantined 2022
bridge on the 2021 raw dual (ORDC ≈ 0 on the un-thinned over-supplied fleet),
before any admissible forward signal reaches the screen. Does a **limited-
foresight dispatch** screen (in-year LP forms scarcity) and/or a **staged
vintage-over-supply thinning** (spread the first coal wave into lookahead-priced
years) drop the coal false-retire **from the LP regime**, not a floor/adder?

**Answer (one line):** **staged thinning does — the coal false-retire drops from
13.96 → 6.5 GW** by holding the marginal coal online long enough to reach the
lookahead-priced years (2024 then retires *nothing*). But **in-year scarcity
still never forms** (ORDC $0.00 every year): the retention is carried by the
G-30 lookahead *pro-forma*, not the in-year dispatch LP, and the
limited-foresight-dispatch lever is **inert on storage-poor ERCOT**. Net: the
first-wave problem is closed by *timing* (staging → lookahead), not by making
the over-supplied in-year LP tight.

## Runs (both registered on the forecast-validation dashboard)

| run | arms | role |
|---|---|---|
| `ercot-2021-2025-realized-g31lookonly` | `entry_lookahead_reprice` | control (reproduces g30lookahead exactly; rule-20 ablation twin) |
| `ercot-2021-2025-realized-g31staged`   | `entry_lookahead_reprice` + `staged_oversupply_thinning` (3 GW/fuel/yr) + `limited_foresight_dispatch` | corrective arm |

Both ERCOT CAMPD-per-plant, realized fuel, 2020 vintage, evolve 2021→2025, 2022
bridged, 2023–2025 scored. The two differ only in the two new G-31 arms (their
ablation twin, rule 20). Zero fitted parameters in either arm (rule 13).

## Does scarcity form in-year? NO — the limited-foresight lever is inert here

**In-year ORDC overlay: $0.00 in every year, both runs.**

```
control g31lookonly  2021/2023/2024/2025: mean $0.00, >$10 in 0 h
staged  g31staged    2021/2023/2024/2025: mean $0.00, >$10 in 0 h
```

`limited_foresight_dispatch` bounds the in-year LP's storage/hydro foresight to
a within-day cycle so peak hours can tighten — but the ERCOT **2020 vintage
carries negligible storage (and 0.5 GW hydro)**, so there is essentially no
cross-day foresight to remove, and staging keeps the *thermal* fleet **fuller**
(un-thinned) than the control, so reserves never fall into the ORDC curve's
steep region. On a genuinely ~22 GW over-supplied vintage fleet there is no
in-year scarcity for any dispatch mechanism to price — the lever is structurally
sound but has no purchase on this fleet. (It is retained default-off for
storage-rich ISOs / later forecast years, where cross-day arbitrage is real.)

## Does the coal wave spread? YES — and the false-retire drops by more than half

Per-year economic coal retirement (GW), staged vs control:

```
year          control (lookonly)              staged (3 GW/fuel/yr)
2022* bridge  coal 13.96  (whole wave)        coal 3.03   (capped; 10.9 GW deferred)
2023          gas_st 1.87                     coal 3.43, gas_ct 3.02, gas_st 3.24
2024          (no retire)                      (NO RETIRE — lookahead retains)
2025          (no retire)                      (NO RETIRE — lookahead retains)
* 2022 = quarantine bridge (evolved, never solved/read)
```

**Coal false-retire: control 13.96 GW → staged 6.47 GW** (a 54 % cut).
The mechanism is exactly the G-30 first-wave fix: capping exits at 3 GW/fuel/yr
holds the marginal coal online through 2022–2023, so it survives into 2024 — the
first year whose screen consumes a *solved* prior year (2023) **plus** the
lookahead pro-forma — and that year retires **nothing**. Staging converts the
un-priceable first wave into exits the forward signal can adjudicate.

**But the total over-retire barely moves (15.83 → 12.73 GW), because staging
trades coal exits for gas exits.** Holding the coal fleet online depresses
energy prices further, so gas that survived in the control now retires up to its
own 3 GW/fuel cap: gas_st 1.87 → 3.24 GW, gas_ct 0 → 3.02 GW. The coal *gate*
improves markedly and the retired-unit **recall band flips FAIL → PASS** (the
units it retires better match the ~1.5 GW that actually left), but the
system-level over-retire is only ~3 GW better — the over-supply is redistributed
across fuels, not resolved.

## The tension: staging weakens the very signal that retains

Because staging keeps the fleet fuller, the lookahead pro-forma it feeds is
**weaker** than the control's each year (a fuller stack → less pro-forma
scarcity):

```
lookahead pro-forma        control            staged
2023 → 2024 screens        $253.57/MWh        $127.14/MWh   (>$200: 636 h → 334 h)
2024 → 2025 screens        $ 78.28/MWh        $ 48.55/MWh   (>$200: 170 h →  87 h)
```

So staging and the lookahead pull in opposite directions: staging *needs* the
lookahead to retain the coal it holds online, but by holding it online it
*dilutes* the lookahead. The 6.5 GW residual coal exit (2022–2023) is exactly
the part that retired before the fleet had thinned enough for even the diluted
lookahead to price. This is the honest limit of the timing fix.

## Cost: the un-thinned fleet balloons the LP

Staging keeps ~10–23 GW of extra capacity online each year, so the per-plant LP
roughly doubles and the cold solve time explodes:

```
per-year cold solve   control ~5 min      staged  2023: 9.5 min · 2024: 22 min · 2025: 60 min
```

The staged 5-year run took **~2.7 h** wall-clock (2025 cold solve alone 3598 s)
vs the control's ~18 min — the un-thinned fleet grows every year as deferred
units accumulate, so the LP swells monotonically. At 3 GW/fuel/yr this is
impractical for routine use; a looser cap (5–6 GW/fuel/yr) would thin faster and
solve faster, at the cost of a larger first wave.

A practical signal that 3 GW/fuel/yr over-throttles exits on this fleet — the
fleet never approaches adequacy, which is *also* why in-year scarcity never
forms.

## Scorecard: control vs staged vs actual

| metric | control | staged | actual |
|---|--:|--:|--:|
| thermal retired GW (2021→25) | 15.83 | **12.73** | 1.53 |
| — coal | 13.96 | **6.47** | 0.93 |
| — gas_st | 1.87 | 3.24 | 0.0 |
| — gas_ct | 0.0 | 3.02 | 0.50 |
| retired-unit recall >300 MW band | FAIL | **PASS** | — |
| solar added GW | 4.0 | 4.0 | 25.08 |
| gas_ct added GW | 6.0 | 6.0 | 3.69 |

(Additions are identical between the two arms: the coal drop did **not** unlock
more solar entry — staging's weaker lookahead carries no extra entry signal.)

## Verdict

- **Staged thinning closes the first-wave problem the G-30 finding identified**,
  from the LP regime, not a floor/adder: it is a per-fuel exit *rate* cap
  (mirrors `ccs_retrofit_max_gw_per_year`), zero fitted parameters, and the
  retain/exit call stays the screen's. Coal false-retire drops 13.96 → 6.5 GW.
  **Retained** as a forecast-side corrective arm (default-off).
- **The primary ask — a limited-foresight *dispatch* screen that makes the
  in-year LP form scarcity — did NOT bite on ERCOT.** The 2020 vintage is
  storage/hydro-poor, so the within-day foresight bound removes almost nothing,
  and the over-supplied fleet never tightens. In-year ORDC stayed $0.00 in every
  year. The lever is kept (structurally correct for storage-rich ISOs) but is
  **inert on this fleet** — reported honestly, not tuned to a number (rule 11).
- **The retention that dropped coal is the G-30 lookahead pro-forma, not in-year
  dispatch scarcity.** Staging's job was purely to *delay* the exits until the
  lookahead could price them; it does not itself create scarcity.
- **Residual root cause (next step), not a fit target (rule 11):** the ~6.5 GW
  coal that still exits does so in 2022–2023, before the fleet thins enough for
  even the diluted lookahead to retain it — and the fleet never thins to
  adequacy because staging deliberately holds it full (the LP-bloat / no-in-year-
  scarcity price of that). The genuine forward fix is not more staging nor an
  adder but a **measured-admissible forced-outage model** (EFORd-based correlated
  derating, e.g. cold-snap/Uri-type events) so tight hours form *physically* in
  the in-year LP — the over-supplied vintage fleet's realized availability is too
  high in forecast mode, so the scarcity that really happened (Winter Storm Uri
  2021) is absent and the LP clears every hour with ample reserves. That is the
  structural direction that would let in-year scarcity form without keeping the
  fleet artificially full.

**Honesty gate met:** no scarcity was manufactured by an adder tuned to a
retirement number. The coal drop comes from a structural exit-rate cap feeding
the zero-DOF lookahead pro-forma; the in-year ORDC stayed exactly $0.00
throughout, reported as-is.
