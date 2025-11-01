/**
 * Markdown Converter API Client
 * Handles all communication with the Flask backend
 */

class MarkdownConverterAPI {
  constructor(baseURL = '') {
    this.baseURL = baseURL;
  }

  /**
   * Upload and convert markdown file
   * @param {File} file - The markdown file to convert
   * @param {Array<string>|string} formats - Output formats array ['docx', 'pdf', 'gdocs'] or legacy string 'docx', 'pdf', 'both'
   * @param {Function} onProgress - Optional progress callback (percent)
   * @returns {Promise<Object>} - Conversion result with job_id and format URLs
   */
  async convertFile(file, formats = ['docx', 'pdf'], onProgress = null) {
    const formData = new FormData();
    formData.append('file', file);

    // Support both new array format and legacy string format
    if (Array.isArray(formats)) {
      // New style: append each format separately
      formats.forEach(format => {
        formData.append('formats', format);
      });
    } else {
      // Legacy style: single format parameter
      formData.append('format', formats);
    }

    try {
      // Use XMLHttpRequest if progress tracking is needed
      if (onProgress) {
        return await this._uploadWithProgress('/api/convert', formData, onProgress);
      }

      // Use Fetch API for simple uploads
      const response = await fetch(`${this.baseURL}/api/convert`, {
        method: 'POST',
        body: formData
        // Don't set Content-Type - browser sets it with boundary
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));

        // Handle authentication required error
        if (response.status === 401 && errorData.auth_url) {
          const error = new Error(errorData.error || 'Authentication required');
          error.authRequired = true;
          error.authUrl = errorData.auth_url;
          throw error;
        }

        throw new Error(errorData.error || `Server error: ${response.status}`);
      }

      return await response.json();

    } catch (error) {
      console.error('Conversion error:', error);
      throw error;
    }
  }

  /**
   * Upload with progress tracking using XMLHttpRequest
   * @private
   */
  _uploadWithProgress(endpoint, formData, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      // Track upload progress
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percentComplete = Math.round((e.loaded / e.total) * 100);
          onProgress(percentComplete);
        }
      });

      // Handle completion
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve(response);
          } catch (e) {
            reject(new Error('Invalid response from server'));
          }
        } else {
          try {
            const error = JSON.parse(xhr.responseText);
            reject(new Error(error.error || `Upload failed with status ${xhr.status}`));
          } catch (e) {
            reject(new Error(`Upload failed with status ${xhr.status}`));
          }
        }
      });

      // Handle network errors
      xhr.addEventListener('error', () => {
        reject(new Error('Network error occurred. Please check your connection.'));
      });

      // Handle timeout
      xhr.addEventListener('timeout', () => {
        reject(new Error('Request timeout. Please try again.'));
      });

      // Handle abort
      xhr.addEventListener('abort', () => {
        reject(new Error('Upload cancelled'));
      });

      // Configure and send request
      xhr.open('POST', `${this.baseURL}${endpoint}`);
      xhr.timeout = 180000; // 3 minutes timeout
      xhr.send(formData);
    });
  }

  /**
   * Download converted file
   * @param {string} jobId - The job identifier
   * @param {string} format - File format: 'docx' or 'pdf'
   * @param {string} filename - Optional custom filename
   * @returns {Promise<void>}
   */
  async downloadFile(jobId, format, filename = null) {
    try {
      const response = await fetch(`${this.baseURL}/api/download/${jobId}/${format}`);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || 'Download failed');
      }

      // Convert response to blob
      const blob = await response.blob();

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = filename || `converted.${format}`;

      // Trigger download
      document.body.appendChild(a);
      a.click();

      // Cleanup
      setTimeout(() => {
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }, 100);

    } catch (error) {
      console.error('Download error:', error);
      throw error;
    }
  }

  /**
   * Validate file before upload
   * @param {File} file - File to validate
   * @returns {Object} - {valid: boolean, error: string|null}
   */
  validateFile(file) {
    const maxSize = 10 * 1024 * 1024; // 10MB
    const validExtensions = ['.md', '.markdown', '.txt'];

    // Check if file exists
    if (!file) {
      return { valid: false, error: 'No file selected' };
    }

    // Check file extension
    const fileName = file.name.toLowerCase();
    const hasValidExtension = validExtensions.some(ext => fileName.endsWith(ext));

    if (!hasValidExtension) {
      return {
        valid: false,
        error: 'Please upload a .md, .markdown, or .txt file'
      };
    }

    // Check file size
    if (file.size > maxSize) {
      const sizeMB = (maxSize / 1024 / 1024).toFixed(0);
      return {
        valid: false,
        error: `File size must be less than ${sizeMB}MB`
      };
    }

    // Check if file is empty
    if (file.size === 0) {
      return { valid: false, error: 'File is empty' };
    }

    return { valid: true, error: null };
  }

  /**
   * Check authentication status
   * @returns {Promise<Object>} - { authenticated: boolean, user: Object|null }
   */
  async checkAuthStatus() {
    try {
      const response = await fetch(`${this.baseURL}/auth/status`);

      if (!response.ok) {
        console.error('Auth status check failed:', response.status);
        return { authenticated: false, user: null };
      }

      return await response.json();

    } catch (error) {
      console.error('Auth status check error:', error);
      return { authenticated: false, user: null };
    }
  }

  /**
   * Get user-friendly error message
   * @param {Error} error - Error object
   * @returns {string} - User-friendly error message
   */
  getUserFriendlyError(error) {
    const errorMessage = error.message || error.toString();

    // Map technical errors to user-friendly messages
    const errorMappings = {
      'Failed to fetch': 'Unable to connect to server. Please check your internet connection.',
      'NetworkError': 'Network error occurred. Please try again.',
      'Network error': 'Network error occurred. Please check your connection.',
      'Invalid file type': 'Please upload a .md, .markdown, or .txt file.',
      'File too large': 'File is too large. Maximum size is 10MB.',
      'timeout': 'Request timeout. The file might be too large or the server is busy.',
      '413': 'File is too large. Maximum size is 10MB.',
      '404': 'Requested resource not found.',
      '500': 'Server error occurred. Please try again later.',
      '503': 'Service temporarily unavailable. Please try again later.',
    };

    // Check for matching error patterns
    for (const [pattern, message] of Object.entries(errorMappings)) {
      if (errorMessage.toLowerCase().includes(pattern.toLowerCase())) {
        return message;
      }
    }

    // Return original message if no mapping found
    return errorMessage || 'An error occurred. Please try again.';
  }
}

// Export singleton instance (makes it available globally)
const api = new MarkdownConverterAPI();
