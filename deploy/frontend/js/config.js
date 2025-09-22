// Frontend Configuration
// These values will be replaced during deployment
const CONFIG = {
    // Backend Web Server URL
    WEB_SERVER_URL: window.WEB_SERVER_URL || 'http://localhost:8502',
    
    // WebSocket URL (usually same as web server)
    WEBSOCKET_URL: window.WEBSOCKET_URL || 'http://localhost:8502',
    
    // API endpoints
    API_BASE: window.API_BASE || '/api',
    
    // Feature flags
    ENABLE_DEBUG: window.ENABLE_DEBUG || false
};

// Export for use in other scripts
window.APP_CONFIG = CONFIG;