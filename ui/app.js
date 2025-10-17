/**
 * Traductor ES → DA - UI Client
 * 
 * Cliente JavaScript para interfaz de traducción de correos.
 * 100% local, sin llamadas externas.
 */

// Estado global
const state = {
    apiUrl: 'http://localhost:8000',
    currentTab: 'text',
    isTranslating: false,
    apiOnline: false,
    timeout: 60000  // 60 segundos timeout
};

/**
 * Fetch con timeout usando AbortController
 */
function fetchWithTimeout(resource, options = {}) {
    const { timeout = state.timeout } = options;
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    
    const fetchOptions = {
        ...options,
        signal: controller.signal
    };
    
    return fetch(resource, fetchOptions).finally(() => clearTimeout(id));
}

// Elementos del DOM
const elements = {
    // Tabs
    tabButtons: document.querySelectorAll('.tab-button'),
    tabContents: document.querySelectorAll('.tab-content'),
    
    // Text tab
    sourceText: document.getElementById('sourceText'),
    targetText: document.getElementById('targetText'),
    sourceCharCount: document.getElementById('sourceCharCount'),
    targetCharCount: document.getElementById('targetCharCount'),
    fileInputText: document.getElementById('fileInputText'),
    copyText: document.getElementById('copyText'),
    saveText: document.getElementById('saveText'),
    
    // HTML tab
    sourceHtml: document.getElementById('sourceHtml'),
    targetHtml: document.getElementById('targetHtml'),
    sourcePreview: document.getElementById('sourcePreview'),
    targetPreview: document.getElementById('targetPreview'),
    fileInputHtml: document.getElementById('fileInputHtml'),
    copyHtml: document.getElementById('copyHtml'),
    saveHtml: document.getElementById('saveHtml'),
    
    // Settings
    glossaryInput: document.getElementById('glossaryInput'),
    maxTokens: document.getElementById('maxTokens'),
    maxTokensValue: document.getElementById('maxTokensValue'),
    apiUrl: document.getElementById('apiUrl'),
    
    // UI controls
    translateBtn: document.getElementById('translateBtn'),
    loadingIndicator: document.getElementById('loadingIndicator'),
    errorMessage: document.getElementById('errorMessage'),
    successMessage: document.getElementById('successMessage'),
    statusIndicator: document.getElementById('statusIndicator')
};

/**
 * Inicialización
 */
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    checkAPIStatus();
    loadSettings();
});

/**
 * Event listeners
 */
function initEventListeners() {
    // Tabs
    elements.tabButtons.forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    
    // Text tab
    elements.sourceText.addEventListener('input', () => {
        updateCharCount(elements.sourceText, elements.sourceCharCount);
        toggleTranslateButton();
    });
    
    elements.fileInputText.addEventListener('change', (e) => {
        loadFile(e.target.files[0], 'text');
    });
    
    elements.copyText.addEventListener('click', () => {
        copyToClipboard(elements.targetText.value, 'text');
    });
    
    elements.saveText.addEventListener('click', () => {
        saveAsFile(elements.targetText.value, 'traduccion.txt', 'text/plain');
    });
    
    // HTML tab
    elements.sourceHtml.addEventListener('input', () => {
        updatePreview(elements.sourceHtml.value, elements.sourcePreview);
        toggleTranslateButton();
    });
    
    elements.fileInputHtml.addEventListener('change', (e) => {
        loadFile(e.target.files[0], 'html');
    });
    
    elements.copyHtml.addEventListener('click', () => {
        copyToClipboard(elements.targetHtml.value, 'html');
    });
    
    elements.saveHtml.addEventListener('click', () => {
        saveAsFile(elements.targetHtml.value, 'traduccion.html', 'text/html');
    });
    
    // Settings
    elements.maxTokens.addEventListener('input', (e) => {
        elements.maxTokensValue.textContent = e.target.value;
        saveSettings();
    });
    
    elements.apiUrl.addEventListener('change', () => {
        state.apiUrl = elements.apiUrl.value;
        saveSettings();
        checkAPIStatus();
    });
    
    elements.glossaryInput.addEventListener('change', saveSettings);
    
    // Translate button
    elements.translateBtn.addEventListener('click', translate);
}

