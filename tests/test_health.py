"""
test_health.py — Verify the health check endpoint.
"""


def test_health_returns_200(client):
    """Health endpoint must return 200."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_structure(client):
    """Response must include status, database, redis, service fields."""
    response = client.get("/api/v1/health")
    data = response.json()

    assert "status" in data
    assert "database" in data
    assert "redis" in data
    assert "service" in data


def test_health_status_is_healthy(client):
    """Status field must be 'healthy'."""
    response = client.get("/api/v1/health")
    assert response.json()["status"] == "healthy"


def test_health_database_connected(client):
    """Database should be connected (PostgreSQL running)."""
    response = client.get("/api/v1/health")
    assert response.json()["database"] == "connected", (
        "PostgreSQL not connected — is it running?"
    )


def test_health_redis_connected(client):
    """Redis should be connected."""
    response = client.get("/api/v1/health")
    assert response.json()["redis"] == "connected", (
        "Redis not connected — is it running?"
    )


def test_root_endpoint(client):
    """Root / endpoint returns a welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Enterprise AI System" in response.json()["message"]
