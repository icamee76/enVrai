class TicDetectorInterface {
    constructor() {
        this.currentConfig = {};
        this.currentStats = {};
        this.isRecording = false;
        
        this.initEventListeners();
        this.initTabs();
        this.loadData();
        
        // Actualisation automatique des statistiques
        setInterval(() => this.updateStats(), 2000);
    }
    
    initEventListeners() {
        // Contrôles principaux
        document.getElementById('startBtn').addEventListener('click', () => this.startDetection());
        document.getElementById('stopBtn').addEventListener('click', () => this.stopDetection());
        
        // Modal
        document.getElementById('addExprBtn').addEventListener('click', () => this.openAddModal());
        document.getElementById('expressionForm').addEventListener('submit', (e) => this.saveExpression(e));
        document.querySelector('.close').addEventListener('click', () => this.closeModal());
        document.getElementById('cancelBtn').addEventListener('click', () => this.closeModal());
        
        // Configuration
        document.getElementById('saveConfigBtn').addEventListener('click', () => this.saveConfig());

        const vadSlider = document.getElementById('vadAggressiveness');
        const vadLabel = document.getElementById('vadValueLabel');
        const sensitivityMap = {
            '0': 'Très sensible (mode calme)',
            '1': 'Sensible',
            '2': 'Normal',
            '3': 'Peu sensible (mode bruyant)'
        };
        vadSlider.addEventListener('input', () => {
            vadLabel.textContent = sensitivityMap[vadSlider.value] || 'Normal';
        });
        
        // Fermeture modal si clic extérieur
        window.addEventListener('click', (e) => {
            const modal = document.getElementById('expressionModal');
            if (e.target === modal) {
                this.closeModal();
            }
        });
    }
    
    initTabs() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');
        
        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const tabName = btn.dataset.tab;
                
                // Désactiver tous les onglets
                tabBtns.forEach(b => b.classList.remove('active'));
                tabContents.forEach(c => c.classList.remove('active'));
                
                // Activer l'onglet sélectionné
                btn.classList.add('active');
                document.getElementById(tabName).classList.add('active');
                
                // Charger les données spécifiques à l'onglet
                if (tabName === 'files') {
                    this.loadMp3Files();
                }
            });
        });
    }
    
    async loadData() {
        await this.loadConfig();
        await this.updateStats();
        await this.loadExpressions();
    }
    
    async loadConfig() {
        try {
            const response = await fetch('/api/config');
            this.currentConfig = await response.json();
            
            // Mettre à jour l'interface
            document.getElementById('whisperModel').value = this.currentConfig.whisper_model || 'base';

            const vadConfig = this.currentConfig.vad_config || { enabled: true, aggressiveness: 2 };
            document.getElementById('vadEnabled').checked = vadConfig.enabled;
            
            const vadSlider = document.getElementById('vadAggressiveness');
            vadSlider.value = vadConfig.aggressiveness;
            
            // Déclencher l'événement 'input' pour mettre à jour le label
            vadSlider.dispatchEvent(new Event('input'));
            
        } catch (error) {
            console.error('Erreur chargement config:', error);
        }
    }
    
    async loadExpressions() {
        try {
            const response = await fetch('/api/expressions');
            const expressions = await response.json();
            
            this.renderExpressions(expressions);
            
        } catch (error) {
            console.error('Erreur chargement expressions:', error);
        }
    }
    
    renderExpressions(expressions) {
        const container = document.getElementById('expressionsList');
        container.innerHTML = '';
        
        Object.entries(expressions).forEach(([key, expr]) => {
            const card = document.createElement('div');
            card.className = 'expression-card';
            
            card.innerHTML = `
                <div class="expression-header">
                    <div class="expression-name">${expr.name}</div>
                    <div class="expression-actions">
                        <label class="toggle-switch">
                            <input type="checkbox" ${expr.enabled ? 'checked' : ''} 
                                   onchange="window.ticInterface.toggleExpression('${key}', this.checked)">
                            <span class="slider"></span>
                        </label>
                        <button class="btn btn-primary btn-small" 
                                onclick="window.ticInterface.editExpression('${key}')">✏️</button>
                        <button class="btn btn-danger btn-small" 
                                onclick="window.ticInterface.deleteExpression('${key}')">🗑️</button>
                    </div>
                </div>
                <div class="expression-details">
                    <div class="detail-row">
                        <span class="detail-label">Patterns:</span>
                        <span>${expr.patterns.join(', ')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Action:</span>
                        <span>${this.getActionText(expr.action)}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">MP3:</span>
                        <span>${expr.mp3_file || 'Aucun'}</span>
                        ${expr.mp3_file ? `<button class="btn btn-secondary btn-small" onclick="window.ticInterface.testMp3('${expr.mp3_file}')">🔊</button>` : ''}
                    </div>
                </div>
            `;
            
            container.appendChild(card);
        });
    }
    
    getActionText(action) {
        const actions = {
            'mp3': '🎵 Jouer MP3',
            'replay': '🔄 Réécouter',
            'both': '🎵➡️🔄 MP3 puis Réécoute'
        };
        return actions[action] || action;
    }
    
    async updateStats() {
        try {
            const response = await fetch('/api/stats');
            this.currentStats = await response.json();
            
            // Mettre à jour le statut
            this.isRecording = this.currentStats.is_recording;
            const statusEl = document.getElementById('status');
            statusEl.textContent = this.isRecording ? 'En cours' : 'Arrêté';
            statusEl.className = `status ${this.isRecording ? 'recording' : 'stopped'}`;
            
            // Mettre à jour les boutons
            document.getElementById('startBtn').disabled = this.isRecording;
            document.getElementById('stopBtn').disabled = !this.isRecording;
            
            this.renderStats();
            this.renderRecentDetections();
            
        } catch (error) {
            console.error('Erreur mise à jour stats:', error);
        }
    }
    
    renderStats() {
        const container = document.getElementById('statsContent');
        const stats = this.currentStats.detection_stats || {};
        
        const totalDetections = Object.values(stats).reduce((a, b) => a + b, 0);
        
        let html = `
            <div class="stats-card">
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">${totalDetections}</div>
                        <div class="stat-label">Total Détections</div>
                    </div>
        `;
        
        Object.entries(stats).forEach(([key, count]) => {
            if (count > 0) {
                const expr = this.currentStats.config?.expressions[key];
                const name = expr?.name || key;
                html += `
                    <div class="stat-item">
                        <div class="stat-value">${count}</div>
                        <div class="stat-label">${name}</div>
                    </div>
                `;
            }
        });
        
        html += `
                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }
    
    renderRecentDetections() {
        const container = document.getElementById('recentDetections');
        const detections = this.currentStats.session_detections || [];
        
        const recent = detections.slice(-10).reverse();
        
        container.innerHTML = recent.map(detection => `
            <div class="detection-item">
                <div class="detection-info">
                    <div class="detection-time">${new Date(detection.timestamp).toLocaleTimeString()}</div>
                    <div class="detection-text">"${detection.text}"</div>
                    <div class="detection-expression">→ ${detection.expression} (${detection.action})</div>
                </div>
                <div class="detection-actions">
                    ${detection.mp3_file ? `<button class="btn btn-secondary btn-small" onclick="window.ticInterface.testMp3('${detection.mp3_file}')">🎵</button>` : ''}
                    ${detection.audio_file ? `<button class="btn btn-secondary btn-small" onclick="window.ticInterface.playRecording('${detection.audio_file}')">🔊</button>` : ''}
                    ${detection.audio_file ? `<a href="/download/recording/${detection.audio_file}" class="btn btn-secondary btn-small">⬇️</a>` : ''}
                </div>
            </div>
        `).join('');
    }
    
    async loadMp3Files() {
        try {
            const response = await fetch('/api/mp3_files');
            const files = await response.json();
            
            const container = document.getElementById('mp3List');
            container.innerHTML = files.map(file => `
                <div class="mp3-item">
                    <span>🎵 ${file}</span>
                    <button class="btn btn-secondary" onclick="window.ticInterface.testMp3('${file}')">🔊 Tester</button>
                </div>
            `).join('');
            
            // Mettre à jour les selects de MP3
            this.updateMp3Selects(files);
            
        } catch (error) {
            console.error('Erreur chargement MP3:', error);
        }
    }
    
    updateMp3Selects(files) {
        const selects = document.querySelectorAll('#exprMp3File');
        selects.forEach(select => {
            const currentValue = select.value;
            select.innerHTML = '<option value="">Aucun</option>' + 
                files.map(file => `<option value="${file}">${file}</option>`).join('');
            select.value = currentValue;
        });
    }
    
    async startDetection() {
        try {
            await fetch('/api/start');
            await this.updateStats();
        } catch (error) {
            console.error('Erreur démarrage:', error);
        }
    }
    
    async stopDetection() {
        try {
            await fetch('/api/stop');
            await this.updateStats();
        } catch (error) {
            console.error('Erreur arrêt:', error);
        }
    }
    
    async toggleExpression(key, enabled) {
        try {
            const expr = this.currentStats.config.expressions[key];
            expr.enabled = enabled;
            
            await fetch(`/api/expressions/${key}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(expr)
            });
            
        } catch (error) {
            console.error('Erreur toggle expression:', error);
        }
    }
    
    openAddModal() {
        document.getElementById('modalTitle').textContent = 'Ajouter une Expression';
        document.getElementById('expressionForm').reset();
        document.getElementById('exprKey').value = '';
        document.getElementById('exprEnabled').checked = true;
        
        this.loadMp3Files(); // Charger les MP3 disponibles
        document.getElementById('expressionModal').style.display = 'block';
    }
    
    async editExpression(key) {
        const expr = this.currentStats.config.expressions[key];
        
        document.getElementById('modalTitle').textContent = 'Modifier l\'Expression';
        document.getElementById('exprKey').value = key;
        document.getElementById('exprName').value = expr.name;
        document.getElementById('exprPatterns').value = expr.patterns.join('\n');
        document.getElementById('exprAction').value = expr.action;
        document.getElementById('exprMp3File').value = expr.mp3_file || '';
        document.getElementById('exprEnabled').checked = expr.enabled;
        
        await this.loadMp3Files(); // Charger les MP3 disponibles
        document.getElementById('expressionModal').style.display = 'block';
    }
    
    async deleteExpression(key) {
        if (confirm('Êtes-vous sûr de vouloir supprimer cette expression ?')) {
            try {
                await fetch(`/api/expressions/${key}`, { method: 'DELETE' });
                await this.loadExpressions();
            } catch (error) {
                console.error('Erreur suppression:', error);
            }
        }
    }
    
    async saveExpression(e) {
        e.preventDefault();
        
        const key = document.getElementById('exprKey').value || 
                    document.getElementById('exprName').value.toLowerCase().replace(/\s+/g, '_');
        
        const exprData = {
            key: key,
            name: document.getElementById('exprName').value,
            patterns: document.getElementById('exprPatterns').value.split('\n').filter(p => p.trim()),
            action: document.getElementById('exprAction').value,
            mp3_file: document.getElementById('exprMp3File').value,
            enabled: document.getElementById('exprEnabled').checked
        };
        
        try {
            const method = document.getElementById('exprKey').value ? 'PUT' : 'POST';
            const url = document.getElementById('exprKey').value ? 
                       `/api/expressions/${key}` : '/api/expressions';
            
            await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(exprData)
            });
            
            this.closeModal();
            await this.loadExpressions();
            
        } catch (error) {
            console.error('Erreur sauvegarde expression:', error);
        }
    }
    
    closeModal() {
        document.getElementById('expressionModal').style.display = 'none';
    }
    
    async saveConfig() {
        try {
            const newConfig = {
                whisper_model: document.getElementById('whisperModel').value,
                vad_config: {
                    enabled: document.getElementById('vadEnabled').checked,
                    aggressiveness: parseInt(document.getElementById('vadAggressiveness').value, 10)
                }
            };
            
            await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newConfig)
            });
            
            alert('Configuration sauvegardée !');
            await this.loadConfig();
            
        } catch (error) {
            console.error('Erreur sauvegarde config:', error);
        }
    }
    
    async testMp3(filename) {
        try {
            await fetch(`/api/play_mp3/${filename}`);
        } catch (error) {
            console.error('Erreur test MP3:', error);
        }
    }
    
    async playRecording(filename) {
        try {
            await fetch(`/api/play_recording/${filename}`);
        } catch (error) {
            console.error('Erreur lecture enregistrement:', error);
        }
    }
}

// Initialiser l'interface quand la page est chargée
document.addEventListener('DOMContentLoaded', () => {
    window.ticInterface = new TicDetectorInterface();
});