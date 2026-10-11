/**
 * Cargo - Generator
 * Content generation and PDF creation logic
 */

// Generate Content
async function generateContent() {
    const data = getFormData();

    // Validate inputs
    const validation = await validateInputs(data);
    if (!validation.valid) {
        showToast(validation.errors[0], 'error');
        return;
    }

    // Disable generate button
    elements.generateBtn.disabled = true;
    elements.generateBtn.textContent = 'Generating...';

    try {
        // Generate content for all airlines
        const result = await apiCall('/api/generate', 'POST', {
            title: data.title,
            content: data.content,
            airlines: data.airlines,
            replacementMode: data.replacementMode,
            originalName: data.originalName,
            caseSensitive: data.caseSensitive
        });

        if (result.success) {
            state.results = result.results;
            state.currentPostIndex = 0;

            // Show results based on output mode
            showResults(data.outputMode, data.settings);

            showToast(`Generated content for ${result.count} airlines`, 'success');
        } else {
            showToast(result.error || 'Generation failed', 'error');
        }
    } catch (error) {
        console.error('Error generating content:', error);
        showToast('Error generating content', 'error');
    } finally {
        elements.generateBtn.disabled = false;
        elements.generateBtn.textContent = 'Generate Content';
    }
}

// Validate Inputs
async function validateInputs(data) {
    try {
        return await apiCall('/api/validate', 'POST', data);
    } catch (error) {
        return {
            valid: false,
            errors: ['Validation failed']
        };
    }
}

// Show Results
function showResults(outputMode, settings) {
    elements.resultsSection.style.display = 'block';

    // Scroll to results
    elements.resultsSection.scrollIntoView({ behavior: 'smooth' });

    // Update summary
    document.getElementById('resultsSummary').textContent =
        `Generated ${state.results.length} items`;

    if (outputMode === 'posts') {
        showPostsView();
    } else if (outputMode === 'pdfs') {
        showPdfsView(settings);
    } else if (outputMode === 'both') {
        showPostsView();
        setTimeout(() => generateBulkPdfs(settings), 500);
    }
}

// Show Posts View
function showPostsView() {
    elements.postsView.style.display = 'block';
    elements.pdfsView.style.display = 'none';

    displayCurrentPost();

    // Navigation
    document.getElementById('prevPostBtn').addEventListener('click', () => {
        if (state.currentPostIndex > 0) {
            state.currentPostIndex--;
            displayCurrentPost();
        }
    });

    document.getElementById('nextPostBtn').addEventListener('click', () => {
        if (state.currentPostIndex < state.results.length - 1) {
            state.currentPostIndex++;
            displayCurrentPost();
        }
    });

    // Copy buttons
    document.getElementById('copyTitleBtn').addEventListener('click', () => {
        const post = state.results[state.currentPostIndex];
        copyToClipboard(post.generatedTitle, 'Title copied!');
    });

    document.getElementById('copyContentBtn').addEventListener('click', () => {
        const post = state.results[state.currentPostIndex];
        copyToClipboard(post.generatedContent, 'Content copied!');
    });

    document.getElementById('copyBothBtn').addEventListener('click', () => {
        const post = state.results[state.currentPostIndex];
        const combined = `${post.generatedTitle}\n\n${post.generatedContent}`;
        copyToClipboard(combined, 'Title and content copied!');
    });

    // Bulk actions
    document.getElementById('copyAllPostsBtn').addEventListener('click', copyAllPosts);
    document.getElementById('exportPostsBtn').addEventListener('click', exportPostsAsJson);
}

// Display Current Post
function displayCurrentPost() {
    const post = state.results[state.currentPostIndex];

    document.getElementById('postAirline').textContent = post.airline;
    document.getElementById('postTitle').textContent = post.generatedTitle;
    document.getElementById('postContent').textContent = post.generatedContent;

    document.getElementById('postCounter').textContent =
        `${state.currentPostIndex + 1} of ${state.results.length}`;

    // Update button states
    document.getElementById('prevPostBtn').disabled = state.currentPostIndex === 0;
    document.getElementById('nextPostBtn').disabled =
        state.currentPostIndex === state.results.length - 1;
}

// Show PDFs View
function showPdfsView(settings) {
    elements.postsView.style.display = 'none';
    elements.pdfsView.style.display = 'block';

    generateBulkPdfs(settings);
}

// Generate Bulk PDFs
async function generateBulkPdfs(settings) {
    const progressBar = document.getElementById('generationProgressBar');
    const statusText = document.getElementById('generationStatus');
    const pdfsReady = document.getElementById('pdfsReady');

    pdfsReady.style.display = 'none';
    progressBar.style.width = '0%';
    statusText.textContent = 'Preparing PDF generation...';

    try {
        // Update progress
        statusText.textContent = `Generating ${state.results.length} PDFs...`;

        // Simulate progress (actual generation happens on server)
        let progress = 0;
        const interval = setInterval(() => {
            progress += 10;
            if (progress <= 90) {
                progressBar.style.width = progress + '%';
            }
        }, 200);

        // Generate PDFs
        const token = getToken();
        const response = await fetch('/api/generate-bulk-pdfs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                results: state.results,
                settings: settings
            })
        });

        clearInterval(interval);
        progressBar.style.width = '100%';

        if (response.ok) {
            // Store blob for download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);

            // Show download button
            statusText.textContent = 'PDFs generated successfully!';
            pdfsReady.style.display = 'block';

            document.getElementById('downloadAllPdfsBtn').onclick = () => {
                const a = document.createElement('a');
                a.href = url;
                a.download = `cargo_pdfs_${Date.now()}.zip`;
                a.click();
                showToast('Downloading PDFs...', 'success');
            };
        } else {
            throw new Error('PDF generation failed');
        }
    } catch (error) {
        console.error('Error generating PDFs:', error);
        statusText.textContent = 'Error generating PDFs';
        showToast('Error generating PDFs', 'error');
    }
}

