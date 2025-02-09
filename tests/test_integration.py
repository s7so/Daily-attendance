import pytest
from flask import Flask

@pytest.fixture
def client():
    app = Flask(__name__)

    @app.route('/ping')
    def ping():
        return 'pong'

    with app.test_client() as client:
        yield client


def test_ping_endpoint(client):
    response = client.get('/ping')
    assert response.status_code == 200
    assert response.data.decode('utf-8') == 'pong' 