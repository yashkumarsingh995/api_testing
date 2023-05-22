from fastapi.testclient import TestClient


def test_health(mock_env):
    from handler import app
    
    client = TestClient(app)
    response = client.get('/health')
    assert response.status_code == 200