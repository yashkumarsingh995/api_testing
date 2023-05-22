import pytest


@pytest.fixture
def mock_env(monkeypatch):
  monkeypatch.setenv('INSTALLER_CODES_TABLE', 'codes_table')
  monkeypatch.setenv('INSTALLER_QUALIFICATION_TABLE', 'qualification_table')