/**
 * Cambiar tab activa
 */
function switchTab(tabName) {
    state.currentTab = tabName;
    
    // Actualizar botones
    elements.tabButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    
    // Actualizar contenido
    document.getElementById('textTab').classList.toggle('active', tabName === 'text');
    document.getElementById('htmlTab').classList.toggle('active', tabName === 'html');
    
    // Toggle translate button
    toggleTranslateButton();
}

/**
 * Actualizar contador de caracteres
 */
function updateCharCount(textarea, countElement) {
    const count = textarea.value.length;
    countElement.textContent = `${count.toLocaleString()} caracteres`;
}

/**
 * Actualizar vista previa HTML
 */
function updatePreview(html, previewElement) {
    if (!html.trim()) {
        previewElement.innerHTML = '<em>La vista previa aparecerá aquí...</em>';
        return;
    }
    
    // Sanitizar HTML antes de mostrar
    const sanitized = sanitizeHTML(html);
    previewElement.innerHTML = sanitized;
}

/**
 * Sanitizar HTML (prevenir XSS)
 */
function sanitizeHTML(html) {
    // Remover scripts
    html = html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
    
    // Remover event handlers
    html = html.replace(/\s*on\w+\s*=\s*["'][^"']*["']/gi, '');
    
    // Remover javascript: en hrefs
    html = html.replace(/href\s*=\s*["']?\s*javascript:/gi, 'href="#');
    
    return html;
}

/**
 * Activar/desactivar botón de traducir
 */
function toggleTranslateButton() {
    const hasContent = state.currentTab === 'text' 
        ? elements.sourceText.value.trim().length > 0
        : elements.sourceHtml.value.trim().length > 0;
    
    elements.translateBtn.disabled = !hasContent || !state.apiOnline || state.isTranslating;
}

/**
 * Verificar estado del API
 */
async function checkAPIStatus() {
    try {
        const response = await fetchWithTimeout(`${state.apiUrl}/health`, {
            method: 'GET',
            timeout: 5000
        });
        
        const data = await response.json();
        
        if (data.status === 'healthy') {
            state.apiOnline = true;
            elements.statusIndicator.classList.add('online');
            elements.statusIndicator.classList.remove('offline');
            elements.statusIndicator.querySelector('.status-text').textContent = 'API en línea';
        } else {
            throw new Error('API no saludable');
        }
    } catch (error) {
        state.apiOnline = false;
        elements.statusIndicator.classList.add('offline');
        elements.statusIndicator.classList.remove('online');
        elements.statusIndicator.querySelector('.status-text').textContent = 
            'API offline - Verifica que el servidor esté corriendo';
    }
    
    toggleTranslateButton();
}

/**
 * Parsear glosario desde textarea
 */
function parseGlossary() {
    const text = elements.glossaryInput.value.trim();
    if (!text) return null;
    
    const glossary = {};
    const lines = text.split('\n');
    
    for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) continue;
        
        const parts = trimmed.split('=');
        if (parts.length === 2) {
            const [es, da] = parts.map(p => p.trim());
            if (es && da) {
                glossary[es] = da;
            }
        }
    }
    
    return Object.keys(glossary).length > 0 ? glossary : null;
}

/**
 * Traducir
 */
async function translate() {
    if (state.isTranslating || !state.apiOnline) return;
    
    state.isTranslating = true;
    elements.translateBtn.disabled = true;
    elements.loadingIndicator.hidden = false;
    elements.errorMessage.hidden = true;
    elements.successMessage.hidden = true;
    
    try {
        const glossary = parseGlossary();
        const maxNewTokens = parseInt(elements.maxTokens.value);
        
        let result;
        
        if (state.currentTab === 'text') {
            result = await translateText(
                elements.sourceText.value,
                maxNewTokens,
                glossary
            );
            
            elements.targetText.value = result.translations.join('\n\n');
            updateCharCount(elements.targetText, elements.targetCharCount);
            elements.copyText.disabled = false;
            elements.saveText.disabled = false;
            
        } else {
            result = await translateHTML(
                elements.sourceHtml.value,
                maxNewTokens,
                glossary
            );
            
            elements.targetHtml.value = result.html;
            updatePreview(result.html, elements.targetPreview);
            elements.copyHtml.disabled = false;
            elements.saveHtml.disabled = false;
        }
        
        showSuccess('✓ Traducción completada exitosamente');
        
    } catch (error) {
        console.error('Error en traducción:', error);
        
        // Manejo específico de timeout
        if (error.name === 'AbortError') {
            showError('⏱️ Timeout: La traducción tardó más de 60 segundos. Intenta con un texto más corto.');
        } else {
            showError(`Error: ${error.message}`);
        }
    } finally {
        state.isTranslating = false;
        elements.loadingIndicator.hidden = true;
        toggleTranslateButton();
    }
}

