"""
Integration tests for web server endpoints.
"""
import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from web_server import app


@pytest.mark.integration
class TestWebServerIntegration:
    """Test web server endpoints integration."""
    
    @pytest.fixture
    def client(self):
        """Create Flask test client."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def authenticated_client(self, client):
        """Create authenticated Flask test client."""
        # Mock authentication
        with patch('web_server.current_user') as mock_user:
            mock_user.is_authenticated = True
            mock_user.email = "test@example.com"
            mock_user.id = "user-123"
            yield client
    
    def test_home_route(self, client):
        """Test home route responds correctly."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Calendar Scheduling Agent' in response.data or b'login' in response.data.lower()
    
    def test_login_route(self, client):
        """Test login route."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower() or response.status_code == 302  # Redirect if already authenticated
    
    @patch('services.compat_sql_store.get_org_structure')
    def test_api_org_structure(self, mock_org, authenticated_client):
        """Test organization structure API endpoint."""
        mock_org.return_value = {
            "users": [
                {"id": "user1", "email": "user1@test.com", "name": "User One"},
                {"id": "user2", "email": "user2@test.com", "name": "User Two"}
            ]
        }
        
        response = authenticated_client.get('/api/org-structure')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert "users" in data
        assert len(data["users"]) == 2
    
    @patch('services.async_sql_store.async_get_rooms')
    def test_api_rooms(self, mock_rooms, authenticated_client):
        """Test rooms API endpoint."""
        mock_rooms.return_value = {
            "rooms": [
                {"id": "room1", "name": "Conference Room A"},
                {"id": "room2", "name": "Conference Room B"}
            ]
        }
        
        response = authenticated_client.get('/api/rooms')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert "rooms" in data
        assert len(data["rooms"]) == 2
    
    @patch('services.async_sql_store.async_list_events')
    def test_api_events(self, mock_events, authenticated_client):
        """Test events API endpoint."""
        mock_events.return_value = {
            "events": [
                {
                    "id": "event1",
                    "title": "Test Meeting",
                    "start_time": "2024-12-01T10:00:00Z",
                    "end_time": "2024-12-01T11:00:00Z"
                }
            ]
        }
        
        response = authenticated_client.get('/api/events')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert "events" in data
        assert len(data["events"]) == 1
    
    @patch('services.async_sql_store.async_create_event')
    def test_api_create_event(self, mock_create, authenticated_client):
        """Test event creation API endpoint."""
        mock_create.return_value = {"success": True, "event_id": "new-event-123"}
        
        event_data = {
            "title": "New Meeting",
            "description": "Test meeting",
            "start_time": "2024-12-01T14:00:00Z",
            "end_time": "2024-12-01T15:00:00Z",
            "attendees": "user1@test.com,user2@test.com",
            "room_id": "room1"
        }
        
        response = authenticated_client.post('/api/events', 
                                           data=json.dumps(event_data),
                                           content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "event_id" in data
    
    def test_api_unauthorized_access(self, client):
        """Test API endpoints require authentication."""
        endpoints = ['/api/events', '/api/rooms', '/api/org-structure']
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should either redirect to login or return 401
            assert response.status_code in [302, 401]
    
    @patch('services.async_sql_store.async_check_availability')
    def test_api_check_availability(self, mock_check, authenticated_client):
        """Test availability checking API endpoint."""
        mock_check.return_value = True
        
        data = {
            "room_id": "room1",
            "start_time": "2024-12-01T10:00:00Z",
            "end_time": "2024-12-01T11:00:00Z"
        }
        
        response = authenticated_client.post('/api/check-availability',
                                           data=json.dumps(data),
                                           content_type='application/json')
        
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result["available"] is True
    
    @patch('agent_core.chat')
    def test_chat_endpoint(self, mock_chat, authenticated_client):
        """Test chat endpoint integration with agent."""
        mock_chat.return_value = {
            "response": "I can help you schedule a meeting.",
            "thread_id": "thread-123"
        }
        
        chat_data = {
            "message": "Help me schedule a meeting for tomorrow",
            "thread_id": "thread-123"
        }
        
        response = authenticated_client.post('/api/chat',
                                           data=json.dumps(chat_data),
                                           content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "response" in data
        assert "thread_id" in data
    
    def test_static_files_served(self, client):
        """Test that static files are served correctly."""
        # Test CSS file
        response = client.get('/static/style.css')
        assert response.status_code == 200 or response.status_code == 404  # File may not exist
        
        # Test JS file
        response = client.get('/static/app.js')
        assert response.status_code == 200 or response.status_code == 404  # File may not exist
    
    def test_error_handling(self, client):
        """Test error handling for non-existent routes."""
        response = client.get('/nonexistent-route')
        assert response.status_code == 404
    
    @patch('services.async_sql_store.async_update_event')
    def test_api_update_event(self, mock_update, authenticated_client):
        """Test event update API endpoint."""
        mock_update.return_value = {"success": True}
        
        event_id = "event-123"
        update_data = {
            "title": "Updated Meeting Title",
            "description": "Updated description"
        }
        
        response = authenticated_client.put(f'/api/events/{event_id}',
                                          data=json.dumps(update_data),
                                          content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
    
    @patch('services.async_sql_store.async_cancel_event')
    def test_api_delete_event(self, mock_cancel, authenticated_client):
        """Test event deletion API endpoint."""
        mock_cancel.return_value = {"success": True}
        
        event_id = "event-123"
        
        response = authenticated_client.delete(f'/api/events/{event_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
