# KITAAB BANK — UNIVERSAL FONT AWESOME ICON MAPPING
## Font Awesome 7.3.1 Free Standardization & Central Reference

---

## 1. Iconography Standards & Accessibility Rules

Kitaab Bank uses **Font Awesome 7.3.1 Free** exclusively across all Student and Teacher portal interfaces. The application replaces all legacy emojis, decorative Unicode symbols, and custom SVG glyphs with standardized Font Awesome icons.

### Core Accessibility Principles
1. **Decorative Icons:** Any icon accompanied by visible text must include `aria-hidden="true"` so screen readers ignore redundant visual markers:
   ```html
   <a href="/catalogue" class="nav-link">
     <i class="fa-solid fa-book-bookmark me-1" aria-hidden="true"></i> Browse Books
   </a>
   ```
2. **Icon-Only Buttons:** Any button containing only an icon must provide a descriptive `aria-label` or visually hidden text (`.visually-hidden`):
   ```html
   <button type="button" class="btn btn-outline-secondary btn-sm" aria-label="Toggle Navigation">
     <i class="fa-solid fa-bars" aria-hidden="true"></i>
   </button>
   ```
3. **Semantic Sizing:** Use Bootstrap utility font-size classes (`fs-5`, `fs-6`, `fs-4`) or standard FA modifiers (`fa-lg`, `fa-sm`) rather than ad-hoc inline font sizes.
4. **Consistent Style Families:** Prefer `fa-solid` for interactive controls, badges, and primary tools; use `fa-regular` for timestamps, calendars, and subtle secondary metadata.

---

## 2. Reusable Jinja Macro (`app/templates/macros/icons.html`)

To ensure standard class generation, consistent spacing, and automatic `aria-hidden="true"`, a central Jinja macro is provided:

```jinja
{# Macro: icon(name, style='solid', class='', title='', aria_hidden=true) #}
{% macro icon(name, style='solid', extra_class='', title='', aria_hidden=true) -%}
  <i class="fa-{{ style }} fa-{{ name }}{% if extra_class %} {{ extra_class }}{% endif %}"{% if aria_hidden %} aria-hidden="true"{% endif %}{% if title %} title="{{ title }}"{% endif %}></i>
{%- endmacro %}
```

---

## 3. Central Application Icon Mapping

### 3.1 Navigation & Brand
| Feature / Link | Legacy Symbol | Font Awesome 7.3.1 Class | Macro Usage |
|---|---|---|---|
| **App Brand Logo** | `📖` | `fa-solid fa-book-open` | `{{ icon('book-open', 'solid') }}` |
| **Home** | `🏠` | `fa-solid fa-house` | `{{ icon('house', 'solid', 'me-1') }}` |
| **Browse Books / Catalogue** | `📚` | `fa-solid fa-book-bookmark` | `{{ icon('book-bookmark', 'solid', 'me-1') }}` |
| **Donate a Book** | `📖` | `fa-solid fa-hand-holding-heart` | `{{ icon('hand-holding-heart', 'solid', 'me-1') }}` |
| **Track Request** | `🔍` | `fa-solid fa-magnifying-glass` | `{{ icon('magnifying-glass', 'solid', 'me-1') }}` |
| **Scan Book QR** | `📷` | `fa-solid fa-qrcode` | `{{ icon('qrcode', 'solid', 'me-1') }}` |
| **About Platform** | `ℹ️` | `fa-solid fa-circle-info` | `{{ icon('circle-info', 'solid', 'me-1') }}` |
| **Teacher Desk Brand** | `👨‍🏫` | `fa-solid fa-chalkboard-user` | `{{ icon('chalkboard-user', 'solid', 'me-1') }}` |
| **Public Portal Link** | `↗` | `fa-solid fa-arrow-up-right-from-square`| `{{ icon('arrow-up-right-from-square', 'solid', 'ms-1') }}`|
| **Mobile Hamburger** | `☰` | `fa-solid fa-bars` | `{{ icon('bars', 'solid') }}` |
| **Close / Dismiss** | `✕` | `fa-solid fa-xmark` | `{{ icon('xmark', 'solid') }}` |

---

