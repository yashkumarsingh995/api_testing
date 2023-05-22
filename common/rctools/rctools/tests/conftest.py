import pytest


@pytest.fixture
def mock_env(monkeypatch):
  monkeypatch.setenv('ALERTS_TABLE', 'alerts_table')
  monkeypatch.setenv('MESSAGES_TABLE', 'messages_table')
  monkeypatch.setenv('RESERVATIONS_TABLE', 'reservations_table')