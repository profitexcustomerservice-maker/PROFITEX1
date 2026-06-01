/**
 * Task Timer and Link Tracking System
 * Handles timer tracking for tasks with images/links
 */

class TaskTimer {
    constructor(submissionId, requiredDuration = 0) {
        this.submissionId = submissionId;
        this.requiredDuration = requiredDuration; // in seconds
        this.timeSpent = 0;
        this.timerInterval = null;
        this.isRunning = false;
        this.startTime = null;
    }

    /**
     * Start the timer
     */
    start() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        this.startTime = Date.now();
        
        this.timerInterval = setInterval(() => {
            this.timeSpent = Math.floor((Date.now() - this.startTime) / 1000);
            this.updateDisplay();
            this.checkMinimumDuration();
        }, 1000);
    }

    /**
     * Stop the timer and save data
     */
    stop() {
        if (!this.isRunning) return;
        
        this.isRunning = false;
        clearInterval(this.timerInterval);
        
        return this.saveTimerData();
    }

    /**
     * Format time to MM:SS format
     */
    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    /**
     * Update timer display on page
     */
    updateDisplay() {
        const display = document.getElementById(`timer-display-${this.submissionId}`);
        if (display) {
            display.textContent = this.formatTime(this.timeSpent);
        }
    }

    /**
     * Check if minimum duration requirement is met
     */
    checkMinimumDuration() {
        const progressBar = document.getElementById(`timer-progress-${this.submissionId}`);
        if (progressBar && this.requiredDuration > 0) {
            const percentage = Math.min((this.timeSpent / this.requiredDuration) * 100, 100);
            progressBar.style.width = percentage + '%';
            progressBar.setAttribute('aria-valuenow', percentage);
            
            // Change color based on progress
            if (percentage < 50) {
                progressBar.className = 'progress-bar bg-danger';
            } else if (percentage < 100) {
                progressBar.className = 'progress-bar bg-warning';
            } else {
                progressBar.className = 'progress-bar bg-success';
            }
        }
    }

    /**
     * Check if minimum duration is met
     */
    isMinimumMet() {
        if (this.requiredDuration === 0) return true;
        return this.timeSpent >= this.requiredDuration;
    }

    /**
     * Save timer data to backend
     */
    async saveTimerData() {
        const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value ||
                         document.querySelector('[name=csrfmiddlewaretoken]')?.content;
        
        try {
            const response = await fetch(`/api/submissions/${this.submissionId}/track_timer/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({
                    time_spent: this.timeSpent,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                console.error('Timer tracking error:', data);
                return {
                    success: false,
                    message: data.detail || 'Failed to save timer data',
                };
            }

            return {
                success: true,
                message: data.message,
                data: data,
            };
        } catch (error) {
            console.error('Error saving timer data:', error);
            return {
                success: false,
                message: 'Error saving timer data',
            };
        }
    }

    /**
     * Get timer status summary
     */
    getStatus() {
        return {
            timeSpent: this.timeSpent,
            requiredDuration: this.requiredDuration,
            isRunning: this.isRunning,
            isMet: this.isMinimumMet(),
            formatted: this.formatTime(this.timeSpent),
            remaining: Math.max(0, this.requiredDuration - this.timeSpent),
        };
    }
}

/**
 * Link tracking helper
 */
class LinkTracker {
    constructor(submissionId) {
        this.submissionId = submissionId;
    }

    /**
     * Track when user opens a link
     */
    async trackLinkOpen(link) {
        const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value ||
                         document.querySelector('[name=csrfmiddlewaretoken]')?.content;
        
        try {
            const response = await fetch(`/api/submissions/${this.submissionId}/track_link_open/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({}),
            });

            const data = await response.json();

            if (!response.ok) {
                console.error('Link tracking error:', data);
                return false;
            }

            // Open link in new window
            if (link) {
                window.open(link, '_blank', 'noopener,noreferrer');
            }

            return true;
        } catch (error) {
            console.error('Error tracking link:', error);
            return false;
        }
    }
}

/**
 * Task thumbnail preview
 */
class TaskPreview {
    constructor(task) {
        this.task = task;
    }

    /**
     * Get thumbnail HTML
     */
    getThumbnailHtml() {
        if (!this.task.media && !this.task.ad_url) {
            return `<div class="task-thumbnail-placeholder bg-light d-flex align-items-center justify-content-center">
                <span class="text-muted">No thumbnail available</span>
            </div>`;
        }

        if (this.task.thumbnail_url) {
            return `<img src="${this.task.thumbnail_url}" class="task-thumbnail" alt="${this.task.title}">`;
        }

        if (this.task.media_type === 'link') {
            return `<div class="task-link-preview bg-light d-flex align-items-center justify-content-center">
                <i class="fas fa-external-link-alt text-muted" style="font-size: 3rem;"></i>
            </div>`;
        }

        return `<div class="task-thumbnail-placeholder bg-light d-flex align-items-center justify-content-center">
            <span class="text-muted">${this.task.media_type || 'Task'}</span>
        </div>`;
    }

    /**
     * Get task action button HTML
     */
    getActionButtonHtml() {
        if (this.task.media_type === 'link' && this.task.ad_url) {
            return `<button class="btn btn-primary btn-block" onclick="openTaskLink('${this.task.ad_url}')">
                <i class="fas fa-external-link-alt"></i> Open Link
            </button>`;
        }

        if (this.task.media_type === 'image') {
            return `<button class="btn btn-primary btn-block" onclick="viewTaskImage()">
                <i class="fas fa-image"></i> View Image
            </button>`;
        }

        return `<button class="btn btn-primary btn-block" onclick="startTask()">
            Start Task
        </button>`;
    }
}

// Export for use in HTML
window.TaskTimer = TaskTimer;
window.LinkTracker = LinkTracker;
window.TaskPreview = TaskPreview;
