/**
 * Module Player
 * 
 * Handles playback of module files using chiptune2.js
 */

class ModulePlayer {
    constructor() {
        this.player = null;
        this.currentModule = null;
        this.isPlaying = false;
        this.isLoading = false;
        this.initPromise = null;

        // Defer initialization to ensure libopenmpt is loaded
        this.initPromise = this.initPlayer();
    }

    async initPlayer() {
        // Wait for libopenmpt to be ready (ModArchive pattern)
        console.log('Waiting for libopenmpt to initialize...');
        return new Promise((resolve) => {
            const tryInitialize = () => {
                try {
                    // Check if ChiptuneJsPlayer is available (loaded from chiptune2.js)
                    if (typeof ChiptuneJsPlayer === 'undefined') {
                        console.log('ChiptuneJsPlayer not yet loaded, waiting...');
                        setTimeout(tryInitialize, 100);
                        return;
                    }

                    // Check if libopenmpt runtime is ready
                    if (typeof libopenmpt !== 'undefined' && libopenmpt.calledRun) {
                        console.log('libopenmpt runtime already initialized');
                        this.player = new ChiptuneJsPlayer(new ChiptuneJsConfig(-1));
                        console.log('✓ Module player initialized successfully!');
                        resolve(true);
                        return;
                    }

                    // If libopenmpt exists but not initialized, set up callback
                    if (typeof libopenmpt !== 'undefined') {
                        console.log('Setting up libopenmpt initialization callback');
                        libopenmpt.onRuntimeInitialized = () => {
                            console.log('libopenmpt runtime initialized via callback');
                            try {
                                this.player = new ChiptuneJsPlayer(new ChiptuneJsConfig(-1));
                                console.log('✓ Module player initialized successfully!');
                                resolve(true);
                            } catch (error) {
                                console.error('Failed to initialize player:', error);
                                console.warn('Module playback will use fallback (download only)');
                                resolve(false);
                            }
                        };
                        return;
                    }

                    // libopenmpt not loaded yet, try again
                    console.log('libopenmpt not yet available, retrying...');
                    setTimeout(tryInitialize, 100);
                } catch (error) {
                    console.error('Error during player initialization:', error);
                    resolve(false);
                }
            };

            tryInitialize();
        });
    }
    
    async play(moduleId) {
        if (this.isLoading) {
            console.log('Already loading a module');
            return false;
        }

        // Wait for player to initialize
        await this.initPromise;

        // If already playing this module, just resume
        if (this.currentModule === moduleId && this.isPlaying) {
            return true;
        }

        // If playing different module, stop it first
        if (this.isPlaying) {
            this.stop();
        }

        this.isLoading = true;

        try {
            // Fetch module file
            const response = await fetch(`/api/module/${moduleId}/download`);
            if (!response.ok) {
                throw new Error('Failed to download module');
            }

            const buffer = await response.arrayBuffer();
            console.log(`Downloaded module ${moduleId}, size: ${buffer.byteLength} bytes`);

            // Play using chiptune2.js if available
            if (this.player && this.player.play) {
                console.log('Playing buffer...');

                // Unlock audio context on first user interaction
                if (this.player.touchLocked && this.player.unlock) {
                    console.log('Unlocking audio context...');
                    this.player.unlock();
                }

                // Resume audio context if suspended (required by modern browsers)
                if (this.player.context && this.player.context.state === 'suspended') {
                    console.log('Resuming audio context...');
                    await this.player.context.resume();
                    console.log('Audio context state:', this.player.context.state);
                }

                this.player.play(buffer);
                this.currentModule = moduleId;
                this.isPlaying = true;
                console.log(`✓ Playing module ${moduleId}`);
                return true;
            } else {
                // Fallback: trigger download
                console.log('Player not available, triggering download');
                const blob = new Blob([buffer], { type: 'application/octet-stream' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `module_${moduleId}.mod`;
                a.click();
                URL.revokeObjectURL(url);
                return false;
            }
        } catch (error) {
            console.error('Error playing module:', error);
            alert('Failed to play module. Please try again.');
            return false;
        } finally {
            this.isLoading = false;
        }
    }
    
    pause() {
        if (this.player && this.player.currentPlayingNode && this.isPlaying) {
            this.player.currentPlayingNode.pause();
            this.isPlaying = false;
            console.log('Playback paused');
            return true;
        }
        return false;
    }

    resume() {
        if (this.player && this.player.currentPlayingNode && !this.isPlaying && this.currentModule) {
            this.player.currentPlayingNode.unpause();
            this.isPlaying = true;
            console.log('Playback resumed');
            return true;
        }
        return false;
    }

    stop() {
        if (this.player && this.player.stop) {
            this.player.stop();
            this.isPlaying = false;
            this.currentModule = null;
            console.log('Playback stopped');
            return true;
        }
        return false;
    }
    
    isPlayingModule(moduleId) {
        return this.currentModule === moduleId && this.isPlaying;
    }
}

// Create global player instance
window.modulePlayer = new ModulePlayer();
