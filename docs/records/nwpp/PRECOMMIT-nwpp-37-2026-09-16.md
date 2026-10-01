# PRECOMMIT — NWPP-37: move the EIA-930 `NG:` unit-slip screen to the frame seam

**Lane** NWPP-37 · **Base sha** `5a696353` (branch `claude/nwpp-37-envelope-screen-tscayg`)
**Date** 2026-09-16 · **Model** Fable · **DATA PROFILE** `nwpp`
**Charter** NWPP-DESK r#7b issuance notice. **No LP is run by this lane** (rule 32 `[R-SHARD]` (a)
is not even reached: there is nothing to solve).

## 0. Ordering of this record — stated rather than implied

The charter fixed the exit criterion before any work began (nine-region byte-identity, with the
SPP-41 control set named). This document records, in order:

* §1, the re-verification of the desk's diagnosis at **my own base sha** — collision rule 6, and the
  charter's first duty. `0d261bdd` (the notice's pin) is an ancestor of `5a696353`; 22 commits
  separate them, none touching `data/eia930`.
* §2, **my own enumeration and classification**, which is the lane's primary deliverable and which
  the charter explicitly told me not to take from the desk.
* §3, the shape decision, taken after §2 and after the frame-level census (§4 of the FINDING) but
  **before** the consumer before/after measurement that is the exit table. The decision rests on the
  enumeration and on a measured cascade property, not on whether the exit table came out clean.

Nothing here was rewritten after the result.

## 1. The defect, re-verified at base sha `5a696353`

`actuals._screen_fuel_spike_columns` is applied at exactly three call sites — `actuals.py:351`
(`_ercot_hourly_frame_screened`), `:412` (`load_eia_hourly_benchmark`), `:488`
(`load_eia_hourly_renewable_gen`) — and **all three are in `actuals.py`**. Its docstring claimed:

> "this seam screens the frame every reader in this module obtains, so no consumer can reach an
> unscreened copy (rule 19 `[R-ONE-MECH]`)"

`frames._eia_hourly_frame_filled` does no screening: it reindexes present rows onto the complete
hourly clock and returns. **Confirmed.** The claim is true of readers in `actuals` and false of
everything else.

## 2. Enumeration + classification — MINE, at base sha

`grep -rn "_eia_hourly_frame_filled" src/market_sim/` → **21 call sites**. Classified on the code at
each site, not on its docstring:

| module:line | reads | class |
|---|---|---|
| `eia930/envelopes.py:109` `measured_monthly_hydro` | `NG: WAT` | **FUEL — unscreened** |
| `eia930/envelopes.py:167` `_hydro_wat_month_hod` | `NG: WAT` | **FUEL — unscreened** |
| `eia930/envelopes.py:440` `measured_gas_floor_profile` | `NG: NG` | **FUEL — unscreened** |
| `eia930/envelopes.py:1050` `caiso_solar_fraction` | `NG: SUN`, `Demand` | **FUEL — unscreened** |
| `data/neighbor_price.py:396` `_neighbor_load` | `NG: SUN`, `NG: WND` (when `kind=="net"`) | **FUEL — unscreened** |
| `data/neighbor_price.py:574` `measured_intertie_hub_price_raw` | `NG: SUN`, `NG: WND` (when `load_shape_kind=="net"`) | **FUEL — unscreened** |
| `eia930/actuals.py:485` `load_eia_hourly_renewable_gen` | `NG: WND`, `NG: SUN` | FUEL — already screened |
| `eia930/envelopes.py:371` `measured_interchange_envelope` | `Total interchange` | TI — outside the screen by ruling |
| `eia930/envelopes.py:1639` `_eia930_net_interchange` | `Total interchange` | TI — outside by ruling |
| `eia930/envelopes.py:1883` `nwpp_net_interchange` | `Total interchange` | TI — outside by ruling |
| `eia930/demand.py:343,390,526,560,600,632,679,735` (8) | `Demand` only | demand — `_screen_demand_*`'s phenomenon, rule 19, NOT TOUCHED |
| `eia930/frames.py:295` `_pool_member_frames` | `UTC time` (pool clock) | clock only |
| `eia930/zonal_shares.py:384` | `UTC time` | clock only |
| `data/virtual_bids.py:274` | `Local time` | clock only |

