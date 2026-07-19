# CAISO 43 — zero-curtailment diagnosis + gas-floor demonstration probe

**Date:** 2026-07-01
**Branch:** `claude/caiso-43-curtailment-g6jjhz`
**Keeper at start:** `2026-07-01-caiso-42-atc-hydro` (corridor ATC forward + EIA-930 monthly hydro)
**Probe bundle:** `results/calibration/caiso43_gasfloor_probe` (3-yr, DIAGNOSTIC — **not a keeper**, see §5)

## TL;DR

The caiso-42 keeper curtails **0 TWh** of solar and prices **0 negative hours** because
the model is **never long midday** — its dispatch is short and importing, so a priced
import/gas tranche is always marginal and no curtailed-solar / export tranche can set a
sub-SRMC price. This session **confirmed and quantified** that diagnosis and **refuted the
four candidate causes** the handoff flagged (export pathway, export-only interchange
shaping, storage, dump cost). The single lever that makes the model long midday — the
measured-EIA-930-`NG:NG` gas-commitment floor — is a **rule-#11 pin to a measured outcome**
(it returns `None` for any forward year), so it is admissible only as a **default-off
diagnostic probe**, never a keeper. The keeper **caiso-42 stands**; closing the miss
cleanly needs a new mechanism (§6), not one of the existing flags.

## The system is short midday, not long (confirmed, 2024)

Reproduced the keeper config for 2024 (`caiso43_diag_base`; the keeper bundle carries no
dispatch parquets). Metrics from `scripts/probes/_caiso_floor_ab.py`:

| 2024 | model (keeper cfg) | reference |
|---|---|---|
| annual gas TWh | 77.8 | EIA-923 67.7 |
| net import TWh | +25.5 | — |
| **export hours %** | **0.0 %** | CAISO exports midday |
| **spring (Apr–May) midday gas MW** | **1,829** | EIA-930 `NG:NG` **6,834** |
| spring midday net import MW | **+659 (import)** | CAISO net-exports midday |
| LMP mean | 44.8 | actual RT ~33 |
| LMP min | 1.4 | actual da min −40.7 |
| spring LMP mean (Apr/May) | 37/35 | actual RT 13.5/10.9 |
| negative-price hours | 0 | present |

The overprice is a **spring-midday floor**: Apr/May midday the model runs only **1.8 GW gas
and imports +0.7 GW** to stay balanced, so its marginal is a ~$41 gas-CC SRMC
(HR×commodity-gas $3.38 + CARB ~$13 + VOM) or a ~$28 import tranche — never a curtailed-solar
/ export price. Real CAISO runs ~6.8 GW gas midday (RA/min-down committed, infra-marginal)
and **exports** its surplus, so curtailed solar sets the ~$0 price.

### Diurnal shape — the miss is concentrated in spring

Annual-average midday (h11–14) gas is actually **~5.9 GW** — close to the EIA-930 ~6.8 GW —
so the fleet is *not* globally under-committed midday. It **collapses to 1.8 GW only in
spring**, where the solar belly is deepest and load lowest. Imports never fall below ~2 GW
even at the solar peak: the cheapest import tranches (PNW hydro $28, Mid-C $36) beat domestic
gas-plus-CARB ($41+), so the LP always takes ~2 GW of cheap hydro and fills the rest with the
minimum gas the balance requires.

## The four hypotheses — all refuted

1. **Corridor ATC forward blocking exports? NO.** `build_caiso_corridor_flow_groups` is built
   one-sided (import envelope only) under `caiso_corridor_atc_forward`; the **export direction
   keeps the physical TTC** (PNW 4,800 / DSW 10,623 MW). ~15 GW of export headroom is open and
   unused. The `export_envelope` (export cap) path only engages under the *separate*
   `caiso_corridor_flow_limit` flag, which is off.
2. **`interchange_shaping_export_only` the missing piece? NO — byte-identical.**
   `caiso43_diag_exponly` (keeper + `--interchange-shaping-export-only`) matched the base on
   **every** metric (gas 77.8, export 0.0 %, spring-mid gas 1,829, LMP mean 44.8, min 1.4).
   Export-only shaping only re-scales the export *sink's* availability envelope; when the
   model never wants to export, capping the sink changes nothing.
3. **Storage absorbing the midday surplus? Not the cause.** Midday battery charging on cheap
   solar is realistic (real CAISO charges midday too) and cannot explain a *short* system —
   the model imports +0.7 GW at spring midday, i.e. it has *no* surplus for storage to hide.
4. **Dump cost too high? NO.** `dump_cost = max(ε, −min_renewable_mc + ε) ≈ $20` (the
   negative-solar-offer magnitude), but the `export_curtail` sink is **$0** and `export_solar`
   is **$8**, both far cheaper than dump — so the LP would export/curtail long before dumping.
   The sinks are simply never used because the model is short.

Every path converges on the same root: **longness**. The whole
curtailment→negative-price stack (`caiso_solar_endogenous_spill`, `negative_renewable_offers`,
the $0/$8 export sinks, the ~$20 dump) is correct and *downstream* of longness — it fires only
once domestic must-take + committed gas exceeds load, which never happens at spring midday.

## The RA must-offer bridge is on but insufficient in spring

`caiso_ra_mustoffer` (min-load 0.26) **is** applied in the keeper — the P2 pass runs even with
`commitment_enabled=False` specifically to inject `caiso_ra_mustoffer_min_gen`. It holds a
merchant CC/CT at min-load only across a midday idle gap **shorter than its min-down time**.
The spring belly (~7 h) exceeds CC min-down for most units, and the economics decommit gas in
the morning shoulder too (cheap hydro imports beat gas), so few units qualify for a bridge and
spring-midday gas collapses to 1.8 GW. The bridge is behaving as designed; it is not the wrong
mechanism, it is just too weak for the deep spring belly, because the LP (no MIP, no startup
cost on a continuous ramp) freely cycles gas that a real unit-commitment would hold online.

