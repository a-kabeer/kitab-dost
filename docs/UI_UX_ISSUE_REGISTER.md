# KITAAB BANK — FRONTEND UI/UX ISSUE REGISTER
## Master Audit & Defect Tracking Log (Planning Stage)

---

## 1. Register Overview & Status Legend

This document serves as the central, page-by-page register of all user-confirmed and audit-discovered user interface, usability, responsiveness, styling, and accessibility issues across **Kitaab Bank (کتاب بینک)**.

### Severity Classification
- **Critical (P0):** Breaks layout usability, causes horizontal page overflow, makes navigation unusable, or violates accessibility standards.
- **Major (P1):** Noticeable visual defect, text wrapping, unaligned elements, inconsistent spacing, or awkward mobile interaction.
- **Moderate (P2):** Suboptimal UI styling, excessive custom CSS, informal icon/emoji usage, or missing responsive polish.
- **Minor (P3):** Subtle visual inconsistency, minor padding discrepancy, or cosmetic enhancement.

### Status Classification
- **CONFIRMED (User-Reported):** Explicitly identified and required by user specification.
- **AUDIT-DISCOVERED (Engineering Audit):** Identified during comprehensive template, CSS, and DOM inspection.
- **PLANNED:** Solution architected and documented in `UI_UX_REDESIGN_PLAN.md`; awaiting user approval to implement.
- **RESOLVED:** Fixed and verified via automated and browser tests.

---

## 2. Confirmed Core Issues (User-Reported)

| Issue ID | Page / Component | Severity | Current Behavior | Expected Behavior | Proposed Fix | Test Required | Status |
|---|---|---|---|---|---|---|---|
| **ISSUE-NAV-01** | Global Navigation (Desktop Header) | **Critical (P0)** | Navigation labels wrap onto a second line on desktop viewports between 1024px and 1280px (and up to 1366px in Urdu/Sindhi), pushing header height from 4.25rem to 6rem+ and causing vertical layout shift. | All primary navigation links and header controls must remain on exactly one line across desktop viewports with zero wrapping. | Implement Bootstrap 5.3 Navbar with `navbar-expand-xl` breakpoint. Collapse navigation into an offcanvas drawer below 1200px. Optimize horizontal padding and group right actions cleanly. | Playwright desktop audit at 1440px, 1280px, 1024px across EN, UR, SD. | **CONFIRMED (User-Reported)** |
| **ISSUE-NAV-02** | Global Navigation (Mobile Navbar) | **Critical (P0)** | Mobile navigation uses an absolute-positioned dropdown menu that dumps links directly beneath the header without backdrop dismissal, scroll locking, or keyboard Esc handling. Touch targets are cramped and locale/theme toggles clutter the top bar. | Mobile navigation should use a modern, accessible slide-in Offcanvas drawer with backdrop, large touch targets (min 48px), keyboard Esc trap, and integrated language/theme selectors. | Replace custom dropdown with Bootstrap 5.3 `.offcanvas-start` (LTR) and `.offcanvas-end` (RTL). Integrate locale and theme switchers into offcanvas footer. | Playwright mobile audit at 390px (iOS) and 360px (Android); touch target verification. | **CONFIRMED (User-Reported)** |
| **ISSUE-CSS-01** | Global Stylesheets (`components.css`, `main.css`, `student.css`, `teacher.css`) | **Major (P1)** | Over 39 KB of bespoke CSS that reinvents standard Bootstrap components (custom navbar, buttons, cards, badges, alerts, forms, tables, modals, flex utilities, spacing). Contains redundant overrides and conflicting selectors. | Standard components and utilities must leverage native Bootstrap 5.3.8 classes. Custom CSS must be streamlined, maintainable, and limited strictly to domain-specific styling. | Replace redundant custom CSS with Bootstrap classes (`container`, `row`, `col-*`, `btn`, `card`, `badge`, `alert`, `table`, `modal`). Retain only design tokens, Nastaliq typography, and print rules. | Full CSS audit and automated stylesheet size reduction; regression test verification. | **CONFIRMED (User-Reported)** |
| **ISSUE-ICO-01** | Universal Iconography (All Portals & Templates) | **Moderate (P2)** | Inconsistent, informal emoji and raw Unicode characters (`📖`, `👨‍🏫`, `🔍`, `✓`, `✕`, `⏳`, `🔒`, `🟢`, `🤝`, `▼`, `☰`) are used as interface icons across all 33 templates and JavaScript scripts. | Consistent, professional, accessible Font Awesome 7.3.1 Free icons (Solid & Regular) used universally with proper sizing and alignment. | Vendor Font Awesome 7.3.1 Free locally in `app/static/vendor/fontawesome/`. Replace all emojis with semantic `<i class="fa-solid fa-*"></i>` tags based on central icon dictionary. | Visual regression audit across all 33 templates; assert zero emoji in interface buttons. | **CONFIRMED (User-Reported)** |

