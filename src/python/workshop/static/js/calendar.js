/**
 * Calendar Utilities for Calendar Scheduling Agent
 * Stage 5: Calendar Integration
 */

class CalendarManager {
    constructor() {
        this.events = [];
        this.rooms = [];
        this.currentDate = new Date();
        this.selectedDate = null;
        this.selectedRoom = null;
        
        // Initialize calendar data
        this.initializeCalendar();
    }

    async initializeCalendar() {
        try {
            await this.loadRooms();
            await this.loadEvents();
            this.renderCalendar();
            this.renderRoomList();
        } catch (error) {
            console.error('Failed to initialize calendar:', error);
        }
    }

    async refreshCalendar() {
        // Refresh all calendar data and re-render components
        try {
            await this.loadEvents();
            this.renderCalendar();
            this.renderRoomList();
            console.log('Calendar refreshed successfully');
        } catch (error) {
            console.error('Failed to refresh calendar:', error);
        }
    }

    async loadRooms() {
        try {
            const response = await fetch('/api/calendar/rooms');
            if (response.ok) {
                const data = await response.json();
                this.rooms = data.rooms || [];
                console.log(`Loaded ${this.rooms.length} rooms`);
            } else {
                console.warn('Failed to load rooms, using fallback data');
                this.rooms = this.getFallbackRooms();
            }
        } catch (error) {
            console.warn('Calendar service not available, using fallback data');
            this.rooms = this.getFallbackRooms();
        }
    }

    async loadEvents() {
        try {
            const startDate = new Date();
            startDate.setDate(startDate.getDate() - 7); // Load from 1 week ago
            const endDate = new Date();
            endDate.setDate(endDate.getDate() + 30); // Load to 30 days ahead

            const response = await fetch(`/api/calendar/events?start=${startDate.toISOString()}&end=${endDate.toISOString()}`);
            if (response.ok) {
                const data = await response.json();
                this.events = data.events || [];
                console.log(`Loaded ${this.events.length} events`);
            } else {
                console.warn('Failed to load events, using fallback data');
                this.events = this.getFallbackEvents();
            }
        } catch (error) {
            console.warn('Calendar service not available, using fallback events');
            this.events = this.getFallbackEvents();
        }
    }

    getFallbackRooms() {
        return [
            { id: 'central-meeting-room-alpha', name: 'Meeting Room Alpha', capacity: 10, room_type: 'meeting_room' },
            { id: 'central-meeting-room-beta', name: 'Meeting Room Beta', capacity: 8, room_type: 'meeting_room' },
            { id: 'central-lecture-hall-main', name: 'Main Lecture Hall', capacity: 200, room_type: 'lecture_hall' },
            { id: 'central-seminar-room-alpha', name: 'Seminar Room Alpha', capacity: 30, room_type: 'seminar_room' }
        ];
    }

    getFallbackEvents() {
        const today = new Date();
        return [
            {
                id: 'demo-1',
                title: 'Team Meeting',
                start_time: new Date(today.getTime() + 2 * 60 * 60 * 1000).toISOString(), // 2 hours from now
                end_time: new Date(today.getTime() + 3 * 60 * 60 * 1000).toISOString(), // 3 hours from now
                room_id: 'central-meeting-room-alpha',
                organizer: 'Demo User'
            },
            {
                id: 'demo-2',
                title: 'Project Review',
                start_time: new Date(today.getTime() + 24 * 60 * 60 * 1000).toISOString(), // Tomorrow
                end_time: new Date(today.getTime() + 25 * 60 * 60 * 1000).toISOString(),
                room_id: 'central-meeting-room-beta',
                organizer: 'Demo User'
            }
        ];
    }

    renderCalendar() {
        const calendarContainer = document.getElementById('calendar-widget');
        if (!calendarContainer) return;

        const today = new Date();
        const year = today.getFullYear();
        const month = today.getMonth();

        // Create calendar header
        const monthNames = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ];

        let calendarHTML = `
            <div class="calendar-header">
                <button class="calendar-nav" id="prev-month">‹</button>
                <h3>${monthNames[month]} ${year}</h3>
                <button class="calendar-nav" id="next-month">›</button>
            </div>
            <div class="calendar-grid">
                <div class="calendar-days-header">
                    <div class="calendar-day-header">Sun</div>
                    <div class="calendar-day-header">Mon</div>
                    <div class="calendar-day-header">Tue</div>
                    <div class="calendar-day-header">Wed</div>
                    <div class="calendar-day-header">Thu</div>
                    <div class="calendar-day-header">Fri</div>
                    <div class="calendar-day-header">Sat</div>
                </div>
                <div class="calendar-days">
        `;

