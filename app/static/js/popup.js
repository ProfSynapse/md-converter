/**
 * CTA Popup Component
 * Handles the AI Readiness Assessment popup on the results screen
 */

class CTAPopup {
  constructor() {
    this.popup = document.getElementById('ctaPopup');
    this.closeBtn = document.getElementById('ctaCloseBtn');
    this.actionBtn = document.getElementById('ctaActionBtn');
    this.hasBeenShown = false;
    this.dismissTimeout = null;

    this.init();
  }

  init() {
    // Check if already dismissed this session
    if (sessionStorage.getItem('ctaPopupDismissed') === 'true') {
      return;
    }

    // Setup event listeners
    if (this.closeBtn) {
      this.closeBtn.addEventListener('click', () => this.dismiss());
    }

    if (this.actionBtn) {
      this.actionBtn.addEventListener('click', () => this.handleCTAClick());
    }

    // Setup trigger to show on results screen
    this.setupTrigger();
  }

  setupTrigger() {
    // Create a MutationObserver to watch for results screen visibility
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
          const resultsScreen = document.getElementById('resultsScreen');

          // Check if results screen is visible (doesn't have 'hidden' class)
          if (resultsScreen && !resultsScreen.classList.contains('hidden')) {
            // Wait 2 seconds after results screen appears, then show popup
            setTimeout(() => {
              if (!resultsScreen.classList.contains('hidden') && !this.hasBeenShown) {
                this.show();
              }
            }, 2000);
          }
        }
      });
    });

    // Observe the results screen for class changes
    const resultsScreen = document.getElementById('resultsScreen');
    if (resultsScreen) {
      observer.observe(resultsScreen, {
        attributes: true,
        attributeFilter: ['class']
      });
    }
  }

  show() {
    if (this.hasBeenShown) return;

    this.hasBeenShown = true;
    this.popup.classList.remove('hidden');
    this.popup.classList.add('popup-show');

    // Initialize icons for popup
    if (typeof lucide !== 'undefined') {
      lucide.createIcons();
    }

    // Auto-dismiss after 20 seconds
    this.dismissTimeout = setTimeout(() => {
      this.hide();
    }, 20000);
  }

  hide() {
    this.popup.classList.add('popup-hide');

    setTimeout(() => {
      this.popup.classList.add('hidden');
      this.popup.classList.remove('popup-show', 'popup-hide');
    }, 300); // Match animation duration

    if (this.dismissTimeout) {
      clearTimeout(this.dismissTimeout);
    }
  }

  dismiss() {
    this.hide();
    sessionStorage.setItem('ctaPopupDismissed', 'true');
  }

  handleCTAClick() {
    // Open AI readiness assessment
    window.open('https://ai-readiness.synapticlabs.ai', '_blank', 'noopener,noreferrer');
    this.dismiss();
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new CTAPopup();
});