---

## 3. Student Portal Issue Register (Audit-Discovered)

### 3.1 Homepage (`app/templates/student/index.html`)
| Issue ID | Component | Severity | Current Behavior | Expected Behavior | Proposed Fix | Test Required | Status |
|---|---|---|---|---|---|---|---|
| **STU-HOME-01** | Hero Section | **Moderate (P2)** | Hero pill uses emoji `🎒` and bespoke `.hero-pill` CSS. Headline typography scaling is fixed (`font-size: 2.75rem;`), causing awkward wrapping on small mobile screens (< 380px). | Hero section should feature responsive Bootstrap typography (`display-5 fw-bold`), semantic `<i class="fa-solid fa-graduation-cap"></i>` badge, and fluid vertical rhythm. | Refactor hero markup with Bootstrap grid and responsive utility classes (`display-6 display-md-5 fw-bold mb-3`). | Viewport test at 360px, 390px, 768px, 1280px. | **AUDIT-DISCOVERED** |
| **STU-HOME-02** | Hero Search Bar | **Moderate (P2)** | Search form uses bespoke CSS with fixed padding and raw emoji `🔍`. Input focus shadow does not coordinate with dark mode theme tokens. | Search input group should use rounded-pill styling, integrated Font Awesome search icon, and theme-adaptive focus ring. | Wrap search in a Bootstrap `.input-group .input-group-lg` with `.rounded-pill`, using theme-aware border and focus ring. | Interactive search test in Light and Dark themes. | **AUDIT-DISCOVERED** |
| **STU-HOME-03** | Live Impact Metrics Strip | **Major (P1)** | Metrics strip uses CSS Grid (`repeat(auto-fit, minmax(220px, 1fr))`) which stacks unevenly (e.g. 3 on row 1, 1 on row 2) at 768px tablet viewports. | Metrics should display in a clean 4-column layout on desktop and 2x2 grid on tablet and mobile viewports. | Replace CSS grid with Bootstrap row: `<div class="row g-3 row-cols-2 row-cols-md-4">`. Standardize cards with `.card .border-0 .shadow-sm`. | Multi-device audit at 768px and 390px. | **AUDIT-DISCOVERED** |
| **STU-HOME-04** | Featured Books Grid | **Moderate (P2)** | Section header has hardcoded inline styles (`style="margin-top: 4rem;"`). Book cards lack fixed aspect ratios for cover images, causing card heights to misalign. | Section header should use Bootstrap spacing (`mt-5 mb-4 d-flex justify-content-between`). Book cards should maintain uniform 3:4 aspect ratio. | Refactor to Bootstrap container grid with `.card .h-100` and image wrapper enforcing `aspect-ratio: 3/4; object-fit: cover;`. | Visual grid alignment test across 4 featured books. | **AUDIT-DISCOVERED** |

---

