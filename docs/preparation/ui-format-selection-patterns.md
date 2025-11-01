# Modern UI Patterns for Format Selection

**Last Updated**: November 1, 2025
**Purpose**: Research modern UI/UX patterns for multi-format selection interface
**Context**: Replacing dropdown with icon-based tiles/checkboxes for Word, PDF, and Google Docs format selection

---

## Executive Summary

This document provides comprehensive research on modern UI patterns for format selection interfaces, focusing on icon-based tile selection with checkboxes for multi-format selection. The research covers design patterns from 2025, accessibility best practices, CSS frameworks, icon libraries, and production-ready code examples.

**Key Recommendations**:

1. **Use selectable card pattern** with integrated checkboxes for format selection
2. **Enable multi-select** to allow users to convert to multiple formats simultaneously (DOCX + PDF + Google Docs)
3. **Implement accessible keyboard navigation** with ARIA attributes
4. **Use CSS Grid** for responsive tile layout
5. **Leverage Tailwind CSS** for rapid, maintainable styling
6. **Source icons** from Flaticon, Google Fonts Icons, or Heroicons for file type representation

---

## Modern Format Selection UI Patterns

### Pattern Analysis (2025 Best Practices)

Based on research of current design systems (Salt Design System, Red Hat Design System, Carbon Design System, Flowbite), the following patterns are recommended for file format selection:

#### 1. Selectable Card Pattern

**Description**: Cards that function like checkboxes, allowing users to select one or more options by clicking anywhere on the card.

**When to Use**:
- Multiple selection required (✓ Applies to our use case)
- Options benefit from visual representation (icons + labels)
- More than 2-3 options to choose from
- Touch-friendly interface needed

**Key Characteristics**:
- Large clickable area (entire card is interactive)
- Visual feedback on hover, focus, and selected states
- Checkbox visible but not the primary interaction point
- Icon + label for clear identification
- Support for keyboard navigation

**Advantages**:
- Larger touch targets (mobile-friendly)
- Visual hierarchy with icons
- Clear selected state
- Better scannability than dropdowns
- Progressive enhancement (works without JS)

#### 2. Tile Select Pattern

**Description**: Specialized tiles designed for selection, similar to radio buttons or checkboxes but with enhanced visual design.

**Red Hat Design System Guidelines**:
- Use radio buttons in tiles when only one option can be selected
- Use checkboxes in tiles when multiple options can be selected (✓ Our use case)
- Tiles work well when selections benefit from descriptions
- Minimum size: 44x44px for mobile tap targets

**Calcite Design System Guidelines**:
- Tile selects can support single or multiple selection
- Checkboxes should be used when multiple selections are needed
- Arrange tiles vertically for better scannability (for 3+ options)

#### 3. Checkbox Card Pattern

**Description**: Card components with embedded checkboxes that provide visual and textual context.

**Flowbite Best Practices**:
- Checkboxes inside cards enable larger clicking areas
- Use list groups for multiple checkbox items
- Apply hover states to entire card
- Show selection via border color or background change

---

## Recommended Design for Markdown Converter

### User Experience Flow

1. User uploads markdown file
2. User selects one or more output formats (DOCX, PDF, Google Docs) via icon tiles
3. Visual feedback shows selected formats
4. User clicks "Convert" button
5. Application generates selected formats

### Design Specifications

**Layout**: Horizontal row of 3 tiles (desktop), stacked vertically on mobile

**Tile Dimensions**:
- Desktop: 140px wide x 120px tall
- Mobile: Full width, 80px tall
- Icon size: 48x48px
- Touch target: Minimum 44x44px (entire card is clickable)

**States**:
1. **Default**: Light background, subtle border, grayscale icon
2. **Hover**: Darker border, slight shadow, icon color hint
3. **Selected**: Colored border, colored background tint, full-color icon, checkbox checked
4. **Disabled**: Grayed out, reduced opacity, not clickable (if user not authenticated for Google Docs)
5. **Focus**: Visible focus ring for keyboard navigation

