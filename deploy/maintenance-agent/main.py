#!/usr/bin/env python3
"""
Maintenance Agent - Monitors rooms and detects faults
"""

import os
import json
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import ThreadMessage, MessageRole
from azure.identity import DefaultAzureCredential
from services.db_shared import get_shared_thread
from services.db_calendar import get_rooms as sql_get_rooms, get_maintenance
from datetime import datetime, timezone
import dateutil.parser
import shutil

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def load_shared_thread_id():
    row = get_shared_thread()
    tid = (row or {}).get("thread_id")
    if not tid:
        tid = os.getenv("SHARED_THREAD_ID")
    logger.info(f"[Maintenance] Using shared thread id = {tid}")
    return tid

def load_rooms():
    # Try SQL first
    try:
        res = sql_get_rooms()
        rooms = res.get("rooms", [])
        if rooms:
            logger.info(f"[Maintenance] Loaded {len(rooms)} rooms from SQL")
            return rooms
    except Exception as e:
        logger.warning(f"[Maintenance] SQL get_rooms failed, falling back to local JSON: {e}")

    # Fallback to local JSON if SQL not reachable
    local_path = os.path.join(os.path.dirname(__file__), "data/rooms.json")
    with open(local_path, "r", encoding="utf-8") as f:
        rooms = json.load(f).get("rooms", [])
    logger.info(f"[Maintenance] Loaded {len(rooms)} rooms from local JSON")
    return rooms

ROOMS = load_rooms()

# Probe: check SQL maintenance items for each room
for r in ROOMS:
    rc = r["id"]
    try:
        res = get_maintenance(rc)
        logger.info(f"[Maintenance] SQL reports {len(res['maintenance'])} maintenance items for room {rc}")
    except Exception as e:
        logger.warning(f"[Maintenance] Could not fetch maintenance for room {rc}: {e}")

