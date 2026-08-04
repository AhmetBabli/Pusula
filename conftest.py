"""
🧪 Pytest Configuration and Fixtures
"""
import pytest
import os
from pathlib import Path


# Add project root to path
PROJECT_ROOT = Path(__file__).parent
os.chdir(PROJECT_ROOT)


@pytest.fixture
def test_db_path(tmp_path):
    """Provide temporary database path for tests"""
    return tmp_path / "test_db.sqlite"


@pytest.fixture
def mock_settings(test_db_path, monkeypatch):
    """Mock settings for tests"""
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-very-long-one-for-testing-purposes")
    monkeypatch.setenv("ENCRYPTION_KEY", "ZQkbOHBv9Wc-0TcQAx4yfFm5833jbGkZPgWoOjHPiOs=")
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")
    
    # Reload settings
    import importlib
    import backend.config
    importlib.reload(backend.config)
    return backend.config.settings


def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow"
    )