### 3.2 Book Catalogue & Filters (`app/templates/student/catalogue.html`)
| Issue ID | Component | Severity | Current Behavior | Expected Behavior | Proposed Fix | Test Required | Status |
|---|---|---|---|---|---|---|---|
| **STU-CAT-01** | Filter & Search Toolbar | **Major (P1)** | Filter panel uses custom `.filter-grid` with unaligned action buttons (`Filter` and `Clear`). On tablet (768px), inputs cram and button labels wrap awkwardly. | Filter controls should render as a clean, responsive toolbar using Bootstrap form selects and inputs with aligned action buttons. | Refactor filter toolbar to a Bootstrap card with `<div class="row g-2 align-items-end">`. Align submit and reset buttons to the bottom of the form row. | Form filtering test with all 5 filters active on tablet and mobile. | **AUDIT-DISCOVERED** |
| **STU-CAT-02** | Active Filter Pills | **Minor (P3)** | Active filter pills use bespoke `.active-filter-pill` with hardcoded colors that do not contrast properly in dark mode. | Active filter tags should use accessible Bootstrap badges (`badge rounded-pill bg-primary-subtle text-primary border border-primary-subtle`) with dismiss icons. | Replace with Bootstrap pill badges containing `<i class="fa-solid fa-xmark ms-1"></i>` and proper theme-adaptive contrast. | Dark mode visual inspection of active filter tags. | **AUDIT-DISCOVERED** |
| **STU-CAT-03** | Empty Search State | **Moderate (P2)** | Empty results display uses raw emoji `📖` and unstyled paragraphs. | Empty state should feature a clean illustration card with `<i class="fa-solid fa-book-open-reader fs-1 text-muted"></i>`, helpful suggestion text, and a reset button. | Build empty state as a centered Bootstrap card (`p-5 text-center bg-surface border rounded-3`). | Search for non-existent keyword to trigger empty state. | **AUDIT-DISCOVERED** |

---

### 3.3 Book Details (`app/templates/student/book_detail.html`)
| Issue ID | Component | Severity | Current Behavior | Expected Behavior | Proposed Fix | Test Required | Status |
|---|---|---|---|---|---|---|---|
| **STU-DET-01** | Information Architecture & Layout | **Major (P1)** | Custom `.book-detail-wrapper` relies on fixed grid columns (`320px 1fr`). On screens between 600px and 850px, the left cover column becomes squished. | Layout should use Bootstrap responsive columns: `col-lg-4` (cover, QR sticker, status) and `col-lg-8` (metadata, description, request callout). | Refactor to `<div class="row g-4">` with responsive column sizing. Cover image scales gracefully with `img-fluid rounded-3`. | Viewport audit at 768px, 1024px, and 1280px. | **AUDIT-DISCOVERED** |
| **STU-DET-02** | Metadata Grid | **Moderate (P2)** | Metadata table uses custom `.meta-table` and `.meta-item` divs with manual borders and inline padding. | Metadata should be presented using an accessible Bootstrap horizontal definition list (`<dl class="row mb-0">`) or bordered table. | Refactor to Bootstrap `<dl class="row">` with `<dt class="col-sm-4 text-muted">` and `<dd class="col-sm-8 fw-semibold">`. | Verify metadata display across English and Urdu RTL. | **AUDIT-DISCOVERED** |
| **STU-DET-03** | Inline Styles & Emojis | **Minor (P3)** | Extensive inline styles (`style="display: flex; ..."`), raw emoji `🏷️`, and raw checkmark `✓` in verified badge. | Zero inline flex styles; replace with Bootstrap utilities (`d-flex gap-2 align-items-center`) and Font Awesome `<i class="fa-solid fa-circle-check text-success"></i>`. | Clean up inline CSS; replace with Bootstrap utility classes and Font Awesome icons. | Code audit verifying removal of inline style rules. | **AUDIT-DISCOVERED** |

---