// Copy All Posts
function copyAllPosts() {
    const combined = state.results.map(post => {
        return `${post.airline}\n\n${post.generatedTitle}\n\n${post.generatedContent}\n\n---\n`;
    }).join('\n');

    copyToClipboard(combined, `Copied all ${state.results.length} posts!`);
}

// Export Posts as JSON
function exportPostsAsJson() {
    const json = JSON.stringify(state.results, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `cargo_export_${Date.now()}.json`;
    a.click();

    showToast('Exported as JSON', 'success');
}

// Template Management
function showSaveTemplateModal() {
    const data = getFormData();

    if (!data.title || !data.content) {
        showToast('Please enter title and content first', 'error');
        return;
    }

    document.getElementById('templateModal').classList.add('active');
    document.getElementById('templateNameInput').value = '';

    document.getElementById('confirmSaveTemplateBtn').onclick = async () => {
        const name = document.getElementById('templateNameInput').value.trim();

        if (!name) {
            showToast('Please enter template name', 'error');
            return;
        }

        await saveTemplate(name, data);
    };
}

async function saveTemplate(name, data) {
    try {
        const result = await apiCall('/api/templates', 'POST', {
            name: name,
            title: data.title,
            content: data.content,
            replacementMode: data.replacementMode,
            originalName: data.originalName,
            caseSensitive: data.caseSensitive,
            settings: data.settings
        });

        if (result.success) {
            showToast('Template saved successfully', 'success');
            closeModals();
        } else {
            showToast(result.error || 'Failed to save template', 'error');
        }
    } catch (error) {
        console.error('Error saving template:', error);
        showToast('Error saving template', 'error');
    }
}

async function showTemplatesModal() {
    try {
        const data = await apiCall('/api/templates');

        if (data && data.success) {
            displayTemplates(data.templates);
            document.getElementById('templatesListModal').classList.add('active');
        } else {
            showToast('Failed to load templates', 'error');
        }
    } catch (error) {
        console.error('Error loading templates:', error);
        showToast('Error loading templates', 'error');
    }
}

function displayTemplates(templates) {
    const container = document.getElementById('templatesList');

    if (templates.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: var(--text-muted);">No templates saved yet</p>';
        return;
    }

    container.innerHTML = templates.map(template => `
        <div class="template-item" style="padding: 16px; border: 1px solid var(--border); border-radius: var(--radius); margin-bottom: 12px;">
            <h3 style="margin-bottom: 4px;">${escapeHtml(template.name)}</h3>
            <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px;">
                Created: ${new Date(template.createdAt).toLocaleDateString()}
            </p>
            <div style="display: flex; gap: 8px;">
                <button onclick="loadTemplate('${template.id}')" class="btn btn-sm btn-primary">Load</button>
                <button onclick="deleteTemplate('${template.id}')" class="btn btn-sm btn-secondary">Delete</button>
            </div>
        </div>
    `).join('');
}

async function loadTemplate(id) {
    try {
        const data = await apiCall(`/api/templates/${id}`);

        if (data && data.success) {
            const template = data.template;

            elements.titleInput.value = template.title;
            elements.contentInput.value = template.content;
            elements.originalNameInput.value = template.originalName || '';
            elements.caseSensitiveCheck.checked = template.caseSensitive || false;

            document.querySelector(`input[name="replacementMode"][value="${template.replacementMode}"]`).checked = true;

            closeModals();
            showToast('Template loaded', 'success');
        } else {
            showToast('Failed to load template', 'error');
        }
    } catch (error) {
        console.error('Error loading template:', error);
        showToast('Error loading template', 'error');
    }
}

async function deleteTemplate(id) {
    if (!confirm('Delete this template?')) return;

    try {
        const data = await apiCall(`/api/templates/${id}`, 'DELETE');

        if (data && data.success) {
            showToast('Template deleted', 'success');
            showTemplatesModal(); // Refresh list
        } else {
            showToast('Failed to delete template', 'error');
        }
    } catch (error) {
        console.error('Error deleting template:', error);
        showToast('Error deleting template', 'error');
    }
}

// Modal close buttons
document.getElementById('cancelTemplateBtn').addEventListener('click', closeModals);
document.getElementById('closeTemplatesBtn').addEventListener('click', closeModals);

// Export functions
window.generateContent = generateContent;
window.loadTemplate = loadTemplate;
window.deleteTemplate = deleteTemplate;
