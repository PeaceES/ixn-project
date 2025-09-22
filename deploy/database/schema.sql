-- PostgreSQL Schema for Calendar Scheduling Agent
-- Compatible with Supabase

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schema
CREATE SCHEMA IF NOT EXISTS calendar;

-- Departments table
CREATE TABLE IF NOT EXISTS calendar.departments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table
CREATE TABLE IF NOT EXISTS calendar.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role_scope VARCHAR(50) DEFAULT 'user',
    department_id UUID REFERENCES calendar.departments(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Groups/Organizations table
CREATE TABLE IF NOT EXISTS calendar.groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    group_type VARCHAR(50) NOT NULL, -- 'society', 'club', 'department'
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User-Group membership table
CREATE TABLE IF NOT EXISTS calendar.user_groups (
    user_id UUID REFERENCES calendar.users(id) ON DELETE CASCADE,
    group_id UUID REFERENCES calendar.groups(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, group_id)
);

-- Rooms table
CREATE TABLE IF NOT EXISTS calendar.rooms (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    capacity INTEGER NOT NULL,
    room_type VARCHAR(50) NOT NULL,
    location VARCHAR(255),
    equipment TEXT[], -- Array of equipment
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Group-Room permissions table
CREATE TABLE IF NOT EXISTS calendar.group_room_permissions (
    group_id UUID REFERENCES calendar.groups(id) ON DELETE CASCADE,
    room_id VARCHAR(100) REFERENCES calendar.rooms(id) ON DELETE CASCADE,
    can_book BOOLEAN DEFAULT true,
    can_view BOOLEAN DEFAULT true,
    PRIMARY KEY (group_id, room_id)
);

-- Events table
CREATE TABLE IF NOT EXISTS calendar.events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    calendar_id VARCHAR(100) REFERENCES calendar.rooms(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    organizer_email VARCHAR(255),
    organizer_id UUID REFERENCES calendar.users(id),
    group_id UUID REFERENCES calendar.groups(id),
    attendee_count INTEGER DEFAULT 1,
    is_recurring BOOLEAN DEFAULT false,
    event_type VARCHAR(50) DEFAULT 'meeting',
    status VARCHAR(50) DEFAULT 'confirmed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT no_overlap CHECK (start_time < end_time)
);

-- Event attendees table
CREATE TABLE IF NOT EXISTS calendar.event_attendees (
    event_id UUID REFERENCES calendar.events(id) ON DELETE CASCADE,
    user_email VARCHAR(255),
    user_id UUID REFERENCES calendar.users(id),
    response_status VARCHAR(50) DEFAULT 'pending',
    PRIMARY KEY (event_id, user_email)
);

-- Shared thread table for inter-agent communication
CREATE TABLE IF NOT EXISTS calendar.shared_thread (
    id SERIAL PRIMARY KEY,
    thread_id VARCHAR(255) NOT NULL,
    updated_at_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255),
    CONSTRAINT unique_thread UNIQUE(id)
);

-- Insert default row (only one row will exist in this table)
INSERT INTO calendar.shared_thread (id, thread_id, updated_by) 
VALUES (1, '', 'system')
ON CONFLICT (id) DO NOTHING;

-- Create indexes for better performance
CREATE INDEX idx_events_calendar_time ON calendar.events(calendar_id, start_time, end_time);
CREATE INDEX idx_events_organizer ON calendar.events(organizer_email);
CREATE INDEX idx_user_groups_user ON calendar.user_groups(user_id);
CREATE INDEX idx_user_groups_group ON calendar.user_groups(group_id);

-- Create views for easier querying
CREATE OR REPLACE VIEW calendar.upcoming_events AS
SELECT 
    e.*,
    r.name as room_name,
    r.location as room_location,
    u.name as organizer_name
FROM calendar.events e
JOIN calendar.rooms r ON e.calendar_id = r.id
LEFT JOIN calendar.users u ON e.organizer_id = u.id
WHERE e.start_time >= CURRENT_TIMESTAMP
    AND e.status = 'confirmed'
ORDER BY e.start_time;

-- Function to check room availability
CREATE OR REPLACE FUNCTION calendar.check_room_availability(
    p_room_id VARCHAR(100),
    p_start_time TIMESTAMP,
    p_end_time TIMESTAMP,
    p_exclude_event_id UUID DEFAULT NULL
)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN NOT EXISTS (
        SELECT 1
        FROM calendar.events
        WHERE calendar_id = p_room_id
            AND status = 'confirmed'
            AND (
                (start_time < p_end_time AND end_time > p_start_time)
            )
            AND (p_exclude_event_id IS NULL OR id != p_exclude_event_id)
    );
END;
$$ LANGUAGE plpgsql;

-- Function to get user's groups
CREATE OR REPLACE FUNCTION calendar.get_user_groups(p_user_id UUID)
RETURNS TABLE(
    group_id UUID,
    group_name VARCHAR(255),
    group_code VARCHAR(50),
    group_type VARCHAR(50),
    user_role VARCHAR(50)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        g.id,
        g.name,
        g.code,
        g.group_type,
        ug.role
    FROM calendar.groups g
    JOIN calendar.user_groups ug ON g.id = ug.group_id
    WHERE ug.user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION calendar.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update trigger to all tables
CREATE TRIGGER update_departments_updated_at BEFORE UPDATE ON calendar.departments
    FOR EACH ROW EXECUTE FUNCTION calendar.update_updated_at();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON calendar.users
    FOR EACH ROW EXECUTE FUNCTION calendar.update_updated_at();

CREATE TRIGGER update_groups_updated_at BEFORE UPDATE ON calendar.groups
    FOR EACH ROW EXECUTE FUNCTION calendar.update_updated_at();

CREATE TRIGGER update_rooms_updated_at BEFORE UPDATE ON calendar.rooms
    FOR EACH ROW EXECUTE FUNCTION calendar.update_updated_at();

CREATE TRIGGER update_events_updated_at BEFORE UPDATE ON calendar.events
    FOR EACH ROW EXECUTE FUNCTION calendar.update_updated_at();