-- PostgreSQL Stored Procedures (converted from SQL Server)
-- These replace the SQL Server stored procedures used in the original system

-- Get rooms as JSON
CREATE OR REPLACE FUNCTION calendar.get_rooms_json()
RETURNS JSON AS $$
BEGIN
    RETURN (
        SELECT json_agg(row_to_json(r))
        FROM (
            SELECT 
                id,
                name,
                capacity,
                room_type,
                location,
                equipment
            FROM calendar.rooms
            ORDER BY name
        ) r
    );
END;
$$ LANGUAGE plpgsql;

-- Get events for a calendar/room as JSON
CREATE OR REPLACE FUNCTION calendar.get_events_json(p_calendar_id VARCHAR(100))
RETURNS JSON AS $$
BEGIN
    RETURN (
        SELECT json_agg(row_to_json(e))
        FROM (
            SELECT 
                id::text,
                calendar_id,
                title,
                description,
                start_time::text,
                end_time::text,
                organizer_email,
                attendee_count,
                is_recurring,
                event_type,
                status
            FROM calendar.events
            WHERE calendar_id = p_calendar_id
                AND status = 'confirmed'
            ORDER BY start_time
        ) e
    );
END;
$$ LANGUAGE plpgsql;

-- Create event from JSON
CREATE OR REPLACE FUNCTION calendar.create_event_json(
    p_event_id UUID,
    p_calendar_id VARCHAR(100),
    p_title VARCHAR(255),
    p_start_utc TIMESTAMP,
    p_end_utc TIMESTAMP,
    p_organizer_email VARCHAR(255),
    p_description TEXT DEFAULT NULL,
    p_attendees_json JSON DEFAULT '[]'
)
RETURNS JSON AS $$
DECLARE
    v_event_id UUID;
    v_organizer_id UUID;
    v_attendee_email VARCHAR(255);
BEGIN
    -- Get organizer ID if email exists
    SELECT id INTO v_organizer_id 
    FROM calendar.users 
    WHERE email = p_organizer_email;
    
    -- Insert the event
    INSERT INTO calendar.events (
        id, calendar_id, title, description, 
        start_time, end_time, organizer_email, 
        organizer_id, status
    ) VALUES (
        COALESCE(p_event_id, uuid_generate_v4()),
        p_calendar_id, p_title, p_description,
        p_start_utc, p_end_utc, p_organizer_email,
        v_organizer_id, 'confirmed'
    ) RETURNING id INTO v_event_id;
    
    -- Insert attendees if provided
    IF p_attendees_json IS NOT NULL AND p_attendees_json::text != '[]' THEN
        FOR v_attendee_email IN 
            SELECT json_array_elements_text(p_attendees_json)
        LOOP
            INSERT INTO calendar.event_attendees (event_id, user_email)
            VALUES (v_event_id, v_attendee_email)
            ON CONFLICT DO NOTHING;
        END LOOP;
    END IF;
    
    -- Return the created event as JSON
    RETURN (
        SELECT row_to_json(e)
        FROM (
            SELECT 
                id::text,
                calendar_id,
                title,
                description,
                start_time::text,
                end_time::text,
                organizer_email,
                status
            FROM calendar.events
            WHERE id = v_event_id
        ) e
    );
END;
$$ LANGUAGE plpgsql;

-- Update event
CREATE OR REPLACE FUNCTION calendar.update_event_json(
    p_event_id UUID,
    p_requester_email VARCHAR(255),
    p_title VARCHAR(255) DEFAULT NULL,
    p_start_utc TIMESTAMP DEFAULT NULL,
    p_end_utc TIMESTAMP DEFAULT NULL,
    p_description TEXT DEFAULT NULL
)
RETURNS JSON AS $$
DECLARE
    v_organizer_email VARCHAR(255);
BEGIN
    -- Check if requester is the organizer
    SELECT organizer_email INTO v_organizer_email
    FROM calendar.events
    WHERE id = p_event_id;
    
    IF v_organizer_email != p_requester_email THEN
        RAISE EXCEPTION 'Only the organizer can update this event';
    END IF;
    
    -- Update the event
    UPDATE calendar.events
    SET 
        title = COALESCE(p_title, title),
        start_time = COALESCE(p_start_utc, start_time),
        end_time = COALESCE(p_end_utc, end_time),
        description = COALESCE(p_description, description)
    WHERE id = p_event_id;
    
    -- Return updated event as JSON
    RETURN (
        SELECT row_to_json(e)
        FROM (
            SELECT 
                id::text,
                calendar_id,
                title,
                description,
                start_time::text,
                end_time::text,
                organizer_email,
                status
            FROM calendar.events
            WHERE id = p_event_id
        ) e
    );
END;
$$ LANGUAGE plpgsql;

