/**
 * History Page
 * 
 * Handles display and filtering of listening history
 */

const History = {
    history: [],
    offset: 0,
    limit: 30,
    hasMore: false,
    searchQuery: '',
    ratingFilter: 'all',
    
    async init() {
        console.log('Initializing History page...');
        await this.loadHistory();
        this.setupEventListeners();
    },
    
    async loadHistory(append = false) {
        const loading = document.getElementById('loading');
        const error = document.getElementById('error');
        const container = document.getElementById('history-container');
        const loadMoreContainer = document.getElementById('load-more-container');
        
        try {
            if (!append) {
                loading.style.display = 'block';
                error.style.display = 'none';
                container.style.display = 'none';
            }
            
            const response = await fetch(`/api/history?limit=${this.limit}&offset=${this.offset}`);
            if (!response.ok) {
                throw new Error('Failed to load history');
            }
            
            const data = await response.json();
            
            if (append) {
                this.history = [...this.history, ...data.history];
            } else {
                this.history = data.history;
            }
            
            this.hasMore = data.has_more;
            
            this.renderHistory();
            
            loading.style.display = 'none';
            container.style.display = 'block';
            
            // Show/hide load more button
            if (this.hasMore) {
                loadMoreContainer.style.display = 'block';
            } else {
                loadMoreContainer.style.display = 'none';
            }
            
        } catch (err) {
            console.error('Error loading history:', err);
            loading.style.display = 'none';
            error.style.display = 'block';
        }
    },
    
    renderHistory() {
        const container = document.getElementById('history-container');
        
        // Filter history
        const filtered = this.filterHistory();
        
        if (filtered.length === 0) {
            container.innerHTML = '<p class="text-muted">No history found matching your filters.</p>';
            return;
        }
        
        container.innerHTML = '';
        
        filtered.forEach(entry => {
            const entryDiv = this.createHistoryEntry(entry);
            container.appendChild(entryDiv);
        });
    },
    
    filterHistory() {
        let filtered = [...this.history];
        
        // Filter by rating
        if (this.ratingFilter !== 'all') {
            filtered = filtered.map(entry => {
                const filteredModules = entry.modules.filter(module => {
                    if (this.ratingFilter === 'rated') {
                        return module.user_rating !== null;
                    } else if (this.ratingFilter === 'unrated') {
                        return module.user_rating === null;
                    } else {
                        const minRating = parseInt(this.ratingFilter);
                        return module.user_rating && module.user_rating.rating >= minRating;
                    }
                });
                
                return {
                    ...entry,
                    modules: filteredModules
                };
            }).filter(entry => entry.modules.length > 0);
        }
        
        // Filter by search query
        if (this.searchQuery) {
            const query = this.searchQuery.toLowerCase();
            filtered = filtered.map(entry => {
                const filteredModules = entry.modules.filter(module => {
                    const title = (module.title || module.filename || '').toLowerCase();
                    const artist = (module.artist || '').toLowerCase();
                    const comment = (module.user_rating?.comment || '').toLowerCase();
                    
                    return title.includes(query) || 
                           artist.includes(query) || 
                           comment.includes(query);
                });
                
                return {
                    ...entry,
                    modules: filteredModules
                };
            }).filter(entry => entry.modules.length > 0);
        }
        
        return filtered;
    },
    
    createHistoryEntry(entry) {
        const entryDiv = document.createElement('div');
        entryDiv.className = 'history-entry';
        
        const date = new Date(entry.date);
        const dateStr = date.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        
        const modulesHtml = entry.modules.map(module => this.createModuleRow(module)).join('');
        
        entryDiv.innerHTML = `
            <h3>${dateStr}</h3>
            <div class="history-modules">
                ${modulesHtml}
            </div>
        `;
        
        return entryDiv;
    },
    
    createModuleRow(module) {
        const stars = module.user_rating 
            ? '★'.repeat(module.user_rating.rating) + '☆'.repeat(5 - module.user_rating.rating)
            : '☆☆☆☆☆';
        
        return `
            <div class="module-card">
                <div class="module-header">
                    <div class="module-info">
                        <h3>${this.escapeHtml(module.title || module.filename)}</h3>
                        ${module.artist ? `<p class="artist">by ${this.escapeHtml(module.artist)}</p>` : ''}
                    </div>
                </div>
                
                <div class="module-meta">
                    <span class="meta-badge format">${module.format?.toUpperCase() || 'MOD'}</span>
                </div>
                
                ${module.user_rating ? `
                    <div class="rating-display">
                        <div class="stars">
                            ${stars.split('').map(s => 
                                `<span class="star ${s === '★' ? 'filled' : ''}">${s}</span>`
                            ).join('')}
                        </div>
                        <span>${module.user_rating.rating}/5</span>
                    </div>
                    ${module.user_rating.comment ? 
                        `<div class="rating-comment">"${this.escapeHtml(module.user_rating.comment)}"</div>` 
                        : ''}
                ` : '<p class="text-muted">Not rated</p>'}
                
                <div class="player-controls">
                    <a href="${module.modarchive_url}" target="_blank" rel="noopener" class="btn btn-secondary">
                        🔗 Mod Archive
                    </a>
                </div>
            </div>
        `;
    },
    
    setupEventListeners() {
        // Search input
        const searchInput = document.getElementById('search-input');
        searchInput.addEventListener('input', (e) => {
            this.searchQuery = e.target.value.trim();
            this.renderHistory();
        });
        
        // Rating filter
        const ratingFilter = document.getElementById('rating-filter');
        ratingFilter.addEventListener('change', (e) => {
            this.ratingFilter = e.target.value;
            this.renderHistory();
        });
        
        // Load more button
        const loadMoreBtn = document.getElementById('load-more-btn');
        loadMoreBtn.addEventListener('click', async () => {
            this.offset += this.limit;
            await this.loadHistory(true);
        });
    },
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => History.init());
} else {
    History.init();
}
