from abc import ABC, abstractmethod
import datetime
from typing import List, Dict, Any, Optional


class CalendarServiceInterface(ABC):
    """Interface for calendar services (both synthetic and real API implementations)"""
    
    @abstractmethod
    async def get_events(self, start_date: datetime.datetime, 
                       end_date: datetime.datetime, 
                       room_id: Optional[str] = None) -> str:
        """
        Get events within a date range, optionally filtered by room.
        
        Args:
            start_date: The beginning of the date range
            end_date: The end of the date range
            room_id: Optional room identifier to filter events
            
        Returns:
            JSON string of event dictionaries
        """
        pass
    
    @abstractmethod
    async def get_rooms(self) -> str:
        """
        Get list of all available rooms.
        
        Returns:
            JSON string of room dictionaries
        """
        pass
    
    @abstractmethod
    async def check_room_availability(self, room_id: str,
                                    start_time: datetime.datetime,
                                    end_time: datetime.datetime) -> str:
        """
        Check if a room is available during the specified time period.
        
        Args:
            room_id: The identifier of the room to check
            start_time: The start time of the period to check
            end_time: The end time of the period to check
            
        Returns:
            JSON string indicating availability
        """
        pass
    
    @abstractmethod
    async def schedule_event(self, event_data: Dict[str, Any]) -> str:
        """
        Schedule a new event if the room is available.
        
        Args:
            event_data: Dictionary containing event details including:
                - title: Event title
                - start_time: Start time of the event
                - end_time: End time of the event
                - room_id: Room identifier
                - organizer: Event organizer
                - description (optional): Event description
                
        Returns:
            JSON string of the created event
            
        Raises:
            ValueError: If room is not available or required fields are missing
        """
        pass
    
    @abstractmethod
    async def generate_synthetic_data(self, num_rooms: int = 10, 
                                   num_events: int = 50) -> tuple[int, int]:
        """
        Generate synthetic calendar data for testing.
        
        Args:
            num_rooms: Number of rooms to generate
            num_events: Number of events to generate
            
        Returns:
            Tuple of (number of rooms created, number of events created)
        """
        pass