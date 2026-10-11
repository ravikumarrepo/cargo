/**
 * Cargo - Main JavaScript
 * Core application logic and UI interactions
 */

// Global state
const state = {
    airlines: [],
    results: [],
    currentPostIndex: 0,
    templates: []
};

// DOM Elements
const elements = {
    // Inputs
    titleInput: document.getElementById('titleInput'),
    contentInput: document.getElementById('contentInput'),
    airlineTextInput: document.getElementById('airlineTextInput'),
    airlineFileInput: document.getElementById('airlineFileInput'),
    originalNameInput: document.getElementById('originalNameInput'),
    caseSensitiveCheck: document.getElementById('caseSensitiveCheck'),

    // Counters
    titleCharCount: document.getElementById('titleCharCount'),
    contentCharCount: document.getElementById('contentCharCount'),
    contentLineCount: document.getElementById('contentLineCount'),
    airlineCount: document.getElementById('airlineCount'),

    // Displays
    airlinesDisplay: document.getElementById('airlinesDisplay'),
    airlinesList: document.getElementById('airlinesList'),

    // Buttons
    parseTextBtn: document.getElementById('parseTextBtn'),
    clearAirlinesBtn: document.getElementById('clearAirlinesBtn'),
    previewBtn: document.getElementById('previewBtn'),
    generateBtn: document.getElementById('generateBtn'),
    saveTemplateBtn: document.getElementById('saveTemplateBtn'),
    templatesBtn: document.getElementById('templatesBtn'),
    newProjectBtn: document.getElementById('newProjectBtn'),

    // Sections
    resultsSection: document.getElementById('resultsSection'),
    postsView: document.getElementById('postsView'),
    pdfsView: document.getElementById('pdfsView')
};

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    checkAuthentication();
    initializeEventListeners();
    setupCharCounters();
    setupReplacementMode();
    setupOutputMode();
    setupTabs();
});

// ============================================================================
// AUTHENTICATION
// ============================================================================

function getToken() {
    return localStorage.getItem('auth_token');
}

function getCurrentUser() {
    const user = localStorage.getItem('current_user');
    return user ? JSON.parse(user) : null;
}

function checkAuthentication() {
    const token = getToken();
    const user = getCurrentUser();

    if (!token || !user) {
        window.location.href = '/login';
        return;
    }

    // Update UI with user info
    document.getElementById('userName').textContent = user.full_name;

    if (user.is_admin) {
        document.getElementById('adminBtn').style.display = 'inline-block';
        document.getElementById('adminBtn').addEventListener('click', () => {
            window.location.href = '/admin';
        });
    }

    // Setup logout
    document.getElementById('logoutBtn').addEventListener('click', logout);
}

async function logout() {
    const token = getToken();
    try {
        await fetch('/api/auth/logout', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
    } catch (e) {
        // Continue with logout even if API call fails
    }

    localStorage.removeItem('auth_token');
    localStorage.removeItem('current_user');
    window.location.href = '/login';
}

// ============================================================================
// API HELPERS
// ============================================================================

async function apiCall(endpoint, method = 'GET', data = null) {
    const token = getToken();
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(endpoint, options);

        // Handle 401 - redirect to login
        if (response.status === 401) {
            window.location.href = '/login';
            return null;
        }

        return await response.json();
    } catch (error) {
        console.error('API error:', error);
        return null;
    }
}

// Event Listeners
function initializeEventListeners() {
    // Parse airlines
    elements.parseTextBtn.addEventListener('click', parseAirlinesFromText);
    elements.airlineFileInput.addEventListener('change', handleFileUpload);
    elements.clearAirlinesBtn.addEventListener('click', clearAirlines);

    // Actions
    elements.previewBtn.addEventListener('click', showPreview);
    elements.generateBtn.addEventListener('click', generateContent);
    elements.saveTemplateBtn.addEventListener('click', showSaveTemplateModal);
    elements.templatesBtn.addEventListener('click', showTemplatesModal);
    elements.newProjectBtn.addEventListener('click', resetProject);

    // Theme toggle
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }

    // Modals
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', closeModals);
    });

    // Click outside modal to close
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModals();
        });
    });
}

