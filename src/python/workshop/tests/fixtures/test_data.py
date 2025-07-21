"""
Test fixtures for the Calendar Scheduler Agent tests.
Contains reusable test data and configuration.
"""

import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any

# Sample calendar events
SAMPLE_EVENTS = [
    {
        "id": "event_001",
        "title": "Team Standup",
        "start": "2024-01-15T09:00:00Z",
        "end": "2024-01-15T09:30:00Z",
        "location": "Conference Room A",
        "description": "Daily team standup meeting",
        "attendees": ["alice@example.com", "bob@example.com", "charlie@example.com"],
        "created": "2024-01-01T00:00:00Z",
        "updated": "2024-01-01T00:00:00Z",
        "status": "confirmed",
        "organizer": "alice@example.com",
        "room_id": "room_001",
        "calendar_id": "calendar_001"
    },
    {
        "id": "event_002",
        "title": "Project Planning",
        "start": "2024-01-15T10:00:00Z",
        "end": "2024-01-15T11:30:00Z",
        "location": "Conference Room B",
        "description": "Monthly project planning session",
        "attendees": ["alice@example.com", "david@example.com", "eve@example.com"],
        "created": "2024-01-01T00:00:00Z",
        "updated": "2024-01-01T00:00:00Z",
        "status": "confirmed",
        "organizer": "david@example.com",
        "room_id": "room_002",
        "calendar_id": "calendar_001"
    },
    {
        "id": "event_003",
        "title": "Client Meeting",
        "start": "2024-01-15T14:00:00Z",
        "end": "2024-01-15T15:00:00Z",
        "location": "Conference Room C",
        "description": "Quarterly client review meeting",
        "attendees": ["alice@example.com", "client@company.com"],
        "created": "2024-01-01T00:00:00Z",
        "updated": "2024-01-01T00:00:00Z",
        "status": "confirmed",
        "organizer": "alice@example.com",
        "room_id": "room_003",
        "calendar_id": "calendar_001"
    },
    {
        "id": "event_004",
        "title": "Training Session",
        "start": "2024-01-15T15:30:00Z",
        "end": "2024-01-15T16:30:00Z",
        "location": "Training Room",
        "description": "Azure AI Services training",
        "attendees": ["bob@example.com", "charlie@example.com", "eve@example.com"],
        "created": "2024-01-01T00:00:00Z",
        "updated": "2024-01-01T00:00:00Z",
        "status": "confirmed",
        "organizer": "bob@example.com",
        "room_id": "room_004",
        "calendar_id": "calendar_001"
    }
]

# Sample rooms
SAMPLE_ROOMS = [
    {
        "id": "room_001",
        "name": "Conference Room A",
        "capacity": 8,
        "equipment": ["projector", "whiteboard", "video_conferencing"],
        "location": "Building A, Floor 2",
        "available": True,
        "features": ["wireless_display", "phone_conference"],
        "booking_url": "https://booking.example.com/room_001"
    },
    {
        "id": "room_002",
        "name": "Conference Room B",
        "capacity": 12,
        "equipment": ["large_screen", "whiteboard", "video_conferencing"],
        "location": "Building A, Floor 2",
        "available": True,
        "features": ["wireless_display", "phone_conference", "recording"],
        "booking_url": "https://booking.example.com/room_002"
    },
    {
        "id": "room_003",
        "name": "Conference Room C",
        "capacity": 6,
        "equipment": ["tv", "whiteboard"],
        "location": "Building B, Floor 1",
        "available": True,
        "features": ["wireless_display"],
        "booking_url": "https://booking.example.com/room_003"
    },
    {
        "id": "room_004",
        "name": "Training Room",
        "capacity": 20,
        "equipment": ["projector", "sound_system", "microphones"],
        "location": "Building B, Floor 1",
        "available": True,
        "features": ["wireless_display", "recording", "streaming"],
        "booking_url": "https://booking.example.com/room_004"
    },
    {
        "id": "room_005",
        "name": "Executive Boardroom",
        "capacity": 15,
        "equipment": ["large_screen", "video_conferencing", "sound_system"],
        "location": "Building A, Floor 3",
        "available": True,
        "features": ["wireless_display", "phone_conference", "recording", "catering"],
        "booking_url": "https://booking.example.com/room_005"
    }
]

# Sample availability responses
SAMPLE_AVAILABILITY = {
    "available": {
        "room_id": "room_001",
        "available": True,
        "conflicts": [],
        "checked_at": "2024-01-15T08:00:00Z",
        "next_available": "2024-01-15T08:00:00Z"
    },
    "busy": {
        "room_id": "room_002",
        "available": False,
        "conflicts": [
            {
                "id": "event_002",
                "title": "Project Planning",
                "start": "2024-01-15T10:00:00Z",
                "end": "2024-01-15T11:30:00Z"
            }
        ],
        "checked_at": "2024-01-15T08:00:00Z",
        "next_available": "2024-01-15T11:30:00Z"
    },
    "partially_available": {
        "room_id": "room_003",
        "available": True,
        "conflicts": [
            {
                "id": "event_003",
                "title": "Client Meeting",
                "start": "2024-01-15T14:00:00Z",
                "end": "2024-01-15T15:00:00Z"
            }
        ],
        "checked_at": "2024-01-15T08:00:00Z",
        "next_available": "2024-01-15T15:00:00Z"
    }
}