        // Get first day of month and number of days
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startDate = new Date(firstDay);
        startDate.setDate(startDate.getDate() - firstDay.getDay()); // Start from Sunday of first week

        // Generate calendar days
        for (let week = 0; week < 6; week++) {
            for (let day = 0; day < 7; day++) {
                const currentDate = new Date(startDate);
                currentDate.setDate(startDate.getDate() + (week * 7) + day);
                
                const isCurrentMonth = currentDate.getMonth() === month;
                const isToday = this.isSameDate(currentDate, today);
                const hasEvents = this.getEventsForDate(currentDate).length > 0;
                
                let classes = 'calendar-day';
                if (!isCurrentMonth) classes += ' other-month';
                if (isToday) classes += ' today';
                if (hasEvents) classes += ' has-events';

                calendarHTML += `
                    <div class="${classes}" data-date="${currentDate.toISOString().split('T')[0]}">
                        <span class="day-number">${currentDate.getDate()}</span>
                        ${hasEvents ? '<span class="event-dot"></span>' : ''}
                    </div>
                `;
            }
        }

        calendarHTML += `
                </div>
            </div>
        `;

        calendarContainer.innerHTML = calendarHTML;

        // Add event listeners
        this.attachCalendarEventListeners();
    }

    attachCalendarEventListeners() {
        // Calendar day clicks
        document.querySelectorAll('.calendar-day').forEach(day => {
            day.addEventListener('click', (e) => {
                const date = e.currentTarget.dataset.date;
                this.selectDate(date);
            });
        });

        // Navigation buttons
        document.getElementById('prev-month')?.addEventListener('click', () => {
            this.currentDate.setMonth(this.currentDate.getMonth() - 1);
            this.renderCalendar();
        });

        document.getElementById('next-month')?.addEventListener('click', () => {
            this.currentDate.setMonth(this.currentDate.getMonth() + 1);
            this.renderCalendar();
        });
    }

    selectDate(dateString) {
        this.selectedDate = dateString;
        
        // Update visual selection
        document.querySelectorAll('.calendar-day').forEach(day => {
            day.classList.remove('selected');
        });
        document.querySelector(`[data-date="${dateString}"]`)?.classList.add('selected');

        // Show events for selected date
        this.showEventsForDate(dateString);
    }

    showEventsForDate(dateString) {
        const events = this.getEventsForDate(new Date(dateString));
        const eventsContainer = document.getElementById('selected-date-events');
        
        if (!eventsContainer) return;

        if (events.length === 0) {
            eventsContainer.innerHTML = `
                <div class="no-events">
                    <p>No events scheduled for ${this.formatDate(new Date(dateString))}</p>
                </div>
            `;
            return;
        }

        let eventsHTML = `<h4>Events for ${this.formatDate(new Date(dateString))}</h4>`;
        events.forEach(event => {
            const room = this.rooms.find(r => r.id === event.room_id);
            const startTime = new Date(event.start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            const endTime = new Date(event.end_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            
            eventsHTML += `
                <div class="event-item">
                    <div class="event-title">${event.title}</div>
                    <div class="event-time">${startTime} - ${endTime}</div>
                    <div class="event-room">${room ? room.name : event.room_id}</div>
                    <div class="event-organizer">Organizer: ${event.organizer}</div>
                </div>
            `;
        });

        eventsContainer.innerHTML = eventsHTML;
    }

    renderRoomList() {
        const roomContainer = document.getElementById('room-availability');
        if (!roomContainer) return;

        let roomHTML = '<h4>Room Availability</h4>';
        
        // Group rooms by type
        const roomTypes = {};
        this.rooms.forEach(room => {
            const type = room.room_type || 'other';
            if (!roomTypes[type]) roomTypes[type] = [];
            roomTypes[type].push(room);
        });

        Object.keys(roomTypes).forEach(type => {
            const typeLabel = type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
            roomHTML += `<div class="room-type-section">
                <h5>${typeLabel}s</h5>
            `;
            
            roomTypes[type].forEach(room => {
                const isAvailable = this.isRoomAvailableNow(room.id);
                roomHTML += `
                    <div class="room-item ${isAvailable ? 'available' : 'occupied'}" data-room-id="${room.id}">
                        <div class="room-name">${room.name}</div>
                        <div class="room-capacity">Capacity: ${room.capacity}</div>
                        <div class="room-status">${isAvailable ? 'Available' : 'Occupied'}</div>
                    </div>
                `;
            });
            roomHTML += '</div>';
        });

        roomContainer.innerHTML = roomHTML;

        // Add room click handlers
        document.querySelectorAll('.room-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const roomId = e.currentTarget.dataset.roomId;
                this.selectRoom(roomId);
            });
        });
    }

    selectRoom(roomId) {
        this.selectedRoom = roomId;
        
        // Update visual selection
        document.querySelectorAll('.room-item').forEach(item => {
            item.classList.remove('selected');
        });
        document.querySelector(`[data-room-id="${roomId}"]`)?.classList.add('selected');

        // Show room details
        this.showRoomDetails(roomId);
    }

    showRoomDetails(roomId) {
        const room = this.rooms.find(r => r.id === roomId);
        if (!room) return;

        const detailsContainer = document.getElementById('room-details');
        if (!detailsContainer) return;

        const upcomingEvents = this.getUpcomingEventsForRoom(roomId);
        
        let detailsHTML = `
            <h4>${room.name}</h4>
            <div class="room-info">
                <p><strong>Capacity:</strong> ${room.capacity} people</p>
                <p><strong>Type:</strong> ${room.room_type?.replace('_', ' ')}</p>
                ${room.location ? `<p><strong>Location:</strong> ${room.location}</p>` : ''}
            </div>
        `;

        if (upcomingEvents.length > 0) {
            detailsHTML += '<h5>Upcoming Events</h5>';
            upcomingEvents.slice(0, 3).forEach(event => {
                const startTime = new Date(event.start_time).toLocaleString();
                detailsHTML += `
                    <div class="upcoming-event">
                        <div class="event-title">${event.title}</div>
                        <div class="event-time">${startTime}</div>
                    </div>
                `;
            });
        } else {
            detailsHTML += '<p>No upcoming events</p>';
        }

        detailsContainer.innerHTML = detailsHTML;
    }

    getEventsForDate(date) {
        return this.events.filter(event => {
            const eventDate = new Date(event.start_time);
            return this.isSameDate(eventDate, date);
        });
    }

    getUpcomingEventsForRoom(roomId) {
        const now = new Date();
        return this.events
            .filter(event => event.room_id === roomId && new Date(event.start_time) > now)
            .sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
    }

    isRoomAvailableNow(roomId) {
        const now = new Date();
        const currentEvents = this.events.filter(event => {
            const start = new Date(event.start_time);
            const end = new Date(event.end_time);
            return event.room_id === roomId && now >= start && now <= end;
        });
        return currentEvents.length === 0;
    }

    isSameDate(date1, date2) {
        return date1.getFullYear() === date2.getFullYear() &&
               date1.getMonth() === date2.getMonth() &&
               date1.getDate() === date2.getDate();
    }

    formatDate(date) {
        return date.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    // Quick action methods
    async createQuickEvent(title, roomId, startTime, duration = 60) {
        try {
            const response = await fetch('/api/calendar/events', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title,
                    room_id: roomId,
                    start_time: startTime,
                    duration_minutes: duration
                })
            });

            if (response.ok) {
                await this.loadEvents(); // Reload events
                this.renderCalendar();
                return { success: true, message: 'Event created successfully' };
            } else {
                throw new Error('Failed to create event');
            }
        } catch (error) {
            console.error('Error creating event:', error);
            return { success: false, message: error.message };
        }
    }

    getAvailableRoomsForTimeSlot(startTime, endTime) {
        const start = new Date(startTime);
        const end = new Date(endTime);
        
        return this.rooms.filter(room => {
            const conflictingEvents = this.events.filter(event => {
                if (event.room_id !== room.id) return false;
                
                const eventStart = new Date(event.start_time);
                const eventEnd = new Date(event.end_time);
                
                // Check for time overlap
                return (start < eventEnd && end > eventStart);
            });
            
            return conflictingEvents.length === 0;
        });
    }

    // Integration with chat interface
    handleCalendarChatCommand(command) {
        const commands = {
            'show calendar': () => this.renderCalendar(),
            'list rooms': () => this.renderRoomList(),
            'today events': () => {
                const today = new Date().toISOString().split('T')[0];
                this.selectDate(today);
            },
            'available rooms': () => {
                const available = this.rooms.filter(room => this.isRoomAvailableNow(room.id));
                return `Available rooms: ${available.map(r => r.name).join(', ')}`;
            }
        };

        if (commands[command.toLowerCase()]) {
            return commands[command.toLowerCase()]();
        }
        
        return null;
    }
}

// Export for use in main app
window.CalendarManager = CalendarManager;
