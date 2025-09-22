-- Seed data for Calendar Scheduling Agent

-- Insert departments
INSERT INTO calendar.departments (id, name, code) VALUES
    ('550e8400-e29b-41d4-a716-446655440001', 'Computer Science', 'CS'),
    ('550e8400-e29b-41d4-a716-446655440002', 'Engineering', 'ENG'),
    ('550e8400-e29b-41d4-a716-446655440003', 'Business', 'BUS'),
    ('550e8400-e29b-41d4-a716-446655440004', 'Arts', 'ARTS')
ON CONFLICT (code) DO NOTHING;

-- Insert demo users
INSERT INTO calendar.users (id, email, name, role_scope, department_id) VALUES
    ('650e8400-e29b-41d4-a716-446655440001', 'john.doe@university.edu', 'John Doe', 'student', '550e8400-e29b-41d4-a716-446655440001'),
    ('650e8400-e29b-41d4-a716-446655440002', 'alice.chen@university.edu', 'Alice Chen', 'student', '550e8400-e29b-41d4-a716-446655440002'),
    ('650e8400-e29b-41d4-a716-446655440003', 'sarah.jones@university.edu', 'Sarah Jones', 'student', '550e8400-e29b-41d4-a716-446655440004'),
    ('650e8400-e29b-41d4-a716-446655440004', 'alex.brown@university.edu', 'Alex Brown', 'student', '550e8400-e29b-41d4-a716-446655440003'),
    ('650e8400-e29b-41d4-a716-446655440005', 'prof.johnson@university.edu', 'Professor Johnson', 'faculty', '550e8400-e29b-41d4-a716-446655440001')
ON CONFLICT (email) DO NOTHING;

-- Insert groups
INSERT INTO calendar.groups (id, name, code, group_type) VALUES
    ('750e8400-e29b-41d4-a716-446655440001', 'Engineering Society', 'eng-soc', 'society'),
    ('750e8400-e29b-41d4-a716-446655440002', 'Computer Science Department', 'cs-dept', 'department'),
    ('750e8400-e29b-41d4-a716-446655440003', 'Robotics Club', 'robotics', 'club'),
    ('750e8400-e29b-41d4-a716-446655440004', 'Drama Club', 'drama', 'club'),
    ('750e8400-e29b-41d4-a716-446655440005', 'Student Government', 'student-gov', 'society')
ON CONFLICT (code) DO NOTHING;

-- Insert user-group memberships
INSERT INTO calendar.user_groups (user_id, group_id, role) VALUES
    ('650e8400-e29b-41d4-a716-446655440001', '750e8400-e29b-41d4-a716-446655440001', 'member'),
    ('650e8400-e29b-41d4-a716-446655440001', '750e8400-e29b-41d4-a716-446655440002', 'member'),
    ('650e8400-e29b-41d4-a716-446655440002', '750e8400-e29b-41d4-a716-446655440001', 'treasurer'),
    ('650e8400-e29b-41d4-a716-446655440002', '750e8400-e29b-41d4-a716-446655440003', 'president'),
    ('650e8400-e29b-41d4-a716-446655440002', '750e8400-e29b-41d4-a716-446655440002', 'member'),
    ('650e8400-e29b-41d4-a716-446655440003', '750e8400-e29b-41d4-a716-446655440004', 'president'),
    ('650e8400-e29b-41d4-a716-446655440004', '750e8400-e29b-41d4-a716-446655440005', 'treasurer'),
    ('650e8400-e29b-41d4-a716-446655440005', '750e8400-e29b-41d4-a716-446655440002', 'faculty')
ON CONFLICT (user_id, group_id) DO NOTHING;

