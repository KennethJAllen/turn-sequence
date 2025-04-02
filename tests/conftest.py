"""Configuration for tests"""
from pathlib import Path
import pytest
from turn_sequence import config

@pytest.fixture(name='config_dir')
def fixture_config_dir() -> Path:
    return Path.cwd() / "config"

@pytest.fixture(name='project_config')
def fixture_project_config(config_dir: Path) -> config.ProjectConfig:
    project_config_path = config_dir / "project_config.yaml"
    project_config = config.load_project_config(project_config_path)
    return project_config

@pytest.fixture(name='sheet_config')
def fixture_sheet_config(config_dir: Path) -> config.GoogleSheetConfig:
    sheet_config_path = config_dir / "sheet_config.yaml"
    sheet_config = config.load_sheet_config(sheet_config_path)
    return sheet_config
