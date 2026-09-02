# PRE-DECLARATION — capx D43: the CAISO dispersion-carrying entry expectation

**Stage 1 (§2) pushed BEFORE the screen-grain probe ran; Stage 2 (§3, the T1-H
composition consequence) appended and pushed BEFORE the arm solve started.**
Graded at full magnitude, misses included, in
`FINDING-capx-d43-caiso-dispersion-2026-09-02.md`.

**Lane:** capx D43 — the first repair measurement on D39's object
(`FINDING-capx-d39-entry-underbuild-2026-09-02.md` §0/§3.1/§7.2): the entry
stack under-builds through ONE term, the energy leg's DISPERSION, which the
zone-flat tail-free stack re-price discards. CAISO first, per D39 §7.2.
Branch `claude/capx-d43-caiso-dispersion`; mechanism commit `9b0174b3`
(`entry_dispersion_expectation_signal`, gated default-off, zero DOF — the
construction and its properties are in that commit's field comment and
`runner._dispersion_expectation_signal`).

**Rule 13 / rule 21 discipline (binding).** The construction has NO parameter:
each zone's realized price-duration curve, indexed by the entering year's
stack-headroom rank on the current year's. Nothing below was, or could be,
sized by a residual, a corridor row, AEO, or any band. The realized surface
used at the screen grain is D39 §2's labelled keeper stand-in
(`caiso231_b1_ungrounded`, 2023–2025 training years), and it is CONTEXT for
the closure table, never a target — the arm is scored on what it says versus
what the model itself paid, and the miss is reported whichever way it falls.

## 1. The runs

```
# screen grain (zero solves) — the D39 basis dumps + keeper duals
uv run python scripts/probes/entry_signal_d43_dispersion_replay.py --mode basis \
  --bundle results/hindcast/caiso-2021-2025-realized-dumps \
  --duals-bundle results/calibration/caiso231_b1_ungrounded \
  --out results/calibration/entry_signal_d43_dispersion_replay_caiso.json

# control: the D39 basis recipe at HEAD (bare invocation + the output-only dump flag)
uv run python scripts/run_capacity_hindcast.py --iso CAISO --start-year 2021 --end-year 2025 \
  --entry-screen-diagnostics --out-dir results/hindcast/caiso-2021-2025-realized-t1h-d43-control
# arm: exactly one solve-affecting field differs
uv run python scripts/run_capacity_hindcast.py --iso CAISO --start-year 2021 --end-year 2025 \
  --entry-screen-diagnostics --entry-dispersion-expectation-signal \
  --out-dir results/hindcast/caiso-2021-2025-realized-t1h-d43-dispersion
```

Both legs registered SUFFIXED on the forecast dashboard; the bare
`caiso-2021-2025-realized` sidecar and every verdict key are untouched.

## 2. Pre-declared outcomes — screen grain (the D43 probe on the D39 basis)

