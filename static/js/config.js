/**
 * Resume Scanner API Configuration
 * 
 * Configured for local Flask backend.
 */

const CONFIG = {
    // Empty string = relative path (same origin)
    // This works perfectly when serving from Flask
    API_BASE_URL: '',

    // API Endpoints
    ENDPOINTS: {
        ANALYZE: '/api/analyze',
        CHAT: '/api/chat',
        CANDIDATES: '/api/candidates',
        HEALTH: '/api/health'
    },

    // Request timeout in milliseconds
    TIMEOUT: 60000,

    // Retry configuration
    RETRY: {
        MAX_ATTEMPTS: 3,
        DELAY_MS: 1000
    }
};

// Helper to get full API URL
function getApiUrl(endpoint) {
    // If base url is empty, it uses current origin
    return CONFIG.API_BASE_URL + endpoint;
}