### 3.4 Book Donation Form & Success (`app/templates/student/donate.html` & `donation_success.html`)
| Issue ID | Component | Severity | Current Behavior | Expected Behavior | Proposed Fix | Test Required | Status |
|---|---|---|---|---|---|---|---|
| **STU-DON-01** | Multi-Section Form Layout | **Major (P1)** | Donation form uses custom `.form-grid-2` and `.donation-section` with manual field spacing. File upload input is an unstyled browser file control. | Form should be structured using clean Bootstrap card sections, floating or standard form labels, and a styled file input with drag-and-drop preview. | Refactor sections using Bootstrap cards, `.form-label fw-semibold`, `.form-control`, and `.form-select`. | Form submission with valid and invalid data. | **AUDIT-DISCOVERED** |
| **STU-DON-02** | Donation Success Screen | **Moderate (P2)** | Donation code card uses raw emoji `📋` and lacks an easy one-click copy button for the donation tracking reference. | Success screen should display a celebration card with Font Awesome `<i class="fa-solid fa-circle-check text-success"></i>`, prominent reference badge, and copy action. | Refactor to Bootstrap card with copy-to-clipboard button and print shortcut. | Complete test donation workflow in browser. | **AUDIT-DISCOVERED** |

---

### 3.5 Book Request Form & Success (`app/templates/student/request_book.html` & `request_success.html`)
| Issue ID | Component | Severity | Current Behavior | Expected Behavior | Proposed Fix | Test Required | Status |
|---|---|---|---|---|---|---|---|
| **STU-REQ-01** | Selected Book Summary Box | **Moderate (P2)** | Selected book mini-summary uses inline CSS with hardcoded padding, border radius, and thumbnail dimensions. | Mini-summary should be a clean Bootstrap horizontal card with responsive thumbnail and badge layout. | Refactor using `<div class="card mb-4 shadow-sm"><div class="card-body d-flex gap-3 align-items-center">`. | Inspect request form across desktop and mobile. | **AUDIT-DISCOVERED** |
| **STU-REQ-02** | Request Success Token Display | **Major (P1)** | Success token card uses bespoke styling. In RTL mode (Urdu/Sindhi), tracking code `KB-REQ-XXXX-XXXX` transposes hyphens if unisolated. | Tracking code must have strict LTR bidi isolation (`unicode-bidi: isolate; direction: ltr;`) and be formatted inside a high-visibility Bootstrap alert card. | Enforce `.kb-code` class on token container; add one-click copy button and direct "Track Request" link. | Request submission test verifying tracking code rendering in Urdu RTL. | **AUDIT-DISCOVERED** |

---

### 3.6 Request Tracking Desk (`app/templates/student/track.html`)
| Issue ID | Component | Severity | Current Behavior | Expected Behavior | Proposed Fix | Test Required | Status |
|---|---|---|---|---|---|---|---|
| **STU-TRK-01** | Tracking Search Form | **Moderate (P2)** | Lookup form card has hardcoded inline CSS with raw emoji `🔍`. Input lacks autofocus on error. | Clean Bootstrap card with input group, uppercase monospace font, and clear search button. | Refactor to Bootstrap card with `.input-group .input-group-lg` and Font Awesome search icon. | Token lookup test with valid and invalid codes. | **AUDIT-DISCOVERED** |
| **STU-TRK-02** | Status Progress Timeline | **Major (P1)** | Status is displayed as a single static alert box without showing the sequential workflow steps (Submitted -> Review -> Approved -> Handed Over). | Display an accessible 4-step progress stepper / timeline showing completed, active, and upcoming stages. | Build a responsive Bootstrap stepper with Font Awesome status icons and clear Urdu/Sindhi text descriptions. | Verify all 5 request statuses (`pending`, `approved`, `rejected`, `completed`, `cancelled`) in stepper. | **AUDIT-DISCOVERED** |

---

### 3.7 QR Scanner & Direct Lookup (`app/templates/student/scan.html`)
| Issue ID | Component | Severity | Current Behavior | Expected Behavior | Proposed Fix | Test Required | Status |
|---|---|---|---|---|---|---|---|
| **STU-SCN-01** | Card Layout & Visual Balance | **Moderate (P2)** | Manual Code card and Live Scanner card have disparate border widths (2px) and raw emojis (`🔢`, `📷`, `📹`, `⏹`, `🔄`). | Two balanced Bootstrap cards with clean 1px borders, subtle elevation, and professional Font Awesome icons. | Refactor both cards using Bootstrap `.card .shadow-sm` and Font Awesome iconography. Retain all JavaScript IDs. | Manual code entry and sample code chip tests. | **AUDIT-DISCOVERED** |
| **STU-SCN-02** | Mobile Camera Reticle Overlay | **Moderate (P2)** | Scanner reticle box uses fixed percentage inset (`inset: 15%`) which clips corner accents on tall phone displays. | Reticle should adapt responsively to standard 4:3 and 16:9 camera aspect ratios without clipping. | Standardize camera container with Bootstrap `.ratio .ratio-4x3` and refined CSS corner accent brackets. | Camera start/stop test on desktop and mobile viewports. | **AUDIT-DISCOVERED** |