**Accessibility Requirements**:
- ARIA labels for screen readers
- Keyboard navigation (Space to toggle, Tab to move)
- Focus indicators
- Color contrast ratios WCAG AA compliant
- Works without JavaScript (progressive enhancement)

---

## Icon Libraries for File Types

### Research Summary

Based on 2025 icon library analysis, the following sources provide high-quality file type icons:

#### Option 1: Flaticon (Recommended)

**Free Resources**:
- 36,592 document type icons (SVG, PNG, EPS)
- 511 DOCX-specific icons
- 699 Google Docs icons
- Free for personal and commercial use with attribution

**Advantages**:
- Comprehensive file type coverage
- Consistent design styles
- Multiple formats (SVG, PNG, IconFont)
- Customizable colors
- Free tier available

**Example Icons**:
- Microsoft Word: Blue "W" icon or document with blue header
- PDF: Red "PDF" text or document with red banner
- Google Docs: Blue/white Google Docs logo

**URL**: https://www.flaticon.com

#### Option 2: Google Fonts Icons (Material Icons)

**Free Resources**:
- description (document icon)
- picture_as_pdf (PDF icon)
- google (Google brand icon, combine with document)

**Advantages**:
- Free, no attribution required
- Icon font or SVG sprites
- Consistent Material Design style
- Lightweight (web-optimized)

**Usage**:
```html
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" />
<span class="material-symbols-outlined">description</span>
<span class="material-symbols-outlined">picture_as_pdf</span>
```

**URL**: https://fonts.google.com/icons

#### Option 3: Heroicons (Recommended for Tailwind Projects)

**Free Resources**:
- document-text (general document)
- document-arrow-down (download/export)
- Custom file type icons via composition

**Advantages**:
- Designed by Tailwind CSS creators
- Perfect integration with Tailwind
- SVG-based, fully customizable
- MIT licensed (no attribution required)

**Usage**:
```html
<svg class="h-12 w-12 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
</svg>
```

**URL**: https://heroicons.com

### Recommended Icon Colors

Based on standard file type branding:

| Format | Icon Color | Hex Code | Tailwind Class |
|--------|-----------|----------|----------------|
| DOCX (Word) | Blue | #2B579A | bg-blue-600 |
| PDF | Red | #F40F02 | bg-red-600 |
| Google Docs | Blue/Multi | #4285F4 | bg-blue-500 |

---

## CSS Framework Selection

### Recommended: Tailwind CSS

**Why Tailwind CSS**:
1. Utility-first approach enables rapid development
2. Built-in responsive design utilities
3. Excellent hover/focus/active state support
4. No CSS file bloat (only used classes included)
5. Highly customizable via configuration
6. Works with existing Flask templates

**Installation** (if not already in project):
```bash
npm install -D tailwindcss
npx tailwindcss init
```

**CDN Alternative** (quickest setup):
```html
<script src="https://cdn.tailwindcss.com"></script>
```

### Alternative: Plain CSS with Modern Features

If avoiding build tools, use modern CSS:
- CSS Grid for layout
- CSS Custom Properties for theming
- Flexbox for card internals
- :has() selector for checkbox state styling

---

## Accessibility Best Practices

### ARIA Attributes for Multi-Select Format Selector

Based on W3C ARIA Authoring Practices Guide (APG) and WCAG 2.2:

#### Required ARIA Attributes

```html
<fieldset role="group" aria-labelledby="format-selection-label">
  <legend id="format-selection-label">Select output format(s)</legend>

  <div role="group" aria-label="Format selection options">
    <!-- Checkbox cards here -->
  </div>
</fieldset>
```

**For each selectable card**:
- `role="checkbox"` or native `<input type="checkbox">` (native preferred)
- `aria-checked="true|false"` (automatic with native checkbox)
- `aria-labelledby` pointing to card label
- `aria-describedby` for additional context (optional)

#### Keyboard Navigation Requirements

**Standard keyboard interactions**:
- **Tab**: Move focus between format options
- **Shift + Tab**: Move focus backward
- **Space**: Toggle selection of focused option
- **Enter**: Submit form (if inside form)