**Count: SIX unscreened `NG:`-column readers, across TWO modules** (`envelopes`, `neighbor_price`).

**Against the desk's count — the desk over-counted, and said so.** r#7b named "SEVEN" in
`envelopes` plus `neighbor_price` ×2, and flagged `demand` ×8, `virtual_bids`, `zonal_shares` for
classification. Measured: of the seven `envelopes` sites only **four** read a `NG:` column — `:371`,
`:1639` and `:1883` read `Total interchange`, which the screen excludes **by ruling** (card P9), so
they are not unscreened readers, they are out of scope. `virtual_bids` and `zonal_shares` read only
a clock column. **All eight `demand.py` sites read `Demand` alone**: the docstrings there say the
renewable CF series are drawn from *the same frame*, which is a statement about a shared clock, not
a fuel-column read — the desk was right to warn, and the answer is that none of them is one.

The desk's warning that its list was partial was also right in the other direction: `neighbor_price`
is confirmed, and the two sites are conditional on `load_shape_kind == "net"`.

## 3. Shape decision — **(A), STRUCTURAL**, and the desk's read of the balance is correct

The charter asked whether I agree that the scope correction shifts the balance toward (A). **I do**,
and on a stronger ground than "a dozen patches is more than two":

1. **(A) is the construction the docstring already asserts.** (B) would leave a false claim true
   only by enumeration, re-falsified by the next module to read `frames`. Rule 24 in spirit: an
   unregistered reader is an unregistered channel.
2. **(B) cannot be made safe by being careful.** Two of the six sites are *conditional* fuel readers
   (`neighbor_price`, only when `kind == "net"`), so a narrow patch has to reproduce the branch
   condition at each site. That is six chances to get it wrong and no way to test the seventh.
3. **The screen is NOT idempotent** (measured, FINDING §7): a second application recomputes the
   p99.9 anchor with the flagged hours removed, which lowers it and can flag further hours. Under
   (B), a reader that is screened at its call site AND later inherits a screened frame cascades.
   Under (A) there is exactly one application point per constructed frame and the question cannot
   arise. This is the argument that actually decides it, and it is a property of the mechanism, not
   a preference.

Pre-registered condition, from the charter, unchanged: **take (A) if and only if it is
byte-identical for every pre-existing region; if it moves another region's series, name it, explain
it, and fall back to (B).**

## 4. Exit criterion, fixed before the measurement

* Frame-level census of what the screen flags, all nine regions × 2019-2026.
* Consumer-level before/after over every EIA-930-derived series the nine regions expose.
* NWPP is expected to move. Any other region that moves must be named and shown to be a defect
  repair rather than a behaviour change, or shape (B) is taken instead.
* Docstring repaired to describe the seam that exists.
* A test pinning the envelope path.
* Full `tests/unit/data` + `tests/regression` run, diffed against the same run at base sha, so
  "no new failures" is measured rather than asserted.

## 5. Files this lane touches

`src/market_sim/data/eia930/frames.py`, `src/market_sim/data/eia930/actuals.py`,
`tests/unit/data/test_eia930_fuel_spike_screen.py` — all inside FILES YOU OWN.

**One file outside that list**: `scripts/data/build_calibration_reference.py`, a **five-line
deletion plus its docstring**. That file applies the screen explicitly to each NWPP member after
`_eia_hourly_frame(member, year)`. Once the constructor screens, that application is the second one,
and it **cascades** (§3 item 3). Removing it is not scope creep — it is the charter's own shape-(A)
instruction ("delete the now-redundant per-call-site applications rather than leaving them stacked,
rule 19"), and leaving it would be shipping a measured regression into a committed artifact's
builder. Byte-identity of that builder's output after the deletion is proved in FINDING §8.

`envelopes.py`, `neighbor_price.py`, `virtual_bids.py`, `zonal_shares.py` are **not modified**: under
(A) they inherit the repair with no edit, which is the point of the shape.

**Not touched**: any per-region registry or config; `ScenarioConfig` (no field added, so rule 28(c)
does not fire and no matrix row is added); `_screen_demand_spikes` / `_screen_demand_dropouts`;
`scripts/calibration_verdict.py`; `frontend/data/**`; the plan; the ledger.