---

## 4. Teacher Portal Issue Register (Audit-Discovered)

### 4.1 Teacher Login (`app/templates/auth/login.html`)
| Issue ID | Component | Severity | Current Behavior | Expected Behavior | Proposed Fix | Test Required | Status |
|---|---|---|---|---|---|---|---|
| **TCHR-LOG-01** | Login Card & Form Styling | **Moderate (P2)** | Login form has hardcoded inline padding (`padding: 2.25rem 2rem;`), raw emoji `👨‍🏫`, and manual label margins. | Centered Bootstrap card (`col-md-6 col-lg-4 mx-auto`) with professional header icon and Bootstrap form controls. | Refactor using Bootstrap grid, `.card .shadow-sm`, `.form-floating` or `.form-label`, and Font Awesome icon. | Login test with valid and invalid credentials. | **AUDIT-DISCOVERED** |

---

### 4.2 Teacher Dashboard (`app/templates/teacher/dashboard.html`)
| Issue ID | Component | Severity | Current Behavior | Expected Behavior | Proposed Fix | Test Required | Status |
|---|---|---|---|---|---|---|---|
| **TCHR-DASH-01** | Pending Actions Alert Banner | **Major (P1)** | Alert banner uses raw emoji `⚠️` and inline flex styling that stacks awkwardly when multiple action buttons are present. | Accessible Bootstrap alert (`alert alert-warning d-flex flex-wrap justify-content-between align-items-center`) with Font Awesome icon. | Refactor with Bootstrap alert and responsive flex classes (`gap-2`). | Test dashboard when pending items > 0 and = 0. | **AUDIT-DISCOVERED** |
| **TCHR-DASH-02** | Quick Actions Grid | **Major (P1)** | Quick actions use bespoke `.action-pill-card` and `.action-pill-icon` with raw emojis. Hover effects use manual translate. | Clean Bootstrap grid of action cards with consistent icon badges and hover transitions. | Replace with `<div class="row row-cols-2 row-cols-md-3 row-cols-xl-6 g-3">` and Bootstrap card pills. | Click test on all 6 quick action cards. | **AUDIT-DISCOVERED** |
| **TCHR-DASH-03** | Primary Metric KPI Cards | **Major (P1)** | Metric cards use CSS grid (`repeat(auto-fit, minmax(220px, 1fr))`) and raw emojis (`📚`, `🟢`, `🔒`, `🤝`). | 4-column Bootstrap grid (`col-12 col-sm-6 col-xl-3`) with consistent height, clean elevation, and Font Awesome metric icons. | Refactor using Bootstrap row/col grid and `.card .h-100 .shadow-sm`. | Responsive test across 360px, 768px, 1024px, 1440px. | **AUDIT-DISCOVERED** |
| **TCHR-DASH-04** | Distribution Progress Bars | **Minor (P3)** | Distribution meters use bespoke `.meter-track` and `.meter-fill` CSS rather than Bootstrap progress bars. | Standard Bootstrap progress component (`progress` and `progress-bar`) with accessible `role="progressbar"`. | Replace with `<div class="progress" style="height: 10px;"><div class="progress-bar bg-primary" ...></div></div>`. | Verify progress bar widths in English and Urdu RTL. | **AUDIT-DISCOVERED** |

---

