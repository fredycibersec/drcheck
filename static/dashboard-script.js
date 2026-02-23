// Dashboard Script - Multi-type Search Support

// ===== UTILITY FUNCTIONS =====

// Toast Notification System
function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };
    
    toast.innerHTML = `
        <div class="toast-icon">${icons[type] || icons.info}</div>
        <div class="toast-message">${message}</div>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
        </button>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, duration);
}

// Connection Status Monitor
let isOnline = navigator.onLine;
const connectionStatus = document.getElementById('connectionStatus');

window.addEventListener('online', () => {
    isOnline = true;
    if (connectionStatus) connectionStatus.style.display = 'none';
    showToast('Conexión restaurada', 'success');
});

window.addEventListener('offline', () => {
    isOnline = false;
    if (connectionStatus) connectionStatus.style.display = 'flex';
    showToast('Sin conexión a internet', 'error');
});

// Copy to Clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (err) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            document.body.removeChild(textArea);
            return true;
        } catch (err) {
            document.body.removeChild(textArea);
            return false;
        }
    }
}

// Input Validation
function validateDomain(domain) {
    const pattern = /^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$/;
    return pattern.test(domain.toLowerCase());
}

function validateIP(ip) {
    const pattern = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (!pattern.test(ip)) return false;
    const parts = ip.split('.');
    return parts.every(part => parseInt(part) >= 0 && parseInt(part) <= 255);
}

function validateHash(hash) {
    const pattern = /^[a-f0-9]{32}$|^[a-f0-9]{40}$|^[a-f0-9]{64}$/;
    return pattern.test(hash.toLowerCase());
}

// Theme Toggle
const themeToggle = document.getElementById('themeToggle');
const sunIcon = document.getElementById('sunIcon');
const moonIcon = document.getElementById('moonIcon');
const body = document.body;

const savedTheme = localStorage.getItem('theme') || 'dark';
body.setAttribute('data-theme', savedTheme);
updateThemeIcons(savedTheme);

function updateThemeIcons(theme) {
    sunIcon.style.display = theme === 'dark' ? 'block' : 'none';
    moonIcon.style.display = theme === 'dark' ? 'none' : 'block';
}

themeToggle.addEventListener('click', () => {
    const currentTheme = body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcons(newTheme);
    
    // Update charts if they exist
    if (reputationChart) updateChartTheme(reputationChart);
    if (searchTypesChart) updateChartTheme(searchTypesChart);
});

// Sidebar Toggle
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar = document.getElementById('sidebar');
const mainContent = document.getElementById('mainContent');

sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
    sidebar.classList.toggle('mobile-open');
    mainContent.classList.toggle('expanded');
});

// Current search type
let currentSearchType = 'domain';

// About Modal Management
const aboutBtn = document.getElementById('aboutBtn');
const aboutModal = document.getElementById('aboutModal');
const closeAboutModal = document.getElementById('closeAboutModal');
const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

// Open modal
if (aboutBtn) {
    aboutBtn.addEventListener('click', () => {
        aboutModal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    });
}

// Close modal
if (closeAboutModal) {
    closeAboutModal.addEventListener('click', () => {
        aboutModal.style.display = 'none';
        document.body.style.overflow = 'auto';
    });
}

// Close modal when clicking outside
if (aboutModal) {
    aboutModal.addEventListener('click', (e) => {
        if (e.target === aboutModal) {
            aboutModal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    });
}

// Close modal with Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && aboutModal.style.display === 'flex') {
        aboutModal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
});

// Tab switching
tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.getAttribute('data-tab');
        
        // Remove active class from all buttons and contents
        tabBtns.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));
        
        // Add active class to clicked button and corresponding content
        btn.classList.add('active');
        const targetContent = document.getElementById(`tab${tabName.charAt(0).toUpperCase() + tabName.slice(1)}`);
        if (targetContent) {
            targetContent.classList.add('active');
        }
    });
});

// View Navigation
const sidebarItems = document.querySelectorAll('.sidebar-item:not(.disabled)');
const views = {
    'domain': document.getElementById('domainView'),
    'ip': document.getElementById('ipView'),
    'hash': document.getElementById('hashView'),
    'stats': document.getElementById('statsView'),
    'history': document.getElementById('historyView'),
    'config': document.getElementById('configView')
};

sidebarItems.forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const viewName = item.getAttribute('data-view');
        
        if (!viewName) return;
        
        currentSearchType = viewName;
        
        // Update active state
        sidebarItems.forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        
        // Show selected view
        Object.keys(views).forEach(key => {
            views[key].style.display = key === viewName ? 'block' : 'none';
        });
        
        // Load data for specific views
        if (viewName === 'stats') {
            setTimeout(() => loadStatistics(), 100);
        } else if (viewName === 'history') {
            setTimeout(() => loadHistory(), 100);
        } else if (viewName === 'config') {
            setTimeout(() => loadAPIConfig(), 100);
        }
    });
});

// Common elements
const forms = {
    domain: document.getElementById('searchForm'),
    ip: document.getElementById('ipSearchForm'),
    hash: document.getElementById('hashSearchForm')
};

const loadings = {
    domain: document.getElementById('loading'),
    ip: document.getElementById('ipLoading'),
    hash: document.getElementById('hashLoading')
};

const errorMessages = {
    domain: document.getElementById('errorMessage'),
    ip: document.getElementById('ipErrorMessage'),
    hash: document.getElementById('hashErrorMessage')
};

const resultsContainers = {
    domain: document.getElementById('resultsContainer'),
    ip: document.getElementById('ipResultsContainer'),
    hash: document.getElementById('hashResultsContainer')
};

// Domain search handlers
let currentAnalysisData = null;
const resetBtn = document.getElementById('resetBtn');
const exportPdfBtn = document.getElementById('exportPdfBtn');
const exportActions = document.getElementById('exportActions');

if (resetBtn) {
    resetBtn.addEventListener('click', () => {
        document.getElementById('domainInput').value = '';
        resultsContainers.domain.style.display = 'none';
        errorMessages.domain.style.display = 'none';
        resetBtn.style.display = 'none';
        exportActions.style.display = 'none';
        currentAnalysisData = null;
    });
}

// Export handlers
async function exportData(endpoint, filename, format) {
    if (!currentAnalysisData) {
        showToast('No hay datos disponibles para exportar', 'error');
        return;
    }
    
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(currentAnalysisData)
        });
        
        if (!response.ok) throw new Error(`Error al generar ${format}`);
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showToast(`${format} exportado exitosamente`, 'success');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

if (exportPdfBtn) {
    exportPdfBtn.addEventListener('click', async () => {
        const domain = currentAnalysisData?.domain || 'report';
        const date = new Date().toISOString().split('T')[0];
        await exportData('/api/export-pdf', `reputation-${domain}-${date}.pdf`, 'PDF');
    });
}

const exportJsonBtn = document.getElementById('exportJsonBtn');
if (exportJsonBtn) {
    exportJsonBtn.addEventListener('click', async () => {
        const domain = currentAnalysisData?.domain || 'report';
        const date = new Date().toISOString().split('T')[0];
        await exportData('/api/export-json', `reputation-${domain}-${date}.json`, 'JSON');
    });
}

const exportCsvBtn = document.getElementById('exportCsvBtn');
if (exportCsvBtn) {
    exportCsvBtn.addEventListener('click', async () => {
        const domain = currentAnalysisData?.domain || 'report';
        const date = new Date().toISOString().split('T')[0];
        await exportData('/api/export-csv', `reputation-${domain}-${date}.csv`, 'CSV');
    });
}

// Copy Results
const copyResultsBtn = document.getElementById('copyResultsBtn');
if (copyResultsBtn) {
    copyResultsBtn.addEventListener('click', async () => {
        if (!currentAnalysisData) {
            showToast('No hay datos disponibles para copiar', 'error');
            return;
        }
        
        let summary = `Dominio: ${currentAnalysisData.domain}\n`;
        summary += `Reputación: ${currentAnalysisData.overall_reputation.toUpperCase()}\n\n`;
        summary += `Fuentes analizadas:\n`;
        
        currentAnalysisData.results.forEach(result => {
            summary += `\n${result.source}\n`;
            summary += `  Estado: ${result.status}\n`;
            if (result.reputation) {
                summary += `  Reputación: ${result.reputation}\n`;
            }
        });
        
        const success = await copyToClipboard(summary);
        
        if (success) {
            copyResultsBtn.classList.add('copied');
            copyResultsBtn.innerHTML = '<svg class="btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg> Copiado';
            showToast('Resumen copiado al portapapeles', 'success');
            
            setTimeout(() => {
                copyResultsBtn.classList.remove('copied');
                copyResultsBtn.innerHTML = '<svg class="btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg> Copiar';
            }, 2000);
        } else {
            showToast('Error al copiar al portapapeles', 'error');
        }
    });
}

// Real-time validation
const domainInput = document.getElementById('domainInput');
if (domainInput) {
    domainInput.addEventListener('input', (e) => {
        const value = e.target.value.trim();
        if (!value) {
            domainInput.classList.remove('valid', 'invalid');
            return;
        }
        
        const isValid = validateDomain(value) || validateHash(value);
        domainInput.classList.toggle('valid', isValid);
        domainInput.classList.toggle('invalid', !isValid);
    });
}

const ipInput = document.getElementById('ipInput');
if (ipInput) {
    ipInput.addEventListener('input', (e) => {
        const value = e.target.value.trim();
        if (!value) {
            ipInput.classList.remove('valid', 'invalid');
            return;
        }
        
        const isValid = validateIP(value);
        ipInput.classList.toggle('valid', isValid);
        ipInput.classList.toggle('invalid', !isValid);
    });
}

const hashInput = document.getElementById('hashInput');
if (hashInput) {
    hashInput.addEventListener('input', (e) => {
        const value = e.target.value.trim();
        if (!value) {
            hashInput.classList.remove('valid', 'invalid');
            return;
        }
        
        const isValid = validateHash(value);
        hashInput.classList.toggle('valid', isValid);
        hashInput.classList.toggle('invalid', !isValid);
    });
}

// Domain search form
if (forms.domain) {
    forms.domain.addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = document.getElementById('domainInput').value.trim();
        if (!input) {
            showToast('Ingresa un dominio o hash', 'warning');
            return;
        }
        
        await performSearch('domain', input);
    });
}

// IP search form
if (forms.ip) {
    forms.ip.addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = document.getElementById('ipInput').value.trim();
        if (!input) return showError('ip', 'Ingresa una dirección IP');
        
        await performSearch('ip', input);
    });
}

// Hash search form  
if (forms.hash) {
    forms.hash.addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = document.getElementById('hashInput').value.trim();
        if (!input) return showError('hash', 'Ingresa un hash (MD5, SHA1 o SHA256)');
        
        await performSearch('hash', input);
    });
}

async function performSearch(type, value) {
    const loading = loadings[type];
    const results = resultsContainers[type];
    const error = errorMessages[type];
    const checkBtn = document.getElementById(`${type}CheckBtn`) || document.getElementById('checkBtn');
    
    if (loading) loading.style.display = 'block';
    if (results) results.style.display = 'none';
    if (error) error.style.display = 'none';
    if (checkBtn) checkBtn.disabled = true;
    
    try {
        let endpoint, body;
        
        if (type === 'ip') {
            endpoint = '/api/check-ip';
            body = { ip: value };
        } else {
            endpoint = '/api/check';
            body = { domain: value };
        }
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Error en el análisis');
        
        displayResults(type, data);
        
        if (type === 'domain') {
            currentAnalysisData = data;
            if (resetBtn) resetBtn.style.display = 'inline-flex';
        }
    } catch (err) {
        showError(type, err.message);
    } finally {
        if (loading) loading.style.display = 'none';
        if (checkBtn) checkBtn.disabled = false;
    }
}

function showError(type, message) {
    const error = errorMessages[type];
    if (error) {
        error.textContent = `❌ ${message}`;
        error.style.display = 'block';
    }
    showToast(message, 'error');
}

function displayResults(type, data) {
    const container = resultsContainers[type];
    if (!container) return;
    
    container.style.display = 'block';
    
    if (type === 'ip') {
        displayIPResults(data);
    } else {
        displayDomainResults(data);
    }
}

function displayIPResults(data) {
    const overallRep = document.getElementById('ipOverallReputation');
    const resultsGrid = document.getElementById('ipResultsGrid');
    
    if (overallRep) {
        overallRep.innerHTML = `
            <h3>IP: <span style="color: var(--text-primary);">${data.ip || data.target}</span></h3>
            <div class="reputation-badge reputation-${data.reputation || 'unknown'}">
                ${getReputationEmoji(data.reputation)} ${(data.reputation || 'UNKNOWN').toUpperCase()}
            </div>
        `;
    }
    
    if (resultsGrid && data.results) {
        resultsGrid.innerHTML = '';
        Object.entries(data.results).forEach(([key, value]) => {
            const card = createInfoCard(key, value);
            resultsGrid.appendChild(card);
        });
    }
}

function displayDomainResults(data) {
    const overallRep = document.getElementById('overallReputation');
    const resultsGrid = document.getElementById('resultsGrid');
    const exportActions = document.getElementById('exportActions');
    
    if (overallRep) {
        const reputation = data.overall_reputation;
        overallRep.innerHTML = `
            <h3>Dominio: <span style="color: var(--text-primary);">${data.domain}</span></h3>
            <div class="reputation-badge reputation-${reputation}">
                ${getReputationEmoji(reputation)} ${reputation.toUpperCase()}
            </div>
        `;
    }
    
    if (exportActions) exportActions.style.display = 'flex';
    
    if (resultsGrid) {
        const automated = [];
        const manual = [];
        
        data.results.forEach(r => r.status === 'info' ? manual.push(r) : automated.push(r));
        
        resultsGrid.innerHTML = '';
        automated.forEach(result => resultsGrid.appendChild(createSourceCard(result)));
        
        const manualDiv = document.getElementById('manualInvestigation');
        const manualGrid = document.getElementById('manualToolsGrid');
        
        if (manual.length > 0 && manualDiv && manualGrid) {
            manualDiv.style.display = 'block';
            manualGrid.innerHTML = '';
            manual.forEach(result => manualGrid.appendChild(createSourceCard(result)));
        } else if (manualDiv) {
            manualDiv.style.display = 'none';
        }
    }
}

function getReputationEmoji(rep) {
    const emojis = {
        'clean': '✅', 'malicious': '🚨', 'suspicious': '⚠️',
        'questionable': '🔍', 'unknown': '❓'
    };
    return emojis[rep] || '❓';
}

function createInfoCard(title, data) {
    const card = document.createElement('div');
    card.className = 'source-card';
    card.style.cssText = 'background: var(--bg-card); border-radius: var(--radius-xl); padding: var(--space-6); border: 1px solid var(--border-primary);';
    
    let content = `<h4 style="margin-bottom: var(--space-4); color: var(--text-primary);">${title.replace(/_/g, ' ').toUpperCase()}</h4>`;
    
    if (typeof data === 'object' && data !== null) {
        content += '<ul style="list-style: none; padding: 0;">';
        for (const [key, value] of Object.entries(data)) {
            if (value === null || value === undefined) continue;
            const displayValue = Array.isArray(value) ? value.join(', ') : value.toString();
            content += `<li style="padding: var(--space-2) 0; border-bottom: 1px solid var(--border-primary); display: flex; justify-content: space-between;"><span style="color: var(--text-secondary);">${key}:</span><span style="color: var(--text-primary); font-weight: 600;">${displayValue}</span></li>`;
        }
        content += '</ul>';
    } else {
        content += `<p style="color: var(--text-secondary);">${data}</p>`;
    }
    
    card.innerHTML = content;
    return card;
}

function createSourceCard(result) {
    const card = document.createElement('div');
    card.className = 'source-card';
    card.style.cssText = 'background: var(--bg-card); border-radius: var(--radius-xl); padding: var(--space-6); border: 1px solid var(--border-primary);';
    
    const statusClass = result.status === 'success' ? 'status-success' : 
                       result.status === 'error' ? 'status-error' : 'status-info';
    
    let reputationHTML = '';
    if (result.status === 'success') {
        reputationHTML = `<div class="reputation-indicator reputation-${result.reputation}" style="padding: var(--space-3); border-radius: var(--radius-md); margin: var(--space-3) 0; font-weight: 600; text-align: center;">${getReputationEmoji(result.reputation)} ${result.reputation.toUpperCase()}</div>`;
    }
    
    let detailsHTML = '';
    if (result.status === 'success' && result.details && Object.keys(result.details).length > 0) {
        detailsHTML = '<ul style="list-style: none; padding: 0; margin-top: var(--space-4);">';
        for (const [key, value] of Object.entries(result.details)) {
            if (value === null || value === undefined || value === '') continue;
            const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            const displayValue = Array.isArray(value) ? value.join(', ') : value.toString();
            detailsHTML += `<li style="padding: var(--space-2) 0; border-bottom: 1px solid var(--border-primary); display: flex; justify-content: space-between;"><span style="color: var(--text-secondary);">${label}:</span><span style="color: var(--text-primary); font-weight: 600; text-align: right;">${displayValue}</span></li>`;
        }
        detailsHTML += '</ul>';
    }
    
    const messageHTML = result.message ? `<p style="color: var(--text-secondary); margin-top: var(--space-2);">${result.message}</p>` : '';
    const linkHTML = result.url ? `<a href="${result.url}" target="_blank" style="display: inline-block; margin-top: var(--space-4); padding: var(--space-2) var(--space-4); background: transparent; color: var(--text-primary); text-decoration: none; border: 1px solid var(--border-primary); border-radius: var(--radius-md);">🔗 Ver Fuente</a>` : '';
    
    card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-4); padding-bottom: var(--space-3); border-bottom: 2px solid var(--border-primary);">
            <div style="font-size: 1.125rem; font-weight: 600;">${result.source}</div>
            <span class="${statusClass}" style="padding: 2px 8px; border-radius: var(--radius-full); font-size: 0.75rem; font-weight: 600;">${result.status}</span>
        </div>
        ${reputationHTML}
        ${messageHTML}
        ${detailsHTML}
        ${linkHTML}
    `;
    
    return card;
}

