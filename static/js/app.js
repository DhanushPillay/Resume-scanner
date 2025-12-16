// Resume Scanner AI - Frontend JavaScript

const greeting = document.getElementById('greeting');
const chatContainer = document.getElementById('chat-container');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const fileInput = document.getElementById('file-input');
const filePreview = document.getElementById('file-preview');
const dropZone = document.getElementById('drop-zone');

let selectedFile = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    messageInput.focus();
});

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
        <span>${file.name}</span>
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
        addMessage('user', `Uploaded: ${selectedFile.name}`);
    } else if (message) {
        addMessage('user', message);
    }

    // Clear input
    messageInput.value = '';

    // Show loading
    const loadingId = showLoading();

    try {
        let response;

        if (selectedFile) {
            // Upload file
            const formData = new FormData();
            formData.append('file', selectedFile);

            response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });

            removeFile();
        } else {
            // Send chat message
            response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });
        }

        const data = await response.json();

        // Remove loading
        removeLoading(loadingId);

        if (data.error) {
            addMessage('assistant', `<p class="error">${data.error}</p>`);
        } else {
            addMessage('assistant', data.html);
        }

    } catch (error) {
        removeLoading(loadingId);
        addMessage('assistant', `<p class="error">Something went wrong. Please try again.</p>`);
        console.error(error);
    }
}

function addMessage(role, content) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = `<div class="content">${content}</div>`;
    chatContainer.appendChild(div);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function showLoading() {
    const id = 'loading-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = 'message assistant';
    div.innerHTML = `
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
    alert(message);
}
