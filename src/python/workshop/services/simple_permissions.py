"""
Simple permission system for university calendar demo.
Just enough to show group-based room booking with basic authorization.
"""

import json
import os
from typing import Dict, List, Optional


class SimplePermissionChecker:
    """Basic permission checker for demo purposes."""
    
    def __init__(self):
        self.users = self._load_users()
        self.groups = self._load_groups()
        self.rooms = self._load_rooms()
    
    def _load_users(self) -> Dict:
        """Load user directory from local file first, then try Azure if available."""
        users = {}
        
        # First try local file (primary source for demo)
        try:
            data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'json', 'user_directory_local.json')
            with open(data_path, 'r') as f:
                users = json.load(f)
                print(f"✅ Loaded {len(users)} users from local directory")
        except FileNotFoundError:
            print("⚠️ Local user directory not found")
        
        # Optionally merge with Azure source if available
        try:
            import httpx
            url = os.getenv("USER_DIRECTORY_URL")
            if url:
                response = httpx.get(url, timeout=5)
                response.raise_for_status()
                azure_users = response.json()
                print(f"✅ Also loaded {len(azure_users)} users from Azure")
                # Merge (local takes precedence)
                for key, value in azure_users.items():
                    if key not in users:
                        users[key] = value
        except Exception as e:
            print(f"ℹ️ Azure user directory not available: {e}")
        
        return users
    
    def _load_groups(self) -> Dict:
        """Load group calendars."""
        try:
            data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'json', 'group_calendars.json')
            with open(data_path, 'r') as f:
                data = json.load(f)
                return {g['id']: g for g in data.get('group_calendars', [])}
        except FileNotFoundError:
            return {}
    
    def _load_rooms(self) -> Dict:
        """Load rooms."""
        try:
            data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'json', 'rooms.json')
            with open(data_path, 'r') as f:
                data = json.load(f)
                return {r['id']: r for r in data.get('rooms', [])}
        except FileNotFoundError:
            return {}
    
    def can_user_book_room_for_group(self, user_id: str, room_id: str, group_id: str) -> tuple[bool, str]:
        """
        Check if user can book a room for a group.
        Returns (can_book, reason)
        """
        # Check if user exists
        if user_id not in self.users:
            return False, f"User '{user_id}' not found"
        
        user = self.users[user_id]
        
        # Check if user is member of the group
        user_groups = user.get('group_memberships', [])
        if group_id not in user_groups:
            return False, f"User '{user['name']}' is not a member of group '{group_id}'"
        
        # Check if group exists
        if group_id not in self.groups:
            return False, f"Group '{group_id}' not found"
        
        group = self.groups[group_id]
        
        # Check if room exists
        if room_id not in self.rooms:
            return False, f"Room '{room_id}' not found"
        
        room = self.rooms[room_id]
        
        # Check if group can use this room
        allowed_rooms = group.get('allowed_rooms', [])
        if room_id not in allowed_rooms:
            return False, f"Group '{group['name']}' is not authorized to use '{room['name']}'"
        
        return True, f"✓ User '{user['name']}' can book '{room['name']}' for '{group['name']}'"
    
    def get_user_groups(self, user_id: str) -> List[str]:
        """Get list of groups user belongs to."""
        if user_id not in self.users:
            return []
        return self.users[user_id].get('group_memberships', [])
    
    def get_group_rooms(self, group_id: str) -> List[str]:
        """Get list of rooms group can book."""
        if group_id not in self.groups:
            return []
        return self.groups[group_id].get('allowed_rooms', [])


# Global instance for easy access
permission_checker = SimplePermissionChecker()