// Statistics functionality
let reputationChart, searchTypesChart;

// Update chart theme colors
function updateChartTheme(chart) {
    const textColor = getComputedStyle(document.body).getPropertyValue('--text-primary').trim();
    const secondaryColor = getComputedStyle(document.body).getPropertyValue('--text-secondary').trim();
    
    if (chart.options.plugins?.legend?.labels) {
        chart.options.plugins.legend.labels.color = textColor;
    }
    
    if (chart.options.scales?.y?.ticks) {
        chart.options.scales.y.ticks.color = secondaryColor;
    }
    
    if (chart.options.scales?.x?.ticks) {
        chart.options.scales.x.ticks.color = secondaryColor;
    }
    
    chart.update();
}

async function loadStatistics() {
    try {
        console.log('[Stats] Loading statistics...');
        const response = await fetch('/api/statistics');
        const data = await response.json();
        console.log('[Stats] Data received:', data);
        
        // Update summary cards
        document.getElementById('totalSearches').textContent = data.summary.total || 0;
        document.getElementById('maliciousCount').textContent = data.reputation_distribution.malicious || 0;
        document.getElementById('suspiciousCount').textContent = data.reputation_distribution.suspicious || 0;
        document.getElementById('cleanCount').textContent = data.reputation_distribution.clean || 0;
        console.log('[Stats] Summary cards updated');
        
        // Render charts
        console.log('[Stats] Rendering charts...');
        renderReputationChart(data.reputation_distribution);
        renderSearchTypesChart(data.summary);
        renderThreatMap(data.threat_map);
        renderRecentSearches(data.recent_searches);
        console.log('[Stats] All charts rendered');
        
    } catch (error) {
        console.error('[Stats] Error loading statistics:', error);
    }
}