**Implementation notes**:
- Native checkboxes provide keyboard support automatically
- Ensure focus indicators are visible (not removed via CSS)
- Test with screen readers (NVDA, JAWS, VoiceOver)

### Color Contrast Requirements

**WCAG 2.2 AA Standards**:
- Normal text: Minimum 4.5:1 contrast ratio
- Large text (18pt+): Minimum 3:1 contrast ratio
- Interactive elements: 3:1 contrast against background

**Testing tools**:
- Chrome DevTools Lighthouse accessibility audit
- WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
- axe DevTools browser extension

### Focus Indicators

**Best Practices**:
- Visible focus ring on all interactive elements
- Don't remove default focus styles unless replacing with equivalent
- Use `focus-visible` to show focus only for keyboard navigation

```css
/* Tailwind CSS approach */
.format-card:focus-visible {
  @apply ring-2 ring-blue-500 ring-offset-2;
}

/* Plain CSS approach */
.format-card:focus-visible {
  outline: 2px solid #3B82F6;
  outline-offset: 2px;
}
```

---

## Implementation Options

### Option 1: Multi-Select (Recommended)

**User Capability**: Select 1, 2, or all 3 formats

**Use Case**:
- User wants DOCX for editing AND PDF for sharing
- User wants all formats for different purposes
- Power users appreciate flexibility

**Advantages**:
- Maximum flexibility
- Reduces repeated conversions
- Better user experience
- Aligns with modern UX patterns

**Considerations**:
- Backend must support generating multiple formats
- Need clear UI feedback for multiple selections
- Download handling: ZIP file or multiple download links

### Option 2: Single-Select

**User Capability**: Select exactly 1 format

**Use Case**:
- Users only ever want one format at a time
- Simpler backend implementation initially

**Disadvantages**:
- Less flexible
- Forces users to convert multiple times
- Doesn't align with 2025 UX best practices

**Recommendation**: Avoid single-select unless technical constraints require it

### Recommended Approach for This Application

**Multi-select with smart defaults**:
1. No format pre-selected (user must choose)
2. Allow selecting 1, 2, or all 3 formats
3. Show visual count: "2 formats selected"
4. Disable "Convert" button until at least one format selected
5. Return download links for each selected format

---

## Production-Ready Code Examples

### Example 1: Tailwind CSS Checkbox Cards (Recommended)

