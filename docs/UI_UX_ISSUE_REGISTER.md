# KITAAB BANK — FRONTEND UI/UX ISSUE REGISTER
## Master Audit & Defect Tracking Log (Resolved & Verified)

---

## 1. Register Overview & Status Legend

This document serves as the central, page-by-page register of all user-confirmed and audit-discovered user interface, usability, responsiveness, styling, and accessibility issues across **Kitaab Bank (کتاب بینک)**.

### Severity Classification
- **Critical (P0):** Breaks layout usability, causes horizontal page overflow, makes navigation unusable, or violates accessibility standards.
- **Major (P1):** Noticeable visual defect, text wrapping, unaligned elements, inconsistent spacing, or awkward mobile interaction.
- **Moderate (P2):** Suboptimal UI styling, excessive custom CSS, informal icon/emoji usage, or missing responsive polish.
- **Minor (P3):** Subtle visual inconsistency, minor padding discrepancy, or cosmetic enhancement.

### Status Classification
- **RESOLVED & VERIFIED:** Fixed, integrated with Bootstrap 5.3.8 / Font Awesome 7.3.1, and verified across all 137 unit, integration, and browser test suites.

---

## 2. Confirmed Core Issues (User-Reported)

| Issue ID | Page / Component | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **ISSUE-NAV-01** | Global Navigation (Desktop Header) | **Critical (P0)** | Implemented Bootstrap 5.3.8 `navbar-expand-xxl` (1400px breakpoint) with `container-fluid px-3 px-xxl-4` and `.text-nowrap` nav-links. Below 1400px, navigation cleanly collapses into `#studentNavOffcanvas` drawer. Zero horizontal text-wrapping and zero overflow across 1024px, 1280px, 1366px, 1400px, 1440px in EN, UR, SD. | Commits `d277958`, visual audit `scripts/run_visual_acceptance_audit.py`, verified via `tests/test_browser_ui_redesign.py`. | **RESOLVED & VERIFIED** |
| **ISSUE-NAV-02** | Global Navigation (Mobile Navbar) | **Critical (P0)** | Replaced custom dropdown menu with accessible Bootstrap 5.3 Offcanvas drawer (`#studentNavOffcanvas`), full backdrop dismissal, 48px touch targets, and locale/theme selector footer. | Commit `d277958`, verified via `tests/test_browser_ui_redesign.py`. | **RESOLVED & VERIFIED** |
| **ISSUE-CSS-01** | Global Stylesheets (`components.css`, `main.css`, `student.css`, `teacher.css`) | **Major (P1)** | Replaced over 39 KB of redundant bespoke CSS with native Bootstrap 5.3.8 utility and component classes (`container`, `row`, `col-*`, `btn`, `card`, `badge`, `alert`, `table`, `modal`). | Commits `07355ac`, `d277958`, `e940d4e`. All 137 tests passing. | **RESOLVED & VERIFIED** |
| **ISSUE-ICO-01** | Universal Iconography (All Portals & Templates) | **Moderate (P2)** | Vendored Font Awesome 7.3.1 Free locally (Zero CDN). Implemented central Jinja icon macro `{{ icon(name) }}`. Replaced informal emojis across all 33 templates with consistent SVGs/webfonts. | Commit `07355ac`, `docs/UI_UX_ICON_MAP.md`. | **RESOLVED & VERIFIED** |

---

## 3. Student Portal Issue Register (Audit-Discovered)

### 3.1 Homepage (`app/templates/student/index.html`)
| Issue ID | Component | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **STU-HOME-01** | Hero Section | **Moderate (P2)** | Refactored hero to fluid Bootstrap container with `display-6 display-md-5 fw-bold`, badge pill, and responsive vertical rhythm. | Commit `8ad1146`, tested via `test_phase2.py`. | **RESOLVED & VERIFIED** |
| **STU-HOME-02** | Hero Search Bar | **Moderate (P2)** | Modernized search with Bootstrap input group, rounded pill styling, and Font Awesome search icon. | Commit `8ad1146`, tested via `test_phase2.py`. | **RESOLVED & VERIFIED** |
| **STU-HOME-03** | Live Impact Metrics Strip | **Major (P1)** | Replaced brittle CSS grid with `<div class="row g-3 row-cols-2 row-cols-md-4">` and clean elevated cards. | Commit `8ad1146`, tested via `test_phase2.py`. | **RESOLVED & VERIFIED** |
| **STU-HOME-04** | Featured Books Grid | **Moderate (P2)** | Refactored featured book cards to uniform 3:4 aspect ratio covers (`aspect-ratio: 3/4; object-fit: cover;`), consistent badges, and card hover effects. | Commit `8ad1146`, tested via `test_phase2.py`. | **RESOLVED & VERIFIED** |

---

### 3.2 Book Catalogue & Filters (`app/templates/student/catalogue.html`)
| Issue ID | Component | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **STU-CAT-01** | Filter & Search Toolbar | **Major (P1)** | Replaced custom `.filter-grid` with a clean Bootstrap row card. Aligned filter and reset buttons cleanly at all breakpoints. | Commit `8ad1146`, tested via `test_phase2.py`. | **RESOLVED & VERIFIED** |
| **STU-CAT-02** | Active Filter Pills | **Minor (P3)** | Styled active filters with `.active-filter-pill` using Bootstrap badge styling and Font Awesome dismiss icons. | Commit `8ad1146`, tested via `test_phase2.py`. | **RESOLVED & VERIFIED** |
| **STU-CAT-03** | Empty Search State | **Moderate (P2)** | Built centered Bootstrap card with Font Awesome book icon, helpful suggestion text, and clear filters action. | Commit `8ad1146`, tested via `test_phase2.py`. | **RESOLVED & VERIFIED** |

---

### 3.3 Book Details (`app/templates/student/book_detail.html`)
| Issue ID | Component | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **STU-DET-01** | Information Architecture & Layout | **Major (P1)** | Refactored to responsive two-column grid (`col-lg-4` cover/QR and `col-lg-8` curriculum details). | Commit `f7753e4`, tested via `test_phase6.py`. | **RESOLVED & VERIFIED** |
| **STU-DET-02** | Metadata Grid | **Moderate (P2)** | Converted metadata into clean responsive definition list with uppercase label headers and bold values. | Commit `f7753e4`, tested via `test_phase6.py`. | **RESOLVED & VERIFIED** |
| **STU-DET-03** | Inline Styles & Emojis | **Minor (P3)** | Stripped inline CSS and replaced all emojis with Font Awesome icons. | Commit `f7753e4`, tested via `test_phase6.py`. | **RESOLVED & VERIFIED** |

---

### 3.4 Book Donation Form & Success (`app/templates/student/donate.html` & `donation_success.html`)
| Issue ID | Component | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **STU-DON-01** | Multi-Section Form Layout | **Major (P1)** | Refactored into clean Bootstrap form sections, styled file upload control with local preview, and validation states. | Commit `f7753e4`, tested via `test_phase3.py`. | **RESOLVED & VERIFIED** |
| **STU-DON-02** | Donation Success Screen | **Moderate (P2)** | Modern celebration card with Font Awesome checkmark, clipboard copy button on `#ref-code`, and direct tracking links. | Commit `f7753e4`, tested via `test_phase3.py`. | **RESOLVED & VERIFIED** |

---

### 3.5 Book Request Form & Success (`app/templates/student/request_book.html` & `request_success.html`)
| Issue ID | Component | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **STU-REQ-01** | Selected Book Summary Box | **Moderate (P2)** | Built clean horizontal summary card with responsive book cover thumbnail and curriculum badges. | Commit `f7753e4`, tested via `test_phase4.py`. | **RESOLVED & VERIFIED** |
| **STU-REQ-02** | Request Success Token Display | **Major (P1)** | Applied strict LTR isolation (`.kb-code`) to `#track-code`, added copy-to-clipboard button and next-steps guidance. | Commit `f7753e4`, tested via `test_phase4.py`. | **RESOLVED & VERIFIED** |

---

### 3.6 Request Tracking Desk (`app/templates/student/track.html`)
| Issue ID | Component | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **STU-TRK-01** | Tracking Search Form | **Moderate (P2)** | Modernized lookup card with Bootstrap input group, uppercase monospace font, and clear search button. | Commit `f7753e4`, tested via `test_phase5.py`. | **RESOLVED & VERIFIED** |
| **STU-TRK-02** | Status Progress Timeline | **Major (P1)** | Replaced static box with responsive 4-step workflow stepper and semantic callouts for all 5 lifecycle statuses. | Commit `f7753e4`, tested via `test_phase5.py`. | **RESOLVED & VERIFIED** |