// Character Counters
function setupCharCounters() {
    elements.titleInput.addEventListener('input', () => {
        const count = elements.titleInput.value.length;
        elements.titleCharCount.textContent = `${count} characters`;
    });

    elements.contentInput.addEventListener('input', () => {
        const text = elements.contentInput.value;
        const charCount = text.length;
        const lineCount = text.split('\n').length;
        elements.contentCharCount.textContent = `${charCount} characters`;
        elements.contentLineCount.textContent = `${lineCount} lines`;
    });
}

// Replacement Mode Toggle
function setupReplacementMode() {
    const radios = document.querySelectorAll('input[name="replacementMode"]');
    const originalNameGroup = document.getElementById('originalNameGroup');

    radios.forEach(radio => {
        radio.addEventListener('change', () => {
            if (radio.value === 'original') {
                originalNameGroup.style.display = 'block';
            } else {
                originalNameGroup.style.display = 'none';
            }
        });
    });
}

// Output Mode Toggle
function setupOutputMode() {
    const radios = document.querySelectorAll('input[name="outputMode"]');
    const pdfSettings = document.getElementById('pdfSettings');

    radios.forEach(radio => {
        radio.addEventListener('change', () => {
            if (radio.value === 'pdfs' || radio.value === 'both') {
                pdfSettings.style.display = 'block';
            } else {
                pdfSettings.style.display = 'none';
            }
        });
    });
}

// Tabs
function setupTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;

            // Update active states
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Show correct tab content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(tab + 'Tab').classList.add('active');
        });
    });
}

// Parse Airlines from Text
async function parseAirlinesFromText() {
    const text = elements.airlineTextInput.value.trim();

    if (!text) {
        showToast('Please enter airline names', 'error');
        return;
    }

    try {
        const formData = new FormData();
        formData.append('text', text);

        const response = await fetch('/api/parse-airlines', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            state.airlines = data.airlines;
            displayAirlines();
            showToast(`Parsed ${data.airlines.length} airlines`, 'success');
        } else {
            showToast(data.error || 'Failed to parse airlines', 'error');
        }
    } catch (error) {
        console.error('Error parsing airlines:', error);
        showToast('Error parsing airlines', 'error');
    }
}

// Handle File Upload
async function handleFileUpload(e) {
    const file = e.target.files[0];

    if (!file) return;

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/parse-airlines', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            state.airlines = data.airlines;
            displayAirlines();
            showToast(`Loaded ${data.airlines.length} airlines from file`, 'success');
        } else {
            showToast(data.error || 'Failed to parse file', 'error');
        }
    } catch (error) {
        console.error('Error uploading file:', error);
        showToast('Error uploading file', 'error');
    }
}

// Display Airlines
function displayAirlines() {
    if (state.airlines.length === 0) {
        elements.airlinesDisplay.style.display = 'none';
        return;
    }

    elements.airlinesDisplay.style.display = 'block';
    elements.airlineCount.textContent = state.airlines.length;

    elements.airlinesList.innerHTML = '';

    state.airlines.forEach((airline, index) => {
        const tag = document.createElement('div');
        tag.className = 'airline-tag';
        tag.innerHTML = `
            <span>${escapeHtml(airline)}</span>
            <button onclick="removeAirline(${index})" title="Remove">&times;</button>
        `;
        elements.airlinesList.appendChild(tag);
    });
}

// Remove Airline
function removeAirline(index) {
    state.airlines.splice(index, 1);
    displayAirlines();
    showToast('Airline removed', 'success');
}

// Clear Airlines
function clearAirlines() {
    if (confirm('Clear all airlines?')) {
        state.airlines = [];
        elements.airlineTextInput.value = '';
        displayAirlines();
        showToast('Airlines cleared', 'success');
    }
}