The instrument is `scripts/probes/entry_signal_d43_dispersion_replay.py --mode basis`
on the committed D39 basis dumps (`caiso-2021-2025-realized-dumps`, key
`af508406`) and the keeper `caiso231_b1_ungrounded` hourly sidecars (prior-year
duals for the constructions; entering-year duals as the realized surface —
D39 §2's labelled stand-in). Every number below is D39's or the committed L-1
replay's (`entry_signal_l1_dual_replay_caiso.json`, shipped arm), read before
the probe ran.

**PS0 — the gates.** The shipped arm reproduces the committed L-1 replay's
thermal energy legs and storage margins to rounding; the reconstructed
current-year headroom passes its gate (implied prior-year VRE ≥ 0, corr > 0.9
with the dump's VRE potential, the stack re-prices its own net load exactly);
the construction reproduces each zone's price multiset at unchanged headroom.
*Falsifier:* any gate fails — then no arm row is reportable.

**PS1 — the dispersion arrives, and it is the duals' own.** At entering-2024
the shipped daily top-4/bottom-4 spread is **12.71 $/MWh**; the arm's is
**≥ 25** (the 2023 keeper surface carries 34.1 on the load-weighted mean,
D39 §2; the rank map re-pairs hours within days so some of it can move
between days). Hours ≥ $100 on the system mean: shipped **0** → arm
**≥ 300** (the 2023 surface carries 708 on the 7-zone LW mean). Mean hourly
cross-zone spread: shipped **0.00** → arm **> 0** (in distribution, each zone
keeps its own duration curve). At entering-2025: shipped spread 14.4 → arm
≥ 20; hours ≥ $100 shipped 0 → arm **50–120** (the 2024 surface carries 85).
*Falsifier:* the arm's daily spread stays below 20 at entering-2024.

**PS2 — the sign flips, and which of the replay's flips reproduce.** D39 §7.2
pre-declares on the L-1 replay's flips (raw 2023 duals at entering-2024:
gas_cc − → +, solar − → +).
* **gas_cc at entering-2024 flips − → +** (shipped −$82.7k; raw duals +$66.6k;
  comonotone coupling of the zonal rows cannot lower a convex functional of
  the zone-mean below the hour-aligned value at unchanged headroom, and the
  2024 headroom rank shift is small).
* **gas_ct at entering-2024 stays −** but its energy leg rises from $1.1k to
  **≥ $100k** against a $128.1k fixed cost (raw duals: $116.9k); a + is
  possible, not predicted.
* **solar at entering-2024 does NOT flip** — this is where the construction
  differs from the raw duals on purpose: the rank map pairs solar's hours
  (the lowest net-load / highest-headroom hours of the CAISO duck) with the
  trough of each zone's duration curve, so the zone-row capture ratio falls
  from the raw-dual arm's 0.82 to **≤ 0.75**, below the shipped 0.90, toward
  the realized 0.63 (D39 §2) — the real cannibalization the stack cannot see.
  At LCOE $41.86 and a $0 attribute credit in the replay's basis (EAC only),
  the margin stays **−**.
* **wind stays +** at both steps (capture ratio ≥ 0.85; LCOE $31.82).
* **Storage: no technology clears at either step** (D39 §7.2's kill gate).
  li-ion 4 h arbitrage rises from the shipped $2.9k / $4.1k to **$20–45k**
  (raw duals $29.2k / $24.6k; the realized 2024/2025 surfaces pay $35.5k /
  $35.7k) against a $148.5k cost and a $46.6k RA credit — D-9's value-stack
  residual, stated before the number so it cannot be traded.
*Falsifiers:* gas_cc does not flip; or solar's capture ratio under the arm is
NOT below the raw-dual arm's 0.82.

**PS3 — the closure table: the one-signed UNDER-expectation closes, and the
residual is the prior year's LEVEL, with the opposite sign where the prior
year was tighter.** Expected ÷ realized energy leg (D39 §3.1 basis, zone-mean
Σ max(p − vc, 0) at the screen's own vc; realized on the entering-year keeper
surface):
| entering | tech | shipped (D39) | arm, pre-declared band |
|---|---|---:|---|
| 2024 | gas_cc | 0.92 | **2–4** (over: the 2023 surface has 708 h ≥ $100 vs 2024's 85) |
| 2024 | gas_ct | 0.07 | **≥ 3** (over, same reason — the peaker IS the tail) |
| 2025 | gas_cc | 0.07 | **0.8–2.0** (2024 → 2025: similar levels, 85 vs 0 h ≥ $100) |
| 2025 | gas_ct | 0.00 | **≥ 5** (2025 realized $413/MW-yr: the 2024 tail over-expects it) |
Storage arbitrage ratio (li-ion 4 h): shipped 0.08 / 0.11 → arm **0.6–1.3** at
both steps. Solar capture: shipped 0.90 / 0.84 → arm within **±0.12** of the
realized 0.63 / 0.64.
The reading this pre-commits to: the dispersion term is closed by
construction (the arm's expected side carries the realized shape), and what
remains is the LEVEL of the prior year — a naive-expectations / fuel-lag term
(2023 gas $ vs 2024's $3.39) that no dispersion construction touches and that
the shipped stack carries too (it prices S on this year's `mc_cost`). An
over-expectation at 2024 is therefore NOT a failure of the construction; it
is the level term now visible with its own sign.
*Falsifier:* any 2024 ratio under the arm is **below** the shipped ratio
(the arm would then have discarded dispersion rather than carried it).

**PS4 — the hour-aligned composition arm (`fwd_expectation_prior_solve`,
computed offline for comparison, not a lane object) lands within ±15 % of the
raw-dual arm on every energy leg** — CAISO's demand and stack move little
between 2023 and 2024, so its delta is small; it keeps the raw duals' solar
flip (hour alignment leaves solar's hours where 2023 priced them).
