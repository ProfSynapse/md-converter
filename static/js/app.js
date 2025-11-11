/**
 * Markdown Converter - Main Application Logic
 * Handles UI interactions, format selection, authentication, and file conversion workflow
 */

document.addEventListener('DOMContentLoaded', () => {
  // Initialize Lucide icons
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }

  // ========== Screen State Management ==========
  const ScreenState = {
    UPLOAD: 'upload',
    CONVERTING: 'converting',
    RESULTS: 'results'
  };

  let currentScreen = ScreenState.UPLOAD;

  // Screens
  const uploadScreen = document.getElementById('uploadScreen');
  const convertingScreen = document.getElementById('convertingScreen');
  const resultsScreen = document.getElementById('resultsScreen');

  // DOM Elements - Upload Screen
  const dropZone = document.getElementById('dropZone');
  const fileInput = document.getElementById('fileInput');
  const fileNameDisplay = document.getElementById('fileNameDisplay');
  const fileName = document.getElementById('fileName');
  const convertBtn = document.getElementById('convertBtn');
  const convertBtnText = document.getElementById('convertBtnText');

  // DOM Elements - Converting Screen
  const convertingFileName = document.getElementById('convertingFileName');
  const convertingFormats = document.getElementById('convertingFormats');
  const convertingStatusMessage = document.getElementById('convertingStatusMessage');
  const convertingProgressText = document.getElementById('convertingProgressText');
  const convertingProgressPercent = document.getElementById('convertingProgressPercent');
  const convertingProgressBar = document.getElementById('convertingProgressBar');

  // DOM Elements - Results Screen
  const convertAnotherBtn = document.getElementById('convertAnotherBtn');
  const downloadDocxBtn = document.getElementById('downloadDocx');
  const downloadPdfBtn = document.getElementById('downloadPdf');
  const openGdocsLink = document.getElementById('openGdocs');

  // DOM Elements - Global
  const errorContainer = document.getElementById('errorContainer');
  const errorMessage = document.getElementById('errorMessage');

  // Format selection elements
  const formatCheckboxes = document.querySelectorAll('.format-checkbox');
  const gdocsCheckbox = document.getElementById('gdocs-checkbox');
  const gdocsCard = document.getElementById('gdocs-card');
  const gdocsAuthBadge = document.getElementById('gdocs-auth-badge');

  // Authentication elements
  const signInBtn = document.getElementById('signInBtn');
  const userProfile = document.getElementById('userProfile');
  const userName = document.getElementById('userName');
  const userPicture = document.getElementById('userPicture');

  // Application State
  let selectedFile = null;
  let currentJobId = null;
  let isProcessing = false;
  let isAuthenticated = false;
  let currentUser = null;

  // ========== Screen Transition Functions ==========

  /**
   * Show a specific screen and hide others
   * @param {string} screen - One of ScreenState values
   */
  function showScreen(screen) {
    // Hide all screens first
    uploadScreen.classList.add('hidden');
    convertingScreen.classList.add('hidden');
    resultsScreen.classList.add('hidden');

    // Show the requested screen with animation
    switch (screen) {
      case ScreenState.UPLOAD:
        uploadScreen.classList.remove('hidden');
        uploadScreen.classList.add('fade-in');
        currentScreen = ScreenState.UPLOAD;
        break;
      case ScreenState.CONVERTING:
        convertingScreen.classList.remove('hidden');
        convertingScreen.classList.add('fade-in');
        currentScreen = ScreenState.CONVERTING;
        break;
      case ScreenState.RESULTS:
        resultsScreen.classList.remove('hidden');
        resultsScreen.classList.add('fade-in');
        currentScreen = ScreenState.RESULTS;
        break;
    }

    // Scroll to top smoothly
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  /**
   * Reset to upload screen and clear state
   */
  function resetToUpload() {
    selectedFile = null;
    currentJobId = null;
    isProcessing = false;
    fileInput.value = '';
    fileNameDisplay.classList.add('hidden');

    // Uncheck all format checkboxes
    formatCheckboxes.forEach(checkbox => {
      checkbox.checked = false;
    });

    updateSelectionCount();
    hideError();
    showScreen(ScreenState.UPLOAD);
  }

  // Make resetToUpload globally accessible for the home button
  window.resetToUpload = resetToUpload;

  // ========== Authentication ==========

  /**
   * Save file and format state to sessionStorage before OAuth redirect
   */
  async function saveStateBeforeOAuth() {
    if (selectedFile) {
      try {
        // Read file content as base64
        const reader = new FileReader();
        const fileContent = await new Promise((resolve, reject) => {
          reader.onload = (e) => resolve(e.target.result);
          reader.onerror = reject;
          reader.readAsDataURL(selectedFile);
        });

        // Get selected formats
        const selectedFormats = getSelectedFormats();

        // Save state
        const state = {
          fileName: selectedFile.name,
          fileType: selectedFile.type,
          fileSize: selectedFile.size,
          fileContent: fileContent, // base64 data URL
          selectedFormats: selectedFormats,
          timestamp: Date.now()
        };
        sessionStorage.setItem('mdconverter_oauth_state', JSON.stringify(state));
      } catch (error) {
        console.error('Failed to save state:', error);
        // Continue with OAuth even if save fails
      }
    }
  }

  /**
   * Restore state after OAuth redirect (if available)
   */
  function restoreStateAfterOAuth() {
    const savedState = sessionStorage.getItem('mdconverter_oauth_state');
    if (savedState) {
      try {
        const state = JSON.parse(savedState);
        // Check if state is recent (within 5 minutes)
        const ageMs = Date.now() - state.timestamp;
        if (ageMs < 5 * 60 * 1000 && state.fileContent) {
          // Recreate the File object from saved content
          fetch(state.fileContent)
            .then(res => res.blob())
            .then(blob => {
              const file = new File([blob], state.fileName, {
                type: state.fileType || 'text/markdown'
              });

              // Restore the file
              selectedFile = file;
              fileName.textContent = file.name;
              fileNameDisplay.classList.remove('hidden');

              // Restore format selections
              if (state.selectedFormats && state.selectedFormats.length > 0) {
                formatCheckboxes.forEach(checkbox => {
                  checkbox.checked = state.selectedFormats.includes(checkbox.value);
                });
              }

              // Update UI
              updateSelectionCount();

              // Show success message
              const formatNames = {
                'docx': 'Word',
                'pdf': 'PDF',
                'gdocs': 'Google Docs'
              };
              const formatList = (state.selectedFormats || []).map(f => formatNames[f] || f).join(', ');
              const message = formatList
                ? `File restored! Ready to convert to ${formatList}.`
                : `File restored! Select your output formats.`;

              showError(message);
              setTimeout(() => hideError(), 5000);
            })
            .catch(err => {
              console.error('Failed to restore file:', err);
            });
        }
      } catch (e) {
        console.error('Failed to restore state:', e);
      }
      // Clear the saved state
      sessionStorage.removeItem('mdconverter_oauth_state');
    }
  }

  /**
   * Check authentication status on page load
   */
  async function checkAuthStatus() {
    try {
      const authStatus = await api.checkAuthStatus();
      isAuthenticated = authStatus.authenticated;
      currentUser = authStatus.user;

      updateAuthUI();
      updateGoogleDocsAvailability();

      // If user just authenticated, restore their previous state
      if (isAuthenticated) {
        restoreStateAfterOAuth();
      }

    } catch (error) {
      console.error('Failed to check auth status:', error);
      // Assume not authenticated on error
      isAuthenticated = false;
      currentUser = null;
      updateAuthUI();
      updateGoogleDocsAvailability();
    }
  }

  /**
   * Update authentication UI based on current state
   */
  function updateAuthUI() {
    if (isAuthenticated && currentUser) {
      // Show user profile
      signInBtn.classList.add('hidden');
      userProfile.classList.remove('hidden');

      userName.textContent = currentUser.name || currentUser.email || 'User';
      if (currentUser.picture) {
        userPicture.src = currentUser.picture;
        userPicture.alt = `${currentUser.name || 'User'} profile picture`;
      }
    } else {
      // Show sign in button
      signInBtn.classList.remove('hidden');
      userProfile.classList.add('hidden');
    }
  }

  /**
   * Enable/disable Google Docs option based on authentication
   */
  function updateGoogleDocsAvailability() {
    if (isAuthenticated) {
      // Enable Google Docs option
      gdocsCheckbox.disabled = false;
      gdocsCard.classList.remove('opacity-50', 'cursor-not-allowed');
      gdocsCard.classList.add('cursor-pointer');
      gdocsAuthBadge.classList.add('hidden');
    } else {
      // Disable Google Docs option
      gdocsCheckbox.disabled = true;
      gdocsCheckbox.checked = false;
      gdocsCard.classList.add('opacity-50', 'cursor-not-allowed');
      gdocsCard.classList.remove('cursor-pointer');
      gdocsAuthBadge.classList.remove('hidden');

      // Update selection count if Google Docs was selected
      updateSelectionCount();
    }
  }

  // ========== Format Selection ==========

  /**
   * Update selection count and button state
   */
  function updateSelectionCount() {
    const selectedFormats = getSelectedFormats();
    const count = selectedFormats.length;

    // Enable/disable convert button
    convertBtn.disabled = !selectedFile || count === 0 || isProcessing;
  }

  /**
   * Get array of selected format values
   * @returns {Array<string>}
   */
  function getSelectedFormats() {
    return Array.from(formatCheckboxes)
      .filter(checkbox => checkbox.checked && !checkbox.disabled)
      .map(checkbox => checkbox.value);
  }

  // Add change listeners to all format checkboxes
  formatCheckboxes.forEach(checkbox => {
    checkbox.addEventListener('change', updateSelectionCount);
  });

  // Handle click on disabled Google Docs card
  gdocsCard.addEventListener('click', async (e) => {
    if (gdocsCheckbox.disabled && !isAuthenticated) {
      e.preventDefault();
      // Save current state before redirect
      await saveStateBeforeOAuth();
      // Redirect to OAuth flow
      window.location.href = '/login/google';
    }
  });

  // Handle click on Sign In button
  signInBtn.addEventListener('click', async (e) => {
    e.preventDefault();
    // Save current state before redirect
    await saveStateBeforeOAuth();
    // Redirect to OAuth flow
    window.location.href = '/login/google';
  });

  // ========== Drag and Drop Handlers ==========

  // Prevent default drag behaviors globally
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
  });

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  // Highlight drop zone when dragging over it
  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => {
      dropZone.classList.add('drag-over');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => {
      dropZone.classList.remove('drag-over');
    }, false);
  });

  // Handle dropped files
  dropZone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    handleFiles(files);
  }, false);

  // ========== Click to Upload ==========

  dropZone.addEventListener('click', () => {
    fileInput.click();
  });

  fileInput.addEventListener('change', (e) => {
    handleFiles(e.target.files);
  });

  // ========== File Handling ==========

  function handleFiles(files) {
    if (files.length === 0) return;

    const file = files[0];

    // Validate file
    const validation = api.validateFile(file);
    if (!validation.valid) {
      showError(validation.error);
      resetFileInput();
      return;
    }

    // Store selected file
    selectedFile = file;

    // Update UI
    fileName.textContent = file.name;
    fileNameDisplay.classList.remove('hidden');
    updateSelectionCount();
    hideError();
  }

  function resetFileInput() {
    selectedFile = null;
    fileInput.value = '';
    fileNameDisplay.classList.add('hidden');
    updateSelectionCount();
  }

  // ========== Conversion ==========

  convertBtn.addEventListener('click', async () => {
    if (!selectedFile || isProcessing) return;

    const selectedFormats = getSelectedFormats();
    if (selectedFormats.length === 0) {
      showError('Please select at least one output format');
      return;
    }

    try {
      isProcessing = true;
      hideError();

      // Transition to converting screen
      showConvertingScreen(selectedFile.name, selectedFormats);

      // Upload and convert
      const result = await api.convertFile(
        selectedFile,
        selectedFormats,
        (progress) => {
          updateConvertingProgress(progress, 'Uploading...');
        }
      );

      // Update progress to complete
      updateConvertingProgress(100, 'Conversion complete!');
      currentJobId = result.job_id;

      // Wait a moment then transition to results screen
      setTimeout(() => {
        showResultsScreen(result);
      }, 800);

    } catch (error) {
      console.error('Conversion error:', error);

      // Handle authentication required error
      if (error.authRequired) {
        showError('Google Docs conversion requires authentication. Please sign in.');
        if (confirm('Sign in with Google now?')) {
          window.location.href = error.authUrl || '/auth/google';
        }
      } else {
        const friendlyError = api.getUserFriendlyError(error);
        showError(friendlyError);
      }

      // Return to upload screen on error
      isProcessing = false;
      showScreen(ScreenState.UPLOAD);

    } finally {
      isProcessing = false;
    }
  });

  /**
   * Show the converting screen with file info
   */
  function showConvertingScreen(filename, formats) {
    // Set file name
    convertingFileName.textContent = filename;

    // Format the formats list nicely
    const formatNames = {
      'docx': 'Word',
      'pdf': 'PDF',
      'gdocs': 'Google Docs'
    };
    const formatList = formats.map(f => formatNames[f] || f).join(', ');
    convertingFormats.textContent = formatList;

    // Reset progress
    updateConvertingProgress(0, 'Uploading...');

    // Show converting screen
    showScreen(ScreenState.CONVERTING);
  }

  /**
   * Update progress on converting screen
   */
  function updateConvertingProgress(percent, message = null) {
    const clampedPercent = Math.min(100, Math.max(0, percent));
    convertingProgressBar.style.width = `${clampedPercent}%`;
    convertingProgressBar.setAttribute('aria-valuenow', clampedPercent);
    convertingProgressPercent.textContent = `${Math.round(clampedPercent)}%`;

    if (message) {
      convertingProgressText.textContent = message;
      convertingStatusMessage.textContent = message;
    }
  }

  /**
   * Show the results screen with download buttons
   */
  function showResultsScreen(result) {
    // Hide all download buttons initially
    downloadDocxBtn.classList.add('hidden');
    downloadPdfBtn.classList.add('hidden');
    openGdocsLink.classList.add('hidden');

    // Show buttons based on conversion results
    if (result.formats) {
      // Multi-format response (new style)
      if (result.formats.docx) {
        downloadDocxBtn.classList.remove('hidden');
      }

      if (result.formats.pdf) {
        downloadPdfBtn.classList.remove('hidden');
      }

      if (result.formats.gdocs) {
        openGdocsLink.classList.remove('hidden');
        openGdocsLink.href = result.formats.gdocs.web_view_link;
      }
    } else {
      // Legacy single format response - show both buttons
      downloadDocxBtn.classList.remove('hidden');
      downloadPdfBtn.classList.remove('hidden');
    }

    // Show results screen
    showScreen(ScreenState.RESULTS);
  }

  // ========== Download Handlers ==========

  downloadDocxBtn.addEventListener('click', () => {
    downloadFile('docx');
  });

  downloadPdfBtn.addEventListener('click', () => {
    downloadFile('pdf');
  });

  // Convert Another button handler
  convertAnotherBtn.addEventListener('click', () => {
    resetToUpload();
  });

  async function downloadFile(format) {
    if (!currentJobId) return;

    try {
      // Get base filename without extension
      const baseFilename = selectedFile.name.replace(/\.(md|markdown|txt)$/i, '');
      const downloadFilename = `${baseFilename}.${format}`;

      // Show loading state
      const btn = format === 'docx' ? downloadDocxBtn : downloadPdfBtn;
      const originalText = btn.innerHTML;
      btn.innerHTML = `
        <svg class="animate-spin h-5 w-5 mr-2 inline" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        Downloading...
      `;
      btn.disabled = true;

      // Download file
      await api.downloadFile(currentJobId, format, downloadFilename);

      // Reset button
      setTimeout(() => {
        btn.innerHTML = originalText;
        btn.disabled = false;
      }, 1000);

    } catch (error) {
      console.error('Download error:', error);
      const friendlyError = api.getUserFriendlyError(error);
      showError(`Download failed: ${friendlyError}`);

      // Reset button
      const btn = format === 'docx' ? downloadDocxBtn : downloadPdfBtn;
      btn.disabled = false;
    }
  }

  // ========== UI Helper Functions ==========

  function showError(message) {
    errorContainer.classList.remove('hidden');
    errorMessage.textContent = message;

    // Auto-hide after 10 seconds
    setTimeout(() => {
      hideError();
    }, 10000);
  }

  // Make hideError globally accessible for the close button
  window.hideError = function() {
    errorContainer.classList.add('hidden');
  };

  // ========== Keyboard Shortcuts ==========

  document.addEventListener('keydown', (e) => {
    // Escape key - depends on current screen
    if (e.key === 'Escape') {
      if (currentScreen === ScreenState.UPLOAD) {
        resetFileInput();
        hideError();
      } else if (currentScreen === ScreenState.RESULTS) {
        resetToUpload();
      }
      // Don't allow escape during conversion
    }

    // Enter key - convert if on upload screen with file selected
    if (e.key === 'Enter' && currentScreen === ScreenState.UPLOAD && selectedFile && !isProcessing && getSelectedFormats().length > 0) {
      convertBtn.click();
    }
  });

  // ========== Accessibility ==========

  // Make drop zone keyboard accessible
  dropZone.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      fileInput.click();
    }
  });

  // ========== Initialization ==========

  console.log('Markdown Converter initialized');

  // Check authentication status on page load
  checkAuthStatus();

  // Set initial selection count
  updateSelectionCount();
});
