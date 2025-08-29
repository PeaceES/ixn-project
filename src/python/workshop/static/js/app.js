/**
 * Calendar Scheduling Agent - Web Interface JavaScript
 * Stage 3: Real-time Output Streaming with WebSocket
 */

class CalendarAgentUI {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.outputContainer = null;
        this.maxOutputLines = 1000; // Limit output to prevent memory issues
        this.calendarManager = null; // Calendar manager instance
        
        this.initializeWebSocket();
        this.enableButtons();
        this.initializeEventListeners();
        this.checkSystemStatus();
        this.startStatusUpdates();
        this.initializeCalendar(); // Initialize calendar integration
    }

    async initializeCalendar() {
        // Initialize calendar manager (Stage 5)
        if (window.CalendarManager) {
            this.calendarManager = new window.CalendarManager();
            console.log('📅 Calendar integration initialized');
        }
    }

    initializeWebSocket() {
        console.log('Initializing WebSocket connection...');
        
        // Connect to SocketIO server
        this.socket = io();
        
        // Connection event handlers
        this.socket.on('connect', () => {
            console.log('WebSocket connected');
            this.isConnected = true;
            this.updateConnectionStatus('Connected', 'success');
        });

        this.socket.on('disconnect', () => {
            console.log('WebSocket disconnected');
            this.isConnected = false;
            this.updateConnectionStatus('Disconnected', 'error');
        });

        this.socket.on('connect_error', (error) => {
            console.log('WebSocket connection error:', error);
            this.updateConnectionStatus('Connection Error', 'error');
        });

        // Agent output streaming
        this.socket.on('agent_output', (data) => {
            this.appendOutput(data.type, data.data, data.timestamp);
        });

        // Agent status updates
        this.socket.on('agent_status', (status) => {
            this.updateAgentStatus(status);
        });

        // Chat message events
        this.socket.on('chat_message', (data) => {
            this.addChatMessage(data.message, data.type, data.timestamp);
        });

        this.socket.on('chat_error', (data) => {
            this.showNotification(data.message, 'error');
            console.error('Chat error:', data.message);
        });

        // Calendar event notifications (Stage 5)
        this.socket.on('calendar_event_created', (data) => {
            this.showNotification(`Event "${data.event.title}" created successfully! 🎉`, 'success');
            
            // Refresh calendar data
            if (this.calendarManager) {
                this.calendarManager.refreshCalendar();
            }
            
            // Add chat message
            this.addChatMessage(
                `✅ New event created: "${data.event.title}" on ${new Date(data.event.start_time).toLocaleString()}`,
                'system'
            );
        });
    }

    updateConnectionStatus(status, type = 'info') {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.textContent = status;
            statusElement.className = `status-${type}`;
        }
    }

    appendOutput(type, data, timestamp) {
        this.outputContainer = this.outputContainer || document.getElementById('chat-output');
        if (!this.outputContainer) return;

        // Create timestamp
        const time = new Date(timestamp * 1000).toLocaleTimeString();
        
        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        // Format the output based on type
        let content = '';
        if (type === 'stdout') {
            content = `<span class="timestamp">[${time}]</span> ${this.escapeHtml(data)}`;
        } else if (type === 'error') {
            content = `<span class="timestamp">[${time}]</span> <strong>ERROR:</strong> ${this.escapeHtml(data)}`;
        } else {
            content = `<span class="timestamp">[${time}]</span> <strong>${type.toUpperCase()}:</strong> ${this.escapeHtml(data)}`;
        }
        
        messageDiv.innerHTML = content;
        this.outputContainer.appendChild(messageDiv);
        
        // Limit number of messages to prevent memory issues
        const messages = this.outputContainer.querySelectorAll('.message');
        if (messages.length > this.maxOutputLines) {
            for (let i = 0; i < messages.length - this.maxOutputLines; i++) {
                messages[i].remove();
            }
        }
        
        // Auto-scroll to bottom
        this.scrollToBottom();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    scrollToBottom() {
        if (this.outputContainer) {
            this.outputContainer.scrollTop = this.outputContainer.scrollHeight;
        }
    }

    clearOutput() {
        if (this.outputContainer) {
            // Keep system messages
            const systemMessages = this.outputContainer.querySelectorAll('.system-message, .info-message');
            this.outputContainer.innerHTML = '';
            systemMessages.forEach(msg => this.outputContainer.appendChild(msg));
        }
    }

    updateAgentStatus(status) {
        // Update agent status in the UI
        const agentStatusElement = document.getElementById('agent-status');
        if (agentStatusElement) {
            if (status.running) {
                agentStatusElement.textContent = `Running (PID: ${status.pid})`;
                agentStatusElement.className = 'status-value status-active';
            } else {
                agentStatusElement.textContent = 'Stopped';
                agentStatusElement.className = 'status-value status-pending';
            }
        }

        // Update button states and chat interface based on agent status
        const startBtn = document.getElementById('start-agent');
        const stopBtn = document.getElementById('stop-agent');
        const restartBtn = document.getElementById('restart-agent');
        const chatInput = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-message');

        if (status.running) {
            if (startBtn) {
                startBtn.disabled = true;
                startBtn.textContent = '🟢 Agent Running';
            }
            if (stopBtn) {
                stopBtn.disabled = false;
                stopBtn.textContent = '🛑 Stop Agent';
            }
            if (restartBtn) {
                restartBtn.disabled = false;
                restartBtn.textContent = '🔄 Restart Agent';
            }
            // Enable chat interface
            if (chatInput) {
                chatInput.disabled = false;
                chatInput.placeholder = "Type your message to the agent...";
            }
            if (sendBtn) {
                sendBtn.disabled = false;
            }
        } else {
            if (startBtn) {
                startBtn.disabled = false;
                startBtn.textContent = '🚀 Start Agent';
            }
            if (stopBtn) {
                stopBtn.disabled = true;
                stopBtn.textContent = '🛑 Stop Agent';
            }
            if (restartBtn) {
                restartBtn.disabled = true;
                restartBtn.textContent = '🔄 Restart Agent';
            }
            // Disable chat interface
            if (chatInput) {
                chatInput.disabled = true;
                chatInput.placeholder = "Start the agent to enable chat...";
            }
            if (sendBtn) {
                sendBtn.disabled = true;
            }
        }

        // Show status message if provided
        if (status.message) {
            this.appendOutput('system', status.message, Date.now() / 1000);
        }
    }

    enableButtons() {
        // Enable the agent control buttons
        const startBtn = document.getElementById('start-agent');
        const stopBtn = document.getElementById('stop-agent');
        const restartBtn = document.getElementById('restart-agent');
        
        if (startBtn) startBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = false;
        if (restartBtn) restartBtn.disabled = false;
        
        console.log('Agent control buttons enabled');
    }

    initializeEventListeners() {
        console.log('Initializing event listeners...');
        
        // Agent control button event listeners
        const startBtn = document.getElementById('start-agent');
        const stopBtn = document.getElementById('stop-agent');
        const restartBtn = document.getElementById('restart-agent');
        
        console.log('Found buttons:', { 
            start: startBtn, 
            stop: stopBtn, 
            restart: restartBtn 
        });
        
        if (startBtn) {
            startBtn.addEventListener('click', (e) => {
                console.log('Start button clicked!');
                e.preventDefault();
                this.startAgent();
            });
        }

        if (stopBtn) {
            stopBtn.addEventListener('click', (e) => {
                console.log('Stop button clicked!');
                e.preventDefault();
                this.stopAgent();
            });
        }

        if (restartBtn) {
            restartBtn.addEventListener('click', (e) => {
                console.log('Restart button clicked!');
                e.preventDefault();
                this.restartAgent();
            });
        }

        // Output control buttons
        const clearBtn = document.getElementById('clear-output');
        const scrollBtn = document.getElementById('scroll-to-bottom');

        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.clearOutput();
            });
        }

        if (scrollBtn) {
            scrollBtn.addEventListener('click', () => {
                this.scrollToBottom();
            });
        }

        document.getElementById('send-message')?.addEventListener('click', () => {
            this.sendMessage();
        });

        document.getElementById('chat-input')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });

        // Quick action buttons
        document.querySelectorAll('.action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const buttonId = e.target.id;
                this.handleQuickAction(buttonId);
            });
        });

        // Calendar integration event listeners (Stage 5)
        this.initializeCalendarEventListeners();
    }

    async checkSystemStatus() {
        try {
            // Check web interface API
            const response = await fetch('/api/status');
            const data = await response.json();
            
            this.updateStatus('Web Interface', 'active');
            
            // Update agent status
            if (data.agent_status === 'running') {
                this.updateStatus('Agent Process', 'active');
            } else {
                this.updateStatus('Agent Process', 'pending', 'Stopped');
            }
            
            // Check calendar server (will implement proper check later)
            this.checkCalendarServer();
            
        } catch (error) {
            console.error('Error checking system status:', error);
            this.updateStatus('Web Interface', 'error');
        }
    }

    async startAgent() {
        console.log('Starting agent...');
        try {
            await this.apiCall('/api/agent/start', { method: 'POST' });
            this.showNotification('Agent started successfully! 🚀', 'success');
            await this.updateStatus();
        } catch (error) {
            console.error('Failed to start agent:', error);
            this.showNotification('Failed to start agent: ' + error.message, 'error');
        }
    }

    async stopAgent() {
        this.showNotification('Stopping agent...', 'info');
        
        try {
            const response = await fetch('/api/agent/stop', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(data.message, 'success');
                this.updateStatus('Agent Process', 'pending', 'Stopped');
            } else {
                this.showNotification(`Failed to stop agent: ${data.message}`, 'error');
            }
        } catch (error) {
            console.error('Error stopping agent:', error);
            this.showNotification('Error stopping agent', 'error');
        }
    }

    async restartAgent() {
        this.showNotification('Restarting agent...', 'info');
        
        try {
            // Stop first
            await fetch('/api/agent/stop', { method: 'POST' });
            
            // Wait a moment
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Start again
            const response = await fetch('/api/agent/start', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Agent restarted successfully', 'success');
                this.updateStatus('Agent Process', 'active');
            } else {
                this.showNotification(`Failed to restart agent: ${data.message}`, 'error');
                this.updateStatus('Agent Process', 'error');
            }
        } catch (error) {
            console.error('Error restarting agent:', error);
            this.showNotification('Error restarting agent', 'error');
        }
    }

    async checkCalendarServer() {
        try {
            // Check if our calendar API endpoints are working
            const response = await fetch('/api/calendar/rooms');
            if (response.ok) {
                this.updateStatus('Calendar Server', 'active');
            } else {
                this.updateStatus('Calendar Server', 'error');
            }
        } catch (error) {
            // Calendar server not running - but our integration still works with fallback data
            this.updateStatus('Calendar Server', 'pending', 'Using fallback data');
        }
    }

    updateStatus(component, status, customText = null) {
        const statusMap = {
            'Web Interface': 'web-status',
            'Agent Process': 'agent-status',
            'Calendar Server': 'calendar-status'
        };

        const elementId = statusMap[component];
        const element = document.getElementById(elementId);
        
        if (!element) return;

        // Remove existing status classes
        element.classList.remove('status-active', 'status-pending', 'status-error');
        
        // Add new status class
        element.classList.add(`status-${status}`);
        
        // Update text
        const statusText = {
            'active': 'Active',
            'pending': customText || 'Pending',
            'error': customText || 'Error'
        };
        
        element.textContent = statusText[status];
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
            color: white;
            padding: 12px 20px;
            border-radius: 4px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            z-index: 1000;
            font-weight: 500;
        `;
        notification.textContent = message;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }

    startStatusUpdates() {
        // Update status every 30 seconds
        setInterval(() => {
            this.checkSystemStatus();
        }, 30000);
    }

    showNotImplemented(message) {
        // Create a temporary notification
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #fff3cd;
            color: #856404;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            max-width: 300px;
            border-left: 4px solid #ffc107;
        `;
        notification.innerHTML = `
            <strong>Coming Soon!</strong><br>
            ${message}
        `;

        document.body.appendChild(notification);

        // Auto-remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    // Utility method for future API calls
    async apiCall(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }

    // Method to add chat messages (enhanced for Stage 4)
    addChatMessage(message, type = 'user', timestamp = null) {
        const chatOutput = document.getElementById('chat-output');
        if (!chatOutput) return;

        const time = timestamp ? new Date(timestamp * 1000).toLocaleTimeString() : new Date().toLocaleTimeString();
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        let senderLabel = '';
        switch(type) {
            case 'user':
                senderLabel = 'You';
                break;
            case 'agent':
                senderLabel = 'Agent';
                break;
            case 'system':
                senderLabel = 'System';
                break;
            default:
                senderLabel = type.charAt(0).toUpperCase() + type.slice(1);
        }
        
        messageDiv.innerHTML = `<span class="timestamp">[${time}]</span> <strong>${senderLabel}:</strong> ${this.escapeHtml(message)}`;
        
        chatOutput.appendChild(messageDiv);
        
        // Limit number of messages to prevent memory issues
        const messages = chatOutput.querySelectorAll('.message');
        if (messages.length > this.maxOutputLines) {
            for (let i = 0; i < messages.length - this.maxOutputLines; i++) {
                messages[i].remove();
            }
        }
        
        this.scrollToBottom();
    }

    // Integration with chat interface
    sendMessage() {
        const chatInput = document.getElementById('chat-input');
        if (!chatInput) return;

        const message = chatInput.value.trim();
        if (!message) {
            this.showNotification('Please enter a message', 'warning');
            return;
        }

        // Check if agent is running
        if (!this.isConnected) {
            this.showNotification('WebSocket not connected. Please refresh the page.', 'error');
            return;
        }

        // Check for calendar commands (Stage 5)
        const calendarResponse = this.handleCalendarCommands(message);
        if (calendarResponse) {
            this.addChatMessage(calendarResponse, 'system');
        }

        // Send message via WebSocket
        this.socket.emit('send_message', { message: message });
        
        // Clear input
        chatInput.value = '';
        
        // Focus back to input for better UX
        chatInput.focus();
    }

    // Calendar integration methods (Stage 5)
    initializeCalendarEventListeners() {
        // Calendar refresh button
        const refreshBtn = document.getElementById('refresh-calendar-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                if (this.calendarManager) {
                    this.calendarManager.refreshCalendar();
                    this.showNotification('Calendar refreshed! 📅', 'success');
                }
            });
        }
    }

    handleQuickAction(buttonId) {
        switch(buttonId) {
            case 'view-calendar-btn':
                this.scrollToCalendar();
                if (this.calendarManager) {
                    this.calendarManager.renderCalendar();
                }
                this.addChatMessage('📅 Calendar view refreshed', 'system');
                break;
            case 'check-rooms-btn':
                this.scrollToRooms();
                if (this.calendarManager) {
                    this.calendarManager.renderRoomList();
                }
                this.addChatMessage('🏢 Room availability updated', 'system');
                break;
            case 'book-meeting-btn':
                this.addChatMessage('➕ Ask me to book a meeting! For example: "Book the Main Conference Room tomorrow at 2pm for a team meeting"', 'system');
                break;
            case 'view-events-btn':
                this.showTodaysEvents();
                break;
            default:
                this.showNotification('Feature coming soon!', 'info');
        }
    }

    handleCalendarCommands(message) {
        const lowerMessage = message.toLowerCase();
        
        // Calendar command shortcuts
        if (lowerMessage.includes('show calendar') || lowerMessage.includes('view calendar')) {
            this.scrollToCalendar();
            return 'Showing calendar view 📅';
        }
        
        if (lowerMessage.includes('check rooms') || lowerMessage.includes('room availability')) {
            this.scrollToRooms();
            return 'Showing room availability 🏢';
        }
        
        if (lowerMessage.includes('today events') || lowerMessage.includes('today\'s events')) {
            this.showTodaysEvents();
            return 'Showing today\'s events 📊';
        }
        
        if (lowerMessage.includes('book meeting') || lowerMessage.includes('schedule meeting')) {
            return 'Please provide meeting details and I\'ll help you book it! For example: "Book the Main Conference Room tomorrow at 2pm for a team meeting" ➕';
        }

        return null; // No calendar command detected
    }

    scrollToCalendar() {
        const calendarCard = document.querySelector('.calendar-card');
        if (calendarCard) {
            calendarCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    scrollToRooms() {
        const roomCard = document.querySelector('.room-card');
        if (roomCard) {
            roomCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    async showTodaysEvents() {
        try {
            const today = new Date();
            const tomorrow = new Date(today);
            tomorrow.setDate(tomorrow.getDate() + 1);
            
            const response = await fetch(`/api/calendar/events?start=${today.toISOString()}&end=${tomorrow.toISOString()}`);
            
            if (response.ok) {
                const data = await response.json();
                const events = data.events || [];
                
                if (events.length === 0) {
                    this.addChatMessage('📊 No events scheduled for today', 'system');
                } else {
                    let message = `📊 Today's events (${events.length}):\n`;
                    events.forEach(event => {
                        const startTime = new Date(event.start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                        message += `• ${startTime} - ${event.title} (${event.room_id})\n`;
                    });
                    this.addChatMessage(message, 'system');
                }
                
                // Also scroll to calendar
                this.scrollToCalendar();
                if (this.calendarManager) {
                    const todayString = today.toISOString().split('T')[0];
                    this.calendarManager.selectDate(todayString);
                }
            }
        } catch (error) {
            console.error('Error fetching today\'s events:', error);
            this.addChatMessage('❌ Could not fetch today\'s events', 'system');
        }
    }
}

// Initialize the UI when the page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Calendar Agent Web Interface initialized');
    console.log('🎉 Stage 5: Calendar Integration is active');
    
    window.calendarAgentUI = new CalendarAgentUI();
    
    // Add welcome message to chat
    setTimeout(() => {
        if (window.calendarAgentUI) {
            window.calendarAgentUI.addChatMessage(
                'Welcome to the Calendar Scheduling Agent! 🎉', 
                'system'
            );
            window.calendarAgentUI.addChatMessage(
                'Calendar integration is now active! You can view the calendar, check room availability, and book meetings using the interface below or by chatting with the agent.', 
                'system'
            );
            window.calendarAgentUI.addChatMessage(
                'Try asking: "show calendar", "check rooms", "book a meeting", or "today\'s events"', 
                'system'
            );
        }
    }, 1000);
});
