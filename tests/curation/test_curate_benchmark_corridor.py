"""Tests for the benchmark-corridor intake on tiny synthetic fixtures.

Trivial-first: a minimal AEO raw CSV (API-native columns) and a minimal manual
unified CSV are written into a tmp raw tree, ``curate`` runs with CLEAN_DIR
redirected to a tmp dir (as in tests/curation/test_curate_capacity_deliverability.py) so
it never touches the real tree, and the written Parquet is asserted schema-valid.
Also covers the AEO series→canonical map + EMM→ISO crosswalk, the fail-loud unit
guard, the vocabulary guard, ISO-total aggregation, missing-source reporting,
the FC-5 context table (anchors carry NO verdict — rule 13), and the
loader↔registry source-inventory consistency.

Scoped to the new loader/schema only (the base capacity.py truncation is out of
scope) — no dispatch/forecast/hindcast solve is run.
"""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_benchmark_corridor as curate_bc
from scripts.lib import benchmark_corridor as bc
from scripts.lib import clean_io
from scripts.lib.benchmark_corridor import aeo
from scripts.lib.clean_io import validate_clean

# Tiny AEO raw fixture (the API-native fetch format). ERCOT (5-1) carries one of
# each corridor quantity + a T56 renewable-capacity row + one UNMAPPED series
# (must be skipped); PJM/East (5-10) and PJM/West (5-11) each carry coal
# capacity so the ISO-total sum can be checked.
_AEO_RAW = """source_release,table_id,region_id,region_name,scenario,series_id,series_name,period,value,unit
aeo2025,62,5-1,Texas Reliability Entity,ref2025,cap_NA_elep_NA_cl_NA_tre_gw,Electricity : Electric Power Sector : Capacity : Coal,2030,5.35,GW
aeo2025,62,5-1,Texas Reliability Entity,ref2025,cap_NA_elep_NA_cmc_NA_tre_gw,Electricity : Electric Power Sector : Capacity : Combined Cycle,2030,35.8,GW
aeo2025,62,5-1,Texas Reliability Entity,ref2025,gen_NA_elep_NA_cl_NA_tre_blnkwh,Electricity : Electric Power Sector : Generation : Coal,2030,20.6,BkWh
aeo2025,62,5-1,Texas Reliability Entity,ref2025,emi_co2_elep_NA_NA_NA_tre_millton,Electricity : Emissions : Carbon Dioxide,2030,99.76,MMst
aeo2025,67,5-1,Texas Reliability Entity,ref2025,cap_gen_elep_NA_slr_phtvl_tre_gw,Renewable Energy : Electric Power Sector : Generating Capacity : Solar Photovoltaic,2030,42.3,GW
aeo2025,62,5-1,Texas Reliability Entity,ref2025,cnsm_NA_elep_NA_elc_NA_tre_blnkwh,Electricity : Electricity Demand : Total Sales,2030,432.8,BkWh
aeo2025,62,5-10,PJM / East,ref2025,cap_NA_elep_NA_cl_NA_rfce_gw,Electricity : Electric Power Sector : Capacity : Coal,2035,4.0,GW
aeo2025,62,5-11,PJM / West,ref2025,cap_NA_elep_NA_cl_NA_rfcw_gw,Electricity : Electric Power Sector : Capacity : Coal,2035,6.0,GW
"""

# Tiny manual unified CSV (canonical columns) — a value transcribed from a
# primary-source table (the way a landed manual download looks).
_MANUAL_CDR = """source,iso,region,vintage,scenario,target_year,quantity,tech,value,unit,source_doc,source_page,note
ERCOT_CDR_2025,ERCOT,ERCOT,2025-12,protocol,2030,capacity,solar,29.4,GW,ERCOT CDR Dec 2025,planned-resources table,CDR-eligible planned solar
"""


def _write_aeo(raw_root: Path, text: str = _AEO_RAW) -> None:
    d = bc.raw_dir_for("AEO2025", raw_root)
    d.mkdir(parents=True, exist_ok=True)
    (d / aeo.RAW_FILENAME).write_text(text)