# Sample evaluation responses
SAMPLE_EVALUATIONS = {
    "excellent": {
        "relevance": 0.95,
        "helpfulness": 0.92,
        "accuracy": 0.94,
        "clarity": 0.90,
        "completeness": 0.88,
        "overall_score": 0.92,
        "feedback": "Excellent response with high relevance and accuracy",
        "suggestions": []
    },
    "good": {
        "relevance": 0.85,
        "helpfulness": 0.82,
        "accuracy": 0.87,
        "clarity": 0.80,
        "completeness": 0.78,
        "overall_score": 0.82,
        "feedback": "Good response with room for improvement in clarity",
        "suggestions": ["Be more specific in the response", "Add more context"]
    },
    "poor": {
        "relevance": 0.45,
        "helpfulness": 0.40,
        "accuracy": 0.50,
        "clarity": 0.35,
        "completeness": 0.30,
        "overall_score": 0.40,
        "feedback": "Poor response needs significant improvement",
        "suggestions": [
            "Improve relevance to the user's question",
            "Provide more helpful information",
            "Check accuracy of facts",
            "Clarify the response"
        ]
    }
}

# Sample user profiles
SAMPLE_USERS = [
    {
        "id": "user_001",
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "role": "Team Lead",
        "permissions": ["read", "write", "admin"],
        "calendar_id": "calendar_001",
        "timezone": "UTC",
        "preferences": {
            "notification_method": "email",
            "meeting_reminders": True,
            "default_meeting_duration": 30
        }
    },
    {
        "id": "user_002",
        "name": "Bob Smith",
        "email": "bob@example.com",
        "role": "Developer",
        "permissions": ["read", "write"],
        "calendar_id": "calendar_002",
        "timezone": "UTC",
        "preferences": {
            "notification_method": "slack",
            "meeting_reminders": True,
            "default_meeting_duration": 60
        }
    },
    {
        "id": "user_003",
        "name": "Charlie Brown",
        "email": "charlie@example.com",
        "role": "Developer",
        "permissions": ["read"],
        "calendar_id": "calendar_003",
        "timezone": "UTC",
        "preferences": {
            "notification_method": "email",
            "meeting_reminders": False,
            "default_meeting_duration": 45
        }
    }
]

# Sample MCP server responses
SAMPLE_MCP_RESPONSES = {
    "event_created": {
        "status": "success",
        "data": {
            "id": "event_new_001",
            "title": "New Meeting",
            "start": "2024-01-16T10:00:00Z",
            "end": "2024-01-16T11:00:00Z",
            "location": "Conference Room A",
            "created": "2024-01-15T08:00:00Z",
            "status": "confirmed"
        },
        "message": "Event created successfully"
    },
    "event_updated": {
        "status": "success",
        "data": {
            "id": "event_001",
            "title": "Updated Meeting",
            "start": "2024-01-16T11:00:00Z",
            "end": "2024-01-16T12:00:00Z",
            "location": "Conference Room B",
            "updated": "2024-01-15T08:00:00Z",
            "status": "confirmed"
        },
        "message": "Event updated successfully"
    },
    "event_deleted": {
        "status": "success",
        "data": {
            "id": "event_001",
            "deleted": True
        },
        "message": "Event deleted successfully"
    },
    "error_response": {
        "status": "error",
        "error": {
            "code": "ROOM_NOT_AVAILABLE",
            "message": "The requested room is not available at the specified time",
            "details": {
                "room_id": "room_001",
                "requested_time": "2024-01-15T10:00:00Z",
                "conflict_with": "event_002"
            }
        }
    }
}

# Sample conversation contexts
SAMPLE_CONVERSATIONS = [
    {
        "id": "conv_001",
        "messages": [
            {
                "role": "user",
                "content": "Schedule a meeting for tomorrow at 2 PM",
                "timestamp": "2024-01-15T08:00:00Z"
            },
            {
                "role": "assistant",
                "content": "I'll help you schedule a meeting for tomorrow at 2 PM. Let me check room availability.",
                "timestamp": "2024-01-15T08:00:01Z"
            },
            {
                "role": "assistant",
                "content": "I found Conference Room A is available tomorrow at 2 PM. Would you like me to book it?",
                "timestamp": "2024-01-15T08:00:05Z"
            }
        ]
    },
    {
        "id": "conv_002",
        "messages": [
            {
                "role": "user",
                "content": "What rooms are available for a team meeting next week?",
                "timestamp": "2024-01-15T08:00:00Z"
            },
            {
                "role": "assistant",
                "content": "Let me check the available rooms for next week. I'll look for rooms that can accommodate team meetings.",
                "timestamp": "2024-01-15T08:00:01Z"
            }
        ]
    }
]