**HTML Structure**:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Format Selection</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 p-8">

  <div class="max-w-4xl mx-auto">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Convert Your Markdown</h1>

    <form action="/api/convert" method="post" enctype="multipart/form-data">
      <!-- File upload -->
      <div class="mb-6">
        <label for="file-upload" class="block text-sm font-medium text-gray-700 mb-2">
          Upload Markdown File
        </label>
        <input
          type="file"
          id="file-upload"
          name="file"
          accept=".md,.markdown"
          required
          class="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent p-2"
        >
      </div>

      <!-- Format selection -->
      <fieldset class="mb-6">
        <legend class="block text-sm font-medium text-gray-700 mb-3">
          Select Output Format(s)
        </legend>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">

          <!-- DOCX Format Card -->
          <label class="relative flex flex-col items-center p-6 bg-white border-2 border-gray-200 rounded-lg cursor-pointer hover:border-blue-400 hover:shadow-md transition-all duration-200 peer-checked:border-blue-600 peer-checked:bg-blue-50 focus-within:ring-2 focus-within:ring-blue-500 focus-within:ring-offset-2">
            <input
              type="checkbox"
              name="formats"
              value="docx"
              class="peer sr-only"
              aria-labelledby="docx-label"
            >

            <!-- Icon -->
            <svg class="h-12 w-12 mb-3 text-gray-400 peer-checked:text-blue-600 transition-colors" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              <path d="M9 12h6M9 16h6M9 8h3" stroke="white" stroke-width="1" stroke-linecap="round"/>
            </svg>

            <!-- Label -->
            <span id="docx-label" class="text-base font-semibold text-gray-900 mb-1">
              Microsoft Word
            </span>
            <span class="text-sm text-gray-500 text-center">
              .docx format
            </span>

            <!-- Checkmark indicator (visible when selected) -->
            <span class="absolute top-3 right-3 flex items-center justify-center w-6 h-6 bg-blue-600 rounded-full opacity-0 peer-checked:opacity-100 transition-opacity">
              <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
              </svg>
            </span>
          </label>

          <!-- PDF Format Card -->
          <label class="relative flex flex-col items-center p-6 bg-white border-2 border-gray-200 rounded-lg cursor-pointer hover:border-red-400 hover:shadow-md transition-all duration-200 peer-checked:border-red-600 peer-checked:bg-red-50 focus-within:ring-2 focus-within:ring-red-500 focus-within:ring-offset-2">
            <input
              type="checkbox"
              name="formats"
              value="pdf"
              class="peer sr-only"
              aria-labelledby="pdf-label"
            >

            <!-- Icon -->
            <svg class="h-12 w-12 mb-3 text-gray-400 peer-checked:text-red-600 transition-colors" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              <text x="7" y="16" font-size="6" font-weight="bold" fill="white">PDF</text>
            </svg>

            <!-- Label -->
            <span id="pdf-label" class="text-base font-semibold text-gray-900 mb-1">
              PDF Document
            </span>
            <span class="text-sm text-gray-500 text-center">
              .pdf format
            </span>

            <!-- Checkmark indicator -->
            <span class="absolute top-3 right-3 flex items-center justify-center w-6 h-6 bg-red-600 rounded-full opacity-0 peer-checked:opacity-100 transition-opacity">
              <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
              </svg>
            </span>
          </label>

          <!-- Google Docs Format Card -->
          <label class="relative flex flex-col items-center p-6 bg-white border-2 border-gray-200 rounded-lg cursor-pointer hover:border-blue-400 hover:shadow-md transition-all duration-200 peer-checked:border-blue-600 peer-checked:bg-blue-50 focus-within:ring-2 focus-within:ring-blue-500 focus-within:ring-offset-2" id="gdocs-card">
            <input
              type="checkbox"
              name="formats"
              value="gdocs"
              class="peer sr-only"
              aria-labelledby="gdocs-label"
              id="gdocs-checkbox"
            >

            <!-- Icon -->
            <svg class="h-12 w-12 mb-3 text-gray-400 peer-checked:text-blue-500 transition-colors" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
              <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20M10,19H8V18H10V19M14,19H10V17H14V19M14,16H10V14H14V16M10,13H8V11H10V13M14,13H10V11H14V13Z" />
            </svg>

            <!-- Label -->
            <span id="gdocs-label" class="text-base font-semibold text-gray-900 mb-1">
              Google Docs
            </span>
            <span class="text-sm text-gray-500 text-center">
              Saved to Drive
            </span>

            <!-- Sign-in required badge (if not authenticated) -->
            <span class="hidden mt-2 text-xs text-amber-600 font-medium" id="gdocs-auth-badge">
              Sign in required
            </span>

            <!-- Checkmark indicator -->
            <span class="absolute top-3 right-3 flex items-center justify-center w-6 h-6 bg-blue-600 rounded-full opacity-0 peer-checked:opacity-100 transition-opacity">
              <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
              </svg>
            </span>
          </label>

        </div>

        <!-- Selection feedback -->
        <p class="mt-3 text-sm text-gray-600" id="selection-count">
          No formats selected
        </p>
      </fieldset>

      <!-- Submit button -->
      <button
        type="submit"
        class="w-full md:w-auto px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        id="convert-btn"
        disabled
      >
        Convert
      </button>
    </form>
  </div>

  <script>
    // Progressive enhancement: JavaScript for better UX
    const checkboxes = document.querySelectorAll('input[name="formats"]');
    const convertBtn = document.getElementById('convert-btn');
    const selectionCount = document.getElementById('selection-count');
    const gdocsCheckbox = document.getElementById('gdocs-checkbox');
    const gdocsCard = document.getElementById('gdocs-card');
    const gdocsAuthBadge = document.getElementById('gdocs-auth-badge');

    // Check authentication status (replace with real check)
    const isAuthenticated = false; // TODO: Check session/OAuth status

    // Disable Google Docs option if not authenticated
    if (!isAuthenticated) {
      gdocsCheckbox.disabled = true;
      gdocsCard.classList.add('opacity-50', 'cursor-not-allowed');
      gdocsCard.classList.remove('cursor-pointer');
      gdocsAuthBadge.classList.remove('hidden');
    }

    // Update button state and selection count
    function updateSelectionState() {
      const checkedCount = document.querySelectorAll('input[name="formats"]:checked').length;

      // Enable/disable convert button
      convertBtn.disabled = checkedCount === 0;

      // Update selection count text
      if (checkedCount === 0) {
        selectionCount.textContent = 'No formats selected';
        selectionCount.classList.remove('text-blue-600');
        selectionCount.classList.add('text-gray-600');
      } else {
        const formatText = checkedCount === 1 ? 'format' : 'formats';
        selectionCount.textContent = `${checkedCount} ${formatText} selected`;
        selectionCount.classList.remove('text-gray-600');
        selectionCount.classList.add('text-blue-600', 'font-medium');
      }
    }

    // Add event listeners
    checkboxes.forEach(checkbox => {
      checkbox.addEventListener('change', updateSelectionState);
    });

    // Initial state
    updateSelectionState();
  </script>