## 5. Gas-floor demonstration probe (3-yr) — what longness delivers, and why it is not a keeper

Config: keeper (`--priced-interchange --caiso-corridor-atc-forward --hydro-eia930-monthly`,
`negative_renewable_offers` default-on) **plus** `--caiso-gas-commitment-floor
--caiso-gas-floor-frac 0.8` — the only lever that makes the model long midday. Bundle
`caiso43_gasfloor_probe` (2023 2024 2025). It is a **rule-#11 diagnostic** (the floor pins the
gas fleet to 0.80 × the *measured* EIA-930 `NG:NG` shape, which `measured_gas_floor_profile`
returns `None` for on any forward year), registered on the dashboard as a probe, **never a
keeper**. Its purpose is to quantify (a) that the curtailment / negative-price stack fires once
the model is long, and (b) the gas-inflation cost that makes the pin inadmissible.

Dashboard id `2026-07-01-caiso-43-gasfloor-probe`. `calibration_verdict` → **NOT-YET** (and
worse than the keeper where it counts). The mechanism fires exactly as designed, but the price
gain is **bought by padding gas**:

| 2024 | keeper caiso-42 | gasfloor probe | direction |
|---|---|---|---|
| spring (Apr–May) midday gas MW | 1,829 | **5,510** (EIA-930 6,834) | model goes long ✓ |
| LMP min | +1.4 | **−20.0** | negatives appear ✓ |
| spring LMP p5 | +27.2 | **−20.0** (actual da p5 −10) | floor collapses ✓ |
| C3a mean LMP | +36.9 % | **+31.0 %** | body better ✓ |
| C3b shape NRMSE | 0.516 | **0.459** | shape better ✓ |
| **C1 CC_REGULAR vol** | +9.57 TWh (+3.3pp) | **+12.48 TWh (+4.3pp)** | mix **worse** ✗ |
| annual gas vs EIA-923 (67.7) | 77.8 (+15 %) | **80.8 (+19 %)** | gas **padded** ✗ |
| C5a CO2 | ~PASS | **+11.6 %** | **worse** ✗ |
| C3c scarcity >$200 | 0 h (vs 35) | 0 h | tail unchanged (AS territory) |

All three years show LMP min = **−$20** — the `negative_renewable_offers` tail fires the moment
the floor makes the model long, and curtailed solar sets the sub-SRMC price. So the whole
curtailment→negative stack is **structurally correct and only waiting on longness** (the point
of the probe). But the floor delivers longness by holding ~3.7 GW extra gas at spring midday
that then **pads the annual mix** (CC_REGULAR over-run and CO2 both rise), on top of being a
measured-`NG:NG` pin. That is precisely CLAUDE.md rule #1's "reach the right number through a
mechanism that isn't real" plus rule #11's forbidden measured-outcome pin — so the probe is a
**diagnostic, not a keeper**, and **caiso-42 remains the keeper**. Export hours stay 0 % even
here: the surplus is absorbed as *curtailment* (solar spilled at −$20) and reduced imports, not
net export — the model reaches "long enough to curtail" but not "long enough to net-export,"
because ~2 GW of $28 PNW-hydro imports stay in the stack midday.

## 6. Recommendation — the next clean mechanism

The clean bridge is insufficient and the effective floor is a measured-outcome pin, so the gap
between them is exactly the **LP-vs-unit-commitment startup-cost gap**: a real CC committed for
the morning and evening ramps stays online through a 7 h spring belly because its **startup
cost exceeds the midday fuel saved by cycling off**, even though the belly is longer than its
min-down time. The LP, ramping a continuous variable from 0, pays no startup cost and cycles
freely. MIP is forbidden (CLAUDE.md Stack), so the admissible fix is a **startup-cost-aware
extension of the RA bridge** (`caiso_ra_mustoffer_min_gen`): today it floors a CC only across a
gap **shorter** than min-down. Extend it to also floor a gap **longer** than min-down when
cycling is uneconomic, using the standard UC restart economics:

```
bridge the gap when   startup_per_mw  >  (MC[g] − LMP_gap) × min_load_frac × gap_hours
```

The right-hand side is the *net* cost of holding the unit at min-load through the gap: the
min-load energy is not spilled, it **displaces the marginal import/gas at the gap-hour LMP**,
so the net cost is only `(MC − LMP)`, not the full `MC`. When gas is near-marginal
(`MC ≈ LMP`) the RHS collapses toward zero and even a small startup cost holds the unit online
— exactly why real CAISO keeps ~6.8 GW gas committed through the spring belly. Every input is
forward-derivable (startup cost, min-load heat rate, commodity gas, CARB) and the LMP is the
model's own P1 dual — **no measured-generation pin**, so unlike the `NG:NG` floor this would be
**keeper-eligible**.

Risk to control in caiso-44: the P1-LMP feedback must not become a residual fit, and the extra
commitment must **export/curtail** (not pad annual gas past EIA-923). Needs its own flag,
default off, unit test on the restart-economics inequality, and a 3-yr before/after on
mix-vs-EIA-923 + monthly LMP before promotion. That is the recommended caiso-44 workstream —
deliberately **not** attempted here, because a subtly-wrong commitment criterion would silently
inflate gas or fit the residual (rule #1/#11), and it needs the full test+validation loop a
new market mechanism warrants.