# Sample error scenarios
SAMPLE_ERRORS = {
    "network_error": {
        "type": "NetworkError",
        "message": "Unable to connect to the calendar service",
        "code": "NETWORK_ERROR",
        "retryable": True
    },
    "permission_error": {
        "type": "PermissionError",
        "message": "User does not have permission to access this resource",
        "code": "PERMISSION_DENIED",
        "retryable": False
    },
    "validation_error": {
        "type": "ValidationError",
        "message": "Invalid date format provided",
        "code": "VALIDATION_ERROR",
        "retryable": False
    },
    "timeout_error": {
        "type": "TimeoutError",
        "message": "Request timed out after 30 seconds",
        "code": "TIMEOUT",
        "retryable": True
    }
}

# Test configuration
TEST_CONFIG = {
    "database_url": "sqlite:///test.db",
    "redis_url": "redis://localhost:6379/0",
    "mcp_server_url": "http://localhost:8000",
    "azure_endpoint": "https://test.openai.azure.com/",
    "timeout_seconds": 30,
    "max_retries": 3,
    "test_mode": True
}

# Helper functions for test data
def get_events_for_date(date_str: str) -> List[Dict[str, Any]]:
    """Get events for a specific date."""
    return [event for event in SAMPLE_EVENTS if event["start"].startswith(date_str)]

def get_available_rooms(time_slot: str) -> List[Dict[str, Any]]:
    """Get available rooms for a specific time slot."""
    # This is a simplified implementation
    return [room for room in SAMPLE_ROOMS if room["available"]]

def get_user_by_email(email: str) -> Dict[str, Any]:
    """Get user by email address."""
    return next((user for user in SAMPLE_USERS if user["email"] == email), None)

def create_mock_event(title: str, start: str, end: str, room_id: str = "room_001") -> Dict[str, Any]:
    """Create a mock event for testing."""
    return {
        "id": f"event_{hash(title + start) % 10000}",
        "title": title,
        "start": start,
        "end": end,
        "location": next((room["name"] for room in SAMPLE_ROOMS if room["id"] == room_id), "Unknown Room"),
        "description": f"Test event: {title}",
        "created": datetime.now(timezone.utc).isoformat(),
        "updated": datetime.now(timezone.utc).isoformat(),
        "status": "confirmed",
        "room_id": room_id,
        "calendar_id": "calendar_001"
    }

def create_mock_availability(room_id: str, available: bool = True, conflicts: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a mock availability response."""
    return {
        "room_id": room_id,
        "available": available,
        "conflicts": conflicts or [],
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "next_available": datetime.now(timezone.utc).isoformat() if available else None
    }

def create_mock_evaluation(score: float = 0.85) -> Dict[str, Any]:
    """Create a mock evaluation response."""
    return {
        "relevance": score,
        "helpfulness": score,
        "accuracy": score,
        "clarity": score * 0.9,
        "completeness": score * 0.95,
        "overall_score": score,
        "feedback": f"Response scored {score:.2f}",
        "suggestions": [] if score > 0.8 else ["Improve clarity", "Add more details"]
    }

# Export all fixtures as JSON strings for easy use in tests
def get_events_json() -> str:
    """Get sample events as JSON string."""
    return json.dumps(SAMPLE_EVENTS, indent=2)

def get_rooms_json() -> str:
    """Get sample rooms as JSON string."""
    return json.dumps(SAMPLE_ROOMS, indent=2)

def get_availability_json(scenario: str = "available") -> str:
    """Get sample availability as JSON string."""
    return json.dumps(SAMPLE_AVAILABILITY.get(scenario, SAMPLE_AVAILABILITY["available"]), indent=2)

def get_evaluation_json(quality: str = "good") -> str:
    """Get sample evaluation as JSON string."""
    return json.dumps(SAMPLE_EVALUATIONS.get(quality, SAMPLE_EVALUATIONS["good"]), indent=2)

# Test date utilities
def get_test_date(days_offset: int = 0) -> str:
    """Get test date with offset."""
    base_date = datetime(2024, 1, 15, tzinfo=timezone.utc)
    test_date = base_date + timedelta(days=days_offset)
    return test_date.isoformat()

def get_test_time_range(start_hour: int = 10, duration_hours: int = 1) -> tuple:
    """Get test time range."""
    start_time = datetime(2024, 1, 15, start_hour, 0, 0, tzinfo=timezone.utc)
    end_time = start_time + timedelta(hours=duration_hours)
    return start_time.isoformat(), end_time.isoformat()

# Constants for easy importing
SAMPLE_EVENT_JSON = get_events_json()
SAMPLE_ROOMS_JSON = get_rooms_json()
SAMPLE_AVAILABILITY_JSON = get_availability_json()
SAMPLE_EVALUATION_JSON = get_evaluation_json()

# Test markers and categories
TEST_MARKERS = {
    "unit": "Unit tests",
    "integration": "Integration tests",
    "smoke": "Smoke tests",
    "azure": "Tests requiring Azure services",
    "mcp": "Tests for MCP client functionality",
    "permissions": "Tests for permission system",
    "evaluation": "Tests for evaluation system",
    "slow": "Slow-running tests",
    "benchmark": "Performance benchmark tests"
}