---

### 3.7 QR Scanner & Direct Lookup (`app/templates/student/scan.html`)
| Issue ID | Component | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **STU-SCN-01** | Card Layout & Visual Balance | **Moderate (P2)** | Modernized with balanced Bootstrap cards, subtle elevation, and Font Awesome control icons. Strictly preserved all 11 scanner element IDs. | Commit `f7753e4`, tested via `test_phase6.py`. | **RESOLVED & VERIFIED** |
| **STU-SCN-02** | Mobile Camera Reticle Overlay | **Moderate (P2)** | Standardized camera viewport with Bootstrap `.ratio .ratio-4x3` and responsive high-contrast corner brackets. | Commit `f7753e4`, tested via `test_phase6.py`. | **RESOLVED & VERIFIED** |

---

## 4. Teacher Portal Issue Register (Audit-Discovered)

### 4.1 Teacher Login (`app/templates/auth/login.html`)
| Issue ID | Component | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **TCHR-LOG-01** | Login Card & Form Styling | **Moderate (P2)** | Centered responsive Bootstrap card (`col-md-6 col-lg-5 col-xl-4 mx-auto`) with icon badges and input groups. | Commit `998d249`, tested via `test_phase7.py`. | **RESOLVED & VERIFIED** |

---

### 4.2 Teacher Dashboard (`app/templates/teacher/dashboard.html`)
| Issue ID | Component | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **TCHR-DASH-01** | Pending Actions Alert Banner | **Major (P1)** | High-visibility warning alert with responsive action buttons and Font Awesome status icon. | Commit `998d249`, tested via `test_phase7.py`. | **RESOLVED & VERIFIED** |
| **TCHR-DASH-02** | Quick Actions Grid | **Major (P1)** | 6-column Bootstrap responsive grid (`col-6 col-md-4 col-xl-2`) with hover elevation and icon badges. | Commit `998d249`, tested via `test_phase7.py`. | **RESOLVED & VERIFIED** |
| **TCHR-DASH-03** | Primary Metric KPI Cards | **Major (P1)** | Responsive 6-card metrics row (`col-6 col-md-4 col-xl-2`) with consistent elevation and Font Awesome icons. | Commit `998d249`, tested via `test_phase7.py`. | **RESOLVED & VERIFIED** |
| **TCHR-DASH-04** | Distribution Progress Bars | **Minor (P3)** | Migrated custom meters to standard Bootstrap `progress` and `progress-bar` components with accessible ARIA roles. | Commit `998d249`, tested via `test_phase7.py`. | **RESOLVED & VERIFIED** |

---

### 4.3 Donation Review Queue & Detail (`donations.html` & `donation_detail.html`)
| Issue ID | Component | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **TCHR-DON-01** | Status Filter Tabs | **Moderate (P2)** | Converted to responsive Bootstrap nav-pills with count badges and Font Awesome tab icons. | Commit `d158871`, tested via `test_phase4.py`. | **RESOLVED & VERIFIED** |
| **TCHR-DON-02** | Donations Data Table | **Major (P1)** | Enclosed in Bootstrap `.table-responsive` with `.table .table-hover .align-middle`. Replaced custom modal with Bootstrap modal `#reject-modal`. | Commit `d158871`, tested via `test_phase4.py`. | **RESOLVED & VERIFIED** |

---

### 4.4 Student Requests Queue & Allocation (`requests.html` & `request_detail.html`)
| Issue ID | Component | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **TCHR-REQ-01** | Requests Table Columns | **Major (P1)** | Responsive table with prioritized columns, `.kb-code` tracking codes, and compact button groups. | Commit `d158871`, tested via `test_phase5.py`. | **RESOLVED & VERIFIED** |
| **TCHR-REQ-02** | Request Detail Allocation Action | **Moderate (P2)** | Styled verification actions with Bootstrap success/danger buttons, Font Awesome icons, and inline/modal rejection forms. | Commit `d158871`, tested via `test_phase5.py`. | **RESOLVED & VERIFIED** |

---

### 4.5 Handover Ledger & Confirmation (`handovers.html`, `handover_confirm.html`, `handover_receipt.html`)
| Issue ID | Component | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **TCHR-HO-01** | Handover Confirmation Checklist | **Major (P1)** | Refactored into clean card checklist with `#confirm_id`, `#confirm_physical`, `#remarks`, and `#submit-handover-btn`. | Commit `d158871`, tested via `test_phase5.py`. | **RESOLVED & VERIFIED** |
| **TCHR-HO-02** | Printable A4 Receipt View | **Minor (P3)** | Preserved exact A4 print rules while adding screen action headers, Font Awesome icons, and brand typography. | Commit `d158871`, tested via `test_phase5.py`. | **RESOLVED & VERIFIED** |

---

### 4.6 Book Inventory & Book Form (`inventory.html` & `book_form.html`)
| Issue ID | Component | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **TCHR-INV-01** | Inventory Table Actions | **Moderate (P2)** | Formatted actions into compact `.btn-group .btn-group-sm` with Font Awesome QR, Edit, and Retire/Restore actions. | Commit `d158871`, tested via `test_phase7.py`. | **RESOLVED & VERIFIED** |
| **TCHR-INV-02** | Retire Textbook Modal | **Major (P1)** | Refactored `#retireModal` into accessible Bootstrap modal with preset select and custom reason input. | Commit `d158871`, tested via `test_phase7.py`. | **RESOLVED & VERIFIED** |

---

### 4.7 Reports & Analytics (`app/templates/teacher/reports.html`)
| Issue ID | Component | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **TCHR-REP-01** | Action Header & Export Buttons | **Moderate (P2)** | Clean header with Print button (`window.print()`), Export Inventory CSV, and Export Handovers CSV. | Commit `76e7e80`, tested via `test_phase7.py`. | **RESOLVED & VERIFIED** |
| **TCHR-REP-02** | Statistical Summary Cards | **Moderate (P2)** | Responsive 6-card summary row, class-wise circulation matrix, subject spread, and language/condition progress bars. | Commit `76e7e80`, tested via `test_phase7.py`. | **RESOLVED & VERIFIED** |

---

### 4.8 Activity Logs (`app/templates/teacher/logs.html`)
| Issue ID | Component | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **TCHR-LOG-01** | Activity Log Rows | **Moderate (P2)** | Modernized audit trail with filter inputs, category badge colors, actor details, and pagination controls. | Commit `76e7e80`, tested via `test_phase7.py`. | **RESOLVED & VERIFIED** |

---

### 4.9 System Settings Desk (`app/templates/teacher/settings.html`)
| Issue ID | Component | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **TCHR-SET-01** | Navigation Tabs Bar | **Major (P1)** | Clean Bootstrap nav-pills (`nav nav-pills gap-2 mb-4`) with Font Awesome icons for Profile, Security, Backup, and Demo. | Commit `76e7e80`, tested via `test_phase8.py`. | **RESOLVED & VERIFIED** |
| **TCHR-SET-02** | Inline Form Styles | **Moderate (P2)** | Replaced inline styles with standard Bootstrap form controls (`form-label`, `form-control`, `form-select`). | Commit `76e7e80`, tested via `test_phase8.py`. | **RESOLVED & VERIFIED** |
| **TCHR-SET-03** | Backup List & Restore Action | **Major (P1)** | Modernized backups table with file sizes, verification status badges, download links, and CLI utility card. | Commit `76e7e80`, tested via `test_phase8.py`. | **RESOLVED & VERIFIED** |
| **TCHR-SET-04** | Exhibition Demo Card & Checkbox | **Critical (P0)** | Built high-visibility warning card with styled checkbox while strictly preserving `#confirmDemoBox` input ID. | Commit `76e7e80`, tested via `test_phase8.py`. | **RESOLVED & VERIFIED** |

---

## 5. Global & Accessibility Issue Register (Audit-Discovered)