/**
 * Traducir texto con timeout
 */
async function translateText(text, maxNewTokens, glossary) {
    const response = await fetchWithTimeout(`${state.apiUrl}/translate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            text: text,
            max_new_tokens: maxNewTokens,
            glossary: glossary
        }),
        timeout: 60000  // 60 segundos
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error en traducción');
    }
    
    return await response.json();
}

/**
 * Traducir HTML con timeout
 */
async function translateHTML(html, maxNewTokens, glossary) {
    const response = await fetchWithTimeout(`${state.apiUrl}/translate/html`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            html: html,
            max_new_tokens: maxNewTokens,
            glossary: glossary
        }),
        timeout: 60000  // 60 segundos
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error en traducción HTML');
    }
    
    return await response.json();
}

/**
 * Cargar archivo
 */
async function loadFile(file, type) {
    if (!file) return;
    
    try {
        const text = await file.text();
        
        if (type === 'text') {
            elements.sourceText.value = text;
            updateCharCount(elements.sourceText, elements.sourceCharCount);
        } else {
            elements.sourceHtml.value = text;
            updatePreview(text, elements.sourcePreview);
        }
        
        toggleTranslateButton();
        
    } catch (error) {
        showError(`Error al cargar archivo: ${error.message}`);
    }
}

/**
 * Copiar al portapapeles
 */
async function copyToClipboard(text, type) {
    try {
        await navigator.clipboard.writeText(text);
        showSuccess(`✓ ${type === 'text' ? 'Texto' : 'HTML'} copiado al portapapeles`);
    } catch (error) {
        showError('Error al copiar al portapapeles');
    }
}

/**
 * Guardar como archivo
 */
function saveAsFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showSuccess(`✓ Archivo guardado: ${filename}`);
}

/**
 * Mostrar mensaje de error
 */
function showError(message) {
    elements.errorMessage.textContent = message;
    elements.errorMessage.hidden = false;
    elements.successMessage.hidden = true;
    
    setTimeout(() => {
        elements.errorMessage.hidden = true;
    }, 5000);
}

/**
 * Mostrar mensaje de éxito
 */
function showSuccess(message) {
    elements.successMessage.textContent = message;
    elements.successMessage.hidden = false;
    elements.errorMessage.hidden = true;
    
    setTimeout(() => {
        elements.successMessage.hidden = true;
    }, 3000);
}

/**
 * Guardar configuración en localStorage
 */
function saveSettings() {
    const settings = {
        apiUrl: elements.apiUrl.value,
        maxTokens: elements.maxTokens.value,
        glossary: elements.glossaryInput.value
    };
    
    localStorage.setItem('translatorSettings', JSON.stringify(settings));
}

/**
 * Cargar configuración desde localStorage
 */
function loadSettings() {
    const saved = localStorage.getItem('translatorSettings');
    if (!saved) return;
    
    try {
        const settings = JSON.parse(saved);
        
        if (settings.apiUrl) {
            elements.apiUrl.value = settings.apiUrl;
            state.apiUrl = settings.apiUrl;
        }
        
        if (settings.maxTokens) {
            elements.maxTokens.value = settings.maxTokens;
            elements.maxTokensValue.textContent = settings.maxTokens;
        }
        
        if (settings.glossary) {
            elements.glossaryInput.value = settings.glossary;
        }
    } catch (error) {
        console.error('Error cargando configuración:', error);
    }
}

// Verificar estado del API cada 30 segundos
setInterval(checkAPIStatus, 30000);

