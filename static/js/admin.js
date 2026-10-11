/**
 * Cargo Admin Dashboard JavaScript
 * Admin functionality for user management and audit logs
 */

// State
const adminState = {
    currentSection: 'overview',
    currentUser: null,
    stats: {},
    users: [],
    auditLogs: [],
    usersPage: 0,
    auditPage: 0,
    usersPerPage: 20,
    auditPerPage: 50
};

// Get token
function getToken() {
    return localStorage.getItem('auth_token') || document.querySelector('meta[name="auth-token"]')?.content;
}

// API Call
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
        if (response.status === 401) {
            window.location.href = '/login';
            return null;
        }
        return await response.json();
    } catch (error) {
        showToast('Network error: ' + error.message, 'error');
        return null;
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    initializeTheme();
    setupEventListeners();

    const user = JSON.parse(localStorage.getItem('current_user') || '{}');
    adminState.currentUser = user;
    document.getElementById('userEmail').textContent = user.email || '';

    await loadStats();
    await loadUsers();
    await loadAuditLog();

    // Auto-refresh stats every 5 seconds
    setInterval(loadStats, 5000);
});

// Event Listeners
function setupEventListeners() {
    // Section Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const section = item.dataset.section;
            switchSection(section);
        });
    });

    // Theme Toggle
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }

    // Logout
    document.getElementById('logoutBtn').addEventListener('click', logout);

    // Search and Filter
    document.getElementById('searchUsers').addEventListener('input', () => {
        adminState.usersPage = 0;
        loadUsers();
    });

    document.getElementById('filterStatus').addEventListener('change', () => {
        adminState.usersPage = 0;
        loadUsers();
    });

    document.getElementById('filterAction').addEventListener('change', () => {
        adminState.auditPage = 0;
        loadAuditLog();
    });

    // Modal
    document.querySelector('.modal-close').addEventListener('click', closeModal);
    document.getElementById('modalCancel').addEventListener('click', closeModal);
    document.getElementById('actionModal').addEventListener('click', (e) => {
        if (e.target.id === 'actionModal') closeModal();
    });
}

// Theme
function initializeTheme() {
    const theme = localStorage.getItem('cargo-theme') || 'light';
    document.documentElement.setAttribute('data-theme', theme);
    if (theme === 'dark') {
        document.body.classList.add('dark-mode');
    }
}

function toggleTheme() {
    const isDark = document.body.classList.toggle('dark-mode');
    const theme = isDark ? 'dark' : 'light';
    localStorage.setItem('cargo-theme', theme);
    document.documentElement.setAttribute('data-theme', theme);
}