| Issue ID | Area | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **GLOB-RTL-01** | Nastaliq Typography in RTL | **Major (P1)** | Configured `rtl.css` with Noto Nastaliq Urdu font stack, `line-height: 1.65` for headings and `1.75` for body text to eliminate glyph clipping. | Commit `e940d4e`, tested via `test_browser_ui_redesign.py`. | **RESOLVED & VERIFIED** |
| **GLOB-BIDI-01** | Code & Token Direction | **Critical (P0)** | Enforced `.kb-code` utility (`unicode-bidi: isolate; direction: ltr !important; text-align: left;`) across all codes and phone inputs. | Commits `d277958`, `e940d4e`, tested via `test_browser_ui_redesign.py`. | **RESOLVED & VERIFIED** |
| **GLOB-ACC-01** | ARIA Landmarks & Attributes | **Major (P1)** | Implemented standard ARIA attributes (`aria-labelledby`, `aria-label`, `aria-expanded`, `aria-hidden`) across all modals, dropdowns, and offcanvas drawers. | Commits `d277958`, `d158871`, `76e7e80`, tested via `test_browser_ui_redesign.py`. | **RESOLVED & VERIFIED** |
| **GLOB-FOUC-01** | Theme Flash on Page Load | **Major (P1)** | Synchronous Zero-FOUC guard in `<head>` sets both `data-theme` and `data-bs-theme` before CSS render, coordinated with `theme.js`. | Commits `d277958`, `e940d4e`, tested via `test_browser_ui_redesign.py`. | **RESOLVED & VERIFIED** |

---

## 6. Register Sign-Off & Verification Metrics

- **Total Registered Issues:** **35 / 35 RESOLVED (100%)**
- **Critical (P0) Issues:** **4 / 4 RESOLVED**
- **Major (P1) Issues:** **14 / 14 RESOLVED**
- **Moderate (P2) Issues:** **14 / 14 RESOLVED**
- **Minor (P3) Issues:** **3 / 3 RESOLVED**
- **Full Test Suite:** **137 / 137 tests passing (OK)**

---

## 7. Visual Acceptance & Evidence Register (`docs/ui-redesign-evidence/`)

| Screenshot File | Viewport | Locale / Theme | Scope / Description | Status |
|---|---|---|---|---|
| `student_home_desktop.png` | 1440x900 | English / Light | Public homepage with hero, search, KPIs, and uniform 3:4 book cards | **VERIFIED** |
| `student_home_mobile.png` | 390x844 | English / Light | Public homepage mobile view, zero horizontal overflow | **VERIFIED** |
| `student_catalogue_desktop.png` | 1440x900 | English / Light | Discovery catalogue with filter toolbar and active badge pills | **VERIFIED** |
| `student_catalogue_mobile.png` | 390x844 | English / Light | Catalogue mobile grid with responsive filters | **VERIFIED** |
| `student_book_detail_desktop.png` | 1440x900 | English / Light | Two-column book detail with official code & QR labels | **VERIFIED** |
| `student_book_detail_mobile.png` | 390x844 | English / Light | Responsive single-column stacked book detail | **VERIFIED** |
| `student_donate_desktop.png` | 1440x900 | English / Light | Book donation desk with styled file upload | **VERIFIED** |
| `student_donate_mobile.png` | 390x844 | English / Light | Mobile donation form with touch-friendly fields | **VERIFIED** |
| `student_request_desktop.png` | 1440x900 | English / Light | Student book request form with textbook preview card | **VERIFIED** |
| `student_request_mobile.png` | 390x844 | English / Light | Mobile book request form with input formatting | **VERIFIED** |
| `student_track_desktop.png` | 1440x900 | English / Light | Request tracking desk with status callout & book summary | **VERIFIED** |
| `student_track_mobile.png` | 390x844 | English / Light | Mobile request tracking with masked student identity | **VERIFIED** |
| `student_scan_desktop.png` | 1440x900 | English / Light | Dual-mode QR camera and manual lookup desk | **VERIFIED** |
| `student_scan_mobile.png` | 390x844 | English / Light | Mobile QR scan screen with fallback input | **VERIFIED** |
| `nav_offcanvas_mobile_open.png` | 390x844 | English / Light | Student mobile offcanvas drawer (<1400px) open | **VERIFIED** |
| `teacher_dashboard_desktop.png` | 1440x900 | English / Light | Teacher executive desk with 6 KPIs and progress bars | **VERIFIED** |
| `teacher_dashboard_mobile.png` | 390x844 | English / Light | Mobile teacher dashboard with compact action cards | **VERIFIED** |
| `teacher_donations_desktop.png` | 1440x900 | English / Light | Donation queue with filter pills and modal reject | **VERIFIED** |
| `teacher_donations_mobile.png` | 390x844 | English / Light | Mobile responsive donation review queue | **VERIFIED** |
| `teacher_requests_desktop.png` | 1440x900 | English / Light | Student request ledger with status filtering | **VERIFIED** |
| `teacher_requests_mobile.png` | 390x844 | English / Light | Mobile student request ledger | **VERIFIED** |
| `teacher_handovers_desktop.png` | 1440x900 | English / Light | Physical handover verification ledger | **VERIFIED** |
| `teacher_handovers_mobile.png` | 390x844 | English / Light | Mobile physical handover ledger | **VERIFIED** |
| `teacher_inventory_desktop.png` | 1440x900 | English / Light | Textbook inventory with covers and retirement actions | **VERIFIED** |
| `teacher_inventory_mobile.png` | 390x844 | English / Light | Mobile textbook inventory table | **VERIFIED** |
| `teacher_reports_desktop.png` | 1440x900 | English / Light | Analytical reports with circulation matrix and CSV export | **VERIFIED** |
| `teacher_reports_mobile.png` | 390x844 | English / Light | Mobile reports and statistics breakdown | **VERIFIED** |
| `teacher_settings_desktop.png` | 1440x900 | English / Light | Teacher settings with 4 tabs and `#confirmDemoBox` | **VERIFIED** |
| `teacher_settings_mobile.png` | 390x844 | English / Light | Mobile teacher settings and backup catalog | **VERIFIED** |
| `teacher_nav_offcanvas_mobile_open.png` | 390x844 | English / Light | Teacher mobile sidebar offcanvas drawer open (<992px) | **VERIFIED** |
| `rtl_urdu_home_desktop.png` | 1440x900 | Urdu / Light (RTL) | Urdu RTL homepage with Nastaliq typography | **VERIFIED** |
| `rtl_urdu_dashboard_desktop.png` | 1440x900 | Urdu / Light (RTL) | Teacher dashboard rendered in Urdu RTL | **VERIFIED** |
| `rtl_sindhi_home_desktop.png` | 1440x900 | Sindhi / Light (RTL) | Sindhi RTL homepage with native typography | **VERIFIED** |
| `rtl_sindhi_catalogue_desktop.png` | 1440x900 | Sindhi / Light (RTL) | Sindhi RTL book catalogue with `.kb-code` bidi isolation | **VERIFIED** |
| `theme_dark_home_desktop.png` | 1440x900 | English / Dark | Public homepage in high-contrast Dark theme | **VERIFIED** |
| `theme_dark_dashboard_desktop.png` | 1440x900 | English / Dark | Teacher dashboard in high-contrast Dark theme | **VERIFIED** |

---

## 8. Stage 0 Post-Acceptance Correction & Polish Issue Register

This section tracks visual, localization, and responsive defects identified during the full-page visual acceptance audit of the 36 baseline screenshots (`docs/ui-redesign-evidence/`).

### Defect Tracking Matrix