function renderReputationChart(distribution) {
    const ctx = document.getElementById('reputationChart');
    console.log('[Chart] Reputation chart canvas:', ctx);
    if (!ctx) {
        console.error('[Chart] Reputation chart canvas not found!');
        return;
    }
    
    if (reputationChart) {
        console.log('[Chart] Destroying existing reputation chart');
        reputationChart.destroy();
    }
    
    console.log('[Chart] Creating reputation chart with data:', distribution);
    reputationChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Maliciosos', 'Sospechosos', 'Limpios'],
            datasets: [{
                data: [
                    distribution.malicious || 0,
                    distribution.suspicious || 0,
                    distribution.clean || 0
                ],
                backgroundColor: ['#ef4444', '#f59e0b', '#10b981'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: getComputedStyle(document.body).getPropertyValue('--text-primary') }
                }
            }
        }
    });
}

function renderSearchTypesChart(summary) {
    const ctx = document.getElementById('searchTypesChart');
    console.log('[Chart] Search types chart canvas:', ctx);
    if (!ctx) {
        console.error('[Chart] Search types chart canvas not found!');
        return;
    }
    
    if (searchTypesChart) {
        console.log('[Chart] Destroying existing search types chart');
        searchTypesChart.destroy();
    }
    
    console.log('[Chart] Creating search types chart with data:', summary);
    searchTypesChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Dominios', 'IPs', 'Hashes'],
            datasets: [{
                label: 'Búsquedas',
                data: [
                    summary.domains || 0,
                    summary.ips || 0,
                    summary.hashes || 0
                ],
                backgroundColor: ['#3b82f6', '#10b981', '#f59e0b'],
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: getComputedStyle(document.body).getPropertyValue('--text-secondary') }
                },
                x: {
                    ticks: { color: getComputedStyle(document.body).getPropertyValue('--text-secondary') }
                }
            }
        }
    });
}

