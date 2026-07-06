"""Tests for the shared clean-data writer/validator (scripts/lib/clean_io.py).

Covers schema pass/fail: a conforming frame round-trips through write_clean +
validate_clean, and each enforced convention (snake_case, UTC tz, dtypes,
nullability, required keys, unexpected columns) raises SchemaError. Also checks
that every shipped schema parses and that provenance metadata is embedded.
"""

import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

import pandas as pd

from scripts.lib import clean_io
from scripts.lib.clean_io import (
    SchemaError,
    clean_exists,
    load_schema,
    read_clean,
    read_clean_metadata,
    validate_clean,
    validate_df,
    write_clean,
)

# Datatypes that must each have a parseable schema (the standardization contract).
ALL_DATATYPES = [
    "lmp",
    "load",
    "demand-profile",
    "ancillary-services",
    "generation",
    "renewables",
    "emissions",
    "emissions-unit-annual",
    "outages",
    "validation",
    "fleet",
    "fuel-prices",
    "reference",
    "egrid",
    "unit-outage-events",
    "partial-outages",
    "capacity-deliverability",
    "confirmed-retirements",
    "gtc-limits",
    "ramp-capability",
    "winter-fuel-inventory",
    "rggi-co2-budgets",
    "carb-cap-schedule",
    "chp-btm-share",
]


def _good_lmp() -> pd.DataFrame:
    """A minimal frame that conforms to the lmp schema."""
    ts = pd.to_datetime(["2024-01-01 00:00", "2024-01-01 01:00"], utc=True)
    return pd.DataFrame(
        {
            "interval_start_utc": ts,
            "iso": pd.array(["CAISO", "CAISO"], dtype="string"),
            "market": pd.array(["DAM", "DAM"], dtype="string"),
            "node": pd.array(["TH_SP15", "TH_SP15"], dtype="string"),
            "lmp_usd_per_mwh": [31.2, 28.7],
        }
    )