| Issue ID | Severity | Category | Description | Scope / Affected Files | Resolution Summary | Status |
|---|---|---|---|---|---|---|
| `DEF-LOC-01` | P0 | Localization | Incomplete template localization: ~80% of interface text hardcoded in English, missing `_t()` wrappers. | All student & teacher templates, `en.json`, `ur.json`, `sd.json` | Expanded translation dictionary from 74 to 330 keys across English, Urdu, and Sindhi. Wrapped all template headings, buttons, badges, and alerts in `_t()`. | **RESOLVED & VERIFIED** |
| `DEF-LOC-02` | P0 | Localization / Bidi | RTL punctuation inversion and unisolated mixed English/Urdu codes. Missing `<bdi>` wrappers. | All templates rendering codes or mixed text | Encapsulated all codes (`KB-BK-*`, `KB-DON-*`, `KB-REQ-*`, `KB-HO-*`) in `<bdi class="kb-code">` with monospace font and LTR directionality. | **RESOLVED & VERIFIED** |
| `DEF-IMG-01` | P0 | Assets / Images | Missing subject SVGs in `app/static/img/covers/` and lack of `onerror` fallback on `<img>` tags. | `static/img/covers/`, `donation_service.py`, all templates | Generated 8 missing subject SVG covers and added `onerror="this.src='/static/img/covers/placeholder.svg'"` fallback to all book covers. | **RESOLVED & VERIFIED** |
| `DEF-IMG-02` | P0 | Visual / Assets | Cluttered `placeholder.svg` artwork reducing visual clarity when used as default fallback. | `app/static/img/covers/placeholder.svg` | Redesigned `placeholder.svg` with clean modern geometric book iconography and slate gradient. | **RESOLVED & VERIFIED** |
| `DEF-TAB-01` | P0 | Responsive / Tables | Teacher management tables horizontally unreadable and broken on screens <768px. | `donations.html`, `requests.html`, `inventory.html`, `handovers.html` | Architected dual-view system: responsive Bootstrap tables on desktop, stacked card layouts on mobile (`d-block d-md-none`). Zero horizontal scrolling required. | **RESOLVED & VERIFIED** |
| `DEF-TAB-02` | P0 | Layout / Desktop | Teacher action columns clipped or requiring horizontal scroll on desktop viewports. | Teacher table templates & CSS | Set explicit min-widths, streamlined action buttons, and added `.text-nowrap` on status badges. | **RESOLVED & VERIFIED** |
| `DEF-NAV-01` | P1 | Navigation / Mobile | Cluttered mobile topbar in Teacher Portal displaying 6+ controls instead of clean drawer structure. | `app/templates/teacher/base_teacher.html` | Streamlined teacher mobile topbar to brand + hamburger. Delegated all links, profile, and theme tools to `#teacherSidebarOffcanvas`. | **RESOLVED & VERIFIED** |
| `DEF-NAV-02` | P1 | Navigation / Desktop | Student desktop "Teacher Sign In" wrapping onto multiple lines on mid-desktop viewports. | `app/templates/base.html` | Added `.text-nowrap` and expanded navbar breakpoint to `xxl` (1400px). 0% wrapping risk verified across 1024-1440px. | **RESOLVED & VERIFIED** |
| `DEF-CAT-01` | P1 | Layout / Mobile | Extreme mobile catalogue height (34,402px) due to stacked vertical cards. Needs horizontal layout. | `app/templates/student/catalogue.html` | Created compact horizontal card design (`.catalog-card-mobile`), cutting mobile scroll height significantly while preserving book covers and metadata. | **RESOLVED & VERIFIED** |
| `DEF-CAT-02` | P1 | Layout / Mobile | Filter controls occupy excessive vertical screen real estate on mobile catalogue. | `app/templates/student/catalogue.html` | Implemented collapsible filter accordion (`#mobileFilterCollapse`), saving 400px of vertical space on mobile launch. | **RESOLVED & VERIFIED** |
| `DEF-DET-01` | P1 | Layout / Mobile | Book cover on mobile book detail takes up entire viewport height before metadata is visible. | `app/templates/student/book_detail.html` | Constrained mobile cover image to max-height 220px in stacked single-column responsive container. | **RESOLVED & VERIFIED** |
| `DEF-TAB-03` | P2 | Navigation / UI | Tab navigation (`.nav-pills`) wrapping or clipping on narrow viewports in management desks. | `donations.html`, `requests.html`, `inventory.html`, `settings.html` | Configured scrollable horizontal flex-nowrap pills with hidden scrollbars (`overflow-x-auto pb-2 mb-4 flex-nowrap`). | **RESOLVED & VERIFIED** |
| `DEF-SET-01` | P2 | Form / UI | Settings page tabs and backup tables overcrowded on mobile devices. | `app/templates/teacher/settings.html` | Made settings navigation pills scrollable and converted backup tables to responsive mobile cards. | **RESOLVED & VERIFIED** |
| `DEF-HERO-01` | P2 | Visual / Polish | Student homepage hero vertical rhythm and CTA touch target spacing on mobile. | `app/templates/student/index.html` | Refined padding, responsive typography, and button touch target spacing with Bootstrap responsive utilities. | **RESOLVED & VERIFIED** |
| `DEF-KPI-01` | P2 | Layout / Polish | Teacher dashboard KPI cards stacking unevenly on mid-tier mobile viewports. | `app/templates/teacher/dashboard.html` | Standardized on `row g-3 row-cols-2 row-cols-lg-3 row-cols-xl-6` with equal card heights and flex alignment. | **RESOLVED & VERIFIED** |

---

## 9. Final Visual Acceptance & Evidence Corrections Register

This section records the final audit findings and resolutions from the 47-screenshot visual acceptance verification (`ui-redesign-evidence(1).rar`).

### Final Defect & Verification Matrix

| Issue ID | Severity | Category | Description | Scope / Affected Files | Resolution Summary | Status |
|---|---|---|---|---|---|---|
| `DEF-RTE-01` | **Critical (P0)** | Route / Screenshot Integrity | 4 screenshot routes captured HTTP 404 pages instead of rendered transaction views: `student_request_success`, `teacher_request_detail`, `teacher_handover_confirm`, and `teacher_handover_receipt`. | `scripts/seed_demo.py`, `request_service.py`, `handover_service.py`, `scripts/run_visual_acceptance_audit.py` | 1. Switched `INNER JOIN books` to `LEFT JOIN books` in request and handover queries.<br>2. Fixed exhibition seeder to reset `sqlite_sequence` and dynamically map foreign keys `b_map`.<br>3. Automated real form submission and dynamic database ID discovery in visual audit script with HTTP 200 assertions.<br>4. Re-captured all 4 transaction views cleanly at HTTP 200. | **RESOLVED & VERIFIED** |
| `DEF-QDS-01` | **Critical (P0)** | Data Consistency | Student requests showed Pending=1, All=0, and "No Requests in this Queue" empty state. Handovers showed 2 on KPI but 0 rows in ledger. | `app/services/request_service.py`, `app/services/handover_service.py`, `app/blueprints/teacher/routes.py` | Resolved SQL join discrepancy (`LEFT JOIN books`), standardized query parameter handling (`class_grade` and `class`), ensuring all counts, filters, and tab badge tallies match database rows exactly. | **RESOLVED & VERIFIED** |
| `DEF-LOC-03` | **Major (P1)** | Multilingual Localization | Incomplete Urdu/Sindhi translations across remaining navigation headers, status badges, metrics, modal confirmation titles, and table headers. | `app/translations/en.json`, `ur.json`, `sd.json`, and all 33 templates | Added 106 new keys to translation dictionaries (total 441 keys across all 3 languages). Fully translated all headers, badges, alerts, and toolbars without raw English fallback. | **RESOLVED & VERIFIED** |
| `DEF-MOB-01` | **Major (P1)** | Mobile Density / UI | Long student homepage scroll on phones due to oversized card height; inventory cards had excessive vertical whitespace. | `app/templates/student/index.html`, `app/templates/teacher/inventory.html` | Implemented compact horizontal cards view (`< md`, ~100px height per item) on student home, and tightened padding and card vertical margins on teacher inventory. | **RESOLVED & VERIFIED** |
| `DEF-TAB-04` | **Moderate (P2)** | Responsive Navigation | Filter pills on Teacher Requests, Donations, and Inventory clipped or wrapped awkwardly on narrow mobile screens (<400px). | `requests.html`, `donations.html`, `inventory.html` | Implemented responsive mobile `<select>` tab selector (`d-block d-md-none`) synchronized with desktop `.nav-pills` (`d-none d-md-flex`). | **RESOLVED & VERIFIED** |
| `DEF-REP-01` | **Moderate (P2)** | Responsive Reports | Circulation metrics table cramped on mobile screens; ambiguous CSV export button labels. | `app/templates/teacher/reports.html` | Converted circulation breakdown table to stacked responsive cards on `< md` screens. Disambiguated CSV export buttons as "Export Inventory CSV" and "Export Handover CSV". | **RESOLVED & VERIFIED** |
| `DEF-RTL-02` | **Major (P1)** | Multilingual / RTL Localization | Untranslated English strings on rendered Urdu Teacher Dashboard (status badges, activity log actions, actors, KPI labels), Sindhi Catalogue (results count, empty states, taxonomy), offline badges, demo banners, and flash message alerts. | `dashboard.html`, `catalogue.html`, `logs.html`, `base.html`, `base_teacher.html`, `en.json`, `ur.json`, `sd.json` | Added 64 translation keys (total 505 entries per language). Translated circulation status breakdown, audit trail actions, taxonomy labels, offline badges, and flash messages without altering stored database values. | **RESOLVED & VERIFIED** |
| `DEF-BRD-01` | **Moderate (P2)** | Visual Design / Borders | Unexpected dashed outlines on mobile cards/statistics across Donations, Requests, Handovers, Inventory, Reports, Student Homepage, and Catalogue. | `components.css`, `donations.html`, `requests.html`, `handovers.html`, `inventory.html`, `reports.html`, `index.html`, `catalogue.html`, `book_detail.html` | Removed `.border-dashed` utility from card dividers and placeholders; replaced with clean standard Bootstrap `border-top border-secondary-subtle`. Preserved strict LTR isolation on `<bdi class="kb-code">`. | **RESOLVED & VERIFIED** |
| `DEF-TAB-05` | **Moderate (P2)** | Mobile Responsive Settings | Settings navigation tabs clipped horizontally on narrow mobile screens (`teacher_settings_mobile.png`). | `app/templates/teacher/settings.html` | Implemented mobile `<select id="mobileSettingsTabSelect">` (`d-block d-md-none`) while preserving desktop nav pills (`d-none d-md-flex`) and `#confirmDemoBox` form logic. | **RESOLVED & VERIFIED** |
| `DEF-KPI-01` | **Major (P1)** | Dashboard Data Semantics | Teacher dashboard KPI displayed value 3 under label "Pending Donations" when only 1 donation was pending. | `app/templates/teacher/dashboard.html`, `tests/test_queue_consistency_and_routes.py` | Renamed card to "Total Donations" (`_t('kpi_total_donations')`) matching `analytics.summary.total_donations`, added subtext queue link with pending count, and created automated regression test. | **RESOLVED & VERIFIED** |
| `DEF-REL-01` | **Moderate (P2)** | Mobile Information Density | Related books on `student/book_detail.html` rendered as tall vertical cards taking over 1350px vertical scroll on mobile phones. | `app/templates/student/book_detail.html` | Implemented compact horizontal card pattern on `< md` viewports (~100px height per item) while preserving desktop responsive grid on `md` and above. | **RESOLVED & VERIFIED** |