-- Cancel event (soft delete)
CREATE OR REPLACE FUNCTION calendar.cancel_event_json(
    p_event_id UUID,
    p_requester_email VARCHAR(255)
)
RETURNS JSON AS $$
DECLARE
    v_organizer_email VARCHAR(255);
BEGIN
    -- Check if requester is the organizer
    SELECT organizer_email INTO v_organizer_email
    FROM calendar.events
    WHERE id = p_event_id;
    
    IF v_organizer_email != p_requester_email THEN
        RAISE EXCEPTION 'Only the organizer can cancel this event';
    END IF;
    
    -- Cancel the event
    UPDATE calendar.events
    SET status = 'cancelled'
    WHERE id = p_event_id;
    
    -- Return cancelled event as JSON
    RETURN (
        SELECT row_to_json(e)
        FROM (
            SELECT 
                id::text,
                calendar_id,
                title,
                description,
                start_time::text,
                end_time::text,
                organizer_email,
                status
            FROM calendar.events
            WHERE id = p_event_id
        ) e
    );
END;
$$ LANGUAGE plpgsql;

-- Lookup entity emails (users and groups)
CREATE OR REPLACE FUNCTION calendar.lookup_entity_emails(p_query VARCHAR(255))
RETURNS JSON AS $$
BEGIN
    RETURN (
        SELECT json_agg(row_to_json(e))
        FROM (
            -- Users
            SELECT 
                'user' as entity_type,
                id::text as entity_id,
                name,
                email,
                department_id::text
            FROM calendar.users
            WHERE LOWER(email) LIKE LOWER('%' || p_query || '%')
                OR LOWER(name) LIKE LOWER('%' || p_query || '%')
            
            UNION ALL
            
            -- Groups (using code as email-like identifier)
            SELECT 
                'group' as entity_type,
                id::text as entity_id,
                name,
                code || '@groups.university.edu' as email,
                NULL as department_id
            FROM calendar.groups
            WHERE LOWER(name) LIKE LOWER('%' || p_query || '%')
                OR LOWER(code) LIKE LOWER('%' || p_query || '%')
            
            LIMIT 20
        ) e
    );
END;
$$ LANGUAGE plpgsql;

-- Get organization structure as JSON
CREATE OR REPLACE FUNCTION calendar.get_org_structure()
RETURNS JSON AS $$
BEGIN
    RETURN json_build_object(
        'departments', (
            SELECT json_agg(row_to_json(d))
            FROM (
                SELECT id::text, name, code
                FROM calendar.departments
                ORDER BY name
            ) d
        ),
        'users', (
            SELECT json_agg(row_to_json(u))
            FROM (
                SELECT 
                    id::text,
                    email,
                    name,
                    role_scope,
                    department_id::text
                FROM calendar.users
                ORDER BY name
            ) u
        ),
        'groups', (
            SELECT json_agg(row_to_json(g))
            FROM (
                SELECT 
                    id::text,
                    name,
                    code,
                    group_type
                FROM calendar.groups
                ORDER BY name
            ) g
        )
    );
END;
$$ LANGUAGE plpgsql;

-- Get user by ID or email
CREATE OR REPLACE FUNCTION calendar.get_user_by_id_or_email(
    p_identifier VARCHAR(255)
)
RETURNS JSON AS $$
BEGIN
    RETURN (
        SELECT row_to_json(u)
        FROM (
            SELECT 
                id::text,
                email,
                name,
                role_scope,
                department_id::text
            FROM calendar.users
            WHERE id::text = p_identifier
                OR email = p_identifier
            LIMIT 1
        ) u
    );
END;
$$ LANGUAGE plpgsql;
-- Get shared thread function
CREATE OR REPLACE FUNCTION calendar.get_shared_thread()
RETURNS JSON AS $$
BEGIN
    RETURN (
        SELECT row_to_json(t)
        FROM (
            SELECT 
                thread_id,
                updated_at_utc::text,
                updated_by
            FROM calendar.shared_thread
            WHERE id = 1
        ) t
    );
END;
$$ LANGUAGE plpgsql;

-- Set shared thread function  
CREATE OR REPLACE FUNCTION calendar.set_shared_thread(
    p_thread_id VARCHAR(255),
    p_updated_by VARCHAR(255) DEFAULT NULL
)
RETURNS JSON AS $$
BEGIN
    -- Update the single row in shared_thread table
    UPDATE calendar.shared_thread
    SET 
        thread_id = p_thread_id,
        updated_at_utc = CURRENT_TIMESTAMP,
        updated_by = COALESCE(p_updated_by, 'system')
WHERE id = 1;
    
    -- Return the updated data
    RETURN (
        SELECT row_to_json(t)
        FROM (
            SELECT 
                thread_id,
                updated_at_utc::text,
                updated_by
            FROM calendar.shared_thread
            WHERE id = 1
        ) t
    );
END;
$$ LANGUAGE plpgsql;
