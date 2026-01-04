/* ============================================
   TRUSTMEBRO - Client-Side Utilities
   ============================================ */

// ============================================
// Flash Messages
// ============================================
function showFlash(message, type = 'info') {
    const container = document.querySelector('.flash-container');
    if (!container) return;
    
    const flash = document.createElement('div');
    flash.className = `flash-message ${type}`;
    flash.textContent = message;
    
    container.appendChild(flash);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        flash.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => flash.remove(), 300);
    }, 5000);
}

// Auto-hide existing flash messages
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.flash-message').forEach(flash => {
        setTimeout(() => {
            flash.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => flash.remove(), 300);
        }, 5000);
    });
});

// ============================================
// Modal Utilities
// ============================================
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('visible');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('visible');
        document.body.style.overflow = '';
    }
}

// Close modal on overlay click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('visible');
        document.body.style.overflow = '';
    }
});

// Close modal on escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.visible').forEach(modal => {
            modal.classList.remove('visible');
        });
        document.body.style.overflow = '';
    }
});

// ============================================
// Copy to Clipboard
// ============================================
async function copyToClipboard(text, successMessage = 'Copied!') {
    try {
        await navigator.clipboard.writeText(text);
        showFlash(successMessage, 'success');
        return true;
    } catch (err) {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        
        try {
            document.execCommand('copy');
            showFlash(successMessage, 'success');
            return true;
        } catch (err) {
            showFlash('Failed to copy', 'error');
            return false;
        } finally {
            document.body.removeChild(textarea);
        }
    }
}

function copyShareLink() {
    const input = document.getElementById('share-link-input');
    if (input) {
        copyToClipboard(input.value, 'Share link copied!');
    }
}

function copyCurrentLink() {
    copyToClipboard(window.location.href, 'Link copied!');
}

function copyCitation() {
    const citation = document.getElementById('citation-text');
    if (citation) {
        copyToClipboard(citation.textContent, 'Citation copied!');
    }
}

// ============================================
// Character Counter
// ============================================
function updateCharCount(textarea, counterId, maxLength = 500) {
    const counter = document.getElementById(counterId);
    if (!textarea || !counter) return;
    
    const length = textarea.value.length;
    const remaining = maxLength - length;
    
    counter.textContent = `${length}/${maxLength}`;
    counter.classList.remove('warning', 'error');
    
    if (remaining < 50) {
        counter.classList.add('warning');
    }
    if (remaining < 0) {
        counter.classList.add('error');
    }
}

// ============================================
// Form Submission
// ============================================
function setButtonLoading(button, loading = true) {
    if (!button) return;
    
    if (loading) {
        button.classList.add('btn-loading');
        button.disabled = true;
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = '<span class="btn-text">' + button.innerHTML + '</span>';
    } else {
        button.classList.remove('btn-loading');
        button.disabled = false;
        if (button.dataset.originalText) {
            button.innerHTML = button.dataset.originalText;
        }
    }
}

// ============================================
// Groq Key Management
// ============================================
const GROQ_KEY_STORAGE = 'trustmebro_groq_key';

function getStoredGroqKey() {
    return localStorage.getItem(GROQ_KEY_STORAGE) || '';
}

function setStoredGroqKey(key) {
    if (key) {
        localStorage.setItem(GROQ_KEY_STORAGE, key);
    } else {
        localStorage.removeItem(GROQ_KEY_STORAGE);
    }
}

function updateGroqStatus() {
    const status = document.getElementById('groq-status');
    const icon = document.getElementById('groq-status-icon');
    const text = document.getElementById('groq-status-text');
    const btn = document.getElementById('groq-status-btn');
    
    if (!status) return;
    
    const key = getStoredGroqKey();
    
    if (key) {
        status.classList.add('active');
        icon.textContent = '✓';
        text.innerHTML = '<strong>Groq API active</strong> - Enhanced generation enabled';
        btn.textContent = 'Change Key';
    } else {
        status.classList.remove('active');
        icon.textContent = '🔑';
        text.innerHTML = '<strong>Optional:</strong> Add Groq API key for enhanced generation';
        btn.textContent = 'Add Key';
    }
}

function openGroqModal() {
    const input = document.getElementById('groq-key-input');
    if (input) {
        input.value = getStoredGroqKey();
    }
    openModal('groq-modal');
}