### 4.3 Donation Review Queue & Detail (`donations.html` & `donation_detail.html`)
| Issue ID | Component | Severity | Current Behavior | Expected Behavior | Proposed Fix | Test Required | Status |
|---|---|---|---|---|---|---|---|
| **TCHR-DON-01** | Status Filter Tabs | **Moderate (P2)** | Status tabs use bespoke `.filter-tabs-bar` and `.filter-tab` with raw emojis (`⏳`, `✓`, `✕`, `📋`). | Clean Bootstrap nav-pills (`nav nav-pills gap-2 mb-3`) with Font Awesome tab icons and count badges. | Refactor to Bootstrap nav-pills with `.nav-link` and `.badge`. | Status tab switching test. | **AUDIT-DISCOVERED** |
| **TCHR-DON-02** | Donations Data Table | **Major (P1)** | Table wrapper lacks standard Bootstrap responsive overflow handling; columns cram on tablet screens. | Bootstrap `.table-responsive` containing `.table .table-hover .align-middle` with prioritized column visibility. | Wrap table in Bootstrap card with `.table-responsive`; use `.d-none .d-md-table-cell` for secondary columns. | Test donation table on tablet (768px) and mobile. | **AUDIT-DISCOVERED** |

---

### 4.4 Student Requests Queue & Allocation (`requests.html` & `request_detail.html`)
| Issue ID | Component | Severity | Current Behavior | Expected Behavior | Proposed Fix | Test Required | Status |
|---|---|---|---|---|---|---|---|
| **TCHR-REQ-01** | Requests Table Columns | **Major (P1)** | Request queue table contains 7 columns without responsive breakpoints, forcing awkward horizontal scrolling on 1024px laptops. | Prioritized responsive table where core info (Student, Book, Status, Action) is prominent and secondary metadata collapses neatly. | Refactor using Bootstrap responsive table classes and compact action button groups. | Test request list on 1024px and 768px. | **AUDIT-DISCOVERED** |
| **TCHR-REQ-02** | Request Detail Allocation Action | **Moderate (P2)** | Action buttons use bespoke classes with raw emojis (`🔒 Lock & Reserve`, `✕ Reject`). | Bootstrap button group with Font Awesome `<i class="fa-solid fa-lock me-1"></i>` and clear confirmation modals. | Replace with Bootstrap `.btn-success` and `.btn-danger` with Font Awesome icons. | Test request approval and rejection flows. | **AUDIT-DISCOVERED** |

---

### 4.5 Handover Ledger & Confirmation (`handovers.html`, `handover_confirm.html`, `handover_receipt.html`)
| Issue ID | Component | Severity | Current Behavior | Expected Behavior | Proposed Fix | Test Required | Status |
|---|---|---|---|---|---|---|---|
| **TCHR-HO-01** | Handover Confirmation Checklist | **Major (P1)** | Confirmation checkboxes use custom `.checkbox-custom` with raw emojis and lack clear visual verification highlights. | Accessible Bootstrap form checks (`form-check form-check-lg`) with high-visibility checked states. | Refactor using `<div class="form-check p-3 bg-light rounded-3 border mb-3">`. | Execute handover confirmation with and without checkboxes. | **AUDIT-DISCOVERED** |
| **TCHR-HO-02** | Printable A4 Receipt View | **Minor (P3)** | Receipt page uses custom CSS font-family that differs from main app font stack; lacks clean breadcrumb back to ledger. | Modernized A4 receipt layout preserving exact print dimensions while sharing clean typography and brand crest. | Clean up receipt screen container while preserving `@media print` rules exactly. | Print preview test in browser verifying 1-page A4 output. | **AUDIT-DISCOVERED** |

---

### 4.6 Book Inventory & Book Form (`inventory.html` & `book_form.html`)
| Issue ID | Component | Severity | Current Behavior | Expected Behavior | Proposed Fix | Test Required | Status |
|---|---|---|---|---|---|---|---|
| **TCHR-INV-01** | Inventory Table Actions | **Moderate (P2)** | Table cell action buttons (`Edit`, `Retire`, `Print`) wrap awkwardly within narrow columns. | Compact Bootstrap button group (`btn-group btn-group-sm`) with tooltip icons or clean dropdown. | Wrap actions in `.btn-group .btn-group-sm` with Font Awesome icons. | Test action buttons across desktop and mobile. | **AUDIT-DISCOVERED** |
| **TCHR-INV-02** | Retire Textbook Modal | **Major (P1)** | Retirement modal uses bespoke `.modal-overlay` and manual JS display toggles instead of Bootstrap's accessible modal component. | Accessible Bootstrap modal (`modal fade`, `modal-dialog`, `modal-content`) with backdrop dismissal and focus management. | Refactor to native Bootstrap 5.3 modal (`id="retireModal"`). | Trigger retirement modal and test escape key dismissal. | **AUDIT-DISCOVERED** |