function renderThreatMap(threats) {
    const container = document.getElementById('threatMapContent');
    if (!container) return;
    
    if (!threats || threats.length === 0) {
        // Show empty state with informative message
        container.innerHTML = `
            <div style="text-align: center; padding: var(--space-8);">
                <div style="font-size: 3rem; margin-bottom: var(--space-4); opacity: 0.3;">🌍</div>
                <h4 style="color: var(--text-primary); margin-bottom: var(--space-2);">Mapa de Amenazas</h4>
                <p style="color: var(--text-secondary); margin-bottom: var(--space-4);">
                    Aún no hay datos de países registrados.<br>
                    Las búsquedas de dominios e IPs mostrarán estadísticas geográficas de amenazas por país aquí.
                </p>
                <div style="background: var(--bg-tertiary); border-radius: var(--radius-lg); padding: var(--space-4); margin-top: var(--space-6); text-align: left;">
                    <p style="font-size: 0.875rem; color: var(--text-secondary); margin: 0;">
                        <strong style="color: var(--text-primary);">💡 Tip:</strong> Realiza búsquedas de dominios o direcciones IP para comenzar a ver estadísticas geográficas de amenazas.
                    </p>
                </div>
            </div>
        `;
        return;
    }
    
    const maxCount = Math.max(...threats.map(t => t[1]));
    
    // Mapeo de códigos de país ISO a nombres completos
    const countryNames = {
        'US': 'United States', 'CN': 'China', 'RU': 'Russia', 'DE': 'Germany', 'GB': 'United Kingdom',
        'FR': 'France', 'JP': 'Japan', 'IN': 'India', 'BR': 'Brazil', 'CA': 'Canada',
        'AU': 'Australia', 'MX': 'Mexico', 'IT': 'Italy', 'ES': 'Spain', 'KR': 'South Korea',
        'NL': 'Netherlands', 'SE': 'Sweden', 'PL': 'Poland', 'TR': 'Turkey', 'AR': 'Argentina',
        'SA': 'Saudi Arabia', 'ZA': 'South Africa', 'EG': 'Egypt', 'SG': 'Singapore',
        'VG': 'British Virgin Islands', 'NZ': 'New Zealand', 'CH': 'Switzerland', 'NO': 'Norway',
        'DK': 'Denmark', 'FI': 'Finland', 'BE': 'Belgium', 'AT': 'Austria', 'PT': 'Portugal'
    };
    
    const countryMapping = {
        'US': 'US', 'CN': 'CN', 'RU': 'RU', 'DE': 'DE', 'GB': 'GB',
        'FR': 'FR', 'JP': 'JP', 'IN': 'IN', 'BR': 'BR', 'CA': 'CA',
        'United States': 'US', 'China': 'CN', 'Russia': 'RU', 'Germany': 'DE', 'United Kingdom': 'GB',
        'France': 'FR', 'Japan': 'JP', 'India': 'IN', 'Brazil': 'BR', 'Canada': 'CA'
    };
    
    // Crear un mapa de intensidad para colorear países
    const threatIntensity = {};
    threats.forEach(([country, count]) => {
        const countryCode = countryMapping[country] || country;
        threatIntensity[countryCode] = count;
    });
    
    // Calcular colores según intensidad
    const getCountryColor = (countryCode) => {
        const count = threatIntensity[countryCode];
        if (!count) return 'var(--bg-tertiary)';
        const intensity = count / maxCount;
        if (intensity > 0.7) return '#ef4444'; // Rojo alto
        if (intensity > 0.4) return '#f59e0b'; // Naranja medio
        if (intensity > 0.2) return '#fbbf24'; // Amarillo bajo
        return '#10b981'; // Verde mínimo
    };
    
    // Usar el archivo SVG existente del mapa mundial
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const bgColor = isDark ? '#1e293b' : '#cbd5e1';
    
    // Crear el contenedor del mapa simplificado
    const worldMapSVG = `
        <div style="background: ${bgColor}; border-radius: var(--radius-lg); padding: var(--space-3); margin-bottom: var(--space-4); position: relative;">
            <!-- Mapa mundial de fondo -->
            <div style="position: relative; max-height: 350px; overflow: hidden;">
                <!-- Imagen de fondo -->
                <img src="static/img/world-map.svg" style="width: 100%; max-height: 350px; object-fit: contain; display: block; opacity: ${isDark ? '0.5' : '0.7'}; filter: ${isDark ? 'brightness(0.8) contrast(1.1)' : 'brightness(1)'};"/>
                
                <!-- SVG Overlay para colorear países según amenazas -->
                <svg viewBox="150 500 1800 900" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;" preserveAspectRatio="xMidYMid meet">
                    <!-- Países con amenazas coloreados -->
                    
                    <!-- América del Norte -->
                    ${threatIntensity['US'] ? `
                    <ellipse cx="450" cy="650" rx="180" ry="120" fill="${getCountryColor('US')}" opacity="0.6">
                        <title>US (United States): ${threatIntensity['US']} amenazas</title>
                    </ellipse>` : ''}
                    
                    ${threatIntensity['CA'] ? `
                    <ellipse cx="450" cy="550" rx="200" ry="80" fill="${getCountryColor('CA')}" opacity="0.6">
                        <title>CA (Canada): ${threatIntensity['CA']} amenazas</title>
                    </ellipse>` : ''}
                    
                    ${threatIntensity['MX'] ? `
                    <ellipse cx="450" cy="780" rx="80" ry="60" fill="${getCountryColor('MX')}" opacity="0.6">
                        <title>MX (Mexico): ${threatIntensity['MX']} amenazas</title>
                    </ellipse>` : ''}
                    
                    <!-- América del Sur -->
                    ${threatIntensity['BR'] ? `
                    <ellipse cx="650" cy="1050" rx="120" ry="140" fill="${getCountryColor('BR')}" opacity="0.6">
                        <title>BR (Brazil): ${threatIntensity['BR']} amenazas</title>
                    </ellipse>` : ''}
                    
                    ${threatIntensity['AR'] ? `
                    <ellipse cx="600" cy="1200" rx="70" ry="100" fill="${getCountryColor('AR')}" opacity="0.6">
                        <title>AR (Argentina): ${threatIntensity['AR']} amenazas</title>
                    </ellipse>` : ''}
                    
                    <!-- Europa -->
                    ${threatIntensity['GB'] ? `
                    <ellipse cx="950" cy="640" rx="40" ry="50" fill="${getCountryColor('GB')}" opacity="0.6">
                        <title>GB (United Kingdom): ${threatIntensity['GB']} amenazas</title>
                    </ellipse>` : ''}
                    
                    ${threatIntensity['FR'] ? `
                    <ellipse cx="980" cy="690" rx="50" ry="55" fill="${getCountryColor('FR')}" opacity="0.6">
                        <title>FR (France): ${threatIntensity['FR']} amenazas</title>
                    </ellipse>` : ''}
                    
                    ${threatIntensity['DE'] ? `
                    <ellipse cx="1030" cy="650" rx="45" ry="50" fill="${getCountryColor('DE')}" opacity="0.6">
                        <title>DE (Germany): ${threatIntensity['DE']} amenazas</title>
                    </ellipse>` : ''}
                    
                    ${threatIntensity['ES'] ? `
                    <ellipse cx="940" cy="730" rx="60" ry="45" fill="${getCountryColor('ES')}" opacity="0.6">
                        <title>ES (Spain): ${threatIntensity['ES']} amenazas</title>
                    </ellipse>` : ''}
                    
                    ${threatIntensity['IT'] ? `
                    <ellipse cx="1040" cy="730" rx="35" ry="70" fill="${getCountryColor('IT')}" opacity="0.6">
                        <title>IT (Italy): ${threatIntensity['IT']} amenazas</title>
                    </ellipse>` : ''}
                    
                    ${threatIntensity['PL'] ? `
                    <ellipse cx="1090" cy="640" rx="50" ry="45" fill="${getCountryColor('PL')}" opacity="0.6">
                        <title>PL (Poland): ${threatIntensity['PL']} amenazas</title>
                    </ellipse>` : ''}
                    
                    ${threatIntensity['RU'] ? `
                    <ellipse cx="1350" cy="610" rx="280" ry="100" fill="${getCountryColor('RU')}" opacity="0.6">
                        <title>RU (Russia): ${threatIntensity['RU']} amenazas</title>
                    </ellipse>` : ''}
                    
                    ${threatIntensity['TR'] ? `
                    <ellipse cx="1120" cy="730" rx="60" ry="35" fill="${getCountryColor('TR')}" opacity="0.6">
                        <title>TR (Turkey): ${threatIntensity['TR']} amenazas</title>
                    </ellipse>` : ''}
                    
                    <!-- Asia -->
                    ${threatIntensity['CN'] ? `
                    <ellipse cx="1450" cy="700" rx="150" ry="120" fill="${getCountryColor('CN')}" opacity="0.6">
                        <title>CN (China): ${threatIntensity['CN']} amenazas</title>
                    </ellipse>` : ''}
                    
                    ${threatIntensity['IN'] ? `
                    <ellipse cx="1320" cy="800" rx="90" ry="110" fill="${getCountryColor('IN')}" opacity="0.6">
                        <title>IN (India): ${threatIntensity['IN']} amenazas</title>
                    </ellipse>` : ''}
                    
                    ${threatIntensity['JP'] ? `
                    <ellipse cx="1680" cy="710" rx="50" ry="90" fill="${getCountryColor('JP')}" opacity="0.6">
                        <title>JP (Japan): ${threatIntensity['JP']} amenazas</title>
                    </ellipse>` : ''}
                    
                    ${threatIntensity['KR'] ? `
                    <ellipse cx="1620" cy="710" rx="35" ry="50" fill="${getCountryColor('KR')}" opacity="0.6">
                        <title>KR (South Korea): ${threatIntensity['KR']} amenazas</title>
                    </ellipse>` : ''}
                    
                    <!-- Medio Oriente -->
                    ${threatIntensity['SA'] ? `
                    <ellipse cx="1180" cy="800" rx="80" ry="70" fill="${getCountryColor('SA')}" opacity="0.6">
                        <title>SA (Saudi Arabia): ${threatIntensity['SA']} amenazas</title>
                    </ellipse>` : ''}
                    
                    <!-- Oceanía -->
                    ${threatIntensity['AU'] ? `
                    <ellipse cx="1650" cy="1150" rx="130" ry="100" fill="${getCountryColor('AU')}" opacity="0.6">
                        <title>AU (Australia): ${threatIntensity['AU']} amenazas</title>
                    </ellipse>` : ''}
                    
                    <!-- África -->
                    ${threatIntensity['ZA'] ? `
                    <ellipse cx="1060" cy="1180" rx="50" ry="70" fill="${getCountryColor('ZA')}" opacity="0.6">
                        <title>ZA (South Africa): ${threatIntensity['ZA']} amenazas</title>
                    </ellipse>` : ''}
                    
                    ${threatIntensity['EG'] ? `
                    <ellipse cx="1100" cy="750" rx="40" ry="50" fill="${getCountryColor('EG')}" opacity="0.6">
                        <title>EG (Egypt): ${threatIntensity['EG']} amenazas</title>
                    </ellipse>` : ''}
                    
                    <!-- Sudeste Asiático -->
                    ${threatIntensity['SG'] ? `
                    <circle cx="1490" cy="920" r="15" fill="${getCountryColor('SG')}" opacity="0.6">
                        <title>SG (Singapore): ${threatIntensity['SG']} amenazas</title>
                    </circle>` : ''}
                    
                    ${threatIntensity['VG'] ? `
                    <circle cx="590" cy="770" r="12" fill="${getCountryColor('VG')}" opacity="0.6">
                        <title>VG (British Virgin Islands): ${threatIntensity['VG']} amenazas</title>
                    </circle>` : ''}
                </svg>
            </div>
        </div>
        <!-- Leyenda de intensidad fuera del contenedor del mapa -->
        <div style="display: flex; align-items: center; gap: var(--space-4); margin-bottom: var(--space-6); padding: var(--space-3); background: var(--bg-tertiary); border-radius: var(--radius-md); flex-wrap: wrap;">
            <span style="color: var(--text-primary); font-weight: 600; font-size: 0.9rem;">Intensidad de Amenazas:</span>
            <div style="display: flex; align-items: center; gap: var(--space-2);">
                <div style="width: 24px; height: 12px; background: #10b981; border-radius: 3px;"></div>
                <span style="color: var(--text-secondary); font-size: 0.85rem;">Baja</span>
            </div>
            <div style="display: flex; align-items: center; gap: var(--space-2);">
                <div style="width: 24px; height: 12px; background: #fbbf24; border-radius: 3px;"></div>
                <span style="color: var(--text-secondary); font-size: 0.85rem;">Media</span>
            </div>
            <div style="display: flex; align-items: center; gap: var(--space-2);">
                <div style="width: 24px; height: 12px; background: #f59e0b; border-radius: 3px;"></div>
                <span style="color: var(--text-secondary); font-size: 0.85rem;">Alta</span>
            </div>
            <div style="display: flex; align-items: center; gap: var(--space-2);">
                <div style="width: 24px; height: 12px; background: #ef4444; border-radius: 3px;"></div>
                <span style="color: var(--text-secondary); font-size: 0.85rem;">Crítica</span>
            </div>
        </div>
    `;
    
    // Crear el HTML con el mapa y las barras
    container.innerHTML = worldMapSVG + `
        <div style="margin-top: var(--space-4);">
            <h4 style="color: var(--text-primary); margin-bottom: var(--space-4); font-size: 0.95rem; font-weight: 600;">📊 Distribución por País</h4>
            ${threats.map(([country, count]) => {
                const countryCode = countryMapping[country] || country;
                const countryFullName = countryNames[countryCode] || country;
                const displayName = countryCode !== country ? country : `${countryCode} (${countryFullName})`;
                return `
                <div class="threat-bar">
                    <div class="threat-country">${displayName}</div>
                    <div class="threat-bar-container">
                        <div class="threat-bar-fill" style="width: ${(count / maxCount) * 100}%"></div>
                    </div>
                    <div class="threat-count">${count} amenaza${count > 1 ? 's' : ''}</div>
                </div>
                `;
            }).join('')}
        </div>
    `;
}