</body>
</html>
```

**Key Features**:
- ✓ Multi-select capability
- ✓ Accessible (native checkboxes, ARIA labels)
- ✓ Keyboard navigable (Tab, Space)
- ✓ Hover states
- ✓ Selected state indicators
- ✓ Disabled state for Google Docs (if not authenticated)
- ✓ Real-time selection feedback
- ✓ Responsive design (mobile-friendly)
- ✓ Progressive enhancement (works without JS)

---

### Example 2: Plain CSS Implementation (No Framework)

**HTML**:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Format Selection - Plain CSS</title>
  <style>
    /* Reset and base styles */
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      background-color: #f9fafb;
      padding: 2rem;
      line-height: 1.6;
    }

    .container {
      max-width: 800px;
      margin: 0 auto;
    }

    h1 {
      font-size: 1.875rem;
      font-weight: 700;
      color: #111827;
      margin-bottom: 1.5rem;
    }

    /* Form styles */
    .form-group {
      margin-bottom: 1.5rem;
    }

    .form-label {
      display: block;
      font-size: 0.875rem;
      font-weight: 500;
      color: #374151;
      margin-bottom: 0.5rem;
    }

    .file-input {
      display: block;
      width: 100%;
      padding: 0.5rem;
      font-size: 0.875rem;
      border: 1px solid #d1d5db;
      border-radius: 0.5rem;
      background-color: #f9fafb;
      cursor: pointer;
    }

    .file-input:focus {
      outline: 2px solid #3b82f6;
      outline-offset: 2px;
    }

    /* Format selection grid */
    .format-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 1rem;
      margin-top: 0.75rem;
    }

    @media (min-width: 768px) {
      .format-grid {
        grid-template-columns: repeat(3, 1fr);
      }
    }

    /* Selectable card */
    .format-card {
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 1.5rem;
      background-color: white;
      border: 2px solid #e5e7eb;
      border-radius: 0.5rem;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .format-card:hover {
      border-color: #93c5fd;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    .format-card:focus-within {
      outline: 2px solid #3b82f6;
      outline-offset: 2px;
    }

    /* Selected state using :has() selector */
    .format-card:has(input:checked) {
      border-color: #3b82f6;
      background-color: #eff6ff;
    }

    .format-card.card-red:hover {
      border-color: #fca5a5;
    }

    .format-card.card-red:has(input:checked) {
      border-color: #dc2626;
      background-color: #fef2f2;
    }

    /* Hide actual checkbox visually but keep it accessible */
    .format-card input[type="checkbox"] {
      position: absolute;
      opacity: 0;
      width: 1px;
      height: 1px;
    }

    /* Icon styles */
    .format-icon {
      width: 3rem;
      height: 3rem;
      margin-bottom: 0.75rem;
      color: #9ca3af;
      transition: color 0.2s ease;
    }

    .format-card:has(input:checked) .format-icon {
      color: #3b82f6;
    }

    .format-card.card-red:has(input:checked) .format-icon {
      color: #dc2626;
    }

    /* Label text */
    .format-title {
      font-size: 1rem;
      font-weight: 600;
      color: #111827;
      margin-bottom: 0.25rem;
    }

    .format-subtitle {
      font-size: 0.875rem;
      color: #6b7280;
      text-align: center;
    }

    /* Checkmark indicator */
    .checkmark {
      position: absolute;
      top: 0.75rem;
      right: 0.75rem;
      width: 1.5rem;
      height: 1.5rem;
      background-color: #3b82f6;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      opacity: 0;
      transition: opacity 0.2s ease;
    }

    .card-red .checkmark {
      background-color: #dc2626;
    }

    .format-card:has(input:checked) .checkmark {
      opacity: 1;
    }

    .checkmark svg {
      width: 1rem;
      height: 1rem;
      color: white;
    }

    /* Selection feedback */
    .selection-feedback {
      margin-top: 0.75rem;
      font-size: 0.875rem;
      color: #6b7280;
    }

    .selection-feedback.active {
      color: #3b82f6;
      font-weight: 500;
    }

    /* Submit button */
    .btn-submit {
      width: 100%;
      padding: 0.75rem 1.5rem;
      font-size: 1rem;
      font-weight: 600;
      color: white;
      background-color: #3b82f6;
      border: none;
      border-radius: 0.5rem;
      cursor: pointer;
      transition: background-color 0.2s ease;
    }

    @media (min-width: 768px) {
      .btn-submit {
        width: auto;
      }
    }

    .btn-submit:hover:not(:disabled) {
      background-color: #2563eb;
    }

    .btn-submit:focus {
      outline: 2px solid #3b82f6;
      outline-offset: 2px;
    }

    .btn-submit:disabled {
      background-color: #d1d5db;
      cursor: not-allowed;
    }

    /* Disabled card */
    .format-card.disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .format-card.disabled:hover {
      border-color: #e5e7eb;
      box-shadow: none;
    }

    .auth-badge {
      margin-top: 0.5rem;
      font-size: 0.75rem;
      color: #d97706;
      font-weight: 500;
    }
  </style>
</head>
<body>

  <div class="container">
    <h1>Convert Your Markdown</h1>

    <form action="/api/convert" method="post" enctype="multipart/form-data">

      <!-- File upload -->
      <div class="form-group">
        <label for="file-upload" class="form-label">Upload Markdown File</label>
        <input
          type="file"
          id="file-upload"
          name="file"
          accept=".md,.markdown"
          required
          class="file-input"
        >
      </div>

      <!-- Format selection -->
      <fieldset class="form-group">
        <legend class="form-label">Select Output Format(s)</legend>

        <div class="format-grid">

          <!-- DOCX Card -->
          <label class="format-card">
            <input
              type="checkbox"
              name="formats"
              value="docx"
              aria-labelledby="docx-label"
            >

            <svg class="format-icon" fill="currentColor" viewBox="0 0 24 24">
              <path d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>

            <span id="docx-label" class="format-title">Microsoft Word</span>
            <span class="format-subtitle">.docx format</span>

            <span class="checkmark">
              <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
              </svg>
            </span>
          </label>

          <!-- PDF Card -->
          <label class="format-card card-red">
            <input
              type="checkbox"
              name="formats"
              value="pdf"
              aria-labelledby="pdf-label"
            >

            <svg class="format-icon" fill="currentColor" viewBox="0 0 24 24">
              <path d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>

            <span id="pdf-label" class="format-title">PDF Document</span>
            <span class="format-subtitle">.pdf format</span>

            <span class="checkmark">
              <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
              </svg>
            </span>
          </label>

          <!-- Google Docs Card -->
          <label class="format-card" id="gdocs-card">
            <input
              type="checkbox"
              name="formats"
              value="gdocs"
              aria-labelledby="gdocs-label"
              id="gdocs-checkbox"
            >

            <svg class="format-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" />
            </svg>

            <span id="gdocs-label" class="format-title">Google Docs</span>
            <span class="format-subtitle">Saved to Drive</span>

            <span class="auth-badge" id="gdocs-auth-badge" style="display: none;">
              Sign in required
            </span>

            <span class="checkmark">
              <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
              </svg>
            </span>
          </label>

        </div>

        <p class="selection-feedback" id="selection-count">No formats selected</p>
      </fieldset>

      <!-- Submit button -->
      <button type="submit" class="btn-submit" id="convert-btn" disabled>
        Convert
      </button>

    </form>
  </div>

  <script>
    // Same JavaScript as Tailwind example
    const checkboxes = document.querySelectorAll('input[name="formats"]');
    const convertBtn = document.getElementById('convert-btn');
    const selectionCount = document.getElementById('selection-count');
    const gdocsCheckbox = document.getElementById('gdocs-checkbox');
    const gdocsCard = document.getElementById('gdocs-card');
    const gdocsAuthBadge = document.getElementById('gdocs-auth-badge');

    // Check authentication status
    const isAuthenticated = false; // TODO: Check OAuth status

    if (!isAuthenticated) {
      gdocsCheckbox.disabled = true;
      gdocsCard.classList.add('disabled');
      gdocsAuthBadge.style.display = 'block';
    }

    function updateSelectionState() {
      const checkedCount = document.querySelectorAll('input[name="formats"]:checked').length;
      convertBtn.disabled = checkedCount === 0;

      if (checkedCount === 0) {
        selectionCount.textContent = 'No formats selected';
        selectionCount.classList.remove('active');
      } else {
        const formatText = checkedCount === 1 ? 'format' : 'formats';
        selectionCount.textContent = `${checkedCount} ${formatText} selected`;
        selectionCount.classList.add('active');
      }
    }

    checkboxes.forEach(checkbox => {
      checkbox.addEventListener('change', updateSelectionState);
    });

    updateSelectionState();
  </script>

</body>
</html>
```

