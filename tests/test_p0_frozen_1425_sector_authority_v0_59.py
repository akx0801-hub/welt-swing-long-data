from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/p0_frozen_1425_sector_authority_v0_59.py"
spec=importlib.util.spec_from_file_location("v059",SCRIPT)
mod=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def test_constants():
    assert mod.REQUIRED_START_HEAD=="4c12c2126bb3f8ba6c6f132f316041c83b91a02a"
    assert mod.V058_RUN==36242803316
    assert mod.V058_ARTIFACT==10905869033
    assert mod.V058_ARTIFACT_DIGEST=="sha256:54dc5168218c7a211c6a0d66fc236c1e95a7cfdabef2acadf79282c8f1b5ae1c"
    assert mod.V058_RS_SHA256=="2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"


def test_sector_contract_is_not_populated_and_not_taxonomy_selected():
    c=mod.inspect_metadata_contract()
    assert c["v021_status"]=="PREPARED_NOT_POPULATED"
    assert c["canonical_taxonomy_selected"] is False
    assert c["canonical_sector_field_selected"] is False
    assert c["mapping_authority_populated"] is False
    assert c["contract_complete"] is False


def test_sector_rs_contract_not_silently_inherited_from_home_market():
    c=mod.sector_rs_contract_analysis()
    assert c["contract_complete"] is False
    assert c["aggregation_mean_or_median"]=="NOT_DEFINED_FOR_SECTOR"
    assert c["leave_one_out_rule"]=="NOT_DEFINED_FOR_SECTOR"
    assert c["minimum_peer_group_size"]=="NOT_NUMERICALLY_DEFINED"


def test_provider_calls_are_zero():
    assert mod.provider_calls()=={
        "market_data":0,
        "yahoo_yfinance":0,
        "eodhd":0,
        "alpha_vantage":0,
        "scalable":0,
    }


def test_sector_column_detector_does_not_treat_rs_output_as_metadata():
    cols=["WS_ID","Sector_RS20_Excess_v0_20","GICS_Sector","Industry_Name","foo"]
    found=mod.detect_sector_columns(cols)
    assert "Sector_RS20_Excess_v0_20" not in found
    assert "GICS_Sector" in found
    assert "Industry_Name" in found