function renderRecentSearches(searches) {
    const container = document.getElementById('recentSearches');
    if (!container) return;
    
    if (!searches || searches.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: var(--space-6);">No hay búsquedas recientes</p>';
        return;
    }
    
    container.innerHTML = searches.map(search => {
        const date = new Date(search.timestamp);
        const reputationEmoji = getReputationEmoji(search.reputation);
        const typeEmoji = search.type === 'domain' ? '🌐' : search.type === 'ip' ? '📍' : '🔐';
        
        return `
            <div class="search-item">
                <div>
                    <span style="font-size: 1.2rem; margin-right: var(--space-2);">${typeEmoji}</span>
                    <strong style="color: var(--text-primary);">${search.target}</strong>
                    <span style="margin-left: var(--space-2); color: var(--text-secondary); font-size: 0.875rem;">
                        ${date.toLocaleString('es-ES', { dateStyle: 'short', timeStyle: 'short' })}
                    </span>
                </div>
                <div>
                    <span class="reputation-badge reputation-${search.reputation}" style="font-size: 0.875rem; padding: var(--space-1) var(--space-3);">
                        ${reputationEmoji} ${search.reputation.toUpperCase()}
                    </span>
                </div>
            </div>
        `;
    }).join('');
}

// ===== HISTORY FUNCTIONALITY =====

