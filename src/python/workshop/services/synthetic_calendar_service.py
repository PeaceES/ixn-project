import datetime
import json
import os
from typing import List, Dict, Any, Optional
import uuid
import random

from services.calendar_service import CalendarServiceInterface


class SyntheticCalendarService(CalendarServiceInterface):
    """Implementation of the calendar service using synthetic data"""
    
    def __init__(self):
        """Initialize the synthetic calendar service"""
        self.data_file = os.path.join(os.path.dirname(__file__), "..", "data", "json", "synthetic_calendar.json")
        self.rooms = []
        self.events = []
        self._ensure_data_directory()
        self._load_data()
        
    def _ensure_data_directory(self):
        """Ensure the data directory exists"""
        data_dir = os.path.dirname(self.data_file)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
    def _load_data(self):
        """Load synthetic calendar data from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.rooms = data.get('rooms', [])
                    self.events = data.get('events', [])
                    # Convert string dates back to datetime objects
                    for event in self.events:
                        if isinstance(event.get('start_time'), str):
                            event['start_time'] = datetime.datetime.fromisoformat(event['start_time'])
                        if isinstance(event.get('end_time'), str):
                            event['end_time'] = datetime.datetime.fromisoformat(event['end_time'])
            else:
                self.rooms = []
                self.events = []
        except Exception as e:
            print(f"Error loading calendar data: {e}")
            self.rooms = []
            self.events = []
    
    def _save_data(self):
        """Save synthetic calendar data to JSON file"""
        try:
            # Convert datetime objects to strings for JSON serialization
            events_for_json = []
            for event in self.events:
                event_copy = event.copy()
                if isinstance(event_copy.get('start_time'), datetime.datetime):
                    event_copy['start_time'] = event_copy['start_time'].isoformat()
                if isinstance(event_copy.get('end_time'), datetime.datetime):
                    event_copy['end_time'] = event_copy['end_time'].isoformat()
                events_for_json.append(event_copy)
            
            data = {
                'rooms': self.rooms,
                'events': events_for_json
            }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving calendar data: {e}")
    
    async def get_events(self, start_date: datetime.datetime, 
                        end_date: datetime.datetime, 
                        room_id: Optional[str] = None) -> str:
        """Get events within a date range, optionally filtered by room"""
        filtered_events = []
        
        # Make sure start_date and end_date are datetime objects
        if isinstance(start_date, str):
            start_date = datetime.datetime.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = datetime.datetime.fromisoformat(end_date)
        
        for event in self.events:
            event_start = event['start_time']
            event_end = event['end_time']
            
            # Check if event overlaps with date range
            if event_start <= end_date and event_end >= start_date:
                if room_id is None or event.get('room_id') == room_id:
                    # Convert datetime objects to strings for JSON response
                    event_copy = event.copy()
                    if isinstance(event_copy.get('start_time'), datetime.datetime):
                        event_copy['start_time'] = event_copy['start_time'].isoformat()
                    if isinstance(event_copy.get('end_time'), datetime.datetime):
                        event_copy['end_time'] = event_copy['end_time'].isoformat()
                    filtered_events.append(event_copy)
                    
        return json.dumps(filtered_events)
    
    async def get_rooms(self) -> str:
        """Get list of all available rooms"""
        return json.dumps(self.rooms)
    
    async def check_room_availability(self, room_id: str,
                                     start_time: datetime.datetime,
                                     end_time: datetime.datetime) -> str:
        """Check if a room is available during the specified time period"""
        try:
            # Convert string times to datetime if needed
            if isinstance(start_time, str):
                start_time = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            if isinstance(end_time, str):
                end_time = datetime.datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            # Check if room exists
            room_exists = any(room['id'] == room_id for room in self.rooms)
            if not room_exists:
                return json.dumps({"available": False, "error": "Room not found"})
            
            # Check for conflicts with existing events
            for event in self.events:
                if event.get('room_id') == room_id:
                    event_start = event['start_time']
                    event_end = event['end_time']
                    
                    # Check for time overlap
                    if start_time < event_end and end_time > event_start:
                        return json.dumps({
                            "available": False,
                            "conflict": {
                                "event_title": event.get('title'),
                                "start_time": event_start.isoformat(),
                                "end_time": event_end.isoformat()
                            }
                        })
            
            return json.dumps({"available": True})
            
        except Exception as e:
            return json.dumps({"available": False, "error": str(e)})
    
    async def schedule_event(self, title: str, start_time: str, end_time: str, 
                            room_id: str, organizer: str, description: str = "") -> str:
        """
        Schedule a new event if the room is available.
        
        Args:
            title: Event title
            start_time: Start time of the event (ISO format string)
            end_time: End time of the event (ISO format string)
            room_id: Room identifier
            organizer: Event organizer
            description: Event description (optional)
            
        Returns:
            JSON string of the created event
            
        Raises:
            ValueError: If room is not available or required fields are missing
        """
        try:
            # Validate required fields
            if not all([title, start_time, end_time, room_id, organizer]):
                return json.dumps({
                    "success": False,
                    "error": "Missing required fields"
                })
            
            # Parse datetime strings
            start_dt = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            # Check room availability
            availability_check = json.loads(await self.check_room_availability(room_id, start_dt, end_dt))
            
            if not availability_check.get("available", False):
                return json.dumps({
                    "success": False,
                    "error": "Room is not available during the requested time",
                    "conflict": availability_check.get("conflict")
                })
            
            # Create new event
            new_event = {
                "id": str(uuid.uuid4()),
                "title": title,
                "start_time": start_dt,
                "end_time": end_dt,
                "room_id": room_id,
                "organizer": organizer,
                "description": description
            }
            
            self.events.append(new_event)
            self._save_data()
            
            return json.dumps({
                "success": True,
                "event": {
                    "id": new_event["id"],
                    "title": new_event["title"],
                    "start_time": new_event["start_time"].isoformat(),
                    "end_time": new_event["end_time"].isoformat(),
                    "room_id": new_event["room_id"],
                    "organizer": new_event["organizer"],
                    "description": new_event["description"]
                }
            })
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Error scheduling event: {str(e)}"
            })
    
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
        try:
            # Generate rooms if they don't exist
            if not self.rooms:
                buildings = ["Science Hall", "Engineering Complex", "Student Center", "Arts Building", "Business Hall"]
                room_types = ["Classroom", "Laboratory", "Conference Room", "Auditorium", "Study Room"]
                features = ["Projector", "Whiteboard", "Computers", "Video Conference", "Audio System"]
                accessibility = ["Wheelchair Accessible", "Hearing Loop", "Braille Signage"]
                
                for i in range(num_rooms):
                    building = random.choice(buildings)
                    room_type = random.choice(room_types)
                    capacity = random.choice([20, 30, 40, 50, 75, 100, 150, 200])
                    
                    room = {
                        "id": f"{building.split()[0][:2].upper()}-{100 + i}",
                        "name": f"Room {building.split()[0][:2]}-{100 + i}",
                        "building": building,
                        "type": room_type,
                        "capacity": capacity,
                        "features": random.sample(features, random.randint(1, 3)),
                        "accessibility": random.sample(accessibility, random.randint(0, 2))
                    }
                    self.rooms.append(room)
            
            # Generate events if they don't exist or if we need more
            current_events = len(self.events)
            events_to_generate = max(0, num_events - current_events)
            
            if events_to_generate > 0:
                event_titles = [
                    "Department Meeting", "Workshop", "Seminar", "Conference", "Training Session",
                    "Team Meeting", "Presentation", "Lecture", "Lab Session", "Study Group"
                ]
                organizers = ["Dr. Smith", "Prof. Johnson", "Ms. Davis", "Mr. Wilson", "Dr. Brown"]
                
                base_date = datetime.datetime.now()
                
                for i in range(events_to_generate):
                    # Random date within next 30 days
                    days_offset = random.randint(0, 30)
                    hour = random.randint(8, 17)  # 8 AM to 5 PM
                    duration = random.choice([1, 2, 3, 4])  # 1-4 hours
                    
                    start_time = base_date + datetime.timedelta(days=days_offset, hours=hour-base_date.hour, minutes=-base_date.minute, seconds=-base_date.second, microseconds=-base_date.microsecond)
                    end_time = start_time + datetime.timedelta(hours=duration)
                    
                    event = {
                        "id": str(uuid.uuid4()),
                        "title": random.choice(event_titles),
                        "start_time": start_time,
                        "end_time": end_time,
                        "room_id": random.choice(self.rooms)["id"],
                        "organizer": random.choice(organizers),
                        "description": f"Scheduled event organized by {random.choice(organizers)}"
                    }
                    self.events.append(event)
            
            self._save_data()
            return len(self.rooms), len(self.events)
            
        except Exception as e:
            print(f"Error generating synthetic data: {e}")
            return 0, 0