// Section Navigation
function switchSection(section) {
    // Update active nav item
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-section="${section}"]`).classList.add('active');

    // Update active section
    document.querySelectorAll('.admin-section').forEach(sec => {
        sec.classList.remove('active');
    });
    document.getElementById(section).classList.add('active');

    adminState.currentSection = section;
}

// Load Stats
async function loadStats() {
    const result = await apiCall('/api/admin/stats');
    if (!result) return;

    adminState.stats = result;
    document.getElementById('statTotal').textContent = result.total || 0;
    document.getElementById('statPending').textContent = result.pending || 0;
    document.getElementById('statApproved').textContent = result.approved || 0;
    document.getElementById('statRejected').textContent = result.rejected || 0;
    document.getElementById('statRevoked').textContent = result.revoked || 0;
    document.getElementById('statSuspended').textContent = result.suspended || 0;
}

// Load Users
async function loadUsers() {
    const search = document.getElementById('searchUsers').value;
    const status = document.getElementById('filterStatus').value;

    const params = new URLSearchParams({
        limit: adminState.usersPerPage,
        offset: adminState.usersPage * adminState.usersPerPage,
        search: search || '',
        status: status || ''
    });

    const result = await apiCall(`/api/admin/users?${params}`);
    if (!result) return;

    adminState.users = result.users || [];
    renderUsersTable();
    renderUsersPagination(result.total);
}

// Render Users Table
function renderUsersTable() {
    const tbody = document.getElementById('usersTableBody');

    if (adminState.users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading">No users found</td></tr>';
        return;
    }

    tbody.innerHTML = adminState.users.map(user => `
        <tr>
            <td><strong>${escapeHtml(user.email)}</strong></td>
            <td>${escapeHtml(user.full_name)}</td>
            <td><span class="status-badge ${user.account_status}">${user.account_status}</span></td>
            <td>${new Date(user.created_at).toLocaleDateString()}</td>
            <td>
                <div class="action-buttons">
                    ${renderUserActions(user)}
                </div>
            </td>
        </tr>
    `).join('');
}

// Render User Actions
function renderUserActions(user) {
    const actions = [];

    switch (user.account_status) {
        case 'pending':
            actions.push(`<button class="btn-sm approve" onclick="approveUser('${user.id}')">Approve</button>`);
            actions.push(`<button class="btn-sm reject" onclick="rejectUser('${user.id}')">Reject</button>`);
            break;
        case 'approved':
            actions.push(`<button class="btn-sm suspend" onclick="suspendUser('${user.id}')">Suspend</button>`);
            actions.push(`<button class="btn-sm revoke" onclick="revokeUser('${user.id}')">Revoke</button>`);
            break;
        case 'suspended':
            actions.push(`<button class="btn-sm restore" onclick="restoreUser('${user.id}')">Restore</button>`);
            break;
        case 'revoked':
            actions.push(`<button class="btn-sm restore" onclick="restoreUser('${user.id}')">Restore</button>`);
            break;
    }

    actions.push(`<button class="btn-sm" onclick="logoutUser('${user.id}')">Logout</button>`);

    return actions.join('');
}

// Render Users Pagination
function renderUsersPagination(total) {
    const totalPages = Math.ceil(total / adminState.usersPerPage);
    const container = document.getElementById('usersPagination');

    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }

    let html = '';

    if (adminState.usersPage > 0) {
        html += `<button onclick="changePage('users', ${adminState.usersPage - 1})">← Previous</button>`;
    }

    for (let i = Math.max(0, adminState.usersPage - 2); i < Math.min(totalPages, adminState.usersPage + 3); i++) {
        html += `<button ${i === adminState.usersPage ? 'class="active"' : ''} onclick="changePage('users', ${i})">${i + 1}</button>`;
    }

    if (adminState.usersPage < totalPages - 1) {
        html += `<button onclick="changePage('users', ${adminState.usersPage + 1})">Next →</button>`;
    }

    container.innerHTML = html;
}

// Load Audit Log
async function loadAuditLog() {
    const action = document.getElementById('filterAction').value;

    const params = new URLSearchParams({
        limit: adminState.auditPerPage,
        offset: adminState.auditPage * adminState.auditPerPage,
        action: action || ''
    });

    const result = await apiCall(`/api/admin/audit-log?${params}`);
    if (!result) return;

    adminState.auditLogs = result.logs || [];
    renderAuditTable();
    renderAuditPagination(result.total);
}

// Render Audit Table
function renderAuditTable() {
    const tbody = document.getElementById('auditTableBody');

    if (adminState.auditLogs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading">No audit entries</td></tr>';
        return;
    }

    tbody.innerHTML = adminState.auditLogs.map(log => `
        <tr>
            <td>${new Date(log.timestamp).toLocaleString()}</td>
            <td><strong>${escapeHtml(log.action)}</strong></td>
            <td>${escapeHtml(log.admin_email || 'N/A')}</td>
            <td>${escapeHtml(log.target_email || 'N/A')}</td>
            <td>${escapeHtml(log.details || '')}</td>
        </tr>
    `).join('');
}

// Render Audit Pagination
function renderAuditPagination(total) {
    const totalPages = Math.ceil(total / adminState.auditPerPage);
    const container = document.getElementById('auditPagination');

    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }

    let html = '';

    if (adminState.auditPage > 0) {
        html += `<button onclick="changePage('audit', ${adminState.auditPage - 1})">← Previous</button>`;
    }

    for (let i = Math.max(0, adminState.auditPage - 2); i < Math.min(totalPages, adminState.auditPage + 3); i++) {
        html += `<button ${i === adminState.auditPage ? 'class="active"' : ''} onclick="changePage('audit', ${i})">${i + 1}</button>`;
    }

    if (adminState.auditPage < totalPages - 1) {
        html += `<button onclick="changePage('audit', ${adminState.auditPage + 1})">Next →</button>`;
    }

    container.innerHTML = html;
}

// Change Page
function changePage(type, page) {
    if (type === 'users') {
        adminState.usersPage = page;
        loadUsers();
    } else {
        adminState.auditPage = page;
        loadAuditLog();
    }
}

// User Actions
function approveUser(userId) {
    showConfirmModal('Approve User', 'Are you sure you want to approve this user?', async () => {
        const result = await apiCall(`/api/admin/users/${userId}/approve`, 'POST');
        if (result && result.success) {
            showToast(result.message, 'success');
            closeModal();
            loadUsers();
            loadStats();
        } else {
            showToast(result?.error || 'Failed to approve user', 'error');
        }
    });
}

function rejectUser(userId) {
    showModalWithInput(
        'Reject User',
        'Enter rejection reason (optional):',
        'textarea',
        async (reason) => {
            const result = await apiCall(`/api/admin/users/${userId}/reject`, 'POST', { reason });
            if (result && result.success) {
                showToast(result.message, 'success');
                closeModal();
                loadUsers();
                loadStats();
            } else {
                showToast(result?.error || 'Failed to reject user', 'error');
            }
        }
    );
}

function revokeUser(userId) {
    showConfirmModal('Revoke Access', 'Are you sure you want to revoke this user\'s access?', async () => {
        const result = await apiCall(`/api/admin/users/${userId}/revoke`, 'POST');
        if (result && result.success) {
            showToast(result.message, 'success');
            closeModal();
            loadUsers();
            loadStats();
        } else {
            showToast(result?.error || 'Failed to revoke access', 'error');
        }
    });
}

function restoreUser(userId) {
    showConfirmModal('Restore Access', 'Are you sure you want to restore this user\'s access?', async () => {
        const result = await apiCall(`/api/admin/users/${userId}/restore`, 'POST');
        if (result && result.success) {
            showToast(result.message, 'success');
            closeModal();
            loadUsers();
            loadStats();
        } else {
            showToast(result?.error || 'Failed to restore access', 'error');
        }
    });
}

function suspendUser(userId) {
    showConfirmModal('Suspend User', 'Are you sure you want to suspend this user?', async () => {
        const result = await apiCall(`/api/admin/users/${userId}/suspend`, 'POST');
        if (result && result.success) {
            showToast(result.message, 'success');
            closeModal();
            loadUsers();
            loadStats();
        } else {
            showToast(result?.error || 'Failed to suspend user', 'error');
        }
    });
}

function logoutUser(userId) {
    showConfirmModal('Logout User', 'Force logout all sessions for this user?', async () => {
        const result = await apiCall(`/api/admin/users/${userId}/logout`, 'POST');
        if (result && result.success) {
            showToast(result.message, 'success');
            closeModal();
        } else {
            showToast(result?.error || 'Failed to logout user', 'error');
        }
    });
}

// Modal Functions
function showConfirmModal(title, message, onConfirm) {
    const modal = document.getElementById('actionModal');
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalMessage').textContent = message;
    document.getElementById('modalInputs').innerHTML = '';

    document.getElementById('modalConfirm').onclick = onConfirm;
    modal.style.display = 'flex';
}

function showModalWithInput(title, message, inputType, onConfirm) {
    const modal = document.getElementById('actionModal');
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalMessage').textContent = message;

    const inputsDiv = document.getElementById('modalInputs');
    const textarea = document.createElement('textarea');
    textarea.id = 'modalInput';
    textarea.placeholder = 'Enter details...';
    inputsDiv.innerHTML = '';
    inputsDiv.appendChild(textarea);

    document.getElementById('modalConfirm').onclick = () => {
        const value = textarea.value;
        onConfirm(value);
    };

    modal.style.display = 'flex';
}

function closeModal() {
    document.getElementById('actionModal').style.display = 'none';
}

// Toast
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Logout
async function logout() {
    const token = getToken();
    await apiCall('/api/auth/logout', 'POST');
    localStorage.removeItem('auth_token');
    localStorage.removeItem('current_user');
    window.location.href = '/login';
}

// Utility
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}
