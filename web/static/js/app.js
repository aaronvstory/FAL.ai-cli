// FAL.AI Video Generator - Modern Web Interface
// Professional JavaScript with drag-and-drop, real-time updates, and beautiful interactions

class VideoGeneratorApp {
    constructor() {
        this.uploadedFiles = new Map();
        this.selectedModel = 'kling_21_pro';
        this.websocket = null;
        this.currentJobId = null;
        this.stats = { generated: 0, uploaded: 0 };
        
        this.init();
    }
    
    init() {
        this.setupWebSocket();
        this.setupEventListeners();
        this.loadModels();
        this.updateStats();
    }
    
    // ========================================================================
    //                           WebSocket Connection                          
    // ========================================================================
    
    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        try {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('✅ WebSocket connected');
                this.updateConnectionStatus(true);
            };
            
            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.job_id && data.status) {
                    this.handleJobUpdate(data.job_id, data.status);
                }
            };
            
            this.websocket.onclose = () => {
                console.log('⚠️ WebSocket disconnected');
                this.updateConnectionStatus(false);
                // Attempt to reconnect after 3 seconds
                setTimeout(() => this.setupWebSocket(), 3000);
            };
            
            this.websocket.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
                this.updateConnectionStatus(false);
            };
            
        } catch (error) {
            console.error('❌ Failed to create WebSocket:', error);
            this.updateConnectionStatus(false);
        }
    }
    
    updateConnectionStatus(connected) {
        const indicator = document.getElementById('statusIndicator');
        if (connected) {
            indicator.className = 'w-3 h-3 rounded-full bg-green-400 pulse';
            indicator.title = 'Connected';
        } else {
            indicator.className = 'w-3 h-3 rounded-full bg-red-400';
            indicator.title = 'Disconnected';
        }
    }
    
    // ========================================================================
    //                           Event Listeners                              
    // ========================================================================
    
    setupEventListeners() {
        // File upload
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        
        // Drag and drop
        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', this.handleDragOver.bind(this));
        dropZone.addEventListener('dragleave', this.handleDragLeave.bind(this));
        dropZone.addEventListener('drop', this.handleDrop.bind(this));
        
        // File input
        fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        
        // Generation form
        const form = document.getElementById('generationForm');
        form.addEventListener('submit', this.handleGeneration.bind(this));
        
        // CFG Scale slider
        const cfgScale = document.getElementById('cfgScale');
        const cfgValue = document.getElementById('cfgValue');
        cfgScale.addEventListener('input', (e) => {
            cfgValue.textContent = e.target.value;
        });
        
        // History modal
        const historyBtn = document.getElementById('historyBtn');
        const historyModal = document.getElementById('historyModal');
        const closeHistoryBtn = document.getElementById('closeHistoryBtn');
        
        historyBtn.addEventListener('click', this.showHistory.bind(this));
        closeHistoryBtn.addEventListener('click', () => this.hideModal(historyModal));
        historyModal.addEventListener('click', (e) => {
            if (e.target === historyModal) this.hideModal(historyModal);
        });
        
        // Escape key handling
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const modals = document.querySelectorAll('.fixed.inset-0:not(.hidden)');
                modals.forEach(modal => this.hideModal(modal));
            }
        });
    }
    
    // ========================================================================
    //                           File Handling                                
    // ========================================================================
    
    handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        document.getElementById('dropZone').classList.add('drag-over');
    }
    
    handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        document.getElementById('dropZone').classList.remove('drag-over');
    }
    
    handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        document.getElementById('dropZone').classList.remove('drag-over');
        
        const files = Array.from(e.dataTransfer.files);
        this.processFiles(files);
    }
    
    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        this.processFiles(files);
    }
    
    async processFiles(files) {
        const validFiles = files.filter(file => file.type.startsWith('image/'));
        
        if (validFiles.length === 0) {
            this.showToast('Please select valid image files', 'error');
            return;
        }
        
        for (const file of validFiles) {
            await this.uploadFile(file);
        }
        
        this.updateFilePreview();
        this.updateStats();
    }
    
    async uploadFile(file) {
        try {
            this.showLoadingOverlay(true);
            
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Upload failed');
            }
            
            const result = await response.json();
            
            this.uploadedFiles.set(result.file_id, {
                ...result,
                originalFile: file
            });
            
            this.stats.uploaded++;
            this.showToast(`✅ ${file.name} uploaded successfully`, 'success');
            
        } catch (error) {
            console.error('Upload error:', error);
            this.showToast(`❌ Failed to upload ${file.name}: ${error.message}`, 'error');
        } finally {
            this.showLoadingOverlay(false);
        }
    }
    
    updateFilePreview() {
        const container = document.getElementById('filePreview');
        const files = Array.from(this.uploadedFiles.values());
        
        if (files.length === 0) {
            container.classList.add('hidden');
            return;
        }
        
        container.innerHTML = files.map(file => `
            <div class="file-preview-item fade-in" data-file-id="${file.file_id}">
                <img src="${file.preview_url}" alt="${file.filename}" loading="lazy">
                <div class="file-preview-overlay">
                    <div class="file-preview-name">${file.filename}</div>
                    <div class="file-preview-size">${this.formatFileSize(file.size)}</div>
                </div>
                <button class="file-remove-btn" onclick="app.removeFile('${file.file_id}')">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `).join('');
        
        container.classList.remove('hidden');
    }
    
    removeFile(fileId) {
        this.uploadedFiles.delete(fileId);
        this.stats.uploaded = Math.max(0, this.stats.uploaded - 1);
        this.updateFilePreview();
        this.updateStats();
        this.showToast('File removed', 'info');
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // ========================================================================
    //                           Model Management                              
    // ========================================================================
    
    async loadModels() {
        try {
            // Show loading state
            document.getElementById('modelSelectionLoading').classList.remove('hidden');
            document.getElementById('modelSelection').classList.add('hidden');
            document.getElementById('modelSelectionError').classList.add('hidden');
            
            const response = await fetch('/api/models');
            const data = await response.json();
            
            // Store models data for cost calculations
            this.modelsData = data.models;
            this.costCalculatorData = data.cost_calculator;
            
            this.renderModels(data.models);
            
            // Update count display
            const modelCount = Object.keys(data.models).length;
            document.getElementById('modelCount').textContent = `${modelCount} models available`;
            
            // Hide loading, show models
            document.getElementById('modelSelectionLoading').classList.add('hidden');
            document.getElementById('modelSelection').classList.remove('hidden');
            
            // Set default model
            if (data.default_model && this.modelsData[data.default_model]) {
                this.selectModel(data.default_model);
            }
        } catch (error) {
            console.error('Failed to load models:', error);
            
            // Show error state
            document.getElementById('modelSelectionLoading').classList.add('hidden');
            document.getElementById('modelSelection').classList.add('hidden');
            document.getElementById('modelSelectionError').classList.remove('hidden');
            
            this.showToast('Failed to load models', 'error');
        }
    }
    
    renderModels(models) {
        const container = document.getElementById('modelSelection');
        
        container.innerHTML = Object.entries(models).map(([key, model]) => {
            const isRecommended = model.recommended;
            const tierColors = {
                'Premium': 'from-purple-500 to-pink-500',
                'Professional': 'from-blue-500 to-indigo-500', 
                'Standard': 'from-green-500 to-teal-500',
                'Legacy Premium': 'from-orange-500 to-red-500',
                'Legacy': 'from-gray-500 to-gray-600',
                'Alternative': 'from-cyan-500 to-blue-500',
                'Budget': 'from-emerald-500 to-green-500'
            };
            
            const tierColor = tierColors[model.tier] || 'from-gray-500 to-gray-600';
            
            return `
                <div class="model-card ${key === this.selectedModel ? 'selected' : ''} ${isRecommended ? 'recommended' : ''}" 
                     data-model="${key}" 
                     role="radio" 
                     aria-checked="${key === this.selectedModel ? 'true' : 'false'}"
                     aria-labelledby="model-title-${key}"
                     aria-describedby="model-desc-${key} model-costs-${key}"
                     tabindex="${key === this.selectedModel ? '0' : '-1'}"
                     onclick="app.selectModel('${key}')"
                     onkeydown="app.handleModelKeydown(event, '${key}')">
                    ${isRecommended ? '<div class="recommended-badge" aria-label="Recommended model">⭐ Recommended</div>' : ''}
                    
                    <div class="model-card-header">
                        <div class="model-card-title" id="model-title-${key}">${model.name}</div>
                        <div class="model-tier-badge bg-gradient-to-r ${tierColor}" aria-label="${model.tier} tier">${model.tier}</div>
                    </div>
                    
                    <div class="model-card-description" id="model-desc-${key}">${model.description}</div>
                    
                    <div class="model-card-costs" id="model-costs-${key}" aria-label="Pricing information">
                        <div class="cost-row">
                            <span class="cost-label">5s:</span>
                            <span class="cost-value" aria-label="5 second cost">${model.cost_breakdown['5_seconds']}</span>
                        </div>
                        <div class="cost-row">
                            <span class="cost-label">10s:</span>
                            <span class="cost-value" aria-label="10 second cost">${model.cost_breakdown['10_seconds']}</span>
                        </div>
                        <div class="cost-row">
                            <span class="cost-label">Rate:</span>
                            <span class="cost-value" aria-label="Per second rate">${model.cost_breakdown.per_second}</span>
                        </div>
                    </div>
                    
                    <div class="model-card-footer">
                        <div class="quality-badge quality-${model.quality.toLowerCase()}" aria-label="${model.quality} quality level">${model.quality} Quality</div>
                        <div class="duration-info" aria-label="Maximum duration">Max: ${model.max_duration}s</div>
                    </div>
                    
                    <div class="model-card-best-for" aria-label="Best use case">
                        <i class="fas fa-star text-yellow-400 text-xs" aria-hidden="true"></i>
                        <span class="text-xs">${model.best_for}</span>
                    </div>
                </div>
            `;
        }).join('');
        
        // Add cost calculator info
        this.updateCostCalculator();
    }
    
    selectModel(modelKey) {
        // Remove previous selection
        document.querySelectorAll('.model-card').forEach(card => {
            card.classList.remove('selected');
            card.setAttribute('aria-checked', 'false');
            card.tabIndex = -1;
        });
        
        // Add selection to clicked model
        const selectedCard = document.querySelector(`[data-model="${modelKey}"]`);
        if (selectedCard) {
            selectedCard.classList.add('selected');
            selectedCard.setAttribute('aria-checked', 'true');
            selectedCard.tabIndex = 0;
            this.selectedModel = modelKey;
            
            // Update duration limits and cost based on model
            const durationInput = document.getElementById('duration');
            const modelData = this.modelsData[modelKey];
            
            if (modelData) {
                const maxDuration = modelData.max_duration;
                durationInput.max = maxDuration;
                
                // Update duration options
                const durationSelect = this.createDurationSelect(modelData.duration_options);
                if (durationSelect) {
                    durationInput.parentElement.replaceChild(durationSelect, durationInput);
                }
                
                // Update cost display
                this.updateCostDisplay(modelKey);
                
                if (parseInt(durationInput.value) > maxDuration) {
                    durationInput.value = maxDuration;
                }
                
                // Announce selection to screen readers
                this.announceModelSelection(modelData);
            }
        }
    }
    
    announceModelSelection(modelData) {
        // Create temporary announcement for screen readers
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = `Selected ${modelData.name}, ${modelData.tier} tier, ${modelData.cost_breakdown['5_seconds']} for 5 seconds`;
        
        document.body.appendChild(announcement);
        
        // Remove after announcement
        setTimeout(() => {
            if (announcement.parentNode) {
                document.body.removeChild(announcement);
            }
        }, 1000);
    }
    
    createDurationSelect(durationOptions) {
        if (!durationOptions || durationOptions.length <= 1) return null;
        
        const select = document.createElement('select');
        select.id = 'duration';
        select.className = 'w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent';
        
        durationOptions.forEach(duration => {
            const option = document.createElement('option');
            option.value = duration;
            option.textContent = `${duration} seconds`;
            select.appendChild(option);
        });
        
        // Add event listener for cost updates
        select.addEventListener('change', () => this.updateCostDisplay(this.selectedModel));
        
        return select;
    }
    
    updateCostDisplay(modelKey) {
        const modelData = this.modelsData[modelKey];
        const duration = parseInt(document.getElementById('duration').value) || 5;
        
        if (modelData) {
            const cost = duration === 5 ? modelData.cost_5s : 
                        duration === 10 ? modelData.cost_10s : 
                        duration * modelData.cost_per_second;
            
            // Update cost display in the interface
            let costDisplay = document.getElementById('currentCostDisplay');
            if (!costDisplay) {
                costDisplay = document.createElement('div');
                costDisplay.id = 'currentCostDisplay';
                costDisplay.className = 'mt-4 p-3 bg-primary/20 border border-primary/30 rounded-lg text-center';
                
                const generateBtn = document.getElementById('generateBtn');
                generateBtn.parentElement.insertBefore(costDisplay, generateBtn);
            }
            
            costDisplay.innerHTML = `
                <div class="text-sm text-gray-300 mb-1">Estimated Cost</div>
                <div class="text-xl font-bold text-primary">$${cost.toFixed(2)}</div>
                <div class="text-xs text-gray-400">${duration}s • ${modelData.name}</div>
            `;
        }
    }
    
    updateCostCalculator() {
        // This can be enhanced to show cost comparison charts
        console.log('Cost calculator updated');
    }
    
    // ========================================================================
    //                           UX Enhancement Functions                      
    // ========================================================================
    
    updatePromptCount(textarea) {
        const count = textarea.value.length;
        const max = parseInt(textarea.maxLength) || 500;
        const countDisplay = document.getElementById('promptCharCount');
        
        countDisplay.textContent = `${count} / ${max}`;
        
        // Change color based on usage
        if (count > max * 0.9) {
            countDisplay.className = 'text-xs text-red-400';
        } else if (count > max * 0.7) {
            countDisplay.className = 'text-xs text-yellow-400';
        } else {
            countDisplay.className = 'text-xs text-gray-400';
        }
    }
    
    insertPromptSuggestion(button) {
        const promptTextarea = document.getElementById('prompt');
        const suggestion = button.textContent.trim();
        const currentValue = promptTextarea.value.trim();
        
        let newValue;
        if (currentValue === '') {
            newValue = `A beautiful ${suggestion.toLowerCase()}`;
        } else {
            newValue = currentValue + `, ${suggestion.toLowerCase()}`;
        }
        
        promptTextarea.value = newValue;
        this.updatePromptCount(promptTextarea);
        
        // Focus back to textarea
        promptTextarea.focus();
        
        // Visual feedback
        button.classList.add('bg-primary/40');
        setTimeout(() => {
            button.classList.remove('bg-primary/40');
        }, 200);
    }
    
    handleModelKeydown(event, modelKey) {
        const models = Object.keys(this.modelsData || {});
        const currentIndex = models.indexOf(modelKey);
        
        switch(event.key) {
            case 'Enter':
            case ' ':
                event.preventDefault();
                this.selectModel(modelKey);
                break;
            case 'ArrowRight':
            case 'ArrowDown':
                event.preventDefault();
                const nextIndex = (currentIndex + 1) % models.length;
                this.focusModel(models[nextIndex]);
                break;
            case 'ArrowLeft':
            case 'ArrowUp':
                event.preventDefault();
                const prevIndex = (currentIndex - 1 + models.length) % models.length;
                this.focusModel(models[prevIndex]);
                break;
            case 'Home':
                event.preventDefault();
                this.focusModel(models[0]);
                break;
            case 'End':
                event.preventDefault();
                this.focusModel(models[models.length - 1]);
                break;
        }
    }
    
    focusModel(modelKey) {
        const modelCard = document.querySelector(`[data-model="${modelKey}"]`);
        if (modelCard) {
            // Update tabindex
            document.querySelectorAll('.model-card').forEach(card => {
                card.tabIndex = -1;
            });
            modelCard.tabIndex = 0;
            modelCard.focus();
        }
    }
    
    // ========================================================================
    //                           Video Generation                              
    // ========================================================================
    
    async handleGeneration(e) {
        e.preventDefault();
        
        // Validation
        if (this.uploadedFiles.size === 0) {
            this.showToast('Please upload at least one image', 'warning');
            return;
        }
        
        const prompt = document.getElementById('prompt').value.trim();
        if (!prompt) {
            this.showToast('Please enter a prompt', 'warning');
            return;
        }
        
        try {
            const firstFile = this.uploadedFiles.values().next().value;
            const formData = new FormData();
            
            // Basic parameters
            formData.append('model', this.selectedModel);
            formData.append('prompt', prompt);
            formData.append('file_id', firstFile.file_id);
            formData.append('duration', document.getElementById('duration').value);
            formData.append('aspect_ratio', document.getElementById('aspectRatio').value);
            
            // Advanced parameters
            const negativePrompt = document.getElementById('negativePrompt').value.trim();
            if (negativePrompt) {
                formData.append('negative_prompt', negativePrompt);
            }
            
            const cfgScale = document.getElementById('cfgScale').value;
            if (cfgScale !== '0.5') {
                formData.append('cfg_scale', cfgScale);
            }
            
            // Submit generation request
            const response = await fetch('/api/generate', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Generation failed');
            }
            
            const result = await response.json();
            this.currentJobId = result.job_id;
            
            // Show progress
            this.showProgress();
            this.showToast('🎬 Video generation started!', 'success');
            
            // Disable generate button
            const generateBtn = document.getElementById('generateBtn');
            generateBtn.disabled = true;
            generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Generating...';
            
        } catch (error) {
            console.error('Generation error:', error);
            this.showToast(`❌ Generation failed: ${error.message}`, 'error');
        }
    }
    
    handleJobUpdate(jobId, status) {
        if (jobId !== this.currentJobId) return;
        
        this.updateProgress(status);
        
        if (status.status === 'completed') {
            this.handleGenerationComplete(status);
        } else if (status.status === 'failed') {
            this.handleGenerationFailed(status);
        }
    }
    
    updateProgress(status) {
        const container = document.getElementById('progressContainer');
        const idle = document.getElementById('idleMessage');
        const statusEl = document.getElementById('progressStatus');
        const percentEl = document.getElementById('progressPercent');
        const messageEl = document.getElementById('progressMessage');
        const progressBar = document.getElementById('progressBar');
        
        // Show progress container
        container.classList.remove('hidden');
        idle.classList.add('hidden');
        
        // Update content
        statusEl.textContent = this.capitalizeFirst(status.status);
        percentEl.textContent = `${status.progress || 0}%`;
        messageEl.textContent = status.message || 'Processing...';
        progressBar.style.width = `${status.progress || 0}%`;
        
        // Add progress glow effect for active states
        if (status.status === 'processing' || status.status === 'uploading') {
            progressBar.classList.add('progress-glow');
        } else {
            progressBar.classList.remove('progress-glow');
        }
    }
    
    handleGenerationComplete(status) {
        this.stats.generated++;
        this.updateStats();
        
        // Reset generate button
        const generateBtn = document.getElementById('generateBtn');
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<i class="fas fa-magic mr-2"></i>Generate Video';
        
        // Show result
        this.displayResult(status.result);
        
        // Hide progress after a delay
        setTimeout(() => {
            this.hideProgress();
        }, 3000);
        
        this.showToast('🎉 Video generated successfully!', 'success');
    }
    
    handleGenerationFailed(status) {
        // Reset generate button
        const generateBtn = document.getElementById('generateBtn');
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<i class="fas fa-magic mr-2"></i>Generate Video';
        
        // Hide progress
        setTimeout(() => {
            this.hideProgress();
        }, 2000);
        
        this.showToast(`❌ Generation failed: ${status.error || 'Unknown error'}`, 'error');
    }
    
    showProgress() {
        const container = document.getElementById('progressContainer');
        const idle = document.getElementById('idleMessage');
        
        container.classList.remove('hidden');
        idle.classList.add('hidden');
    }
    
    hideProgress() {
        const container = document.getElementById('progressContainer');
        const idle = document.getElementById('idleMessage');
        
        container.classList.add('hidden');
        idle.classList.remove('hidden');
    }
    
    displayResult(result) {
        const container = document.getElementById('resultsContainer');
        const noResults = document.getElementById('noResults');
        
        // Show results container
        container.classList.remove('hidden');
        noResults.classList.add('hidden');
        
        // Create result card
        const resultCard = document.createElement('div');
        resultCard.className = 'result-card p-4 fade-in';
        resultCard.innerHTML = `
            <div class="result-video mb-4">
                <video controls class="w-full h-full rounded-lg" preload="metadata">
                    <source src="${result.video_url || result.video?.url}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            </div>
            
            <div class="text-sm text-gray-400 mb-3">
                Generated: ${new Date().toLocaleString()}
            </div>
            
            <div class="result-actions">
                <button class="result-btn primary" onclick="app.downloadVideo('${result.video_url || result.video?.url}')">
                    <i class="fas fa-download mr-1"></i> Download
                </button>
                <button class="result-btn" onclick="app.shareVideo('${result.video_url || result.video?.url}')">
                    <i class="fas fa-share mr-1"></i> Share
                </button>
                <button class="result-btn" onclick="app.copyVideoUrl('${result.video_url || result.video?.url}')">
                    <i class="fas fa-copy mr-1"></i> Copy URL
                </button>
            </div>
        `;
        
        // Add to top of results
        container.insertBefore(resultCard, container.firstChild);
        
        // Limit to 5 recent results
        const results = container.querySelectorAll('.result-card');
        if (results.length > 5) {
            for (let i = 5; i < results.length; i++) {
                results[i].remove();
            }
        }
    }
    
    // ========================================================================
    //                           Result Actions                               
    // ========================================================================
    
    async downloadVideo(url) {
        try {
            const response = await fetch(url);
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = `fal-video-${Date.now()}.mp4`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            window.URL.revokeObjectURL(downloadUrl);
            this.showToast('Download started', 'success');
            
        } catch (error) {
            console.error('Download error:', error);
            this.showToast('Download failed', 'error');
        }
    }
    
    async shareVideo(url) {
        if (navigator.share) {
            try {
                await navigator.share({
                    title: 'Generated Video',
                    text: 'Check out this video I generated with FAL.AI!',
                    url: url
                });
                this.showToast('Shared successfully', 'success');
            } catch (error) {
                if (error.name !== 'AbortError') {
                    this.copyVideoUrl(url);
                }
            }
        } else {
            this.copyVideoUrl(url);
        }
    }
    
    async copyVideoUrl(url) {
        try {
            await navigator.clipboard.writeText(url);
            this.showToast('URL copied to clipboard', 'success');
        } catch (error) {
            console.error('Copy error:', error);
            this.showToast('Failed to copy URL', 'error');
        }
    }
    
    // ========================================================================
    //                           History Management                            
    // ========================================================================
    
    async showHistory() {
        try {
            const response = await fetch('/api/history');
            const data = await response.json();
            
            this.renderHistory(data.history);
            this.showModal(document.getElementById('historyModal'));
            
        } catch (error) {
            console.error('Failed to load history:', error);
            this.showToast('Failed to load history', 'error');
        }
    }
    
    renderHistory(history) {
        const container = document.getElementById('historyContent');
        
        if (history.length === 0) {
            container.innerHTML = `
                <div class="text-center text-gray-400 py-8">
                    <i class="fas fa-history text-3xl mb-4 opacity-50"></i>
                    <p>No generation history yet</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = history.map(item => `
            <div class="history-item">
                <div class="history-thumbnail">
                    ${item.result?.video_url ? `
                        <video class="w-full h-full object-cover" preload="metadata" muted>
                            <source src="${item.result.video_url}" type="video/mp4">
                        </video>
                    ` : `
                        <div class="w-full h-full bg-gray-800 flex items-center justify-center">
                            <i class="fas fa-video text-gray-600"></i>
                        </div>
                    `}
                </div>
                
                <div class="history-details">
                    <div class="history-title">Video Generation</div>
                    <div class="history-meta">
                        ${new Date(item.timestamp).toLocaleString()} • ${item.status}
                    </div>
                </div>
                
                <div class="history-actions">
                    ${item.result?.video_url ? `
                        <button class="result-btn primary" onclick="app.downloadVideo('${item.result.video_url}')">
                            <i class="fas fa-download"></i>
                        </button>
                    ` : ''}
                </div>
            </div>
        `).join('');
    }
    
    // ========================================================================
    //                           UI Utilities                                 
    // ========================================================================
    
    showModal(modal) {
        modal.classList.remove('hidden');
        modal.classList.add('fade-in');
    }
    
    hideModal(modal) {
        modal.classList.add('hidden');
        modal.classList.remove('fade-in');
    }
    
    showLoadingOverlay(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (show) {
            overlay.classList.remove('hidden');
        } else {
            overlay.classList.add('hidden');
        }
    }
    
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="flex items-center justify-between">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 opacity-70 hover:opacity-100">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }
    
    updateStats() {
        document.getElementById('statsGenerated').textContent = this.stats.generated;
        document.getElementById('statsUploaded').textContent = this.stats.uploaded;
    }
    
    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
}

// Initialize the application
const app = new VideoGeneratorApp();

// Global functions for HTML onclick handlers
window.app = app;