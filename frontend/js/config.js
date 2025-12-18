/**
 * Resume Scanner API Configuration
 * 
 * IMPORTANT: Update API_BASE_URL to your deployed backend URL
 * 
 * Examples:
 * - Railway: https://resume-scanner-production.up.railway.app
 * - Render: https://resume-scanner.onrender.com
 * - Local: http://localhost:5000
 */

const CONFIG = {
    // ⚠️ CHANGE THIS to your Railway/Render backend URL
    API_BASE_URL: 'https://your-backend-url.railway.app',

    // API Endpoints (don't change these)
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
    return CONFIG.API_BASE_URL + endpoint;
}

// Check if we're running locally
function isLocalDev() {
    return window.location.hostname === 'localhost' ||
        window.location.hostname === '127.0.0.1' ||
        window.location.protocol === 'file:';
}

// Auto-detect API URL for local development
if (isLocalDev() && CONFIG.API_BASE_URL.includes('your-backend-url')) {
    CONFIG.API_BASE_URL = 'http://localhost:5000';
    console.log('Development mode: Using local API at', CONFIG.API_BASE_URL);
}
