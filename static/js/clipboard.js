/**
 * Cargo - Clipboard Operations
 * Handles all clipboard copy functionality
 */

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @param {string} successMessage - Message to show on success
 */
async function copyToClipboard(text, successMessage = 'Copied to clipboard!') {
    try {
        // Try modern Clipboard API first
        if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(text);
            showToast(successMessage, 'success');
            return true;
        }

        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.left = '-9999px';
        textarea.style.top = '0';
        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();

        const successful = document.execCommand('copy');
        document.body.removeChild(textarea);

        if (successful) {
            showToast(successMessage, 'success');
            return true;
        } else {
            throw new Error('Copy command failed');
        }
    } catch (error) {
        console.error('Failed to copy:', error);
        showToast('Failed to copy to clipboard', 'error');

        // Show manual copy prompt as last resort
        showManualCopyPrompt(text);
        return false;
    }
}

/**
 * Show manual copy prompt
 * @param {string} text - Text to display for manual copying
 */
function showManualCopyPrompt(text) {
    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>Copy Text</h2>
                <button class="modal-close" onclick="this.closest('.modal').remove()">&times;</button>
            </div>
            <div class="modal-body">
                <p style="margin-bottom: 12px; color: var(--text-secondary);">
                    Please copy the text manually:
                </p>
                <textarea
                    readonly
                    class="form-control"
                    rows="10"
                    style="font-size: 13px;"
                    onclick="this.select()"
                >${text}</textarea>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">Close</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Auto-select text
    const textarea = modal.querySelector('textarea');
    textarea.select();
}

/**
 * Copy formatted content (title + content)
 * @param {string} title - Content title
 * @param {string} content - Content body
 * @param {string} separator - Separator between title and content
 */
async function copyFormatted(title, content, separator = '\n\n') {
    const combined = `${title}${separator}${content}`;
    return await copyToClipboard(combined);
}

/**
 * Copy multiple items with delimiters
 * @param {Array} items - Array of objects with title and content
 * @param {string} itemSeparator - Separator between items
 */
async function copyMultipleItems(items, itemSeparator = '\n\n---\n\n') {
    const combined = items.map(item => {
        if (item.airline) {
            return `${item.airline}\n\n${item.generatedTitle}\n\n${item.generatedContent}`;
        }
        return `${item.generatedTitle}\n\n${item.generatedContent}`;
    }).join(itemSeparator);

    return await copyToClipboard(combined);
}

/**
 * Check if clipboard API is available
 * @returns {boolean}
 */
function isClipboardAvailable() {
    return !!(navigator.clipboard && navigator.clipboard.writeText);
}

/**
 * Request clipboard permissions (for browsers that require it)
 */
async function requestClipboardPermissions() {
    try {
        if (navigator.permissions && navigator.permissions.query) {
            const result = await navigator.permissions.query({ name: 'clipboard-write' });
            return result.state === 'granted' || result.state === 'prompt';
        }
        return true; // Assume granted if permissions API not available
    } catch (error) {
        return true; // Assume granted on error
    }
}

// Export functions for use in other modules
window.copyToClipboard = copyToClipboard;
window.copyFormatted = copyFormatted;
window.copyMultipleItems = copyMultipleItems;
window.isClipboardAvailable = isClipboardAvailable;
window.requestClipboardPermissions = requestClipboardPermissions;