-- Insert rooms
INSERT INTO calendar.rooms (id, name, capacity, room_type, location, equipment) VALUES
    ('central-meeting-room-alpha', 'Meeting Room Alpha', 10, 'meeting_room', 'Main Building, 2nd Floor', ARRAY['projector', 'whiteboard']),
    ('central-meeting-room-beta', 'Meeting Room Beta', 8, 'meeting_room', 'Main Building, 2nd Floor', ARRAY['tv_screen', 'whiteboard']),
    ('central-lecture-hall-main', 'Main Lecture Hall', 200, 'lecture_hall', 'Main Building, Ground Floor', ARRAY['projector', 'microphone', 'speakers']),
    ('central-lecture-hall-a', 'Lecture Hall A', 100, 'lecture_hall', 'Science Building, 1st Floor', ARRAY['projector', 'microphone']),
    ('central-lecture-hall-b', 'Lecture Hall B', 100, 'lecture_hall', 'Science Building, 1st Floor', ARRAY['projector', 'microphone']),
    ('central-conference-room', 'Main Conference Room', 25, 'conference_room', 'Admin Building, 3rd Floor', ARRAY['projector', 'video_conferencing', 'whiteboard']),
    ('central-computer-lab-1', 'Computer Lab 1', 30, 'computer_lab', 'Tech Building, 2nd Floor', ARRAY['computers', 'projector']),
    ('central-computer-lab-2', 'Computer Lab 2', 30, 'computer_lab', 'Tech Building, 2nd Floor', ARRAY['computers', 'projector']),
    ('arts-drama-studio', 'Drama Studio', 50, 'studio', 'Arts Building, Ground Floor', ARRAY['stage_lighting', 'sound_system']),
    ('arts-music-room', 'Music Room', 20, 'studio', 'Arts Building, 1st Floor', ARRAY['piano', 'sound_system'])
ON CONFLICT (id) DO NOTHING;

-- Insert group-room permissions
INSERT INTO calendar.group_room_permissions (group_id, room_id, can_book, can_view) VALUES
    -- Engineering Society can book most rooms
    ('750e8400-e29b-41d4-a716-446655440001', 'central-meeting-room-alpha', true, true),
    ('750e8400-e29b-41d4-a716-446655440001', 'central-meeting-room-beta', true, true),
    ('750e8400-e29b-41d4-a716-446655440001', 'central-lecture-hall-a', true, true),
    ('750e8400-e29b-41d4-a716-446655440001', 'central-lecture-hall-b', true, true),
    ('750e8400-e29b-41d4-a716-446655440001', 'central-conference-room', true, true),
    
    -- CS Department can book computer labs and lecture halls
    ('750e8400-e29b-41d4-a716-446655440002', 'central-computer-lab-1', true, true),
    ('750e8400-e29b-41d4-a716-446655440002', 'central-computer-lab-2', true, true),
    ('750e8400-e29b-41d4-a716-446655440002', 'central-lecture-hall-main', true, true),
    ('750e8400-e29b-41d4-a716-446655440002', 'central-lecture-hall-a', true, true),
    
    -- Drama Club can book drama studio
    ('750e8400-e29b-41d4-a716-446655440004', 'arts-drama-studio', true, true),
    ('750e8400-e29b-41d4-a716-446655440004', 'arts-music-room', true, true),
    
    -- Student Government can book conference room
    ('750e8400-e29b-41d4-a716-446655440005', 'central-conference-room', true, true),
    ('750e8400-e29b-41d4-a716-446655440005', 'central-meeting-room-alpha', true, true)
ON CONFLICT (group_id, room_id) DO NOTHING;

-- Insert sample events
INSERT INTO calendar.events (title, description, calendar_id, start_time, end_time, organizer_email, organizer_id, group_id, status) VALUES
    ('Engineering Society Meeting', 'Weekly planning meeting', 'central-meeting-room-alpha', 
     CURRENT_TIMESTAMP + INTERVAL '1 day', CURRENT_TIMESTAMP + INTERVAL '1 day' + INTERVAL '1 hour',
     'alice.chen@university.edu', '650e8400-e29b-41d4-a716-446655440002', '750e8400-e29b-41d4-a716-446655440001', 'confirmed'),
    
    ('CS101 Lecture', 'Introduction to Programming', 'central-lecture-hall-main',
     CURRENT_TIMESTAMP + INTERVAL '2 days', CURRENT_TIMESTAMP + INTERVAL '2 days' + INTERVAL '2 hours',
     'prof.johnson@university.edu', '650e8400-e29b-41d4-a716-446655440005', '750e8400-e29b-41d4-a716-446655440002', 'confirmed'),
    
    ('Drama Rehearsal', 'Spring play rehearsal', 'arts-drama-studio',
     CURRENT_TIMESTAMP + INTERVAL '3 days', CURRENT_TIMESTAMP + INTERVAL '3 days' + INTERVAL '3 hours',
     'sarah.jones@university.edu', '650e8400-e29b-41d4-a716-446655440003', '750e8400-e29b-41d4-a716-446655440004', 'confirmed');