def _write_manual(raw_root: Path, source: str, text: str) -> None:
    path = bc.unified_csv_path(source, raw_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


class TestBenchmarkCorridorSchema(unittest.TestCase):
    def test_schema_loads_and_matches(self) -> None:
        schema = clean_io.load_schema("benchmark-corridor")
        self.assertEqual(schema.datatype, "benchmark-corridor")
        self.assertEqual(
            schema.key_columns,
            ("source", "iso", "region", "scenario", "target_year", "quantity", "tech"),
        )


class TestAeoParse(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.raw_root = Path(self._tmp.name) / "raw"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_maps_series_and_crosswalks_iso(self) -> None:
        _write_aeo(self.raw_root)
        df = bc.parse_source("AEO2025", self.raw_root)
        # 5 mapped ERCOT rows + 2 PJM coal rows; the unmapped demand series dropped.
        self.assertEqual(len(df), 7)
        ercot = df[df["iso"] == "ERCOT"]
        coal = ercot[(ercot["quantity"] == "capacity") & (ercot["tech"] == "coal")]
        self.assertAlmostEqual(float(coal["value"].iloc[0]), 5.35)
        self.assertEqual(coal["unit"].iloc[0], "GW")
        # BkWh generation is relabelled to TWh (numerically identical), value verbatim.
        gen = ercot[(ercot["quantity"] == "generation") & (ercot["tech"] == "coal")]
        self.assertEqual(gen["unit"].iloc[0], "TWh")
        self.assertAlmostEqual(float(gen["value"].iloc[0]), 20.6)
        # CO2 -> tech=total, MMst_co2.
        co2 = ercot[ercot["quantity"] == "co2"]
        self.assertEqual(co2["tech"].iloc[0], "total")
        self.assertEqual(co2["unit"].iloc[0], "MMst_co2")
        # T56 renewable split present.
        self.assertIn("solar", set(ercot["tech"]))
        # PJM/East + PJM/West both crosswalk to PJM.
        self.assertEqual(
            set(df[df["iso"] == "PJM"]["region"]), {"PJM / East", "PJM / West"}
        )

    def test_unit_drift_fails_loud(self) -> None:
        bad = _AEO_RAW.replace(
            "Electricity : Electric Power Sector : Capacity : Coal,2030,5.35,GW",
            "Electricity : Electric Power Sector : Capacity : Coal,2030,5.35,MW",
        )
        _write_aeo(self.raw_root, bad)
        with self.assertRaises(ValueError):
            bc.parse_source("AEO2025", self.raw_root)

    def test_absent_raw_is_empty(self) -> None:
        df = bc.parse_source("AEO2025", self.raw_root)
        self.assertTrue(df.empty)


class TestUnifiedCsvAndVocab(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.raw_root = Path(self._tmp.name) / "raw"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_manual_csv_parses(self) -> None:
        _write_manual(self.raw_root, "ERCOT_CDR_2025", _MANUAL_CDR)
        df = bc.parse_source("ERCOT_CDR_2025", self.raw_root)
        self.assertEqual(len(df), 1)
        self.assertEqual(df["source"].iloc[0], "ERCOT_CDR_2025")
        self.assertEqual(df["tech"].iloc[0], "solar")

    def test_bad_tech_rejected(self) -> None:
        bad = _MANUAL_CDR.replace(",capacity,solar,", ",capacity,unobtanium,")
        _write_manual(self.raw_root, "ERCOT_CDR_2025", bad)
        with self.assertRaises(ValueError):
            bc.parse_source("ERCOT_CDR_2025", self.raw_root)

    def test_bad_quantity_rejected(self) -> None:
        bad = _MANUAL_CDR.replace(",2030,capacity,solar,", ",2030,megawattage,solar,")
        _write_manual(self.raw_root, "ERCOT_CDR_2025", bad)
        with self.assertRaises(ValueError):
            bc.parse_source("ERCOT_CDR_2025", self.raw_root)


class TestCurateAndLoad(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        self.raw_root.mkdir(parents=True)
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_curate_roundtrip_and_missing_sources(self) -> None:
        _write_aeo(self.raw_root)
        _write_manual(self.raw_root, "ERCOT_CDR_2025", _MANUAL_CDR)
        combined, present, missing = curate_bc.assemble(raw_root=self.raw_root)
        self.assertEqual(set(present), {"AEO2025", "ERCOT_CDR_2025"})
        # The other six registered sources report missing (never placeholder rows).
        self.assertIn("StdScen2024", missing)
        self.assertIn("NYISO_GOLDBOOK_2026", missing)
        written = curate_bc.curate(raw_root=self.raw_root)
        self.assertEqual(len(written), 1)
        schema = validate_clean(written[0])
        self.assertEqual(schema.datatype, "benchmark-corridor")
        df = pd.read_parquet(written[0])
        self.assertEqual(list(df.columns), list(bc.CANONICAL_COLUMNS))

    def test_iso_totals_sums_regions(self) -> None:
        from market_sim.data.benchmark_corridor import iso_totals

        _write_aeo(self.raw_root)
        combined, _, _ = curate_bc.assemble(raw_root=self.raw_root)
        tot = iso_totals(combined)
        pjm_coal = tot[
            (tot["iso"] == "PJM")
            & (tot["quantity"] == "capacity")
            & (tot["tech"] == "coal")
            & (tot["target_year"] == 2035)
        ]
        self.assertEqual(len(pjm_coal), 1)
        self.assertAlmostEqual(float(pjm_coal["value"].iloc[0]), 10.0)  # 4.0 + 6.0

    def test_corridor_context_is_verdict_free(self) -> None:
        from market_sim.data.benchmark_corridor import corridor_context

        _write_aeo(self.raw_root)
        combined, present, missing = curate_bc.assemble(raw_root=self.raw_root)
        ctx = corridor_context(combined, missing_sources=missing, iso="ERCOT")
        self.assertTrue(ctx["context_only"])
        self.assertEqual(ctx["sources"], ["AEO2025"])
        self.assertTrue(all("verdict" not in r for r in ctx["rows"]))
        self.assertTrue(all(r["iso"] == "ERCOT" for r in ctx["rows"]))
        self.assertIn("StdScen2024", ctx["missing_sources"])

    def test_emit_corridor_json(self) -> None:
        _write_aeo(self.raw_root)
        out = Path(self._tmp.name) / "corridor.json"
        curate_bc.emit_corridor_json(out, raw_root=self.raw_root)
        payload = json.loads(out.read_text())
        self.assertTrue(payload["context_only"])
        self.assertTrue(len(payload["rows"]) > 0)
        self.assertTrue(all("verdict" not in r for r in payload["rows"]))


class TestIsoPlanningQuantities(unittest.TestCase):
    """The ISO planning-document quantities (peak/energy/reserve margin, D22).

    An ISO load forecast publishes peak MW and annual GWh, not a capacity mix,
    so these three quantities are what let rubric §6's ISO sources land at all.
    """

    def test_iso_planning_quantities_are_in_vocab(self) -> None:
        for q in ("peak_demand", "energy_demand", "reserve_margin"):
            self.assertIn(q, bc.QUANTITY_VOCAB)

    def test_unified_csv_with_peak_and_energy_parses(self) -> None:
        with TemporaryDirectory() as td:
            raw_root = Path(td)
            _write_manual(
                raw_root,
                "PJM_LOAD_2026",
                "source,iso,region,vintage,scenario,target_year,quantity,tech,"
                "value,unit,source_doc,source_page,note\n"
                "PJM_LOAD_2026,PJM,PJM RTO,2026-01,reference,2030,peak_demand,"
                "total,183008,MW,PJM 2026 Load Report,Table B-1,rto total\n"
                "PJM_LOAD_2026,PJM,PJM RTO,2026-01,reference,2030,energy_demand,"
                "total,1086262,GWh,PJM 2026 Load Report,Table E-1,rto total\n",
            )
            df = bc.parse_source("PJM_LOAD_2026", raw_root)
        self.assertEqual(len(df), 2)
        self.assertEqual(set(df["quantity"]), {"peak_demand", "energy_demand"})
        self.assertEqual(set(df["unit"]), {"MW", "GWh"})

    def test_iso_totals_sums_extensive_quantities(self) -> None:
        from market_sim.data.benchmark_corridor import iso_totals

        df = pd.DataFrame(
            [
                _corridor_row("PJM", "East", "peak_demand", 100.0, "MW"),
                _corridor_row("PJM", "West", "peak_demand", 150.0, "MW"),
            ]
        )
        out = iso_totals(df)
        self.assertEqual(len(out), 1)
        self.assertAlmostEqual(float(out["value"].iloc[0]), 250.0)

    def test_iso_totals_refuses_to_sum_reserve_margin_across_regions(self) -> None:
        """A ratio summed across regions is nonsense — fail loud, never return it."""
        from market_sim.data.benchmark_corridor import iso_totals

        df = pd.DataFrame(
            [
                _corridor_row("PJM", "East", "reserve_margin", 0.15, "fraction"),
                _corridor_row("PJM", "West", "reserve_margin", 0.15, "fraction"),
            ]
        )
        with self.assertRaises(ValueError) as ctx:
            iso_totals(df)
        self.assertIn("intensive", str(ctx.exception).lower())

    def test_iso_totals_passes_through_single_region_reserve_margin(self) -> None:
        from market_sim.data.benchmark_corridor import iso_totals

        df = pd.DataFrame(
            [_corridor_row("ERCOT", "ERCOT", "reserve_margin", -0.1266, "fraction")]
        )
        out = iso_totals(df)
        self.assertEqual(len(out), 1)
        self.assertAlmostEqual(float(out["value"].iloc[0]), -0.1266)


def _corridor_row(
    iso: str, region: str, quantity: str, value: float, unit: str
) -> dict:
    """One canonical row for the aggregation tests."""
    return {
        "source": "TEST",
        "iso": iso,
        "region": region,
        "vintage": "2026-01",
        "scenario": "reference",
        "target_year": 2030,
        "quantity": quantity,
        "tech": "total",
        "value": value,
        "unit": unit,
        "source_doc": None,
        "source_page": None,
        "note": None,
    }


class TestRegistryConsistency(unittest.TestCase):
    def test_loader_inventory_matches_registered_sources(self) -> None:
        from market_sim.data.benchmark_corridor import EXPECTED_SOURCES

        registry = bc.load_registry()
        self.assertEqual(set(EXPECTED_SOURCES), set(registry))

    def test_fetchable_sources_are_exactly_those_with_a_fetcher(self) -> None:
        """`fetchable` marks the sources an in-repo script can actually land.

        AEO2025 via the EIA API (`fetch_aeo_electricity.py`); ERCOT CDR and the
        PJM Load Forecast via `fetch_iso_planning_benchmarks.py`, which
        machine-extracts their published XLSX. The rest have no static file URL
        (PDF, or a JavaScript document portal) and stay manual downloads.
        """
        registry = bc.load_registry()
        fetchable = {s for s, spec in registry.items() if spec.fetchable}
        self.assertEqual(fetchable, {"AEO2025", "ERCOT_CDR_2025", "PJM_LOAD_2026"})


if __name__ == "__main__":
    unittest.main()
