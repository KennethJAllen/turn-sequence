"""Tests for data_pipeline.py"""
from turn_sequence import utils
from turn_sequence.config import GoogleSheetConfig

def test_get_gsheet_df(sheet_config: GoogleSheetConfig):
    for gid in sheet_config.gid:
        df = utils.get_gsheet_df(sheet_config.id, gid)
        # Check that columns exist
        assert len(df.columns) > 0