---

### 4.7 Reports & Analytics (`app/templates/teacher/reports.html`)
| Issue ID | Component | Severity | Current Behavior | Expected Behavior | Proposed Fix | Test Required | Status |
|---|---|---|---|---|---|---|---|
| **TCHR-REP-01** | Action Header & Export Buttons | **Moderate (P2)** | Export buttons have raw emojis (`🖨️`, `📥`) and inline gap styles. | Bootstrap button group with Font Awesome `<i class="fa-solid fa-print me-1"></i>` and `<i class="fa-solid fa-file-csv me-1"></i>`. | Refactor header to `<div class="d-flex flex-wrap gap-2">` with Bootstrap buttons. | Test CSV export downloads. | **AUDIT-DISCOVERED** |
| **TCHR-REP-02** | Statistical Summary Cards | **Moderate (P2)** | Grid cards use custom CSS grid with inline styles (`style="grid-template-columns: repeat(...) ;"`). | Bootstrap grid row (`row g-3 row-cols-2 row-cols-lg-4`) with uniform card heights. | Refactor to Bootstrap grid cards. | Responsive layout test across viewports. | **AUDIT-DISCOVERED** |

---

### 4.8 Activity Logs (`app/templates/teacher/logs.html`)
| Issue ID | Component | Severity | Current Behavior | Expected Behavior | Proposed Fix | Test Required | Status |
|---|---|---|---|---|---|---|---|
| **TCHR-LOG-01** | Activity Log Rows | **Moderate (P2)** | Activity list uses bespoke `.activity-row` and `.badge-act-*` classes with raw emoji header. | Bootstrap list group (`list-group list-group-flush`) with clean entity badges and relative timestamps. | Refactor using Bootstrap card with `.list-group` and Font Awesome action icons. | Test activity log pagination and filtering. | **AUDIT-DISCOVERED** |

---

### 4.9 System Settings Desk (`app/templates/teacher/settings.html`)
| Issue ID | Component | Severity | Current Behavior | Expected Behavior | Proposed Fix | Test Required | Status |
|---|---|---|---|---|---|---|---|
| **TCHR-SET-01** | Navigation Tabs Bar | **Major (P1)** | 4 tabs (Profile, Security, Backup, Demo) use bespoke `.filter-tabs-bar` with raw emojis (`🏫`, `🔒`, `💾`, `✨`). | Clean Bootstrap Nav-Pills (`nav nav-pills nav-fill gap-2 mb-4`) with Font Awesome icons. | Refactor to `<ul class="nav nav-pills">` with `.nav-link` and `.active` classes. | Tab switching test across all 4 settings panels. | **AUDIT-DISCOVERED** |
| **TCHR-SET-02** | Inline Form Styles | **Moderate (P2)** | Settings forms contain dozens of redundant inline styles (`style="width: 100%; padding: ..."`). | Clean Bootstrap form controls (`form-label`, `form-control`, `form-select`) without inline CSS. | Strip inline style attributes; apply standard Bootstrap form classes. | Form submission test for school profile and password. | **AUDIT-DISCOVERED** |
| **TCHR-SET-03** | Backup List & Restore Action | **Major (P1)** | Backup table rows contain manual status tags and custom restore confirmation modals. | Bootstrap table with status badges (`badge bg-success-subtle text-success`) and accessible Bootstrap restore modal. | Refactor backup table using Bootstrap table classes and native modal. | Create backup and trigger restore modal test. | **AUDIT-DISCOVERED** |
| **TCHR-SET-04** | Exhibition Demo Card & Checkbox | **Critical (P0)** | Mandatory safety checkbox `#confirmDemoBox` is embedded in a bespoke alert card with raw emojis. | High-visibility warning card with styled checkbox (`form-check-input`) while strictly preserving `#confirmDemoBox` ID. | Wrap in Bootstrap `.alert .alert-warning` and `.form-check`, strictly maintaining input ID. | Test Exhibition demo activation and safe exit. | **AUDIT-DISCOVERED** |