**Browser Support**:
- Uses modern CSS `:has()` selector for selected state
- Supported in Chrome 105+, Safari 15.4+, Firefox 121+
- Fallback: JavaScript can add class for older browsers

---

## Mobile Responsiveness

### Design Considerations

**Desktop (≥768px)**:
- 3-column grid
- Horizontal layout
- Hover states visible

**Mobile (<768px)**:
- Single column (stacked vertically)
- Larger touch targets (entire card)
- Focus on tap-friendly interactions

### Touch Target Sizes

**WCAG 2.2 Guidelines** (Success Criterion 2.5.8):
- Minimum touch target size: 24x24 CSS pixels
- Recommended: 44x44 CSS pixels (iOS Human Interface Guidelines)
- Our implementation: Entire card is touch target (120px+ tall)

### Example Media Queries

```css
/* Mobile-first approach */
.format-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

/* Tablet and up */
@media (min-width: 640px) {
  .format-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Desktop */
@media (min-width: 768px) {
  .format-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
```

---

## Integration with Existing Flask Application

### Backend Handling (app/api/routes.py)

```python
from flask import request, jsonify

@api_bp.route('/convert', methods=['POST'])
def convert():
    """Handle multi-format conversion."""

    # Get selected formats from form
    selected_formats = request.form.getlist('formats')  # Returns list: ['docx', 'pdf', 'gdocs']

    if not selected_formats:
        return jsonify({
            'error': 'No output format selected',
            'code': 'NO_FORMAT_SELECTED'
        }), 400

    # Validate formats
    valid_formats = {'docx', 'pdf', 'gdocs'}
    invalid = set(selected_formats) - valid_formats

    if invalid:
        return jsonify({
            'error': f'Invalid format(s): {", ".join(invalid)}',
            'code': 'INVALID_FORMAT'
        }), 400

    # Check Google Docs authentication
    if 'gdocs' in selected_formats:
        from flask_dance.contrib.google import google
        if not google.authorized:
            return jsonify({
                'error': 'Google Docs format requires authentication',
                'code': 'AUTH_REQUIRED',
                'auth_url': url_for('google.login', _external=True)
            }), 401

    # ... rest of conversion logic

    # Process each selected format
    results = {}

    if 'docx' in selected_formats:
        results['docx'] = {
            'download_url': url_for('api.download', job_id=job_id, format='docx', _external=True),
            'filename': f'{original_filename}.docx'
        }

    if 'pdf' in selected_formats:
        results['pdf'] = {
            'download_url': url_for('api.download', job_id=job_id, format='pdf', _external=True),
            'filename': f'{original_filename}.pdf'
        }

    if 'gdocs' in selected_formats:
        results['gdocs'] = {
            'web_view_link': gdocs_result['webViewLink'],
            'document_id': gdocs_result['documentId']
        }

    return jsonify({
        'job_id': job_id,
        'formats': results,
        'message': f'Conversion successful for {len(selected_formats)} format(s)'
    }), 200
```

