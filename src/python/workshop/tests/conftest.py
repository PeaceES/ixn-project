"""
Pytest configuration and fixtures for the Calendar Scheduler Agent tests.
"""
import asyncio
import os
import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile
import shutil
from typing import AsyncGenerator, Generator

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment variables
os.environ["TESTING"] = "true"
os.environ["PROJECT_CONNECTION_STRING"] = "test_connection_string"
os.environ["MODEL_DEPLOYMENT_NAME"] = "test_model"
os.environ["ENABLE_AUTO_EVALUATION"] = "false"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_azure_client():
    """Mock Azure AI Projects client."""
    with patch("azure.ai.projects.aio.AIProjectClient") as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_default_azure_credential():
    """Mock Azure Default Credentials."""
    with patch("azure.identity.DefaultAzureCredential") as mock_credential:
        mock_instance = MagicMock()
        mock_credential.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_calendar_mcp_client():
    """Mock Calendar MCP Client."""
    with patch("services.mcp_client.CalendarMCPClient") as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_calendar_events():
    """Sample calendar events for testing."""
    return [
        {
            "id": "event1",
            "title": "Team Meeting",
            "start": "2024-01-15T10:00:00Z",
            "end": "2024-01-15T11:00:00Z",
            "location": "Conference Room A",
            "description": "Weekly team sync"
        },
        {
            "id": "event2", 
            "title": "Project Review",
            "start": "2024-01-15T14:00:00Z",
            "end": "2024-01-15T15:00:00Z",
            "location": "Conference Room B",
            "description": "Monthly project review"
        }
    ]


@pytest.fixture
def sample_rooms():
    """Sample room data for testing."""
    return [
        {
            "id": "room1",
            "name": "Conference Room A",
            "capacity": 10,
            "equipment": ["projector", "whiteboard"]
        },
        {
            "id": "room2",
            "name": "Conference Room B", 
            "capacity": 6,
            "equipment": ["tv", "conference_phone"]
        }
    ]


@pytest.fixture
def temp_directory():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_agent_thread():
    """Mock agent thread for testing."""
    mock_thread = MagicMock()
    mock_thread.id = "test_thread_id"
    return mock_thread


@pytest.fixture
def mock_agent():
    """Mock agent for testing."""
    mock_agent = MagicMock()
    mock_agent.id = "test_agent_id"
    mock_agent.name = "Test Calendar Agent"
    return mock_agent


@pytest.fixture
def mock_stream_event_handler():
    """Mock stream event handler."""
    with patch("agent.stream_event_handler.StreamEventHandler") as mock_handler:
        mock_instance = MagicMock()
        mock_handler.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_utilities():
    """Mock utilities class."""
    with patch("utils.utilities.Utilities") as mock_utils:
        mock_instance = MagicMock()
        mock_utils.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_permissions():
    """Mock permissions system."""
    with patch("services.simple_permissions.SimplePermissions") as mock_perms:
        mock_instance = MagicMock()
        mock_perms.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def temp_db_file():
    """Create temporary database file for tests."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    os.unlink(path) if os.path.exists(path) else None


@pytest.fixture
def in_memory_db():
    """Create in-memory SQLite database for fast tests."""
    return ":memory:"


@pytest.fixture
def sample_events():
    """Provide sample event data for tests."""
    return [
        {
            "id": "event-1",
            "title": "Morning Standup", 
            "description": "Daily team standup",
            "start_time": "2024-12-01T09:00:00Z",
            "end_time": "2024-12-01T09:30:00Z",
            "attendees": "team@company.com",
            "organizer": "manager@company.com"
        },
        {
            "id": "event-2",
            "title": "Client Meeting",
            "description": "Quarterly business review",
            "start_time": "2024-12-01T14:00:00Z", 
            "end_time": "2024-12-01T15:00:00Z",
            "attendees": "client@external.com,sales@company.com",
            "organizer": "sales@company.com"
        },
        {
            "id": "event-3",
            "title": "Team Lunch",
            "description": "Monthly team lunch",
            "start_time": "2024-12-02T12:00:00Z",
            "end_time": "2024-12-02T13:00:00Z", 
            "attendees": "team@company.com",
            "organizer": "hr@company.com"
        }
    ]


@pytest.fixture
def sample_scheduling_request():
    """Provide sample scheduling request for agent tests."""
    return {
        "action": "schedule_meeting",
        "title": "Test Meeting",
        "description": "Test meeting description",
        "start_time": "2024-12-01T10:00:00Z",
        "end_time": "2024-12-01T11:00:00Z",
        "attendees": ["user1@test.com", "user2@test.com"],
        "organizer": "organizer@test.com"
    }


@pytest.fixture
def mock_sql_store():
    """Mock SQL store for unit tests."""
    from services.async_sql_store import AsyncSQLStore
    with patch.object(AsyncSQLStore, '__init__', return_value=None):
        mock_store = AsyncMock(spec=AsyncSQLStore)
        yield mock_store


@pytest.fixture(autouse=True)
def cleanup_environment():
    """Cleanup environment after each test."""
    yield
    # Clean up any test-specific environment variables
    test_env_vars = [k for k in os.environ.keys() if k.startswith("TEST_")]
    for var in test_env_vars:
        del os.environ[var]


# Markers for test organization
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
pytest.mark.azure = pytest.mark.azure
pytest.mark.mcp = pytest.mark.mcp
pytest.mark.permissions = pytest.mark.permissions
pytest.mark.evaluation = pytest.mark.evaluation
pytest.mark.smoke = pytest.mark.smoke