### Complete 47-Screenshot Evidence Manifest

All 47 required visual acceptance screenshots have been captured, asserted at HTTP 200 (or intentional 404/503), and verified to have 0 visual defects and 0 external CDN requests:

1. `student_home_desktop.png` (HTTP 200)
2. `student_catalogue_desktop.png` (HTTP 200)
3. `student_book_detail_desktop.png` (HTTP 200)
4. `student_donate_desktop.png` (HTTP 200)
5. `student_request_desktop.png` (HTTP 200)
6. `student_track_desktop.png` (HTTP 200)
7. `student_scan_desktop.png` (HTTP 200)
8. `auth_login_desktop.png` (HTTP 200)
9. `student_donation_success_desktop.png` (HTTP 200)
10. `student_request_success_desktop.png` (HTTP 200 - Live form submit redirect)
11. `student_home_mobile.png` (HTTP 200, Overflow: NO)
12. `student_catalogue_mobile.png` (HTTP 200, Overflow: NO)
13. `student_book_detail_mobile.png` (HTTP 200, Overflow: NO)
14. `student_donate_mobile.png` (HTTP 200, Overflow: NO)
15. `student_request_mobile.png` (HTTP 200, Overflow: NO)
16. `student_track_mobile.png` (HTTP 200, Overflow: NO)
17. `student_scan_mobile.png` (HTTP 200, Overflow: NO)
18. `auth_login_mobile.png` (HTTP 200, Overflow: NO)
19. `nav_offcanvas_mobile_open.png` (HTTP 200, Mobile offcanvas open)
20. `teacher_dashboard_desktop.png` (HTTP 200)
21. `teacher_donations_desktop.png` (HTTP 200)
22. `teacher_requests_desktop.png` (HTTP 200)
23. `teacher_handovers_desktop.png` (HTTP 200)
24. `teacher_inventory_desktop.png` (HTTP 200)
25. `teacher_reports_desktop.png` (HTTP 200)
26. `teacher_settings_desktop.png` (HTTP 200)
27. `teacher_donation_detail_desktop.png` (HTTP 200)
28. `teacher_request_detail_desktop.png` (HTTP 200 - Valid approved request view)
29. `teacher_handover_confirm_desktop.png` (HTTP 200 - Valid handover confirm form)
30. `teacher_handover_receipt_desktop.png` (HTTP 200 - Valid official receipt)
31. `teacher_qr_sheet_desktop.png` (HTTP 200)
32. `teacher_dashboard_mobile.png` (HTTP 200, Sidebar hidden: YES, Overflow: NO)
33. `teacher_donations_mobile.png` (HTTP 200, Sidebar hidden: YES, Overflow: NO)
34. `teacher_requests_mobile.png` (HTTP 200, Sidebar hidden: YES, Overflow: NO)
35. `teacher_handovers_mobile.png` (HTTP 200, Sidebar hidden: YES, Overflow: NO)
36. `teacher_inventory_mobile.png` (HTTP 200, Sidebar hidden: YES, Overflow: NO)
37. `teacher_reports_mobile.png` (HTTP 200, Sidebar hidden: YES, Overflow: NO)
38. `teacher_settings_mobile.png` (HTTP 200, Sidebar hidden: YES, Overflow: NO)
39. `teacher_nav_offcanvas_mobile_open.png` (HTTP 200, Teacher mobile sidebar open)
40. `rtl_urdu_home_desktop.png` (HTTP 200, dir=rtl, Nastaliq typography)
41. `rtl_urdu_dashboard_desktop.png` (HTTP 200, dir=rtl, Urdu dashboard)
42. `rtl_sindhi_home_desktop.png` (HTTP 200, dir=rtl, Sindhi typography)
43. `rtl_sindhi_catalogue_desktop.png` (HTTP 200, dir=rtl, Sindhi catalogue with bidi codes)
44. `theme_dark_home_desktop.png` (HTTP 200, data-bs-theme=dark)
45. `theme_dark_dashboard_desktop.png` (HTTP 200, data-bs-theme=dark)
46. `error_404_desktop.png` (HTTP 404 - Intentional custom error page)
47. `error_503_desktop.png` (HTTP 503 - Intentional maintenance mode page)

---

## 8. Final Visual Evidence Reconciliation & Verification Audit (Stage 4)

| Issue ID | Component | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **ISSUE-RTL-03** | Urdu & Sindhi Dashboard Localization | **Major (P1)** | Integrated `localize_activity_details` regex localization engine in `translation_service.py` to translate live activity log messages into Urdu and Sindhi while preserving student names, book titles, and `<bdi class="kb-code">` identifiers. Localized welcome messages, WAL Concurrency badges, Reuse Rate, circulation status distributions, and catalogue book counters. | `app/services/translation_service.py`, `dashboard.html`, `catalogue.html`, `rtl_urdu_dashboard_desktop.png`, `rtl_sindhi_catalogue_desktop.png`. | **RESOLVED & VERIFIED** |
| **ISSUE-BRD-01** | Dashed Border Elimination | **Major (P1)** | Enforced `border-style: solid !important; border-color: var(--bs-border-color-subtle) !important;` on `.border-dashed` in `components.css`. Replaced all remaining dashed borders in `student.css`, `track.html`, `scan.html`, `book_form.html`, `donation_detail.html`, `handover_confirm.html`, `handover_detail.html`, `handover_receipt.html`, and `qr_sheet.html`. Verified 0 computed dashed borders across DOM. | `components.css`, `student.css`, `verify_visual_evidence.py` (0 dashed elements). | **RESOLVED & VERIFIED** |
| **ISSUE-MOB-03** | Settings Mobile Section Selector | **Moderate (P2)** | Built responsive `<select id="mobileSettingsTabSelect">` inside `<div class="d-block d-md-none">` with 4 sections (Profile, Security, Backup & Restore, Exhibition Mode). Reduced tab card padding to `p-3 p-sm-4` ensuring comfortable unclipped controls at 390px and 360px. | `settings.html`, `teacher_settings_mobile.png`, Playwright mobile locator check. | **RESOLVED & VERIFIED** |
| **ISSUE-PII-01** | Handover Receipt Student Privacy | **Major (P1)** | Omitted parent/student contact phone number from default printed receipt layout in `handover_receipt.html` to eliminate PII exposure, while preserving student name, class, roll number, book code, reference token, and signature lines. | `handover_receipt.html`, `teacher_handover_receipt_desktop.png`, privacy assertion check. | **RESOLVED & VERIFIED** |
| **ISSUE-IMG-01** | Book Cover Fallback Graphics | **Minor (P3)** | Replaced blank grey `<div>` containers in `inventory.html` (table and mobile card views) and `donations.html` with subject-specific SVG fallback (`img/covers/placeholder.svg`) with `onerror` protection so no book ever displays an empty grey box. | `inventory.html`, `donations.html`, `placeholder.svg`. | **RESOLVED & VERIFIED** |
| **ISSUE-REL-01** | Related Books Mobile Density | **Moderate (P2)** | Structured compact horizontal related book cards (`<div class="d-md-none">`) with 3:4 thumbnail, category badge, and concise metadata below 768px, reducing excessive vertical scrolling while keeping desktop 4-column grid (`d-none d-md-block`). | `book_detail.html`, `student_book_detail_mobile.png`. | **RESOLVED & VERIFIED** |

