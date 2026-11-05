# KITAAB BANK — VISUAL CORRECTION & POLISH PLAN
## Post-Audit Visual Polish, Localization & Responsive Enhancement Architecture

**Initiative:** Final Screenshot-Based UI/UX Correction & Polish  
**Branch:** `ui/bootstrap-fontawesome-redesign`  
**Baseline Commit:** `ea13ec8`  
**Visual Baseline:** 36 Verified Full-Page Screenshots (`docs/ui-redesign-evidence/`)  

---

## 1. Executive Strategy & Scope Boundaries

This plan addresses visual defects and usability friction points identified in the 36-screenshot visual audit. It focuses strictly on presentation, responsive behavior, localization, and image resilience while preserving:
- 100% offline self-hosted architecture (Zero external CDNs).
- All Flask backend routes, query parameters, form schemas, CSRF protection, and database constraints.
- All existing JavaScript integrations (`qr_scanner.js`, theme switching, modal triggers).
- Full regression suite integrity (137/137 discovery tests, Phase 1, Concurrency).

---

## 2. Issue Classification Matrix

### Category A: Confirmed Screenshot Defects (P0 - Immediate Action)
1. **DEF-LOC-01 (P0): Incomplete Urdu and Sindhi Localization**
   - *Observation:* Major interface sections in Urdu (`rtl_urdu_home_desktop.png`, `rtl_urdu_dashboard_desktop.png`) and Sindhi (`rtl_sindhi_home_desktop.png`, `rtl_sindhi_catalogue_desktop.png`) still display raw English strings.
   - *Fix:* Audit all 33 templates, extract static strings, expand `en.json`, `ur.json`, `sd.json`, and wrap in `_t()`.
2. **DEF-BIDI-01 (P0): Inverted English Full Stops & Mixed Punctuation**
   - *Observation:* English full stops appear at the beginning of Urdu/Sindhi sentences.
   - *Fix:* Enforce `<bdi>` tags on mixed content and proper `dir="rtl"` vs `dir="ltr"` container boundaries.
3. **DEF-IMG-01 (P0): Missing Social Studies & Subject Cover Images**
   - *Observation:* Social Studies books display broken image icons with raw browser alt text when images are missing.
   - *Fix:* Add missing subject SVGs (`social_class7.svg`, `social_class8.svg`, `english_class6.svg`, `english_class8.svg`, `urdu_class7.svg`, `computer_class6.svg`, `islamiat_class7.svg`, `islamiat_class8.svg`), modernize `placeholder.svg`, and add universal `onerror` fallback handlers.
4. **DEF-TBL-01 (P0): Teacher Tables Overflow & Missing Mobile Actions**
   - *Observation:* Desktop tables at 1440px clip action columns. On mobile (<768px), table view truncates essential columns and actions become inaccessible.
   - *Fix:* Implement dual-mode presentation: responsive record cards on mobile (`d-md-none`) and optimized visible-actions table on desktop (`d-none d-md-block`).

### Category B: Major Responsive Defects (P1)
5. **DEF-NAV-01 (P1): Student Desktop Navbar "Teacher Sign In" Wrapping**
   - *Observation:* "Teacher Sign In" button text wraps into 2 lines on desktop header at tight widths.
   - *Fix:* Apply `.text-nowrap` to sign-in button and fine-tune container margins.
6. **DEF-THDR-01 (P1): Teacher Mobile Header Overcrowding**
   - *Observation:* Mobile teacher toolbar shows 6+ controls, causing text and buttons to collide.
   - *Fix:* Simplify mobile toolbar to Hamburger + Brand, moving Language, Theme, Public Portal, and Logout into `#teacherSidebarOffcanvas`.
7. **DEF-CAT-01 (P1): Mobile Catalogue Vertical Height**
   - *Observation:* 34,000px tall mobile catalogue with repetitive full-width cards.
   - *Fix:* Modernize mobile catalogue into compact horizontal book cards (~96px thumbnail) and collapsible filter accordion.
8. **DEF-DET-01 (P1): Mobile Book Detail Giant Cover**
   - *Observation:* Full-width 3:4 cover image dominates mobile screen before book details appear.
   - *Fix:* Constrain mobile cover preview to `max-width: 220px` with centered metadata and clear CTA.

### Category C: Usability & Refinement Polish (P2)
9. **DEF-TAB-01 (P2): Horizontally Clipped Navigation Tabs**
   - *Observation:* Filter pills on donations, requests, inventory, and settings clip on narrow viewports.
   - *Fix:* Add `flex-nowrap overflow-x-auto` or `flex-wrap` with visual scroll padding.
10. **DEF-HOM-01 (P2): Homepage Mobile Hero Spacing & Search Placeholder**
    - *Observation:* Hero text and search input are overly tall on mobile; long search placeholder truncates.
    - *Fix:* Use responsive search placeholder (`Search books...` on mobile) and tightened vertical rhythm.
11. **DEF-KPI-01 (P2): Teacher Dashboard Metric Wrapping on Mobile**
    - *Observation:* Uneven single-column card stacking on mobile.
    - *Fix:* Enforce structured 2-column mobile KPI cards (`row-cols-2 row-cols-md-3 row-cols-xl-6`).

---

## 3. Implementation Sequence

| Milestone | Scope | Deliverables | Target Commit |
|---|---|---|---|
| **CORR-1** | Urdu/Sindhi Localization & Bidi Polish | Audit all templates, expand dictionaries (`en.json`, `ur.json`, `sd.json`), fix punctuation inversion with `<bdi>` and `.kb-code`. | `feat(i18n)` |
| **CORR-2** | Cover Image Fallbacks & Missing SVGs | Create missing subject SVGs, modernize `placeholder.svg`, add universal `onerror` fallback across all card & detail views. | `fix(images)` |
| **CORR-3** | Teacher Tables Desktop & Mobile Cards | Implement responsive record cards (<768px) and compact desktop tables across Donations, Requests, Inventory, Handovers. | `refactor(tables)` |
| **CORR-4** | Teacher Mobile Header & Drawer | Streamline mobile header; move language, theme, and logout into `#teacherSidebarOffcanvas`. | `fix(teacher-nav)` |
| **CORR-5** | Student Navbar Sign-In & Mobile Search | Prevent Sign In button wrapping; implement responsive search placeholder on homepage. | `fix(student-nav)` |
| **CORR-6** | Compact Mobile Catalogue & Collapsible Filters | Horizontal book cards on phones; collapsible filter drawer/accordion with active badge count. | `refactor(catalogue)` |
| **CORR-7** | Mobile Book Detail Layout | Constrain mobile cover dimensions; center metadata and elevate Request button. | `refactor(detail)` |
| **CORR-8** | Tab Navigation, Settings & Dashboard Polish | Prevent tab clipping with scroll-safe navs; tighten homepage hero; align 2-column KPI cards. | `refactor(polish)` |
| **CORR-9** | Screenshot Capture & Full Regression Run | Capture updated 36 evidence screenshots + missing views; execute 137 unit tests, Phase 1, Concurrency, and Playwright audits. | `test(visual)` |
| **CORR-10** | Documentation & Final Sign-Off | Update `docs/UI_UX_ISSUE_REGISTER.md`, `docs/PROGRESS.md`, and deliver final acceptance report. | `docs(polish)` |
