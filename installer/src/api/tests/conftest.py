import pytest


@pytest.fixture
def mock_env(monkeypatch):
  monkeypatch.setenv('ALERTS_TABLE', 'alerts_table')
  monkeypatch.setenv('INSTALLER_SERVICE_AREA_TABLE_NAME', 'service_area_table')
  monkeypatch.setenv('JOB_SCHEDULE_TABLE', 'job_schedule_table')
  monkeypatch.setenv('JOBS_TABLE', 'jobs_table')
  monkeypatch.setenv('MESSAGES_TABLE', 'messages_table')
  monkeypatch.setenv('RESERVATIONS_TABLE', 'reservations_table')