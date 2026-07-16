# RC-1B-RELAND — items 2 & 4 patch (transport-blocked, apply via git-CLI)

**Status 2026-07-16 (RC-1B-RELAND session).** Items **1** (per-ISO
`capacity_market_clearing` gate) and **3** (probe-flag rewire) are already on
this branch — landed by concurrent work with code identical to the reland's,
plus this session verified/kept them. Items **2** (per-delivery-year vintage
resolution) and **4** (R5b NEISO `claimed_capability` basis) are **complete and
fully tested locally but could not be pushed**: they require rewriting
`constants.py` (300 KB / 6.9k lines) and `capacity.py` (164 KB / 3.5k lines),
which exceed the `push_files` inline-content transport (the Read/emit tools cap
at 25 k tokens; these files are 66 k+ tokens each). This is the same transport
limit that caused the original RC-1B revert. `git push` is disabled on this
remote (HTTP 413), so items 2 & 4 are delivered here as a **git-apply patch**.

## What the patch contains (`items2-4.patch`)

A `git diff` against this branch's tip, touching six files:

- `src/market_sim/config/constants.py` — **item 2**: `MARKET_DESIGN_VINTAGES`
  (one `MarketDesign` per on-disk delivery year: PJM 2021/22–2027/28, NYISO
  2021-22–2025-26, ISO-NE 2020/21–2027/28, MISO 2025-26 + 2026-27) +
  `resolve_demand_curve_vintage(iso, year)`; the `capacity_price_per_firm_mw_yr`
  method gains a `year` param + gated vintage consultation. **item 4**:
  `THERMAL_ACCREDITATION_BASIS_BY_ISO["NEISO"] = "claimed_capability"` + its
  cited docstring.
- `src/market_sim/model/capacity.py` — **item 4**: the `claimed_capability`
  branch in `thermal_accreditation_fraction` and the reserve-margin-build
  nameplate-basis check; plus wiring `iso=` into `capacity_revenue_per_mw_yr`'s
  price call (item 1 at that call site, which the concurrent work left on the
  scalar path).
- `src/market_sim/config/scenarios.py` — one `TIER_TAGS` row for
  `capacity_market_clearing_by_iso` (registry hygiene).
- `tests/test_capacity.py` — `TestClaimedCapabilityBasis` (item 4).
- `tests/test_capacity_demand_curve.py` — `TestPerIsoClearingGate`,
  `TestVintageResolution`, `TestVintageP0BReconciliation` (items 1/2; every
  vintage number re-derived from the P-0B CSV, rule 13).
- `model-methodology-spec.md` — §5.9 subsections for the per-ISO gate, the
  per-delivery-year vintage, and the `claimed_capability` basis.

Every `MARKET_DESIGN_VINTAGES` anchor and cap fraction was independently
re-derived from `data/raw/capacity-market/demand-curve/<iso>/<iso>.csv` and
matches to the CSV; the four registry keeper curves (`_PJM_VRR_CURVE` 2026/27,
`_NYISO_ICAP_CURVE` 2025-26, `_NEISO_FCA_CURVE` 2027-28, `_MISO_RBDC_CURVE`
2025-26) are reproduced byte-identically by their same-year vintage entries.

## Apply

```sh
git fetch origin claude/rc1b-plumbing-reland-lqrl7r
git checkout claude/rc1b-plumbing-reland-lqrl7r
git apply docs/handoffs/rc1b-items2-4-patch/items2-4.patch
uv run python -c "import market_sim.runner"   # clean
uv run python -m pytest -q tests/test_capacity.py tests/test_capacity_demand_curve.py tests/test_storage.py
# then push via git-CLI (or a size-appropriate transport)
```

With the patch applied, the full touched-module suite passes (392 tests, this
session). The patch was verified `git apply --check`-clean against the branch
tip it was generated from.

## Storage.py note

`estimate_capacity_value`'s item-2 `year`→vintage plumbing is **not** in this
patch and **not** on the branch: an earlier push landed it, but the branch's
`MarketDesign` method had no `year` param yet, so the storage-new-entry path
raised at runtime. `storage.py` was restored to the byte-identical 2-arg form to
keep the branch consistent. When this patch lands (adding `year` to the method),
re-add the storage plumbing: `estimate_capacity_value` calls
`capacity_price_per_firm_mw_yr(config, reserve_position, iso=iso, year=year)`
(drop the `del year` stub) — a two-line change, so the storage-entry screen
rides the per-delivery-year vintage too.

## Parameter registry

Regenerating `scripts/generate_parameter_registry.py` after this patch adds 25
entries (22 `market_design_vintages.*`, `scenario.capacity_market_clearing_by_iso`,
`thermal_accreditation_basis_by_iso.NEISO`, and a pre-existing gap
`scenario.entry_screen_diagnostics`); `validate_parameters.py` exits 0. The
1.39 MB `frontend/data/parameters.json` + `docs/parameter-citations.md` are
deferred to the same size-appropriate transport (the inline citations in
`constants.py` are the rule-5 source of truth).

*RC-1B-RELAND, 2026-07-16. No LP solved. No holdout year touched (rule 22).
Nothing on the backcast dashboard.*
