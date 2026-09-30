# `licensed/` — owner-licensed Southeast daily gas hub series (SOCO)

**Status 2026-09-29 (lane soco-90): NOT SUPPLIED, and the owner ruled "Don't buy"** (FINDING-soco-90 §6): a daily series cannot perform the joint C3a repair. Kept inert for reference.

## Licence

A vendor daily index (NGI Daily Gas Price Index, S&P Platts Gas Daily, or ICE) is **not redistributable**
(`docs/data-licensing.md` §5). Everything in this directory except this README and `SHA256SUMS.txt` is
gitignored. Never `git add -f` it, never push it to a shard branch, never paste values into a doc beyond
aggregate statistics.

## File contract — `se_daily_hub.csv`

| column | meaning |
|---|---|
| `date` | **flow date** (gas day), ISO `YYYY-MM-DD`. If the vendor gives trade date only, add a flow-date row for each weekend/holiday flow day it covers; the probe otherwise forward-fills the last print. |
| `hub` | `SNG` (primary) or `TZ4` (alternate). |
| `price_usd_mmbtu` | daily index (volume-weighted average), $/MMBtu, nominal. |

Coverage: every flow date 2019-01-01 .. 2025-12-31. No gaps (the probe raises on an unpriced day).

**Hub choice (fixed before the data is seen).** Primary: **Southern Natural Gas (SNG / "Sonat")**, the
system-wide transporter for the SOCO footprint (Southern Company Gas holds 50 %; `SOURCES_soco_gas.md`).
One hub for all three zones, so no blend weights and no free parameter. Alternate, reported only:
**Transco Zone 4**, which reaches north Georgia via the Dalton lateral. **Transco Zone 5 is out of scope**:
it prices deliveries into the Carolinas/Virginia, not the SOCO footprint.

**Time basis.** Calendar flow day d prices CST hours 0-23 of d, the clock the armed `gas_daily_shape` uses.
(The NAESB gas day runs 09:00-09:00 CT; that offset is ignored, as it is for Henry Hub today.)

## Optional transport table — `sng_transport.csv`

`year,usage_usd_mmbtu,fuel_retention_frac`: SNG's published FERC-tariff firm usage (commodity) charge and
fuel retention, per year. Public (FERC eTariff), so it may be committed elsewhere; nothing is fitted.
Replacement delivered price = `hub / (1 - retention) + usage`.

## Identity record

When the file lands: `sha256sum se_daily_hub.csv >> SHA256SUMS.txt` with the vendor, product name,
licence reference and fetch date on a comment line. Commit only `SHA256SUMS.txt`.

## Shards

A shard clones from GitHub, so it **cannot see this file**. A solve that uses it needs the owner to place
the file in each shard container (or provide a private fetch URL through an environment secret). The
parent must verify the shard's `sha256` against `SHA256SUMS.txt` before accepting a leg.

## Probe

`uv run python scripts/probes/_soco90_se_daily_replacement.py --out <scratch> --series licensed --hub SNG`
