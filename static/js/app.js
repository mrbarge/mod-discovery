/**
 * ModPlayer Main Application
 * 
 * Handles daily selection display, rating, and playback
 */

const App = {
    modules: [],
    currentRatingModule: null,
    selectedRating: 0,
    
    async init() {
        console.log('Initializing ModPlayer...');
        await this.loadDailySelection();
        this.setupEventListeners();
    },
    
    async loadDailySelection() {
        const loading = document.getElementById('loading');
        const error = document.getElementById('error');
        const container = document.getElementById('modules-container');
        const dateHeader = document.getElementById('selection-date');
        
        try {
            loading.style.display = 'block';
            error.style.display = 'none';
            container.style.display = 'none';
            
            const response = await fetch('/api/daily');
            if (!response.ok) {
                throw new Error('Failed to load daily selection');
            }
            
            const data = await response.json();
            this.modules = data.modules;
            
            // Update date header
            const date = new Date(data.date);
            dateHeader.textContent = date.toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
            
            // Render modules
            this.renderModules();
            
            loading.style.display = 'none';
            container.style.display = 'block';
            
        } catch (err) {
            console.error('Error loading daily selection:', err);
            loading.style.display = 'none';
            error.style.display = 'block';
        }
    },
    
    renderModules() {
        const container = document.getElementById('modules-container');
        container.innerHTML = '';
        
        this.modules.forEach(module => {
            const card = this.createModuleCard(module);
            container.appendChild(card);
        });
    },
    
    createModuleCard(module) {
        const card = document.createElement('div');
        card.className = 'module-card';
        card.dataset.moduleId = module.id;
        
        // Determine source badge
        const sourceBadges = {
            'recent': '🆕 Recent Upload',
            'rated': '⭐ Highly Rated',
            'favourites': '❤️ Top Favourite',
            'featured': '🌟 Featured',
            'random': '🎲 Random Pick'
        };
        const sourceBadge = sourceBadges[module.source_type] || '🎵 Module';
        
        card.innerHTML = `
            <div class="module-header">
                <div class="module-info">
                    <h3>${this.escapeHtml(module.title || module.filename)}</h3>
                    ${module.artist ? `<p class="artist">by ${this.escapeHtml(module.artist)}</p>` : ''}
                    <p class="filename">${this.escapeHtml(module.filename)}</p>
                </div>
            </div>
            
            <div class="module-meta">
                <span class="meta-badge format">${module.format?.toUpperCase() || 'MOD'}</span>
                <span class="meta-badge">${sourceBadge}</span>
                ${module.size ? `<span class="meta-badge">${this.formatFileSize(module.size)}</span>` : ''}
            </div>
            
            <div class="player-controls">
                <button class="btn btn-primary btn-play" data-module-id="${module.id}">
                    ▶ Play
                </button>
                <button class="btn btn-secondary" onclick="App.openRatingModal(${module.id})">
                    ${module.user_rating ? '✏️ Edit Rating' : '⭐ Rate'}
                </button>
                <a href="${module.modarchive_url}" target="_blank" rel="noopener" class="btn btn-secondary">
                    🔗 Mod Archive
                </a>
            </div>
            
            ${this.renderRating(module.user_rating)}
        `;
        
        return card;
    },
    
    renderRating(rating) {
        if (!rating) {
            return '<p class="text-muted">No rating yet</p>';
        }
        
        const stars = '★'.repeat(rating.rating) + '☆'.repeat(5 - rating.rating);
        
        return `
            <div class="rating-display">
                <div class="stars">
                    ${stars.split('').map(s => `<span class="star ${s === '★' ? 'filled' : ''}">${s}</span>`).join('')}
                </div>
                <span>${rating.rating}/5</span>
            </div>
            ${rating.comment ? `<div class="rating-comment">"${this.escapeHtml(rating.comment)}"</div>` : ''}
        `;
    },
    
    setupEventListeners() {
        // Play/Stop button clicks
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('btn-play')) {
                const moduleId = parseInt(e.target.dataset.moduleId);
                const isCurrentlyPlaying = e.target.textContent.includes('Stop');

                if (isCurrentlyPlaying) {
                    // Stop the currently playing module
                    this.stopModule(e.target);
                } else {
                    // Play the module (always restarts from beginning)
                    this.playModule(moduleId, e.target);
                }
            }
        });
        
        // Rating modal
        const modal = document.getElementById('rating-modal');
        const closeBtn = modal.querySelector('.close');
        const submitBtn = document.getElementById('submit-rating');
        
        closeBtn.onclick = () => this.closeRatingModal();
        window.onclick = (e) => {
            if (e.target === modal) {
                this.closeRatingModal();
            }
        };
        
        // Star rating
        document.querySelectorAll('#rating-modal .star').forEach(star => {
            star.onclick = () => {
                const value = parseInt(star.dataset.value);
                this.selectRating(value);
            };
        });
        
        submitBtn.onclick = () => this.submitRating();
    },
    
    async playModule(moduleId, button) {
        const originalText = button.textContent;
        button.disabled = true;
        button.textContent = '⏳ Loading...';

        try {
            const success = await window.modulePlayer.play(moduleId);
            if (success) {
                this.updatePlayButtons(moduleId);
            }
        } catch (error) {
            console.error('Playback error:', error);
            button.textContent = originalText;
        } finally {
            button.disabled = false;
        }
    },

    stopModule(button) {
        if (window.modulePlayer.stop()) {
            button.textContent = '▶ Play';
            button.disabled = false;
        }
    },

    updatePlayButtons(currentModuleId) {
        // Update all play buttons to reflect current state
        document.querySelectorAll('.btn-play').forEach(btn => {
            const btnModuleId = parseInt(btn.dataset.moduleId);
            if (btnModuleId === currentModuleId) {
                btn.textContent = '⏹ Stop';
            } else {
                btn.textContent = '▶ Play';
                btn.disabled = false;
            }
        });
    },

    handlePlaybackEnd(moduleId) {
        // Reset the play button when playback ends
        console.log('Resetting button state for module', moduleId);
        const button = document.querySelector(`.btn-play[data-module-id="${moduleId}"]`);
        if (button) {
            button.textContent = '▶ Play';
            button.disabled = false;
        }
    },
    
    openRatingModal(moduleId) {
        const module = this.modules.find(m => m.id === moduleId);
        if (!module) return;
        
        this.currentRatingModule = module;
        this.selectedRating = module.user_rating?.rating || 0;
        
        const modal = document.getElementById('rating-modal');
        const title = document.getElementById('modal-module-title');
        const comment = document.getElementById('rating-comment');
        
        title.textContent = module.title || module.filename;
        comment.value = module.user_rating?.comment || '';
        
        this.updateStarDisplay(this.selectedRating);
        
        modal.style.display = 'block';
    },
    
    closeRatingModal() {
        document.getElementById('rating-modal').style.display = 'none';
        this.currentRatingModule = null;
        this.selectedRating = 0;
    },
    
    selectRating(value) {
        this.selectedRating = value;
        this.updateStarDisplay(value);
    },
    
    updateStarDisplay(rating) {
        document.querySelectorAll('#rating-modal .star').forEach((star, index) => {
            if (index < rating) {
                star.textContent = '★';
                star.classList.add('filled');
            } else {
                star.textContent = '☆';
                star.classList.remove('filled');
            }
        });
    },
    
    async submitRating() {
        if (!this.currentRatingModule || this.selectedRating === 0) {
            alert('Please select a rating');
            return;
        }
        
        const comment = document.getElementById('rating-comment').value.trim();
        
        try {
            const response = await fetch('/api/rate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    module_id: this.currentRatingModule.id,
                    rating: this.selectedRating,
                    comment: comment || null
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to save rating');
            }
            
            const data = await response.json();
            
            // Update module in local state
            const module = this.modules.find(m => m.id === this.currentRatingModule.id);
            if (module) {
                module.user_rating = data.rating;
            }
            
            // Re-render modules
            this.renderModules();
            this.setupEventListeners();
            
            this.closeRatingModal();
            
            // Show success message
            this.showNotification('Rating saved successfully!');
            
        } catch (error) {
            console.error('Error saving rating:', error);
            alert('Failed to save rating. Please try again.');
        }
    },
    
    showNotification(message) {
        // Simple notification (could be enhanced with a toast component)
        const notification = document.createElement('div');
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: var(--success);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 0.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 10000;
        `;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    },
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
    
    formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }
};

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => App.init());
} else {
    App.init();
}
