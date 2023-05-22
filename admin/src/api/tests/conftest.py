import pytest


@pytest.fixture
def mock_env(monkeypatch):
  monkeypatch.setenv('INSTALLER_CODES_TABLE', 'codes_table')
  monkeypatch.setenv('JOB_SCHEDULE_TABLE', 'job_schedule_table')
  monkeypatch.setenv('JOBS_TABLE', 'jobs_table')