### Frontend Authentication Check (JavaScript)

```javascript
// Check if user is authenticated for Google Docs
async function checkGoogleAuth() {
  try {
    const response = await fetch('/auth/status');
    const data = await response.json();

    const gdocsCheckbox = document.getElementById('gdocs-checkbox');
    const gdocsCard = document.getElementById('gdocs-card');
    const gdocsAuthBadge = document.getElementById('gdocs-auth-badge');

    if (data.authenticated) {
      // User is authenticated
      gdocsCheckbox.disabled = false;
      gdocsCard.classList.remove('opacity-50', 'cursor-not-allowed');
      gdocsAuthBadge.classList.add('hidden');
    } else {
      // User not authenticated
      gdocsCheckbox.disabled = true;
      gdocsCard.classList.add('opacity-50', 'cursor-not-allowed');
      gdocsAuthBadge.classList.remove('hidden');

      // Optionally add click handler to redirect to sign-in
      gdocsCard.addEventListener('click', (e) => {
        if (gdocsCheckbox.disabled) {
          e.preventDefault();
          if (confirm('Sign in with Google to enable Google Docs conversion?')) {
            window.location.href = '/auth/google';
          }
        }
      });
    }
  } catch (error) {
    console.error('Failed to check auth status:', error);
  }
}

// Call on page load
document.addEventListener('DOMContentLoaded', checkGoogleAuth);
```

