"""Tests for data_pipeline.py"""
from turn_sequence import data_pipeline
from turn_sequence.config import GoogleSheetConfig

def test_get_gsheet_df(sheet_config: GoogleSheetConfig):
    for gid in sheet_config.gid:
        df = data_pipeline.get_gsheet_df(sheet_config.id, gid)
        # Check that columns exist
        assert len(df.columns) > 0