function saveGroqKey() {
    const input = document.getElementById('groq-key-input');
    if (!input) return;
    
    const key = input.value.trim();
    setStoredGroqKey(key);
    
    // Also save to session via API
    fetch('/save_groq_key', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ key: key })
    }).then(response => {
        if (response.ok) {
            updateGroqStatus();
            closeModal('groq-modal');
            showFlash(key ? 'Groq API key saved!' : 'Groq API key removed', 'success');
        }
    }).catch(err => {
        showFlash('Failed to save key', 'error');
    });
}

function clearGroqKey() {
    setStoredGroqKey('');
    saveGroqKey();
}

// Initialize Groq status on page load
document.addEventListener('DOMContentLoaded', () => {
    updateGroqStatus();
    
    // Sync stored key to session on page load
    const key = getStoredGroqKey();
    if (key) {
        fetch('/save_groq_key', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: key })
        });
    }
});

// ============================================
// Share Link Creation
// ============================================
async function createShareLink(paperId) {
    const btn = document.getElementById('share-btn');
    setButtonLoading(btn, true);
    
    try {
        const response = await fetch(`/create_share/${paperId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.success) {
            const result = document.getElementById('share-result');
            const input = document.getElementById('share-link-input');
            const expiry = document.getElementById('share-expiry');
            
            if (result && input) {
                input.value = data.share_url;
                if (expiry) {
                    expiry.textContent = `Expires: ${new Date(data.expires_at).toLocaleString()}`;
                }
                result.classList.add('visible');
            }
            
            showFlash('Share link created!', 'success');
        } else {
            showFlash(data.error || 'Failed to create share link', 'error');
        }
    } catch (err) {
        showFlash('Failed to create share link', 'error');
    } finally {
        setButtonLoading(btn, false);
    }
}

// ============================================
// Gallery Voting
// ============================================
async function vote(postId, value) {
    // Check if logged in
    if (!document.body.dataset.loggedIn) {
        showFlash('Please log in to vote', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`/vote/${postId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ value: value })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update vote count display
            const countEl = document.getElementById('vote-count');
            if (countEl) {
                countEl.textContent = data.new_count;
            }
            
            // Update button states
            const upBtn = document.querySelector('.vote-btn.up');
            const downBtn = document.querySelector('.vote-btn.down');
            
            upBtn?.classList.remove('active');
            downBtn?.classList.remove('active');
            
            if (data.user_vote === 1) {
                upBtn?.classList.add('active');
            } else if (data.user_vote === -1) {
                downBtn?.classList.add('active');
            }
        } else {
            showFlash(data.error || 'Failed to vote', 'error');
        }
    } catch (err) {
        showFlash('Failed to vote', 'error');
    }
}

// ============================================
// Report Submission
// ============================================
function openReportModal() {
    openModal('report-modal');
}