let historyData = [];
let filteredHistoryData = [];

async function loadHistory() {
    const loading = document.getElementById('historyLoading');
    const empty = document.getElementById('historyEmpty');
    const grid = document.getElementById('historyGrid');
    
    if (loading) loading.style.display = 'block';
    if (grid) grid.innerHTML = '';
    if (empty) empty.style.display = 'none';
    
    try {
        const response = await fetch('/api/statistics');
        const data = await response.json();
        
        historyData = data.recent_searches || [];
        filteredHistoryData = [...historyData];
        
        if (loading) loading.style.display = 'none';
        
        if (historyData.length === 0) {
            if (empty) empty.style.display = 'block';
        } else {
            renderHistory();
        }
    } catch (error) {
        console.error('Error loading history:', error);
        if (loading) loading.style.display = 'none';
        if (empty) empty.style.display = 'block';
    }
}

function renderHistory() {
    const grid = document.getElementById('historyGrid');
    if (!grid) return;
    
    grid.innerHTML = '';
    
    if (filteredHistoryData.length === 0) {
        document.getElementById('historyEmpty').style.display = 'block';
        return;
    }
    
    document.getElementById('historyEmpty').style.display = 'none';
    
    filteredHistoryData.forEach((search, index) => {
        const card = createHistoryCard(search, index);
        grid.appendChild(card);
    });
}

