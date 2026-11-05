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
