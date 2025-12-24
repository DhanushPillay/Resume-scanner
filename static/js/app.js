/**
 * Resume Scanner AI - Frontend Application
 * Connects to backend API for resume analysis
 */

// DOM Elements
const greeting = document.getElementById('greeting');
const chatContainer = document.getElementById('chat-container');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const fileInput = document.getElementById('file-input');
const filePreview = document.getElementById('file-preview');
const dropZone = document.getElementById('drop-zone');
const connectionStatus = document.getElementById('connection-status');

let selectedFile = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    messageInput.focus();
    checkConnection();
    setupQuickActions();
});

// Check API connection
async function checkConnection() {
    const statusDot = connectionStatus.querySelector('.status-dot');
    const statusText = connectionStatus.querySelector('.status-text');

    try {
        const response = await fetch(getApiUrl(CONFIG.ENDPOINTS.HEALTH || '/api/health'), {
            method: 'GET',
            mode: 'cors'
        });

        if (response.ok) {
            statusDot.classList.add('connected');
            statusText.textContent = 'Connected';
        } else {
            throw new Error('API returned error');
        }
    } catch (error) {
        // Try a simple GET to root to check if server is up
        try {
            const rootResponse = await fetch(CONFIG.API_BASE_URL, { mode: 'cors' });
            if (rootResponse.ok) {
                statusDot.classList.add('connected');
                statusText.textContent = 'Connected';
                return;
            }
        } catch (e) { }

        statusDot.classList.add('error');
        statusText.textContent = 'Disconnected';
        console.warn('API connection failed:', error);
    }
}

// Setup quick action buttons
function setupQuickActions() {
    document.querySelectorAll('.quick-action').forEach(btn => {
        btn.addEventListener('click', () => {
            const action = btn.dataset.action;
            switch (action) {
                case 'upload':
                    fileInput.click();
                    break;
                case 'github':
                    messageInput.value = 'https://github.com/';
                    messageInput.focus();
                    messageInput.setSelectionRange(19, 19);
                    break;
                case 'compare':
                    messageInput.value = 'Compare all analyzed candidates';
                    sendMessage();
                    break;
            }
        });
    });
}

// Send message on Enter
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Send button click
sendBtn.addEventListener('click', sendMessage);

// File input change
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        selectFile(e.target.files[0]);
    }
});

// Drag and drop
document.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('active');
});

document.addEventListener('dragleave', (e) => {
    if (e.relatedTarget === null) {
        dropZone.classList.remove('active');
    }
});

document.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('active');

    if (e.dataTransfer.files.length > 0) {
        const file = e.dataTransfer.files[0];
        if (file.name.match(/\.(pdf|docx)$/i)) {
            selectFile(file);
        } else {
            showError('Please upload a PDF or DOCX file');
        }
    }
});

function selectFile(file) {
    selectedFile = file;
    filePreview.innerHTML = `
        <span class="file-name">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
            </svg>
            ${file.name}
        </span>
        <button class="remove-btn" onclick="removeFile()">×</button>
    `;
    filePreview.classList.add('active');
}

function removeFile() {
    selectedFile = null;
    fileInput.value = '';
    filePreview.classList.remove('active');
}

async function sendMessage() {
    const message = messageInput.value.trim();

    if (!message && !selectedFile) return;

    // Hide greeting, show chat
    greeting.classList.add('hidden');
    chatContainer.classList.add('active');

    // Add user message
    if (selectedFile) {
        addMessage('user', `
            <div class="file-upload-msg">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                </svg>
                Analyzing: ${selectedFile.name}
            </div>
        `);
    } else if (message) {
        addMessage('user', escapeHtml(message));
    }

    // Clear input
    messageInput.value = '';

    // Show loading
    const loadingId = showLoading();

    try {
        let response;

        if (selectedFile) {
            // Upload file to API
            const formData = new FormData();
            formData.append('file', selectedFile);

            response = await fetch(getApiUrl(CONFIG.ENDPOINTS.ANALYZE), {
                method: 'POST',
                body: formData,
                mode: 'cors'
            });

            removeFile();
        } else {
            // Send chat message to API
            response = await fetch(getApiUrl(CONFIG.ENDPOINTS.CHAT), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message }),
                mode: 'cors'
            });
        }

        const data = await response.json();

        // Remove loading
        removeLoading(loadingId);

        if (data.error) {
            addMessage('assistant', `<p class="error">${escapeHtml(data.error)}</p>`);
        } else {
            addMessage('assistant', data.html);
        }

    } catch (error) {
        removeLoading(loadingId);
        addMessage('assistant', `
            <div class="error-msg">
                <p class="error">Failed to connect to the server.</p>
                <p class="error-details">Make sure your backend is running at:<br><code>${CONFIG.API_BASE_URL}</code></p>
            </div>
        `);
        console.error('API Error:', error);
    }
}

function addMessage(role, content) {
    const div = document.createElement('div');
    div.className = `message ${role}`;

    const avatar = role === 'assistant' ? `
        <div class="avatar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M8 14s1.5 2 4 2 4-2 4-2"/>
                <line x1="9" y1="9" x2="9.01" y2="9"/>
                <line x1="15" y1="9" x2="15.01" y2="9"/>
            </svg>
        </div>
    ` : '';

    div.innerHTML = `${avatar}<div class="content">${content}</div>`;
    chatContainer.appendChild(div);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function showLoading() {
    const id = 'loading-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = 'message assistant';
    div.innerHTML = `
        <div class="avatar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M8 14s1.5 2 4 2 4-2 4-2"/>
                <line x1="9" y1="9" x2="9.01" y2="9"/>
                <line x1="15" y1="9" x2="15.01" y2="9"/>
            </svg>
        </div>
        <div class="loading">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    chatContainer.appendChild(div);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return id;
}

function removeLoading(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function showError(message) {
    // Show toast notification
    const toast = document.createElement('div');
    toast.className = 'toast error';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