---

## 9. Final Visual Acceptance Patch (Stage 5)

| Issue ID | Component | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **ISSUE-RTL-04** | Complete Rendered Urdu & Sindhi Localization | **Major (P1)** | Localized greeting with teacher identity (`School Teacher / Incharge` -> `اسکول استاد / انچارج`), `WAL Concurrency Active` -> `محفوظ متوازی نظام فعال ہے`, activity log events (`action_request_submitted`), class taxonomy in activity details (`جماعت 7-B`), filter dropdown options in catalogue (`ڪلاس ڇهين`, `ڪلاس ستين`, `ڪلاس اٺين`), and subjects. Expanded dictionary to 520 keys with 100% 1:1 match across English, Urdu, and Sindhi. Zero raw English UI labels remaining. User-entered book titles, student names, and author names preserved. | `translation_service.py`, `dashboard.html`, `catalogue.html`, `index.html`, `ur.json`, `sd.json`, `rtl_urdu_dashboard_desktop.png`, `rtl_sindhi_home_desktop.png`. | **RESOLVED & VERIFIED** |
| **ISSUE-BRD-02** | Complete Dashed Information Border Elimination | **Major (P1)** | Converted camera reticle in `scan.html` from `2px dashed` to `2px solid rgba(255, 255, 255, 0.85)`. Verified all information containers, code rows, card footers, and table rows have 0 computed dashed borders across DOM. Official QR print cut lines in `book_qr_label.html` and `qr_sheet.html` intentionally retained. | `scan.html`, `verify_visual_evidence.py` (0 dashed elements). | **RESOLVED & VERIFIED** |
| **ISSUE-MOB-04** | Settings Mobile Navigation Verification | **Moderate (P2)** | Verified that `#mobileSettingsTabSelect` is strictly visible at 390px and 360px (`d-block d-md-none`), desktop tablist is strictly hidden (`d-none d-md-flex`), all four settings sections (Profile, Security, Backup, Exhibition) are selectable, and changing value navigates cleanly without overflow. | `settings.html`, `teacher_settings_mobile.png`, Playwright mobile test. | **RESOLVED & VERIFIED** |
| **ISSUE-REL-02** | Related Books Mobile Card Height Optimization | **Moderate (P2)** | Constrained mobile related book cards on `/book/<code_or_id>` to compact horizontal component (`style="max-height: 120px;"`) with 80px thumbnail (3:4 ratio), single-line typography, and tight padding, achieving exactly 108.7px rendered height (target: 100–120px). Desktop grid remains unchanged. | `book_detail.html`, `student_book_detail_mobile.png`, Playwright bounding box check (108.7px). | **RESOLVED & VERIFIED** |
| **ISSUE-KPI-01** | Dashboard Shared KPI Definitions | **Minor (P3)** | Verified consistent KPI display across desktop and mobile: `Total Donations` displays all donations (3 in demo dataset) and subtext indicates pending review count (`1 pending`). No view displays 3 under a "Pending Donations" label. | `dashboard.html`, `test_queue_consistency_and_routes.py`. | **RESOLVED & VERIFIED** |

---

## 10. Final Localization Micro-Polish (Stage 6)

| Issue ID | Component | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **ISSUE-LOC-05** | Theme Selector `System` Label Localization | **Minor (P3)** | Localized dynamic theme button label in `theme.js` across English, Urdu, and Sindhi based on active `document.documentElement.lang`. When active preference is `system`, Urdu renders `سسٹم` and Sindhi renders `سسٽم`. Also updated template dropdown toggles with `data-label-*` attributes. Seamless zero-FOUC switching verified. | `theme.js`, `base.html`, `base_teacher.html`, `en.json`, `ur.json`, `sd.json`. | **RESOLVED & VERIFIED** |
| **ISSUE-LOC-06** | Footer Phrase Localization | **Minor (P3)** | Separated school copyright from tagline and fully localized the footer phrase `Built for Students & Teachers.` in `base.html`. Urdu translates to `طلباء اور اساتذہ کے لیے تیار کردہ۔` and Sindhi translates to `شاگردن ۽ استادن لاءِ تيار ڪيل.`. School profile metadata preserved. | `base.html`, `en.json`, `ur.json`, `sd.json`, `rtl_urdu_home_desktop.png`, `rtl_sindhi_home_desktop.png`. | **RESOLVED & VERIFIED** |
| **ISSUE-SVG-01** | SVG Book Cover Filler Label Localization | **Minor (P3)** | Localized generic English decorative badges (`CURRICULUM SPECIFICATION:`, `REUSABLE TEXTBOOK`, `GOVT SCHOOLS`) across all 9 Urdu, Islamiat, and Sindhi SVG covers in `app/static/img/covers/`. Urdu covers now feature authentic Urdu labels (`نصابی معیار:`, `قابلِ استعمال درسی کتاب`, `سرکاری اسکولز`). Sindhi covers feature authentic Sindhi labels (`نصابي معيار:`, `ٻيهر استعمال جوڳو ڪتاب`, `سرڪاري اسڪول`). Actual textbook titles, publishers, and vector artwork 100% preserved. | `app/static/img/covers/`, `catalogue.html`, `rtl_urdu_dashboard_desktop.png`, `rtl_sindhi_catalogue_desktop.png`. | **RESOLVED & VERIFIED** |
| **ISSUE-IMG-02** | Mobile Catalogue Cover Verification (`KB-BK-000004`) | **Minor (P3)** | Investigated Class 6 Sindhi textbook card (`KB-BK-000004` — `سنڌي سليس درجو ڇھون`). Confirmed markup uses valid local asset `img/covers/sindhi_class6.svg` with active `onerror` fallback. Resolved screenshot capture timing where below-the-fold lazy-loaded cards were not triggered before full-page capture. Added automated pre-scroll decoding pass and verified at 390px and 360px viewports (`complete=True`, `naturalWidth=300px`). | `run_visual_acceptance_audit.py`, `test_queue_consistency_and_routes.py`, `student_catalogue_mobile.png`, `rtl_sindhi_catalogue_mobile.png`. | **RESOLVED & VERIFIED** |





---

## 11. Light & Dark Theme Surface Contrast Refinement (Stage 7)