class CleanIORedirectMixin(unittest.TestCase):
    """Redirect CLEAN_DIR to a temp dir so writes never touch the repo."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = Path(self._tmp.name) / "clean"

    def tearDown(self):
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()


class TestSchemasLoad(unittest.TestCase):
    def test_every_datatype_has_parseable_schema(self):
        for dt in ALL_DATATYPES:
            schema = load_schema(dt)
            self.assertEqual(schema.datatype, dt)
            self.assertGreaterEqual(schema.schema_version, 1)
            self.assertTrue(schema.columns, f"{dt} declares no columns")

    def test_unknown_datatype_raises(self):
        with self.assertRaises(SchemaError):
            load_schema("does-not-exist")

    def test_keys_and_nonnullable_are_declared_columns(self):
        # Sanity on the contract itself: every key column is a declared column.
        for dt in ALL_DATATYPES:
            schema = load_schema(dt)
            names = set(schema.column_map)
            for key in schema.key_columns:
                self.assertIn(key, names, f"{dt} key {key!r} not declared")


class TestValidatePass(unittest.TestCase):
    def test_conforming_lmp_passes(self):
        schema = validate_df(_good_lmp(), "lmp")
        self.assertEqual(schema.datatype, "lmp")

    def test_optional_local_column_allowed(self):
        df = _good_lmp()
        df["interval_start_local"] = pd.to_datetime(
            ["2024-01-01 00:00", "2024-01-01 01:00"]
        )  # tz-naive wall clock
        validate_df(df, "lmp")

    def test_reference_allows_additional_columns(self):
        df = pd.DataFrame(
            {
                "key": pd.array(["a", "b"], dtype="string"),
                "table_specific_value_mw": [1.0, 2.0],
            }
        )
        validate_df(df, "reference")


class TestValidateFail(unittest.TestCase):
    def test_non_snake_case_column_fails(self):
        df = _good_lmp().rename(columns={"lmp_usd_per_mwh": "LMP"})
        with self.assertRaises(SchemaError):
            validate_df(df, "lmp")

    def test_naive_utc_column_fails(self):
        df = _good_lmp()
        df["interval_start_utc"] = pd.to_datetime(
            ["2024-01-01 00:00", "2024-01-01 01:00"]
        )  # tz-naive -> not acceptable for a UTC column
        with self.assertRaises(SchemaError):
            validate_df(df, "lmp")

    def test_non_utc_tz_fails(self):
        # A fixed -08:00 offset (no IANA zone db needed) is tz-aware but not UTC.
        import datetime as dt

        pacific = dt.timezone(dt.timedelta(hours=-8))
        df = _good_lmp()
        df["interval_start_utc"] = pd.to_datetime(
            ["2024-01-01 00:00", "2024-01-01 01:00"]
        ).tz_localize(pacific)
        with self.assertRaises(SchemaError):
            validate_df(df, "lmp")

    def test_missing_required_key_fails(self):
        df = _good_lmp().drop(columns=["node"])
        with self.assertRaises(SchemaError):
            validate_df(df, "lmp")

    def test_unexpected_column_fails_on_closed_schema(self):
        df = _good_lmp()
        df["surprise_mw"] = [1.0, 2.0]
        with self.assertRaises(SchemaError):
            validate_df(df, "lmp")

    def test_wrong_dtype_fails(self):
        df = _good_lmp()
        df["lmp_usd_per_mwh"] = pd.array(["cheap", "dear"], dtype="string")
        with self.assertRaises(SchemaError):
            validate_df(df, "lmp")

    def test_null_in_nonnullable_fails(self):
        df = _good_lmp()
        df.loc[0, "lmp_usd_per_mwh"] = None
        with self.assertRaises(SchemaError):
            validate_df(df, "lmp")


class TestWriteRoundTrip(CleanIORedirectMixin):
    def test_write_then_validate_clean(self):
        path = write_clean(
            _good_lmp(),
            "lmp",
            iso="CAISO",
            year=2024,
            market="DAM",
            source="data/raw/lmp-data/CAISO/CAISO_dam_hourly_2024.csv",
        )
        self.assertTrue(path.exists())
        # path composed by clean_path: .../lmp/CAISO/DAM/lmp_2024.parquet
        self.assertEqual(path.name, "lmp_2024.parquet")
        self.assertIn("CAISO", path.parts)
        self.assertIn("DAM", path.parts)

        schema = validate_clean(path)
        self.assertEqual(schema.datatype, "lmp")

    def test_metadata_embedded(self):
        path = write_clean(
            _good_lmp(),
            "lmp",
            iso="CAISO",
            year=2024,
            market="DAM",
            source="raw/lmp.csv",
        )
        meta = read_clean_metadata(path)
        self.assertEqual(meta["datatype"], "lmp")
        self.assertEqual(meta["schema_version"], "1")
        self.assertEqual(meta["iso"], "CAISO")
        self.assertEqual(meta["market"], "DAM")
        self.assertEqual(meta["source"], "raw/lmp.csv")
        self.assertIn("units", meta)
        self.assertIn("created_utc", meta)

    def test_write_rejects_bad_frame(self):
        bad = _good_lmp().rename(columns={"lmp_usd_per_mwh": "LMP"})
        with self.assertRaises(SchemaError):
            write_clean(bad, "lmp", iso="CAISO", year=2024)

    def test_validate_clean_detects_version_drift(self):
        path = write_clean(_good_lmp(), "lmp", iso="CAISO", year=2024, market="DAM")
        # Forge a mismatched embedded version by rewriting metadata.
        import pyarrow.parquet as pq

        table = pq.read_table(path)
        md = dict(table.schema.metadata or {})
        md[b"market_sim.schema_version"] = b"999"
        pq.write_table(table.replace_schema_metadata(md), path)
        with self.assertRaises(SchemaError):
            validate_clean(path)


class TestReadClean(CleanIORedirectMixin):
    def test_read_clean_round_trips_frame(self):
        write_clean(_good_lmp(), "lmp", iso="CAISO", year=2024, market="DAM")
        self.assertTrue(clean_exists("lmp", iso="CAISO", year=2024, market="DAM"))
        df = read_clean("lmp", iso="CAISO", year=2024, market="DAM")
        pd.testing.assert_frame_equal(df, _good_lmp())

    def test_read_clean_column_projection(self):
        write_clean(_good_lmp(), "lmp", iso="CAISO", year=2024, market="DAM")
        df = read_clean(
            "lmp",
            iso="CAISO",
            year=2024,
            market="DAM",
            validate=False,
            columns=["interval_start_utc", "lmp_usd_per_mwh"],
        )
        self.assertEqual(list(df.columns), ["interval_start_utc", "lmp_usd_per_mwh"])

    def test_read_clean_missing_raises_with_hint(self):
        self.assertFalse(clean_exists("lmp", iso="CAISO", year=1999, market="DAM"))
        with self.assertRaises(FileNotFoundError) as ctx:
            read_clean("lmp", iso="CAISO", year=1999, market="DAM")
        self.assertIn("curate_lmp.py", str(ctx.exception))

    def test_read_clean_validates_by_default(self):
        path = write_clean(_good_lmp(), "lmp", iso="CAISO", year=2024, market="DAM")
        # Corrupt the embedded version so default-validating read rejects it.
        import pyarrow.parquet as pq

        table = pq.read_table(path)
        md = dict(table.schema.metadata or {})
        md[b"market_sim.schema_version"] = b"999"
        pq.write_table(table.replace_schema_metadata(md), path)
        with self.assertRaises(SchemaError):
            read_clean("lmp", iso="CAISO", year=2024, market="DAM")


class TestRegenerateEntrypoint(unittest.TestCase):
    def test_datatype_list_matches_schemas(self):
        from scripts.regenerate_clean import DATATYPES

        self.assertEqual(sorted(DATATYPES), sorted(ALL_DATATYPES))


if __name__ == "__main__":
    unittest.main()