function createHistoryCard(search, index) {
    const card = document.createElement('div');
    card.className = 'history-card';
    
    const date = new Date(search.timestamp);
    const dateStr = date.toLocaleString('es-ES', { 
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    
    const typeIcons = {
        'domain': '🌐',
        'ip': '📍',
        'hash': '🔐'
    };
    
    const typeLabels = {
        'domain': 'Dominio',
        'ip': 'Dirección IP',
        'hash': 'Hash'
    };
    
    const reputationEmoji = getReputationEmoji(search.reputation);
    
    const relativeTime = getRelativeTime(date);
    
    card.innerHTML = `
        <div class="history-card-header">
            <div class="history-card-type">
                <span class="history-card-type-icon">${typeIcons[search.type]}</span>
                <span>${typeLabels[search.type]}</span>
            </div>
            <div class="history-card-date">
                ${relativeTime}<br/>
                ${dateStr}
            </div>
        </div>
        
        <div class="history-card-target">${search.target}</div>
        
        <div class="history-card-reputation reputation-${search.reputation}">
            ${reputationEmoji} ${search.reputation.toUpperCase()}
        </div>
        
        <div class="history-card-meta">
            ${search.country ? `
                <div class="history-card-meta-item">
                    <span class="history-card-meta-label">País:</span>
                    <span class="history-card-meta-value">${search.country}</span>
                </div>
            ` : ''}
            <div class="history-card-meta-item">
                <span class="history-card-meta-label">Tipo:</span>
                <span class="history-card-meta-value">${typeLabels[search.type]}</span>
            </div>
        </div>
        
        <div class="history-card-actions">
            <button class="history-card-btn" onclick="repeatSearch('${search.type}', '${search.target}')">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                </svg>
                Repetir
            </button>
            <button class="history-card-btn" onclick="copyHistoryItem('${search.target}', '${search.reputation}', '${search.type}')">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                </svg>
                Copiar
            </button>
        </div>
    `;
    
    return card;
}

function getRelativeTime(date) {
    const now = new Date();
    const diff = now - date;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (seconds < 60) return 'Hace un momento';
    if (minutes < 60) return `Hace ${minutes} min`;
    if (hours < 24) return `Hace ${hours}h`;
    if (days < 7) return `Hace ${days} días`;
    return date.toLocaleDateString('es-ES');
}

function repeatSearch(type, target) {
    // Switch to the appropriate view
    const viewMap = {
        'domain': 'domain',
        'ip': 'ip',
        'hash': 'hash'
    };
    
    const targetView = viewMap[type];
    if (!targetView) return;
    
    // Find and click the sidebar item
    const sidebarItem = document.querySelector(`[data-view="${targetView}"]`);
    if (sidebarItem) {
        sidebarItem.click();
        
        // Fill in the input and trigger search
        setTimeout(() => {
            const inputMap = {
                'domain': 'domainInput',
                'ip': 'ipInput',
                'hash': 'hashInput'
            };
            
            const input = document.getElementById(inputMap[type]);
            if (input) {
                input.value = target;
                input.form.requestSubmit();
            }
        }, 100);
    }
    
    showToast(`Repitiendo búsqueda de ${target}`, 'info');
}

async function copyHistoryItem(target, reputation, type) {
    const text = `Tipo: ${type}\nObjetivo: ${target}\nReputación: ${reputation.toUpperCase()}`;
    const success = await copyToClipboard(text);
    
    if (success) {
        showToast('Información copiada', 'success');
    } else {
        showToast('Error al copiar', 'error');
    }
}

// History filters
const historyFilter = document.getElementById('historyFilter');
const reputationFilter = document.getElementById('reputationFilter');

if (historyFilter) {
    historyFilter.addEventListener('change', applyHistoryFilters);
}

if (reputationFilter) {
    reputationFilter.addEventListener('change', applyHistoryFilters);
}

function applyHistoryFilters() {
    const typeFilter = historyFilter?.value || 'all';
    const repFilter = reputationFilter?.value || 'all';
    
    filteredHistoryData = historyData.filter(search => {
        const typeMatch = typeFilter === 'all' || search.type === typeFilter;
        const repMatch = repFilter === 'all' || search.reputation === repFilter;
        return typeMatch && repMatch;
    });
    
    renderHistory();
}

// Clear history button
const clearHistoryBtn = document.getElementById('clearHistoryBtn');
if (clearHistoryBtn) {
    clearHistoryBtn.addEventListener('click', async () => {
        if (!confirm('¿Estás seguro de que quieres eliminar todo el historial?')) {
            return;
        }
        
        try {
            // Clear history by sending empty data (you'll need to implement this endpoint)
            showToast('Historial limpiado', 'success');
            historyData = [];
            filteredHistoryData = [];
            renderHistory();
            document.getElementById('historyEmpty').style.display = 'block';
        } catch (error) {
            showToast('Error al limpiar historial', 'error');
        }
    });
}

// ============================================
// Configuration Management (API Keys)
// ============================================

const apiConfigForm = document.getElementById('apiConfigForm');
const saveConfigBtn = document.getElementById('saveConfigBtn');
const testConfigBtn = document.getElementById('testConfigBtn');
const loadConfigBtn = document.getElementById('loadConfigBtn');

// Load API configuration
async function loadAPIConfig() {
    try {
        const response = await fetch('/api/config/status');
        if (!response.ok) throw new Error('Error al cargar configuración');
        
        const data = await response.json();
        const sources = data.sources || {};
        
        // Update status indicators with source information
        Object.keys(sources).forEach(sourceKey => {
            const source = sources[sourceKey];
            const statusElement = document.getElementById(`status-${sourceKey}`);
            
            if (statusElement) {
                if (source.configured) {
                    // Show source: config (encrypted) or env (environment variable)
                    const sourceLabel = source.source === 'config' ? '🔒 Config' : source.source === 'env' ? '🌐 Env Var' : '✅ Activa';
                    statusElement.textContent = `✅ ${sourceLabel}`;
                    statusElement.style.background = 'var(--accent-success)';
                    statusElement.style.color = 'white';
                    statusElement.title = source.source === 'config' ? 'API key desde configuración encriptada' : source.source === 'env' ? 'API key desde variable de entorno' : 'Configurada';
                } else {
                    statusElement.textContent = '❌ No configurada';
                    statusElement.style.background = 'var(--bg-tertiary)';
                    statusElement.style.color = 'var(--text-secondary)';
                    statusElement.title = 'No configurada';
                }
            }
        });
        
        // Update summary counts
        updateConfigSummary(sources);
        
        // Load masked API keys
        await loadMaskedAPIKeys();
        
    } catch (error) {
        console.error('Error loading API config:', error);
        showToast('Error al cargar configuración', 'error');
    }
}

// Load masked API keys for display
async function loadMaskedAPIKeys() {
    try {
        const response = await fetch('/api/config/get');
        if (!response.ok) return;
        
        const data = await response.json();
        const apiKeys = data.api_keys || {};
        
        // Update input placeholders with masked values
        Object.keys(apiKeys).forEach(source => {
            const input = document.querySelector(`input[name="${source}"]`);
            if (input && apiKeys[source]) {
                input.placeholder = apiKeys[source];
            }
        });
    } catch (error) {
        console.error('Error loading masked API keys:', error);
    }
}

// Update configuration summary
function updateConfigSummary(sources) {
    const tier1Sources = ['virustotal', 'abuseipdb', 'alienvault_otx'];
    const tier2Sources = ['urlscan', 'malware_bazaar', 'threatfox'];
    const tier3Sources = ['shodan', 'urlvoid', 'securitytrails'];
    const tier4Sources = ['ipapi', 'ipdata'];
    
    const tier1Configured = tier1Sources.filter(s => sources[s]?.configured).length;
    const tier2Configured = tier2Sources.filter(s => sources[s]?.configured).length;
    const tier3Configured = tier3Sources.filter(s => sources[s]?.configured).length;
    const tier4Configured = tier4Sources.filter(s => sources[s]?.configured).length;
    
    document.getElementById('tier1Count').textContent = `${tier1Configured}/${tier1Sources.length}`;
    document.getElementById('tier2Count').textContent = `${tier2Configured}/${tier2Sources.length}`;
    document.getElementById('tier3Count').textContent = `${tier3Configured}/${tier3Sources.length}`;
    document.getElementById('tier4Count').textContent = `${tier4Configured}/${tier4Sources.length}`;
}

// Save API configuration
if (apiConfigForm) {
    apiConfigForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(apiConfigForm);
        const apiKeys = {};
        
        // Collect non-empty API keys
        for (const [key, value] of formData.entries()) {
            if (value && value.trim()) {
                apiKeys[key] = value.trim();
            }
        }
        
        try {
            saveConfigBtn.disabled = true;
            saveConfigBtn.textContent = 'Guardando...';
            
            const response = await fetch('/api/config/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_keys: apiKeys })
            });
            
            if (!response.ok) throw new Error('Error al guardar configuración');
            
            const result = await response.json();
            showToast(result.message || 'Configuración guardada correctamente', 'success');
            
            // Reload configuration status
            setTimeout(() => loadAPIConfig(), 500);
            
            // Clear form (keep placeholders with masked values)
            apiConfigForm.reset();
            
        } catch (error) {
            console.error('Error saving config:', error);
            showToast(error.message || 'Error al guardar configuración', 'error');
        } finally {
            saveConfigBtn.disabled = false;
            saveConfigBtn.innerHTML = `
                <svg class="btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"></path>
                </svg>
                Guardar Configuración
            `;
        }
    });
}

