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
                        // Use 0 for no repeat (play once) instead of -1 (infinite loop)
                        this.player = new ChiptuneJsPlayer(new ChiptuneJsConfig(0));
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
                                // Use 0 for no repeat (play once) instead of -1 (infinite loop)
                                this.player = new ChiptuneJsPlayer(new ChiptuneJsConfig(0));
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

        // Always stop any current playback first
        if (this.isPlaying || this.currentModule) {
            this.stop();
        }

        this.isLoading = true;
        this.currentModule = moduleId;

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
                this.isPlaying = true;
                console.log(`✓ Playing module ${moduleId}`);

                // Monitor playback state to detect when it ends
                this.monitorPlayback();

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

    stop() {
        if (this.player && this.player.stop) {
            this.player.stop();
            this.isPlaying = false;
            this.currentModule = null;

            // Stop monitoring
            if (this.monitorInterval) {
                clearInterval(this.monitorInterval);
                this.monitorInterval = null;
            }

            console.log('Playback stopped');
            return true;
        }
        return false;
    }

    monitorPlayback() {
        // Clear any existing monitor
        if (this.monitorInterval) {
            clearInterval(this.monitorInterval);
        }

        // Reset position tracking
        this.lastPosition = 0;

        // Poll every 500ms to check if playback has ended
        this.monitorInterval = setInterval(() => {
            if (!this.isPlaying) {
                clearInterval(this.monitorInterval);
                this.monitorInterval = null;
                return;
            }

            // Check if the player is still valid
            if (!this.player || !this.player.currentPlayingNode) {
                clearInterval(this.monitorInterval);
                this.monitorInterval = null;
                return;
            }

            // Check if the audio source has finished
            try {
                const position = this.getPosition();
                if (position === 0 && this.lastPosition > 0) {
                    // Song ended, stop it
                    console.log('Module playback ended');
                    this.handlePlaybackEnd();
                }
                this.lastPosition = position;
            } catch (e) {
                // Error accessing node means it probably ended
                console.log('Playback monitoring error (likely ended):', e);
                this.handlePlaybackEnd();
            }
        }, 500);
    }

    handlePlaybackEnd() {
        console.log('Handling playback end');
        const endedModuleId = this.currentModule;

        // Stop playback
        this.stop();

        // Notify the app that playback ended
        if (window.App && window.App.handlePlaybackEnd) {
            window.App.handlePlaybackEnd(endedModuleId);
        }
    }

    getPosition() {
        if (this.player && this.player.currentPlayingNode && this.player.currentPlayingNode.position) {
            return this.player.currentPlayingNode.position();
        }
        return 0;
    }

    isPlayingModule(moduleId) {
        return this.currentModule === moduleId && this.isPlaying;
    }
}

// Create global player instance
window.modulePlayer = new ModulePlayer();