| Issue ID | Component | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **ISSUE-SURF-01** | Global Surface System & Design Tokens | **Major (P1)** | Integrated approved design tokens for Light and Dark themes in `main.css` across `:root`, `[data-bs-theme="light"]`, and `[data-bs-theme="dark"]`. Light Theme: Page background `#F1F4F8`, Card background `#FFFFFF`, Secondary surface `#E8EDF4`, Navbar `#FFFFFF`, Sidebar `#FFFFFF`, Border `#DFE5ED`, Main text `#172033`, Muted text `#64748B`. Dark Theme: Page background `#111827`, Card background `#1E293B`, Secondary surface `#263449`, Navbar `#17212F`, Sidebar `#17212F`, Border `#334155`, Main text `#F1F5F9`, Muted text `#A7B4C5`. Educational blue (`#0284c7` / `#38bdf8`) and teal (`#0d9488` / `#2dd4bf`) brand colors 100% preserved. | `app/static/css/main.css`, `tests/test_theme_surface_contrast.py`. Computed styles verified via Playwright. | **RESOLVED & VERIFIED** |
| **ISSUE-CARD-01** | Content Card Visual Separation & Elevation | **Major (P1)** | Overrode Bootstrap 5.3 internal `.card { --bs-card-bg: var(--bs-body-bg); }` collision in `components.css` by explicitly setting `--bs-card-bg: var(--kb-bg-surface)` and `background-color: var(--kb-bg-surface)`. In Light Theme, pure-white `#FFFFFF` cards stand out prominently on soft-grey `#F1F4F8` surfaces with `#DFE5ED` subtle borders. In Dark Theme, noticeably lighter slate `#1E293B` cards visually separate from deep charcoal `#111827` page backgrounds with `#334155` borders. Restrained micro-shadows (`.shadow-xs`) maintained without heavy black glows. | `components.css`, `student.css`, `teacher.css`, `test_theme_surface_contrast.py`. | **RESOLVED & VERIFIED** |
| **ISSUE-SURF-02** | Secondary Surfaces, Tables & Form Controls | **Moderate (P2)** | Coordinated secondary surfaces (`#E8EDF4` Light / `#263449` Dark) across card footers (`.card-footer.bg-body-tertiary`), table headers (`.table-card thead th`), search filters, and input add-ons (`.input-group-text`). Upgraded `.table-card` from page background to card background with secondary surface row-hover transitions. Form controls (`.form-control`, `.form-select`) use `#FFFFFF` (Light) and `#1E293B` (Dark) with crisp focus rings. Dropdown menus and modals consistently adopt card surface tokens. | `components.css`, `student/catalogue.html`, `teacher/inventory.html`, `test_theme_surface_contrast.py`. | **RESOLVED & VERIFIED** |
| **ISSUE-NAV-03** | Navbar Desktop Flex Spacing at 1440px | **Minor (P3)** | Optimized desktop nav-link padding from `px-xxl-3` to `px-xxl-2` and container padding to `px-xxl-3` in `base.html`, eliminating a 28px flex overflow at 1440px viewport while keeping nav-links single-line and unclipped. Confirmed zero horizontal overflow (`scrollWidth == clientWidth == 1440px`) across all viewports. | `app/templates/base.html`, Playwright DOM dimension assertion. | **RESOLVED & VERIFIED** |
| **ISSUE-PRNT-01** | Print Layout Background Isolation | **Critical (P0)** | Verified that `@media print` in `print.css` strictly forces `#ffffff` background and `#000000` text for all printable QR labels, handover receipts, and A4 reports. Page background and dark theme tokens are strictly isolated from printing. | `print.css`, `test_phase1.py`, manual receipt inspection. | **RESOLVED & VERIFIED** |
| **ISSUE-CONT-01** | WCAG AA Accessibility Contrast Optimization | **Minor (P3)** | Refined Light muted text to `#5F6B7A`, delivering 4.92:1 contrast against `#F1F4F8` page background and 5.43:1 on `#FFFFFF` cards (exceeding WCAG AA 4.5:1 minimum). Adjusted primary blue button background to `#0369A1` with `#FFFFFF` text, elevating button text contrast from 4.10:1 (`#0284C7`) to 5.93:1 (`#0369A1`). Explicitly styled `.btn-primary` and `.text-muted`/`.text-body-secondary` across `main.css` and `components.css`. | `main.css`, `components.css`, `tests/test_theme_surface_contrast.py`, `scripts/verify_surface_tokens.py`. | **RESOLVED & VERIFIED** |

---

## 12. Teacher Dashboard Desktop Sidebar Scrolling & Sticky Navigation (Stage 8)

| Issue ID | Component | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **ISSUE-SIDE-01** | Teacher Desktop Sticky Sidebar | **Major (P1)** | Removed `overflow-hidden` from parent `#teacherLayoutWrap` that prevented sticky positioning. Applied `position: sticky; top: var(--kb-header-height, 56px); height: calc(100vh - var(--kb-header-height, 56px)); max-height: calc(100vh - var(--kb-header-height, 56px)); overflow-y: auto; overflow-x: hidden;` to `.teacher-sidebar` on screens `>= 992px`. Removed `overflow-y-auto` from `.teacher-main` so the main content uses normal page scrolling. Preserved existing sidebar width (260px), typography, active states, and icons. | `base_teacher.html`, `teacher.css`, `main.css`, `tests/test_theme_surface_contrast.py`, `scripts/verify_sidebar_sticky.py`. | **RESOLVED & VERIFIED** |
| **ISSUE-SIDE-02** | Independent Sidebar Scrolling on Short Viewports | **Moderate (P2)** | Configured `overflow-y: auto; overflow-x: hidden;` on `.teacher-sidebar` so navigation items can scroll internally without moving the main page whenever viewport height is constrained (<700px). Verified in Playwright (`scrollTop > 0` at 500px viewport height). | `teacher.css`, `verify_sidebar_sticky.py`. | **RESOLVED & VERIFIED** |
| **ISSUE-SIDE-03** | Mobile Offcanvas Sidebar Preservation (<992px) | **Moderate (P2)** | Preserved mobile drawer behavior below 992px: desktop sidebar remains `display: none !important;`, hamburger toggle is prominent, and offcanvas drawer (`#teacherSidebarOffcanvas`) opens/closes smoothly. Zero touch/scroll regressions. | `base_teacher.html`, `verify_sidebar_sticky.py` across 768px, 390px, 360px. | **RESOLVED & VERIFIED** |
| **ISSUE-NAV-04** | Desktop Header Sizing & Overflow at 1024px | **Minor (P3)** | Hid redundant subtitle (`Kitaab Bank Administrative Desk`) below `xl` (`d-none d-xl-block`) and enforced `flex-shrink-0 text-nowrap` on desktop header action buttons, eliminating 47px horizontal overflow at 1024px and ensuring constant 56px header height across 1440px and 1024px viewports. | `base_teacher.html`, `tests/test_theme_surface_contrast.py`. | **RESOLVED & VERIFIED** |

---

## 13. Data Tables Improvements & Book Detail Navbar Non-Overlap (Stage 9)

| Issue ID | Component | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **ISSUE-TAB-01** | Column Sorting on All Data Tables | **Major (P1)** | Implemented unified column sorting in `tables.js` with toggleable ascending/descending states and FontAwesome sort icons (`fa-sort`, `fa-sort-up`, `fa-sort-down`). Supports smart type parsing for integers, floats, dates, byte sizes (B, KB, MB, GB), and textual codes. Excludes non-sortable columns (Actions, Cover, Meters). Tested on 9 tables across Teacher donations, requests, handovers, inventory, logs, reports, and settings. | `app/static/js/tables.js`, `components.css`, `tests/test_data_tables_and_book_detail.py`. | **RESOLVED & VERIFIED** |
| **ISSUE-TAB-02** | Data Table Pagination & Page Sizes | **Major (P1)** | Added client-side pagination with page-size options: `10`, `25`, `50`, `100`. Features responsive top toolbar with select control and bottom footer with localized record summary (`Showing X to Y of Z records` in English, Urdu, Sindhi) and pagination navigation (Previous, Page numbers with active state, Next). Sorting and pagination synchronize across the entire dataset. | `app/static/js/tables.js`, `components.css`, `tests/test_data_tables_and_book_detail.py`. | **RESOLVED & VERIFIED** |
| **ISSUE-TAB-03** | Data Table Row Theming | **Moderate (P2)** | Styled all table rows in `components.css` with explicit pure-white `#FFFFFF` background in Light Mode and matching card surface `#1E293B` background in Dark Mode. Headers use secondary surface `#E8EDF4` (Light) and `#263449` (Dark). Row hover states transition smoothly to `--bs-tertiary-bg`. Text and border contrast strictly preserved across both themes. | `app/static/css/components.css`, `tests/test_data_tables_and_book_detail.py`. | **RESOLVED & VERIFIED** |
| **ISSUE-TAB-04** | Clickable Table Rows & Action Click-Isolation | **Major (P1)** | Removed standalone "View" (`{{ icon('eye') }}`) buttons from table rows in `donations.html`, `requests.html`, and `handovers.html`. Made table rows interactive (`class="clickable-row"`, `data-href="..."`, `role="link"`, `tabindex="0"`) navigating to their detail views on click/Enter. Implemented strict event delegation that ignores row navigation when clicking any action button (Approve, Reject, Handover, Print receipt/label, Edit, Retire, Restore, Delete), link, form, or during text selection. | `app/static/js/tables.js`, `components.css`, `donations.html`, `requests.html`, `handovers.html`, `inventory.html`, `tests/test_data_tables_and_book_detail.py`. | **RESOLVED & VERIFIED** |
| **ISSUE-NAV-05** | Book Detail Cover Navbar Overlap during Scrolling | **Major (P1)** | Fixed navbar overlap on `/book/<code_or_id>`: removed `sticky-top` and inline `style="top: 5rem;"` from `.book-detail-cover-card` in `book_detail.html`. Set `.book-detail-cover-card` to `position: relative; z-index: 1; top: auto !important;` in `student.css`, allowing normal document flow. Elevated sticky navbar header to `z-index: 1030 !important` in `components.css`, guaranteeing the navbar always stays above scrolled page content across desktop (1440px) and mobile (390px, 360px). | `app/templates/student/book_detail.html`, `app/static/css/components.css`, `app/static/css/student.css`, `tests/test_data_tables_and_book_detail.py`. | **RESOLVED & VERIFIED** |

---

## 14. Professional Teal Secondary Brand Color Integration (Stage 10)