---

## 5. Global & Accessibility Issue Register (Audit-Discovered)

| Issue ID | Area | Severity | Current Behavior | Expected Behavior | Proposed Fix | Test Required | Status |
|---|---|---|---|---|---|---|---|
| **GLOB-RTL-01** | Nastaliq Typography in RTL | **Major (P1)** | Heading elements (`h1`, `h2`, `h3`, `.dashboard-title`) experience vertical glyph clipping in Urdu/Sindhi due to standard 1.15–1.2 line heights. | Nastaliq headings must have a minimum line-height of `1.6` and body text `1.75` to allow proper rendering of complex Arabic ligatures. | Add RTL-specific typography rules in `rtl.css` enforcing `line-height: 1.6` on headings and `1.75` on body text. | Visual typography inspection in Urdu and Sindhi. | **AUDIT-DISCOVERED** |
| **GLOB-BIDI-01** | Code & Token Direction | **Critical (P0)** | Without strict isolation, mixed Latin codes (`KB-BK-000001`, `KB-REQ-7K9M-2X4P`) can transpose hyphen segments or digits when rendered inline in Urdu/Sindhi text. | All school codes, tokens, and technical identifiers must be strictly isolated with `unicode-bidi: isolate; direction: ltr !important;`. | Enforce `.kb-code` utility on all `<code>`, `<pre>`, and code badges across all templates. | Playwright RTL test asserting correct text sequence of codes. | **AUDIT-DISCOVERED** |
| **GLOB-ACC-01** | ARIA Landmarks & Attributes | **Major (P1)** | Dropdown buttons, modals, and mobile toggles lack essential ARIA attributes (`aria-expanded`, `aria-haspopup`, `aria-controls`, `aria-label`). | Full WCAG 2.1 AA compliance with proper ARIA roles, states, and keyboard navigation support. | Implement standard Bootstrap accessibility attributes across all navbars, dropdowns, and modals. | Accessibility audit via axe-core / Playwright accessibility checks. | **AUDIT-DISCOVERED** |
| **GLOB-FOUC-01** | Theme Flash on Page Load | **Major (P1)** | When migrating to Bootstrap 5.3, if `data-bs-theme` is applied late via external JS, a flash of white/dark theme occurs during render. | Zero Flash of Unstyled Content (FOUC); document element must have correct theme attribute set before first paint. | Update inline `<head>` script to set both `data-theme` and `data-bs-theme` synchronously before any CSS link tags. | Page reload test with network throttling in dark mode. | **AUDIT-DISCOVERED** |

---

## 6. Issue Register Summary & Action Plan

### Issue Count by Category
- **Confirmed Core Issues (User-Reported):** 4
- **Audit-Discovered Student Portal Issues:** 14
- **Audit-Discovered Teacher Portal Issues:** 13
- **Audit-Discovered Global & Accessibility Issues:** 4
- **Total Registered Issues:** **35**

### Issue Count by Severity
- **Critical (P0):** 4 (Desktop nav wrapping, mobile offcanvas, bidi isolation, demo checkbox ID)
- **Major (P1):** 14 (CSS bloat, metric cards, table responsiveness, modals, RTL line height, ARIA)
- **Moderate (P2):** 14 (Font Awesome icons, empty states, search bars, filter cards, button groups)
- **Minor (P3):** 3 (Receipt back link, active filter pill contrast, metadata cleanup)

All 35 registered issues are directly mapped to architectural solutions in [`docs/UI_UX_REDESIGN_PLAN.md`](file:///d:/My%20Folder/My%20Work/Kitab%20Dost/docs/UI_UX_REDESIGN_PLAN.md). Implementation will commence upon user review and authorization.
