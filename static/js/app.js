/**
 * Markdown Converter - Main Application Logic
 * Handles UI interactions, format selection, authentication, and file conversion workflow
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const dropZone = document.getElementById('dropZone');
  const fileInput = document.getElementById('fileInput');
  const fileNameDisplay = document.getElementById('fileNameDisplay');
  const fileName = document.getElementById('fileName');
  const convertBtn = document.getElementById('convertBtn');
  const convertBtnText = document.getElementById('convertBtnText');
  const progressContainer = document.getElementById('progressContainer');
  const progressBar = document.getElementById('progressBar');
  const progressPercent = document.getElementById('progressPercent');
  const statusMessage = document.getElementById('statusMessage');
  const downloadContainer = document.getElementById('downloadContainer');
  const downloadDocxBtn = document.getElementById('downloadDocx');
  const downloadPdfBtn = document.getElementById('downloadPdf');
  const openGdocsLink = document.getElementById('openGdocs');
  const errorContainer = document.getElementById('errorContainer');
  const errorMessage = document.getElementById('errorMessage');

  // Format selection elements
  const formatCheckboxes = document.querySelectorAll('.format-checkbox');
  const selectionCount = document.getElementById('selection-count');
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

  // ========== Authentication ==========

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

    // Update selection count text
    if (count === 0) {
      selectionCount.textContent = 'No formats selected';
      selectionCount.classList.remove('text-brand-aqua', 'font-medium');
      selectionCount.classList.add('text-gray-600');
    } else {
      const formatText = count === 1 ? 'format' : 'formats';
      selectionCount.textContent = `${count} ${formatText} selected`;
      selectionCount.classList.remove('text-gray-600');
      selectionCount.classList.add('text-brand-aqua', 'font-medium');
    }

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
  gdocsCard.addEventListener('click', (e) => {
    if (gdocsCheckbox.disabled && !isAuthenticated) {
      e.preventDefault();
      if (confirm('Sign in with Google to enable Google Docs conversion?')) {
        window.location.href = '/login/google';
      }
    }
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
    hideDownloads();
    hideProgress();
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
      convertBtn.disabled = true;
      convertBtnText.textContent = 'Converting...';

      // Show progress
      showProgress('Uploading file...');
      hideError();
      hideDownloads();

      // Upload and convert
      const result = await api.convertFile(
        selectedFile,
        selectedFormats,
        (progress) => {
          updateProgress(progress, 'Uploading...');
        }
      );

      // Update UI for successful conversion
      updateProgress(100, 'Conversion complete!');
      currentJobId = result.job_id;

      // Show download buttons after short delay
      setTimeout(() => {
        hideProgress();
        showDownloads(result);
      }, 500);

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

      hideProgress();

    } finally {
      isProcessing = false;
      convertBtn.disabled = false;
      convertBtnText.textContent = 'Convert File';
    }
  });

  // ========== Download Handlers ==========

  downloadDocxBtn.addEventListener('click', () => {
    downloadFile('docx');
  });

  downloadPdfBtn.addEventListener('click', () => {
    downloadFile('pdf');
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

  function showProgress(message) {
    progressContainer.classList.remove('hidden');
    statusMessage.textContent = message;
    updateProgress(0);
  }

  function hideProgress() {
    progressContainer.classList.add('hidden');
  }

  function updateProgress(percent, message = null) {
    const clampedPercent = Math.min(100, Math.max(0, percent));
    progressBar.style.width = `${clampedPercent}%`;
    progressBar.setAttribute('aria-valuenow', clampedPercent);
    progressPercent.textContent = `${Math.round(clampedPercent)}%`;

    if (message) {
      statusMessage.textContent = message;
    }
  }

  function showDownloads(result) {
    downloadContainer.classList.remove('hidden');

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
  }

  function hideDownloads() {
    downloadContainer.classList.add('hidden');
  }

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
    // Escape key - clear selection
    if (e.key === 'Escape') {
      resetFileInput();
      hideError();
      hideDownloads();
      hideProgress();
    }

    // Enter key - convert if file selected
    if (e.key === 'Enter' && selectedFile && !isProcessing && getSelectedFormats().length > 0) {
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