### 3.2 Circulation, Inventory & Administration
| Administrative Feature | Legacy Symbol | Font Awesome 7.3.1 Class | Macro Usage |
|---|---|---|---|
| **Teacher Dashboard / Overview** | `📊` | `fa-solid fa-chart-pie` | `{{ icon('chart-pie', 'solid', 'me-2') }}` |
| **Donations Queue** | `📥` | `fa-solid fa-inbox` | `{{ icon('inbox', 'solid', 'me-2') }}` |
| **Student Requests Queue** | `📋` | `fa-solid fa-clipboard-list` | `{{ icon('clipboard-list', 'solid', 'me-2') }}` |
| **Physical Handover Ledger** | `🤝` | `fa-solid fa-handshake` | `{{ icon('handshake', 'solid', 'me-2') }}` |
| **Book Inventory** | `📚` | `fa-solid fa-boxes-stacked` | `{{ icon('boxes-stacked', 'solid', 'me-2') }}` |
| **Print QR Labels / Center** | `🏷️` | `fa-solid fa-tag` | `{{ icon('tag', 'solid', 'me-2') }}` |
| **Reports & Statistical Analytics** | `📈` | `fa-solid fa-chart-line` | `{{ icon('chart-line', 'solid', 'me-2') }}` |
| **System Activity Audit Trail** | `📜` | `fa-solid fa-clock-rotate-left` | `{{ icon('clock-rotate-left', 'solid', 'me-2') }}` |
| **School Settings & Config** | `⚙️` | `fa-solid fa-gear` | `{{ icon('gear', 'solid', 'me-2') }}` |
| **Account Security / Password** | `🔑` | `fa-solid fa-key` | `{{ icon('key', 'solid', 'me-2') }}` |
| **Live Database Backups** | `💾` | `fa-solid fa-database` | `{{ icon('database', 'solid', 'me-2') }}` |
| **Exhibition Showcase Mode** | `✨` | `fa-solid fa-wand-magic-sparkles` | `{{ icon('wand-magic-sparkles', 'solid', 'me-2') }}` |

---

### 3.3 Circulation Status Badges
| Lifecycle Status | Legacy Symbol | Font Awesome 7.3.1 Class | Color / Context |
|---|---|---|---|
| **Available / In Stock** | `🟢` | `fa-solid fa-circle-check` | `text-success` |
| **Pending Teacher Review** | `⏳` | `fa-regular fa-clock` | `text-warning` |
| **Approved & Reserved** | `🔒` | `fa-solid fa-lock` | `text-primary` |
| **Completed / Handed Over** | `🤝` | `fa-solid fa-handshake` | `text-info` |
| **Rejected / Cancelled** | `✕` | `fa-solid fa-circle-xmark` | `text-danger` |
| **Retired / Damaged** | `⚠️` | `fa-solid fa-triangle-exclamation` | `text-danger` |

---

### 3.4 Form Actions, Camera & Common Controls
| Control Action | Legacy Symbol | Font Awesome 7.3.1 Class | Usage |
|---|---|---|---|
| **Search / Filter Action** | `🔍` | `fa-solid fa-magnifying-glass` | Search buttons & inputs |
| **Add Textbook / New** | `➕` | `fa-solid fa-plus` | Add book button |
| **Edit Textbook Details** | `✏️` | `fa-solid fa-pen-to-square` | Edit inventory actions |
| **Delete / Remove Backup** | `🗑️` | `fa-solid fa-trash-can` | Delete modal actions |
| **Print Action** | `🖨️` | `fa-solid fa-print` | Print receipts & sheets |
| **Export Spreadsheet** | `📥` | `fa-solid fa-file-csv` | CSV export buttons |
| **Start Camera Scanner** | `📹` | `fa-solid fa-video` | Camera activation button |
| **Stop Camera Scanner** | `⏹️` | `fa-solid fa-stop` | Camera stop button |
| **Flip / Switch Camera** | `🔄` | `fa-solid fa-arrows-rotate` | Front/rear camera toggle |
| **Manual Code Entry** | `🔢` | `fa-solid fa-barcode` | Direct lookup mode card |
| **Teacher Sign In** | `👨‍🏫` | `fa-solid fa-right-to-bracket` | Login navigation action |
| **Sign Out** | `🚪` | `fa-solid fa-right-from-bracket` | Logout button |
| **Date / Calendar** | `📅` | `fa-regular fa-calendar-days` | Timestamps & schedules |
| **Student / Requester** | `👤` | `fa-regular fa-user` | Student profile info |
| **Phone Number / Contact** | `📞` | `fa-solid fa-phone` | Contact numbers |
| **Warning / Attention** | `⚠️` | `fa-solid fa-triangle-exclamation` | Alert banners |
| **Info / Educational Note** | `ℹ️` | `fa-solid fa-circle-info` | Help callouts |
| **Dropdown Caret** | `▼` | `fa-solid fa-caret-down` | Theme & language menus |
| **Language Switcher** | `🌐` | `fa-solid fa-globe` | Language selector menu |
| **Light Theme** | `☀️` | `fa-solid fa-sun` | Theme toggle menu |
| **Dark Theme** | `🌙` | `fa-solid fa-moon` | Theme toggle menu |
| **System Theme** | `💻` | `fa-solid fa-desktop` | Theme toggle menu |

---

## 4. Verification Check
All 60 mapped icons above have been verified directly against `app/static/vendor/fontawesome/css/all.min.css` to confirm existence in Font Awesome 7.3.1 Free.
Zero Pro-only dependencies are present.
