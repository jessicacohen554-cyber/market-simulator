"""Tests for PortfolioConfig validation and the config-file loader."""

import json

import pytest

from lce_portfolio.config import PortfolioConfig


def test_valid_defaults() -> None:
    """The default config constructs without error."""
    cfg = PortfolioConfig()
    assert cfg.mode == "premium_cap"


def test_excess_sale_fraction_default_is_full_resale() -> None:
    """ADR 0005 (amended & ratified 2026-07-02): surplus credited at full
    hourly ISO-average LMP — excess_sale_fraction defaults to 1.0."""
    assert PortfolioConfig().excess_sale_fraction == 1.0


def test_new_fields_defaults_and_validation() -> None:
    """eac_premium_mwh / additionality_only default empty/False and validate."""
    cfg = PortfolioConfig()
    assert cfg.eac_premium_mwh == {}
    assert cfg.additionality_only is False
    # a positive premium is accepted; a negative one is rejected.
    ok = PortfolioConfig(eac_premium_mwh={"nuclear_existing": 5.0})
    assert ok.eac_premium_mwh["nuclear_existing"] == 5.0
    import pytest

    with pytest.raises(ValueError):
        PortfolioConfig(eac_premium_mwh={"nuclear_existing": -1.0})


@pytest.mark.parametrize(
    "kwargs",
    [
        {"mode": "nonsense"},
        {"lcoe_sensitivity": "medium"},
        {"excess_sale_fraction": 1.5},
        {"hours": 0},
        {"premium_deltas": (1.0, -2.0)},
        {"matching_targets": (0.5, 1.5)},
        {"load_growth_years": -1},
    ],
)
def test_invalid_raises(kwargs) -> None:
    """Out-of-range or unknown values are rejected on construction."""
    with pytest.raises(ValueError):
        PortfolioConfig(**kwargs)


def test_with_overrides_revalidates() -> None:
    """with_overrides applies changes and re-runs validation."""
    cfg = PortfolioConfig().with_overrides(iso="ERCOT", excess_sale_fraction=0.5)
    assert cfg.iso == "ERCOT" and cfg.excess_sale_fraction == 0.5
    with pytest.raises(ValueError):
        cfg.with_overrides(mode="bad")


def test_from_file_json(tmp_path) -> None:
    """from_file reads JSON, coerces list fields to tuples, rejects unknown keys."""
    path = tmp_path / "run.json"
    path.write_text(
        json.dumps(
            {"iso": "PJM", "premium_deltas": [1, 5, 10], "lcoe_sensitivity": "high"}
        )
    )
    cfg = PortfolioConfig.from_file(path)
    assert cfg.iso == "PJM"
    assert cfg.premium_deltas == (1, 5, 10)
    assert cfg.lcoe_sensitivity == "high"


def test_from_file_unknown_key(tmp_path) -> None:
    """Unknown config keys raise rather than silently dropping."""
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"iso": "PJM", "bogus": 1}))
    with pytest.raises(ValueError):
        PortfolioConfig.from_file(path)