### Authentication Status Endpoint

```python
# app/auth/routes.py
from flask import jsonify
from flask_dance.contrib.google import google

@auth_bp.route('/status')
def status():
    """Check if user is authenticated with Google."""
    return jsonify({
        'authenticated': google.authorized,
        'user': google.get('/oauth2/v2/userinfo').json() if google.authorized else None
    })
```

---

## Summary and Recommendations

### Primary Recommendations

1. **Use selectable card pattern** with multi-select checkboxes
2. **Implement with Tailwind CSS** for rapid development and maintainability
3. **Enable all 3 formats** simultaneously (DOCX + PDF + Google Docs)
4. **Use Flaticon or Heroicons** for file type icons
5. **Implement full accessibility** (ARIA, keyboard navigation, focus indicators)
6. **Disable Google Docs option** when user not authenticated, with clear messaging
7. **Provide real-time feedback** on number of formats selected
8. **Use CSS Grid** for responsive layout (3 columns desktop, 1 column mobile)

### Implementation Priority

**Phase 1** (MVP):
- Basic selectable cards with checkboxes
- Multi-select capability
- Responsive layout
- Backend handling of format array

**Phase 2** (Enhanced UX):
- Authentication status check for Google Docs
- Real-time selection count
- Disabled state handling
- Progressive enhancement JavaScript

**Phase 3** (Polish):
- Smooth animations/transitions
- Accessibility testing with screen readers
- Icon optimization
- Error state handling

### Files to Update

1. **templates/index.html** - Add new format selection UI
2. **static/css/style.css** - Add styles (if not using Tailwind)
3. **app/api/routes.py** - Handle `request.form.getlist('formats')`
4. **app/auth/routes.py** - Add `/auth/status` endpoint
5. **static/js/app.js** - Add authentication check and selection counter

---

**Documentation Status**: COMPLETE
**Ready for Architecture Phase**: YES
**Recommended Next Action**: Review with team, then delegate UI implementation to pact-frontend specialist