async function submitReport(postId) {
    const reason = document.querySelector('input[name="report-reason"]:checked');
    const notes = document.getElementById('report-notes');
    
    if (!reason) {
        showFlash('Please select a reason', 'warning');
        return;
    }
    
    const btn = document.getElementById('report-submit-btn');
    setButtonLoading(btn, true);
    
    try {
        const response = await fetch(`/report/${postId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                reason: reason.value,
                notes: notes?.value || ''
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            closeModal('report-modal');
            showFlash('Report submitted. Thank you!', 'success');
        } else {
            showFlash(data.error || 'Failed to submit report', 'error');
        }
    } catch (err) {
        showFlash('Failed to submit report', 'error');
    } finally {
        setButtonLoading(btn, false);
    }
}

// ============================================
// Gallery Filters
// ============================================
function applyFilter() {
    const voice = document.getElementById('filter-voice');
    const template = document.getElementById('filter-template');
    
    const params = new URLSearchParams(window.location.search);
    
    if (voice && voice.value) {
        params.set('voice', voice.value);
    } else {
        params.delete('voice');
    }
    
    if (template && template.value) {
        params.set('template', template.value);
    } else {
        params.delete('template');
    }
    
    // Preserve tab
    const currentTab = params.get('tab');
    if (currentTab) {
        params.set('tab', currentTab);
    }
    
    window.location.search = params.toString();
}

// ============================================
// Auth Tabs
// ============================================
function showAuthTab(tab) {
    // Update tab buttons
    document.querySelectorAll('.auth-tab').forEach(t => {
        t.classList.remove('active');
    });
    document.querySelector(`.auth-tab[data-tab="${tab}"]`)?.classList.add('active');
    
    // Update forms
    document.querySelectorAll('.auth-form').forEach(f => {
        f.classList.remove('active');
    });
    document.getElementById(`${tab}-form`)?.classList.add('active');
}

// ============================================
// Admin Tabs
// ============================================
function showAdminTab(tab) {
    // Update tab buttons
    document.querySelectorAll('.admin-tab').forEach(t => {
        t.classList.remove('active');
    });
    document.querySelector(`.admin-tab[data-tab="${tab}"]`)?.classList.add('active');
    
    // Update panels
    document.querySelectorAll('.admin-panel').forEach(p => {
        p.classList.remove('active');
    });
    document.getElementById(`${tab}-panel`)?.classList.add('active');
}

// ============================================
// Admin Actions
// ============================================
async function adminAction(action, targetType, targetId, extra = {}) {
    if (!confirm(`Are you sure you want to ${action} this ${targetType}?`)) {
        return;
    }
    
    try {
        const response = await fetch('/admin/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: action,
                target_type: targetType,
                target_id: targetId,
                ...extra
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showFlash(`Action completed: ${action}`, 'success');
            // Reload to show changes
            setTimeout(() => window.location.reload(), 500);
        } else {
            showFlash(data.error || 'Action failed', 'error');
        }
    } catch (err) {
        showFlash('Action failed', 'error');
    }
}

async function addKeyword() {
    const input = document.getElementById('new-keyword');
    if (!input || !input.value.trim()) {
        showFlash('Please enter a keyword', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/admin/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: 'add_keyword',
                keyword: input.value.trim()
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            input.value = '';
            showFlash('Keyword added', 'success');
            setTimeout(() => window.location.reload(), 500);
        } else {
            showFlash(data.error || 'Failed to add keyword', 'error');
        }
    } catch (err) {
        showFlash('Failed to add keyword', 'error');
    }
}

async function removeKeyword(keywordId) {
    if (!confirm('Remove this keyword?')) return;
    
    try {
        const response = await fetch('/admin/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: 'remove_keyword',
                keyword_id: keywordId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showFlash('Keyword removed', 'success');
            setTimeout(() => window.location.reload(), 500);
        } else {
            showFlash(data.error || 'Failed to remove keyword', 'error');
        }
    } catch (err) {
        showFlash('Failed to remove keyword', 'error');
    }
}

// ============================================
// Publish Modal
// ============================================
function openPublishModal() {
    openModal('publish-modal');
}

async function publishPaper(paperId) {
    const checkbox = document.getElementById('policy-agree');
    
    if (!checkbox || !checkbox.checked) {
        showFlash('Please agree to the policies', 'warning');
        return;
    }
    
    const btn = document.getElementById('publish-submit-btn');
    setButtonLoading(btn, true);
    
    try {
        const response = await fetch(`/publish/${paperId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.success) {
            closeModal('publish-modal');
            showFlash('Published to gallery!', 'success');
            
            // Redirect to gallery post
            if (data.post_url) {
                setTimeout(() => {
                    window.location.href = data.post_url;
                }, 1000);
            }
        } else {
            showFlash(data.error || 'Failed to publish', 'error');
        }
    } catch (err) {
        showFlash('Failed to publish', 'error');
    } finally {
        setButtonLoading(btn, false);
    }
}

// ============================================
// Length Hint Toggle
// ============================================
function updateLengthHint() {
    const selected = document.querySelector('input[name="length"]:checked');
    if (!selected) return;
    
    const hints = {
        'abstract': 'Quick read - abstract only (no Groq key needed)',
        'short': 'Standard paper with key sections (Groq key recommended)',
        'full': 'Comprehensive academic paper (Groq key required)'
    };
    
    const hintEl = document.getElementById('length-hint');
    if (hintEl) {
        hintEl.textContent = hints[selected.value] || '';
    }
}

// ============================================
// Range Slider Value Display
// ============================================
function updateSliderValue(slider) {
    const display = document.getElementById(`${slider.id}-value`);
    if (display) {
        display.textContent = slider.value;
    }
}

// ============================================
// Form Submit with Loading
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    // Add loading state to generate form
    const generateForm = document.getElementById('generate-form');
    if (generateForm) {
        generateForm.addEventListener('submit', (e) => {
            const btn = generateForm.querySelector('button[type="submit"]');
            setButtonLoading(btn, true);
        });
    }
});

// ============================================
// Toggle Switch Handler
// ============================================
function initToggleSwitches() {
    document.querySelectorAll('.toggle-switch input').forEach(input => {
        input.addEventListener('change', (e) => {
            // The CSS handles visual state via :checked
            // This is for any additional JS logic if needed
        });
    });
}

document.addEventListener('DOMContentLoaded', initToggleSwitches);