// Get Form Data
function getFormData() {
    return {
        title: elements.titleInput.value.trim(),
        content: elements.contentInput.value.trim(),
        airlines: state.airlines,
        replacementMode: document.querySelector('input[name="replacementMode"]:checked').value,
        originalName: elements.originalNameInput.value.trim(),
        caseSensitive: elements.caseSensitiveCheck.checked,
        outputMode: document.querySelector('input[name="outputMode"]:checked').value,
        settings: {
            pageSize: document.getElementById('pageSizeSelect').value,
            orientation: document.getElementById('orientationSelect').value,
            fontSize: parseInt(document.getElementById('fontSizeInput').value),
            margin: parseInt(document.getElementById('marginInput').value)
        }
    };
}

// Show Preview
async function showPreview() {
    const data = getFormData();

    // Validate
    if (!data.title || !data.content) {
        showToast('Please enter title and content', 'error');
        return;
    }

    if (data.airlines.length === 0) {
        showToast('Please add airlines', 'error');
        return;
    }

    // Populate airline select
    const select = document.getElementById('previewAirlineSelect');
    select.innerHTML = data.airlines.map((airline, i) =>
        `<option value="${i}">${escapeHtml(airline)}</option>`
    ).join('');

    // Load preview for first airline
    await loadPreview(data.airlines[0], data);

    // Show modal
    document.getElementById('previewModal').classList.add('active');

    // Update on airline change
    select.addEventListener('change', async () => {
        const airline = data.airlines[select.value];
        await loadPreview(airline, data);
    });
}

// Load Preview
async function loadPreview(airline, formData) {
    try {
        const response = await fetch('/api/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: formData.title,
                content: formData.content,
                airline: airline,
                replacementMode: formData.replacementMode,
                originalName: formData.originalName,
                caseSensitive: formData.caseSensitive
            })
        });

        const preview = await response.json();

        // Display preview
        document.getElementById('previewOriginalTitle').textContent = preview.originalTitle;
        document.getElementById('previewGeneratedTitle').textContent = preview.generatedTitle;
        document.getElementById('previewOriginalContent').textContent = preview.originalContent;
        document.getElementById('previewGeneratedContent').textContent = preview.generatedContent;

        const stats = `${preview.totalReplacements} replacement(s) made (Title: ${preview.titleReplacements}, Content: ${preview.contentReplacements})`;
        document.getElementById('previewStats').textContent = stats;

        if (preview.warning) {
            document.getElementById('previewStats').innerHTML += `<br><span style="color: var(--warning)">⚠️ ${preview.warning}</span>`;
        }
    } catch (error) {
        console.error('Error loading preview:', error);
        showToast('Error loading preview', 'error');
    }
}

// Close Preview
document.getElementById('closePreviewBtn').addEventListener('click', closeModals);

// Reset Project
function resetProject() {
    if (confirm('Start a new project? All unsaved data will be lost.')) {
        elements.titleInput.value = '';
        elements.contentInput.value = '';
        elements.airlineTextInput.value = '';
        elements.originalNameInput.value = '';
        elements.caseSensitiveCheck.checked = false;
        state.airlines = [];
        state.results = [];
        state.currentPostIndex = 0;
        displayAirlines();
        elements.resultsSection.style.display = 'none';
        showToast('Project reset', 'success');
    }
}

// Close Modals
function closeModals() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.classList.remove('active');
    });
}

// Show Toast Notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Export for use in other files
window.state = state;
window.elements = elements;
window.getFormData = getFormData;
window.showToast = showToast;
window.escapeHtml = escapeHtml;
window.displayAirlines = displayAirlines;
window.removeAirline = removeAirline;

// Theme Management
function initializeTheme() {
    // Check for saved theme preference or default to light mode
    const savedTheme = localStorage.getItem('cargo-theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('cargo-theme', newTheme);

    showToast(`Switched to ${newTheme} mode`, 'success');
}

window.toggleTheme = toggleTheme;
window.initializeTheme = initializeTheme;
