# Handoff — PJM C3a / C3c: the 2025 summer-scarcity structural miss

**Owner lane:** PJM calibration. **Opened by:** pjm-118 (2026-07-24, keeper
`2026-07-24-pjm-118-netrev-level`). **Assigned model:** Opus/Fable (core-infra
lane, CLAUDE.md rule 26). **Status of the offer-level lane:** CLOSED / at frontier.

## Where pjm-118 left PJM

The pjm-118 offer-level retune **closed C1** (fuel-mix all 16/16; CC_REGULAR 2023
316.8→319.1, CT_PEAKER 2025 32.0→30.6). The keeper is NOT-YET on exactly two
gates, both the **same** phenomenon:

- **C3a mean LMP — FAIL 2025 (−10.5%)** (2023 +5.0% / 2024 −3.3% both PASS).
- **C3c price tail / scarcity — FAIL 2024 & 2025** (2025: model 15 h > $200 vs
  actual 59 h; 2024: model 1 h vs 18 h).

A four-run offer-level sweep (pjm-118 lane, candidates A/B/C/D) **proved these
are not offer-curve misses** — raising CC `econ_high` lifts 2025 price but breaks
C1 CC-2023; lowering CC `econ_low` fixes C1 but floods 2025 and lowers price;
raising CC-`peak` + CT offers is **inert** (+0.02 $/MWh, tail p99 82.6→84.6
unchanged). **Do not re-open the offer surface for this** (rules 1/11/13/26).

## The signature — it is a SUMMER supply-adequacy / scarcity-formation miss

Monthly model-vs-actual load-weighted LMP, 2025:

| month | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Δ $/MWh | −1.0 | −2.1 | +0.9 | +1.8 | +1.9 | **−19.9** | **−9.8** | −4.2 | **−8.1** | **−6.5** | −3.3 | −4.3 |

Winter is fine; the entire miss is **June–October**. The model's 2025 price tail
caps at **$324 (48 h > $100, 6 h > $200)** against real summer scarcity (**59 h >
$200**). Root cause: **too much cheap supply clears the summer peaks, so scarcity
never forms.** Three non-exclusive drivers, in priority order:

### Lane 1 — Outage completeness at summer peaks (START HERE)

The model keeps too much thermal capacity *available* at the June–July peaks
because event-coincident forced outages are not modeled.

**Data-source decision (affirmed, per owner preference "DAM only if granular /
unit-specific"):**
- **Base = CAMPD unit-outage data — KEEP IT.** It is unit-specific (per-`unit_id`,
  dated `outage_start/end`, `duration_days`); the keeper runs it via
  `unit_outage_short_windows=True` + the ≥5-day parent overlay.
- **PJM DAM `gen_outages_by_type` is AGGREGATE ONLY** — RTO / sub-region totals, a
  single fleet-wide availability fraction, **never per-unit or per-fuel-class**
  (`data/pjm_outages.py::pjm_dam_availability_series`). It does **not** meet the
  granular/unit-specific bar, so it is **not** the base. Default-OFF; not in the
  keeper.

**The gap CAMPD structurally cannot fill (this is the lever):** the ≥5-day
duration floor makes short (<5-day) event-coincident forced outages invisible,
and the short-windows detector is **coal-only** (CF≥0.55 baseload gate) — so
**CT/CC summer forced outages are unmodeled** ("stays unmodeled pending a
max-gen-event registry intake", per the pjm-118 attestation). These are precisely
the peak-hour de-ratings that would tighten the June/July stack.

**Recommended work, in order:**
1. **Preferred (unit-level, keeps the granular base):** intake a **unit-level
   event / max-gen-event outage registry** for PJM (or extend
   `derive_campd_unit_outages.py --short-windows` to CT/CC and <5-day non-coal),
   so the summer forced outages enter unit-specific. This is the on-preference
   path (unit-specific > aggregate).
2. **Fallback / cross-check (aggregate top-up):** turn on the already-intaked
   **DAM overlay** (`pjm_dam_availability`, wiring ready in
   `docs/handoffs/pjm-dam-availability-wiring-2026-07.md`) as a fleet-wide
   *residual* derate on top of CAMPD — it is forced+maintenance-complete where
   CAMPD is not. Use it to **measure the size of the missing summer de-rate**
   (is the June gap ~a few GW of unmodeled CT/CC outage?) before committing to
   the unit-level intake. Aggregate, so it is a diagnostic/complement, not the
   keeper base.
   - **Watch double-counting:** DAM total includes the ≥5-day CAMPD events already
     modeled. Apply DAM only as `max(0, DAM_derate − CAMPD_derate)` (the residual),
     or scope it to the classes/windows CAMPD omits (CT/CC, <5-day).

### Lane 2 — Import abundance at summer peaks

The model imports in **34% of hours vs 1.7% actual** (−18 TWh energy-balance
drift); cheap seam imports meet the summer peaks instead of domestic peakers.
The seam is priced via `reference_price_interface` + `PJM_SEAM_LADDER_BY_YEAR`
(measured Q-Q duration ladders) with `pjm_measured_interface_limits`. Investigate
whether the **summer** import availability/price is too loose (the ladders are
duration-curve-level, not hour-placed — a peak-hour import that should be scarce
may be filled from the cheap end of the ladder). This is the same "cheap supply"
mechanism as Lane 1 from the interchange side.

### Lane 3 — Scarcity price formation

Even when the stack tightens, verify the reserve co-opt actually produces the
>$200 tail. The keeper runs `energy_reserve_coopt` + `pjm_reserve_supply_cap` +
`pjm_reserve_pergen` (4 ORDC steps, req mean ~3 GW). Check whether the PJM
reserve penalty-factor curve (RTO/sub-zone RCPF) is steep/high enough to price
the summer shortage hours — this is the ERCOT-107 scarcity-tail lane's PJM
analogue (see `claude/ercot-107-scarcity-tail-*`). One mechanism per phenomenon
(rule 19): do not stack a price adder on top of a supply fix — first tighten
supply (Lanes 1/2), then confirm the co-opt prices it.

## How to reproduce the keeper (recipe is on main; hourly parquets are not)

`results/calibration/pjm_netrev_retune/meta.json` is the faithful replay recipe.
Per-year, rule-12 chain (a single 3-year process OOMs ~16 GB):

```
python scripts/replay_keeper.py results/calibration/pjm_netrev_retune \
  --years 2023 --out-dir results/calibration/pjm_netrev_retune            # then 2025, then 2024
# add --reuse-solved for the 2nd/3rd year if the reuse gate accepts (dirty tree refuses it)
```

Then rebuild the multi-year aggregates the per-year chain overwrites
(`system.parquet` from `hourly/system_*`, and `--rebuild-benchmark` for the
`_shared/PJM` eia923/eia930/campd inputs so C3a/C5a score all years), and
`scripts/dashboard_add_run.py` to (re)build the payload. **Known env limit:** the
1.72 MB `runs/<id>.js` payload could not be pushed from the pjm-118 session
(content-API output limit; `git push` 413-blocked) — regenerate + push it from a
git-push-capable runner so the run renders on the run explorer.

## Gates / discipline

- Holdouts: 2022 (validation) and 2019 + H1-2026 (locked test) are quarantined
  until PJM has a calibration-complete marker (none yet). Score only 2023–2025.
- Any structural mechanism (outage intake, seam re-price, reserve curve) is
  scored **leave-one-year-out within 2023–2025** before promotion (rule 22).
- The measured outage inputs re-derive only on a **source-data change**, never a
  residual (rule 23); the DAM/CAMPD choice above is a coverage decision, not a
  tuning knob.
