# Changelog

All notable changes to the Domain Reputation Checker Web App.

## [1.2.0] - 2026-01-23

### Added
- **Reset Button**
  - Clears search input and hides results
  - Appears after a search is performed
  - Styled with secondary gradient theme
  - Resets all UI states cleanly

- **PDF Export Feature**
  - Professional PDF report generation
  - Includes all analysis data and source details
  - Color-coded reputation indicators
  - Formatted tables with proper styling
  - Auto-downloads with timestamped filename
  - Export button appears after successful analysis
  - Loading state during PDF generation

### Changed
- Added `reportlab` dependency for PDF generation
- Enhanced button styling with secondary and export variants
- Improved UX with state management for buttons
- Added visual feedback during PDF generation

### Technical Details

**Reset Button:**
- ID: `resetBtn`
- Class: `btn btn-secondary`
- Shows after search, hides on reset
- Clears: input, results, errors, and stored data

**PDF Export:**
- Endpoint: `POST /api/export-pdf`
- Library: ReportLab
- Format: Letter size, styled tables
- Colors: Match web theme (#00d4ff, #0099cc)
- Includes: Domain, reputation, timestamp, all sources
- Filename: `domain-reputation-{domain}-{date}.pdf`

**Button Styles:**
- `.btn-secondary`: Gray gradient for reset
- `.btn-export`: Green gradient for PDF export
- `.export-actions`: Flex container for action buttons

---

## [1.1.0] - 2026-01-23

### Added
- **Favicon Support** 
  - Added custom shield-check SVG favicon with gradient theme
  - Created PNG (32x32) fallback for browsers without SVG support
  - Generated ICO format for legacy browser compatibility
  - Comprehensive favicon meta tags for all browsers

- **Improved IP Geolocation Data Display**
  - Smart formatting for location objects (city, region, country)
  - Compact array display (shows first 3 items with count)
  - Inline key-value pairs for nested objects
  - Automatic filtering of empty/null values
  - Better text wrapping in detail cards

- **Enhanced Card Layout**
  - Added flex gap for better spacing
  - Labels now stay on one line (no wrapping)
  - Values wrap properly with word-break
  - Improved alignment with flex-start
  - Better visual hierarchy

### Changed
- Updated Flask app to serve static files from `/static` folder
- Modified data formatting in backend to skip empty values
- Enhanced JavaScript to intelligently format complex data types

### Files Modified
- `templates/index.html` - Added favicon links, improved JavaScript formatting
- `app.py` - Added static folder configuration, improved data filtering
- Created `static/` directory with 3 favicon formats

### Technical Details

**Favicon Creation:**
- SVG: Vector format with gradient matching app theme
- PNG: 32x32 raster fallback
- ICO: Multi-resolution (32x32, 16x16) for legacy support

**Data Formatting Improvements:**
- Location objects: "City, Region, Country (CC)" format
- Arrays: "item1, item2, item3 (+N more)" format
- Objects: "key: value, key: value" inline format
- Automatic null/empty filtering

**CSS Enhancements:**
- `.detail-label`: `white-space: nowrap`, `flex-shrink: 0`
- `.detail-value`: `word-break: break-word`, `text-align: right`
- `.details-list li`: Added `gap: 10px`, `align-items: flex-start`

### Browser Compatibility
- Modern browsers: SVG favicon
- Safari, older Chrome/Firefox: PNG favicon
- IE11 and older: ICO favicon

---

## [1.0.0] - 2026-01-23

### Initial Release
- Flask backend with REST API
- Modern dark-themed UI
- Multi-source domain analysis
- Responsive design
- Mobile-friendly layout
- Real-time loading indicators
- Color-coded reputation badges