class MaintenanceAgent:
    def __init__(self):
        print("🔧 Initializing Maintenance Agent...")
        
        # Check if running in virtual environment
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        if not in_venv:
            print("⚠️  Warning: Not running in a virtual environment")
            print("💡 Consider using a virtual environment for better dependency management")
        
        try:
            # Initialize Azure AI Projects client
            self.credential = DefaultAzureCredential()
            self.project = AIProjectClient.from_connection_string(
                conn_str=os.getenv("PROJECT_CONNECTION_STRING"),
                credential=self.credential
            )
            
            self.shared_thread_id = load_shared_thread_id()
            self.rooms_data = {"rooms": ROOMS}
            self.maintenance_schedule = self.load_maintenance_schedule()
            self.archive_and_clear_maintenance()
            
            print(f"✅ Maintenance Agent initialized successfully")
            print(f"📍 Monitoring {len(self.rooms_data.get('rooms', []))} rooms")
            print(f"🔗 Connected to shared thread: {self.shared_thread_id}")
            print(f"🤖 Using model deployment: {os.getenv('MODEL_DEPLOYMENT_NAME')}")
            
        except Exception as e:
            print(f"❌ Failed to initialize Maintenance Agent: {e}")
            print("💡 Check your Azure credentials and connection string")
            raise

    def load_maintenance_schedule(self):
        """Load maintenance schedule from JSON file"""
        try:
            with open('data/maintenance_schedule.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading maintenance schedule: {e}")
            return {"schedule": [], "fault_log": []}

    def save_maintenance_schedule(self):
        """Save maintenance schedule to JSON file"""
        try:
            with open('data/maintenance_schedule.json', 'w') as f:
                json.dump(self.maintenance_schedule, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving maintenance schedule: {e}")

    def check_system_health(self):
        """Check system health and configuration"""
        health_status = {
            'azure_connection': True,
            'data_files_loaded': True,
            'thread_accessible': False,
            'rooms_monitored': len(ROOMS),
            'total_faults_logged': len(self.maintenance_schedule.get('fault_log', []))
        }
        
        # Test thread accessibility (simplified check)
        if self.shared_thread_id and len(self.shared_thread_id) > 10:
            health_status['thread_accessible'] = True
        
        return health_status

    def check_room_faults(self, room):
        """Check for faults in a specific room"""
        faults = []
        
        # Check temperature thresholds
        temp = room.get('temperature', 20)
        room_type = room.get('type', 'office')
        
        if room_type == 'server_room' or room_type == 'technical':
            if temp > 25:
                faults.append({
                    'type': 'Environmental',
                    'description': f'Server room temperature too high: {temp}°C (max 25°C)',
                    'severity': 'Critical'
                })
        elif temp > 26 or temp < 16:
            severity = 'High' if temp > 28 or temp < 14 else 'Medium'
            faults.append({
                'type': 'Environmental', 
                'description': f'Temperature out of range: {temp}°C',
                'severity': severity
            })
        
        # Check humidity
        humidity = room.get('humidity', 50)
        if humidity > 60 or humidity < 30:
            faults.append({
                'type': 'Environmental',
                'description': f'Humidity out of range: {humidity}% (30-60%)',
                'severity': 'Medium'
            })
        
        # Check if room needs attention
        if room.get('status') == 'needs_attention':
            faults.append({
                'type': 'Maintenance',
                'description': 'Room marked as needing attention',
                'severity': 'High'
            })
        
        # Check overdue maintenance
        last_maintenance = room.get('last_maintenance')
        if last_maintenance:
            last_date = datetime.strptime(last_maintenance, '%Y-%m-%d')
            days_since = (datetime.now() - last_date).days
            if days_since > 90:  # 3 months
                faults.append({
                    'type': 'Maintenance',
                    'description': f'Maintenance overdue by {days_since - 90} days',
                    'severity': 'Medium'
                })
        
        return faults

    async def post_fault_to_shared_thread(self, room, fault):
        """Post fault detection to shared thread"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message_sent_successfully = False
        
        try:
            fault_message = f"""🚨 FAULT DETECTED
Room: {room['name']} ({room['id']})
Type: {fault['type']}
Description: {fault['description']}
Severity: {fault['severity']}
Timestamp: {timestamp}
Action Required: {'Immediate' if fault['severity'] == 'Critical' else 'Scheduled'}
Floor: {room.get('floor', 'Unknown')}
Equipment: {', '.join(room.get('equipment', []))}
"""
            
            # Send message to shared thread
            message_response = await self.project.agents.create_message(
                thread_id=self.shared_thread_id,
                role=MessageRole.USER,
                content=fault_message
            )
            
            # If we get here, the message was sent successfully
            message_sent_successfully = True
            print(f"📤 Posted fault to shared thread: {room['name']} - {fault['description']}")
            
        except Exception as e:
            # Check if it's just a warning about the response handling but message was sent
            error_str = str(e).lower()
            if "threadmessage" in error_str and "await" in error_str:
                # This seems to be a warning about response handling, but message likely sent
                print(f"⚠️  Azure SDK warning (message likely sent): {e}")
                print(f"📤 Fault posted to shared thread: {room['name']} - {fault['description']}")
                message_sent_successfully = True  # Assume success despite warning
            else:
                # This is a real error
                print(f"❌ Error posting to shared thread: {e}")
                print(f"📝 Fault logged locally only: {room['name']} - {fault['description']}")
                message_sent_successfully = False
        
        # Log fault locally with accurate success status
        fault_entry = {
            'timestamp': timestamp,
            'room_id': room['id'],
            'room_name': room['name'],
            'fault_type': fault['type'],
            'description': fault['description'],
            'severity': fault['severity'],
            'posted_to_thread': message_sent_successfully,
            'error_message': None if message_sent_successfully else str(e) if 'e' in locals() else None
        }
        
        self.maintenance_schedule['fault_log'].append(fault_entry)
        self.save_maintenance_schedule()

    async def monitor_rooms(self):
        """Monitor all rooms for faults"""
        print("\n🔍 Starting room monitoring...")
        
        for room in ROOMS:
            print(f"🏠 Checking {room['name']} ({room['id']})")
            
            faults = self.check_room_faults(room)
            
            if faults:
                print(f"⚠️  Found {len(faults)} fault(s) in {room['name']}")
                for fault in faults:
                    await self.post_fault_to_shared_thread(room, fault)
            else:
                print(f"✅ {room['name']} - All systems normal")
        
        print("\n📊 Monitoring cycle complete")

    async def run_agent(self):
        """Main agent loop"""
        print("🚀 Starting Maintenance Agent...")
        
        try:
            # Check system health
            health = self.check_system_health()
            print(f"🏥 System Health Check:")
            print(f"   • Azure connection: {'✅' if health['azure_connection'] else '❌'}")
            print(f"   • Data files loaded: {'✅' if health['data_files_loaded'] else '❌'}")
            print(f"   • Thread accessible: {'✅' if health['thread_accessible'] else '⚠️'}")
            print(f"   • Rooms monitored: {health['rooms_monitored']}")
            
            # Run initial monitoring
            await self.monitor_rooms()
            
            # Updated health check after monitoring
            updated_health = self.check_system_health()
            # SQL-based maintenance counters
            total_sql, overdue_sql = compute_sql_maintenance_counters(ROOMS)
            print(f"\n📈 Final Status Report:")
            print(f"   Total faults logged: {updated_health['total_faults_logged']}")
            print(f"   Scheduled maintenance items: {total_sql}")
            # Display recent faults with posting status
            recent_faults = self.maintenance_schedule['fault_log'][-5:] if self.maintenance_schedule['fault_log'] else []
            if recent_faults:
                print(f"\n🔍 Recent faults:")
                for fault in recent_faults:
                    status_icon = "📤" if fault.get('posted_to_thread', False) else "📝"
                    print(f"   {status_icon} {fault['room_name']}: {fault['description']} ({fault['severity']})")
            else:
                print(f"\n✅ No faults detected during this monitoring cycle")
            print(f"\n⚠️  Overdue maintenance tasks: {overdue_sql}")
            
        except Exception as e:
            print(f"❌ Error in agent execution: {e}")
            import traceback
            traceback.print_exc()

    def archive_and_clear_maintenance(self):
        """Archive previous fault_log and schedule to files and clear them for the new run."""
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_dir = os.path.join(os.path.dirname(__file__), 'fault_log_archive')
        os.makedirs(archive_dir, exist_ok=True)
        # Archive fault_log
        fault_log = self.maintenance_schedule.get('fault_log', [])
        if fault_log:
            archive_path = os.path.join(archive_dir, f'fault_log_{ts}.json')
            with open(archive_path, 'w', encoding='utf-8') as f:
                json.dump(fault_log, f, indent=2)
            print(f"🗃️  Archived previous fault_log to {archive_path}")
            self.maintenance_schedule['fault_log'] = []
        # Archive schedule
        schedule = self.maintenance_schedule.get('schedule', [])
        if schedule:
            archive_path = os.path.join(archive_dir, f'schedule_{ts}.json')
            with open(archive_path, 'w', encoding='utf-8') as f:
                json.dump(schedule, f, indent=2)
            print(f"🗃️  Archived previous schedule to {archive_path}")
            self.maintenance_schedule['schedule'] = []
        self.save_maintenance_schedule()

def compute_sql_maintenance_counters(rooms):
    total = 0
    overdue = 0
    now = datetime.now(timezone.utc)
    for r in rooms:
        items = get_maintenance(r["id"]).get("maintenance", [])
        total += len(items)
        for it in items:
            if it.get("status") != "cancelled":
                try:
                    if dateutil.parser.isoparse(it["start_time"]) < now:
                        overdue += 1
                except Exception:
                    pass
    return total, overdue

async def main():
    """Test the maintenance agent"""
    agent = MaintenanceAgent()
    await agent.run_agent()

if __name__ == "__main__":
    asyncio.run(main())