// Test API configuration
if (testConfigBtn) {
    testConfigBtn.addEventListener('click', async () => {
        try {
            testConfigBtn.disabled = true;
            testConfigBtn.innerHTML = `
                <svg class="btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                </svg>
                Verificando...
            `;
            
            const response = await fetch('/api/config/verify');
            if (!response.ok) throw new Error('Error al verificar APIs');
            
            const data = await response.json();
            
            // Create detailed modal with results
            showAPIVerificationModal(data);
            
            showToast(`✅ ${data.total_unique} API(s) configuradas (${data.total_config} config, ${data.total_env} env)`, 'success');
            
        } catch (error) {
            console.error('Error verifying APIs:', error);
            showToast(error.message || 'Error al verificar APIs', 'error');
        } finally {
            testConfigBtn.disabled = false;
            testConfigBtn.innerHTML = `
                <svg class="btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                Verificar APIs
            `;
        }
    });
}

// Show API verification modal with detailed results
function showAPIVerificationModal(data) {
    const modalHTML = `
        <div class="modal" id="verifyModal" style="display: flex;">
            <div class="modal-content" style="max-width: 800px;">
                <div class="modal-header">
                    <h2>🔍 Verificación de API Keys</h2>
                    <button class="modal-close" onclick="document.getElementById('verifyModal').remove()">
                        <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                <div class="modal-body" style="max-height: 70vh; overflow-y: auto;">
                    <!-- Summary -->
                    <div style="background: var(--bg-tertiary); padding: var(--space-4); border-radius: var(--radius-lg); margin-bottom: var(--space-6);">
                        <h3 style="margin-bottom: var(--space-3); color: var(--text-primary);">📊 Resumen</h3>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--space-4);">
                            <div>
                                <div style="font-size: 2rem; font-weight: bold; color: var(--accent-primary);">${data.total_unique}</div>
                                <div style="color: var(--text-secondary); font-size: 0.875rem;">APIs Únicas Configuradas</div>
                            </div>
                            <div>
                                <div style="font-size: 2rem; font-weight: bold; color: var(--accent-success);">${data.total_config}</div>
                                <div style="color: var(--text-secondary); font-size: 0.875rem;">Desde Archivo Config</div>
                            </div>
                            <div>
                                <div style="font-size: 2rem; font-weight: bold; color: var(--accent-info);">${data.total_env}</div>
                                <div style="color: var(--text-secondary); font-size: 0.875rem;">Variables de Entorno</div>
                            </div>
                        </div>
                        <div style="margin-top: var(--space-3); padding: var(--space-3); background: var(--bg-primary); border-radius: var(--radius-md); font-size: 0.875rem; color: var(--text-secondary);">
                            <strong>ℹ️ Prioridad:</strong> ${data.sources_priority}
                        </div>
                    </div>
                    
                    <!-- Config File Keys -->
                    ${data.total_config > 0 ? `
                    <div style="margin-bottom: var(--space-6);">
                        <h3 style="margin-bottom: var(--space-3); color: var(--text-primary); display: flex; align-items: center; gap: var(--space-2);">
                            <span style="font-size: 1.5rem;">🔒</span> Archivo de Configuración (${data.total_config})
                        </h3>
                        <div style="background: var(--bg-tertiary); border-radius: var(--radius-lg); overflow: hidden;">
                            ${Object.entries(data.config_file).map(([source, info]) => `
                                <div style="padding: var(--space-3); border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <div style="font-weight: 600; color: var(--text-primary); text-transform: uppercase; font-size: 0.875rem;">${source.replace('_', ' ')}</div>
                                        <div style="font-family: monospace; color: var(--text-secondary); font-size: 0.875rem; margin-top: var(--space-1);">${info.masked_value}</div>
                                    </div>
                                    <div style="text-align: right;">
                                        <span style="background: var(--accent-success); color: white; padding: 0.25rem 0.75rem; border-radius: var(--radius-full); font-size: 0.75rem; font-weight: 600;">✓ Config</span>
                                        <div style="font-size: 0.75rem; color: var(--text-tertiary); margin-top: var(--space-1);">${info.length} caracteres</div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    ` : '<div style="padding: var(--space-4); text-align: center; color: var(--text-secondary); margin-bottom: var(--space-6);">📝 No hay APIs configuradas en el archivo de configuración</div>'}
                    
                    <!-- Environment Variables -->
                    ${data.total_env > 0 ? `
                    <div>
                        <h3 style="margin-bottom: var(--space-3); color: var(--text-primary); display: flex; align-items: center; gap: var(--space-2);">
                            <span style="font-size: 1.5rem;">⚙️</span> Variables de Entorno (${data.total_env})
                        </h3>
                        <div style="background: var(--bg-tertiary); border-radius: var(--radius-lg); overflow: hidden;">
                            ${Object.entries(data.environment_variables).map(([source, info]) => `
                                <div style="padding: var(--space-3); border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <div style="font-weight: 600; color: var(--text-primary); text-transform: uppercase; font-size: 0.875rem;">${source.replace('_', ' ')}</div>
                                        <div style="font-family: monospace; color: var(--text-tertiary); font-size: 0.75rem; margin-top: var(--space-1);">${info.env_var}</div>
                                        <div style="font-family: monospace; color: var(--text-secondary); font-size: 0.875rem; margin-top: var(--space-1);">${info.masked_value}</div>
                                    </div>
                                    <div style="text-align: right;">
                                        <span style="background: var(--accent-info); color: white; padding: 0.25rem 0.75rem; border-radius: var(--radius-full); font-size: 0.75rem; font-weight: 600;">⚙️ ENV</span>
                                        <div style="font-size: 0.75rem; color: var(--text-tertiary); margin-top: var(--space-1);">${info.length} caracteres</div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    ` : '<div style="padding: var(--space-4); text-align: center; color: var(--text-secondary);">🌍 No hay APIs configuradas en variables de entorno</div>'}
                </div>
            </div>
        </div>
    `;
    
    // Append modal to body
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Add click outside to close
    const modal = document.getElementById('verifyModal');
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// Load from file
if (loadConfigBtn) {
    loadConfigBtn.addEventListener('click', () => {
        showToast('Función de importación en desarrollo', 'info');
        // TODO: Implement configuration import from file
    });
}