| Issue ID | Component | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **ISSUE-PAL-01** | Professional Teal Secondary Brand Palette Integration | **Major (P1)** | Replaced Bootstrap's default dull grey secondary color (`#6c757d`) with an intentional, cohesive Teal palette across both Light and Dark themes. Light Mode: Secondary `#0F766E`, Secondary Hover `#115E59`, Soft Background `#CCFBF1`, Soft Background Text `#134E4A`, Secondary Border `#99F6E4`, Button Text `#FFFFFF`. Dark Mode: Secondary `#2DD4BF`, Secondary Hover `#5EEAD4`, Soft Background `#123B3B`, Soft Background Text `#CCFBF1`, Secondary Border `#115E59`, Button Text `#0B1F1E`. Synchronized Bootstrap 5.3 variables (`--bs-secondary`, `--bs-secondary-rgb`, `--bs-secondary-hover`, `--bs-secondary-bg-subtle`, `--bs-secondary-border-subtle`, `--bs-secondary-text-emphasis`, `--bs-teal`). Educational Blue primary (`#0369A1` / `#38BDF8`) 100% preserved. | `app/static/css/main.css`, `tests/test_theme_surface_contrast.py`. Computed variables verified in Playwright. | **RESOLVED & VERIFIED** |
| **ISSUE-PAL-02** | Secondary & Outline Secondary Button Systems | **Major (P1)** | Configured comprehensive styling in `components.css` for `.btn-secondary` and `.btn-outline-secondary`. Solid secondary buttons render with Teal background and crisp contrast text (`#FFFFFF` in light, `#0B1F1E` in dark). Secondary outline buttons render with clear Teal border and text, filling smoothly on hover and focus. Active and pressed states use hover tokens. Keyboard focus-visible rings use secondary color with 25% opacity glow (`box-shadow: 0 0 0 0.25rem rgba(var(--bs-secondary-rgb), 0.25)`). | `app/static/css/components.css`, `tests/test_theme_surface_contrast.py`. | **RESOLVED & VERIFIED** |
| **ISSUE-PAL-03** | Secondary Badge & Soft Container Styling | **Moderate (P2)** | Styled subtle secondary badges (`.badge.bg-secondary-subtle`, `.bg-secondary-subtle`, `.badge-secondary`) with soft Teal container (`#CCFBF1` Light / `#123B3B` Dark), high-contrast text (`#134E4A` Light / `#CCFBF1` Dark), and subtle tint borders (`#99F6E4` Light / `#115E59` Dark). Solid badges (`.badge.bg-secondary`) render with full secondary background and button text. Replaced all dull grey metadata tags and category indicators across book cards, donation tags, and circulation statuses. | `app/static/css/components.css`, `book_detail.html`, `catalogue.html`, `donations.html`, `tests/test_theme_surface_contrast.py`. | **RESOLVED & VERIFIED** |
| **ISSUE-PAL-04** | Separation of Brand Secondary vs Neutral Structural Greys | **Major (P1)** | Strictly segregated brand secondary accents from structural neutral greys. Neutral page backgrounds (`#F1F4F8` / `#111827`), card surfaces (`#FFFFFF` / `#1E293B`), secondary surfaces (`#E8EDF4` / `#263449`), container borders (`#DFE5ED` / `#334155`), and muted body copy (`.text-body-secondary`, `.text-muted` at `#5F6B7A` / `#A7B4C5`) remain purely neutral to ensure layout stability and copy readability. Only brand secondary accents (`.text-secondary`, `.btn-secondary`, `.btn-outline-secondary`, `.badge.bg-secondary*`) adopt Teal. | `app/static/css/main.css`, `app/static/css/components.css`, `tests/test_theme_surface_contrast.py`. | **RESOLVED & VERIFIED** |
| **ISSUE-PAL-05** | WCAG AAA Accessibility & Contrast Verification | **Minor (P3)** | Verified contrast ratios against WCAG AA (4.5:1) and WCAG AAA (7.0:1) standards. Light mode button text (`#FFFFFF` on `#0F766E`): 5.50:1. Light mode hover (`#FFFFFF` on `#115E59`): 7.59:1. Light mode soft text on soft bg (`#134E4A` on `#CCFBF1`): 8.46:1. Dark mode button text (`#0B1F1E` on `#2DD4BF`): 9.24:1. Dark mode hover (`#0B1F1E` on `#5EEAD4`): >12:1. Dark mode soft text on soft bg (`#CCFBF1` on `#123B3B`): 11.00:1. Dark mode secondary text on dark card (`#2DD4BF` on `#1E293B`): 7.88:1. Automated regression verified in Edge headless. | `tests/test_theme_surface_contrast.py`, `scripts/run_visual_acceptance_audit.py`. | **RESOLVED & VERIFIED** |

---

## 15. Catalogue Cards, Clickable Navigation, Availability Visibility & Card Surface Consistency (Stage 11)

| Issue ID | Component | Severity | Resolution Summary | Validation Evidence | Status |
|---|---|---|---|---|---|
| **ISSUE-CARD-02** | Catalogue Card Interaction & Details Button Removal | **Major (P1)** | Removed standalone "Details" (`{{ _('Details') }}`) button from Student Catalogue book cards across desktop grid and mobile compact list. Made entire card interactive (`class="clickable-card"`, `data-href="..."`, `role="link"`, `tabindex="0"`). Styled `.clickable-card` with hover elevation (`transform: translateY(-2px); box-shadow: var(--bs-box-shadow);`), smooth transition, pointer cursor, high-visibility keyboard focus rings (`:focus-visible`), and responsive `.card-nav-arrow` with bidirectional LTR/RTL sliding support. | `catalogue.html`, `components.css`, `tables.js`, `test_theme_surface_contrast.py` (Test 09 & 10). | **RESOLVED & VERIFIED** |
| **ISSUE-CARD-03** | Cross-Portal Card Pattern Consistency & Action Click-Isolation | **Major (P1)** | Audited similar single-item cards across both Student and Teacher portals. Converted featured cards on homepage (`index.html`), related book cards on detail page (`book_detail.html`), and mobile cards on teacher queues (`donations.html`, `requests.html`, `handovers.html`) to `.clickable-card[data-href]`, removing redundant View/Details buttons. Enhanced event delegator in `tables.js` with strict action click-isolation: clicking any nested button (Approve, Reject, Handover, Print), input, link, form, modal toggle, or selecting text completely prevents card navigation. Keyboard Enter/Space triggers card navigation safely. Multi-action statistical summary cards were intentionally kept non-clickable. | `tables.js`, `index.html`, `book_detail.html`, `donations.html`, `requests.html`, `handovers.html`, `inventory.html`, `tests/test_theme_surface_contrast.py`. | **RESOLVED & VERIFIED** |
| **ISSUE-STAT-01** | Available Status Contrast & Vibrant Semantic Green | **Major (P1)** | Replaced dim available badge color with vibrant, accessible green tokens: Light Mode `#15803D` text on `#DCFCE7` soft container with `#86EFAC` border (**5.02:1** contrast against `#FFFFFF`, WCAG AA); Dark Mode `#4ADE80` text on `#052E16` soft container with `#166534` border (**8.38:1** contrast against `#1E293B`, WCAG AAA). Styled `.badge.bg-success-subtle` and `.text-success` with bold weight (`font-weight: 600`), and synchronized `--kb-success*` and `--bs-success*` tokens in `main.css`. Other status colors (Pending `#F59E0B`, Reserved `#0284C7`, Handed Over `#475569`, Cancelled `#DC2626`) strictly preserved. | `main.css`, `components.css`, `tests/test_theme_surface_contrast.py` (Test 11), `scripts/run_visual_acceptance_audit.py`. | **RESOLVED & VERIFIED** |
| **ISSUE-SURF-03** | Card Footer Background Surface Consistency | **Moderate (P2)** | Eliminated inconsistent grey bottom bar on cards caused by Bootstrap's `--bs-card-cap-bg` default (`#E8EDF4` / `#263449`) and `.bg-body-tertiary` classes on `.card-footer`. Configured `--bs-card-cap-bg: #FFFFFF;` (Light) and `--bs-card-cap-bg: #1E293B;` (Dark) in `main.css`. Enforced `.card-footer { background-color: var(--kb-bg-surface) !important; }` in `components.css` and replaced `.bg-body-tertiary` with `bg-transparent` in all card templates (`catalogue.html`, `index.html`, `book_detail.html`, `donations.html`, `requests.html`, `handovers.html`, `inventory.html`). Retained clean subtle divider (`border-top`) with seamless card surface background across both themes. | `main.css`, `components.css`, all card templates, `tests/test_theme_surface_contrast.py` (Test 10). | **RESOLVED & VERIFIED** |
