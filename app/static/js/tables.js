/**
 * Kitaab Bank - Unified Data Table Enhancement Engine
 * 
 * Capabilities:
 * 1. Column Sorting (Ascending / Descending with FontAwesome icons)
 * 2. Client-side Pagination with Page-Size Options: 10, 25, 50, 100
 * 3. Sorting & Pagination Synchronization
 * 4. Clickable Table Rows with Action Button Click-Isolation
 * 5. Full Localization (English, Urdu, Sindhi) & Offline Support
 */

(function () {
  'use strict';

  // Localization Dictionary for Table Controls
  const I18N = {
    en: {
      show: 'Show',
      entries: 'entries',
      showing: 'Showing',
      to: 'to',
      of: 'of',
      records: 'records',
      prev: 'Previous',
      next: 'Next',
      summary: 'Showing {start} to {end} of {total} records'
    },
    ur: {
      show: 'دکھائیں',
      entries: 'اندراجات',
      showing: 'دکھائے جا رہے ہیں',
      to: 'تا',
      of: 'کل',
      records: 'اندراجات',
      prev: 'پچھلا',
      next: 'اگلا',
      summary: '{total} میں سے {start} تا {end} اندراجات'
    },
    sd: {
      show: 'ڏيکاريو',
      entries: 'اندراج',
      showing: 'ڏيکاري پيا وڃن',
      to: 'کان',
      of: 'ڪل',
      records: 'اندراج',
      prev: 'پوئتي',
      next: 'اڳتي',
      summary: '{total} مان {start} کان {end} اندراج'
    }
  };

  function getLang() {
    const htmlLang = (document.documentElement.getAttribute('lang') || 'en').toLowerCase();
    return I18N[htmlLang] ? htmlLang : 'en';
  }

  function getTranslation() {
    return I18N[getLang()];
  }

  /**
   * Extract comparable value from a table cell.
   * Handles numbers, dates, currency/percentages, and raw text.
   */
  function getCellValue(td) {
    if (!td) return '';
    if (td.dataset && td.dataset.sortValue !== undefined) {
      return td.dataset.sortValue;
    }
    // Check if there's a badge, bdi, or code element inside
    const bdi = td.querySelector('bdi.kb-code');
    if (bdi) return bdi.textContent.trim();

    return td.textContent.trim();
  }

  function parseSortValue(val) {
    if (typeof val !== 'string') return val;
    val = val.trim();

    // Check if numeric with byte units (B, KB, MB, GB)
    const byteMatch = val.match(/^([\d.]+)\s*(B|KB|MB|GB)$/i);
    if (byteMatch) {
      const num = parseFloat(byteMatch[1]);
      const unit = byteMatch[2].toUpperCase();
      const mult = unit === 'GB' ? 1073741824 : (unit === 'MB' ? 1048576 : (unit === 'KB' ? 1024 : 1));
      return num * mult;
    }

    // Check if numeric (including commas, percentages)
    const cleanNum = val.replace(/,/g, '').replace(/%/g, '');
    if (cleanNum !== '' && !isNaN(cleanNum) && !isNaN(parseFloat(cleanNum))) {
      return parseFloat(cleanNum);
    }

    // Check if date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
    const dateMatch = val.match(/^(\d{4})-(\d{2})-(\d{2})(?:[T\s](\d{2}):(\d{2})(?::(\d{2}))?)?/);
    if (dateMatch) {
      const ts = new Date(val.replace(' ', 'T')).getTime();
      if (!isNaN(ts)) return ts;
    }

    return val.toLowerCase();
  }

  /**
   * Enhanced DataTable Instance
   */
  class EnhancedDataTable {
    constructor(table) {
      this.table = table;
      this.tbody = table.querySelector('tbody');
      this.thead = table.querySelector('thead');
      if (!this.tbody || !this.thead) return;

      // Extract rows (ignoring empty-state single-row colspan tables)
      const allRows = Array.from(this.tbody.querySelectorAll('tr'));
      if (allRows.length === 1 && allRows[0].querySelector('td[colspan]')) {
        return; // Empty state row, skip enhancing
      }

      this.rows = allRows;
      this.totalRecords = this.rows.length;
      if (this.totalRecords === 0) return;

      this.pageSize = 10;
      this.currentPage = 1;
      this.sortCol = null;
      this.sortDir = 'asc'; // 'asc' or 'desc'

      this.initUI();
      this.initSorting();
      this.initRowClicking();
      this.render();
    }

    initUI() {
      const t = getTranslation();
      const parentCard = this.table.closest('.card');
      const tableResponsive = this.table.closest('.table-responsive') || this.table;

      // 1. Create Top Toolbar (Page Size Selector)
      this.toolbar = document.createElement('div');
      this.toolbar.className = 'table-toolbar d-flex flex-wrap align-items-center justify-content-between gap-2 p-2 p-md-3 border-bottom bg-body-tertiary';
      this.toolbar.innerHTML = `
        <div class="d-flex align-items-center gap-2">
          <label class="small text-body-secondary mb-0 fw-semibold">${t.show}</label>
          <select class="form-select form-select-sm table-page-size shadow-xs" style="width: auto; min-width: 70px;">
            <option value="10" ${this.pageSize === 10 ? 'selected' : ''}>10</option>
            <option value="25" ${this.pageSize === 25 ? 'selected' : ''}>25</option>
            <option value="50" ${this.pageSize === 50 ? 'selected' : ''}>50</option>
            <option value="100" ${this.pageSize === 100 ? 'selected' : ''}>100</option>
          </select>
          <span class="small text-body-secondary fw-semibold">${t.entries}</span>
        </div>
        <div class="small text-body-secondary d-none d-sm-block table-top-info">
          <span class="badge bg-secondary-subtle text-secondary-emphasis border border-secondary-subtle">${this.totalRecords} ${t.records}</span>
        </div>
      `;

      // Insert toolbar right before table / table-responsive
      tableResponsive.parentNode.insertBefore(this.toolbar, tableResponsive);

      // Listen for page size change
      const select = this.toolbar.querySelector('.table-page-size');
      select.addEventListener('change', (e) => {
        this.pageSize = parseInt(e.target.value, 10);
        this.currentPage = 1;
        this.render();
      });

      // 2. Setup or replace Footer (Pagination & Counter)
      let existingFooter = parentCard ? parentCard.querySelector('.card-footer') : null;
      if (existingFooter) {
        this.footer = existingFooter;
        this.footer.className = 'card-footer bg-body-tertiary py-2 px-3 small text-body-secondary d-flex flex-wrap justify-content-between align-items-center gap-2 table-pagination-footer';
      } else {
        this.footer = document.createElement('div');
        this.footer.className = 'table-pagination-footer d-flex flex-wrap justify-content-between align-items-center gap-2 py-2 px-3 bg-body-tertiary border-top small text-body-secondary';
        tableResponsive.parentNode.appendChild(this.footer);
      }
    }

    initSorting() {
      const headerRow = this.thead.querySelector('tr');
      if (!headerRow) return;

      const ths = Array.from(headerRow.querySelectorAll('th'));
      ths.forEach((th, idx) => {
        const text = th.textContent.trim().toLowerCase();
        // Skip columns that shouldn't be sorted (Actions, Cover, or explicitly marked)
        if (
          th.dataset.sortable === 'false' ||
          th.classList.contains('no-sort') ||
          text.includes('action') ||
          text.includes('cover') ||
          text.includes('meter') ||
          text.includes('volume') ||
          text.includes('عمليات') ||
          text.includes('تصوير') ||
          text.includes('ڪارروائي') ||
          text.includes('ڦوٽو')
        ) {
          return;
        }

        th.classList.add('sortable-th');
        th.setAttribute('tabindex', '0');
        th.setAttribute('role', 'button');
        th.setAttribute('aria-sort', 'none');

        // Add sort icon
        const iconSpan = document.createElement('span');
        iconSpan.className = 'sort-icon';
        iconSpan.innerHTML = '<i class="fa-solid fa-sort" aria-hidden="true"></i>';
        th.appendChild(iconSpan);

        const handleSort = () => {
          if (this.sortCol === idx) {
            this.sortDir = this.sortDir === 'asc' ? 'desc' : 'asc';
          } else {
            this.sortCol = idx;
            this.sortDir = 'asc';
          }
          this.sortRows();
          this.updateSortHeaders(ths);
          this.currentPage = 1;
          this.render();
        };

        th.addEventListener('click', handleSort);
        th.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleSort();
          }
        });
      });
    }

    sortRows() {
      if (this.sortCol === null) return;
      const colIdx = this.sortCol;
      const dirMult = this.sortDir === 'asc' ? 1 : -1;

      this.rows.sort((rowA, rowB) => {
        const cellA = rowA.children[colIdx];
        const cellB = rowB.children[colIdx];

        const rawA = getCellValue(cellA);
        const rawB = getCellValue(cellB);

        const valA = parseSortValue(rawA);
        const valB = parseSortValue(rawB);

        if (typeof valA === 'number' && typeof valB === 'number') {
          return (valA - valB) * dirMult;
        }
        return String(valA).localeCompare(String(valB), undefined, { numeric: true, sensitivity: 'base' }) * dirMult;
      });
    }

    updateSortHeaders(ths) {
      ths.forEach((th, idx) => {
        const iconSpan = th.querySelector('.sort-icon');
        if (!iconSpan) return;

        if (this.sortCol === idx) {
          th.classList.remove('sorted-asc', 'sorted-desc');
          th.classList.add(this.sortDir === 'asc' ? 'sorted-asc' : 'sorted-desc');
          th.setAttribute('aria-sort', this.sortDir === 'asc' ? 'ascending' : 'descending');
          iconSpan.innerHTML = this.sortDir === 'asc' 
            ? '<i class="fa-solid fa-sort-up" aria-hidden="true"></i>' 
            : '<i class="fa-solid fa-sort-down" aria-hidden="true"></i>';
        } else {
          th.classList.remove('sorted-asc', 'sorted-desc');
          th.setAttribute('aria-sort', 'none');
          iconSpan.innerHTML = '<i class="fa-solid fa-sort" aria-hidden="true"></i>';
        }
      });
    }

    initRowClicking() {
      this.rows.forEach(row => {
        if (row.dataset.href) {
          row.classList.add('clickable-row');
          row.setAttribute('tabindex', '0');
          row.setAttribute('role', 'link');
        }
      });
    }

    render() {
      const t = getTranslation();
      const totalPages = Math.ceil(this.totalRecords / this.pageSize) || 1;
      if (this.currentPage > totalPages) this.currentPage = totalPages;
      if (this.currentPage < 1) this.currentPage = 1;

      const startIndex = (this.currentPage - 1) * this.pageSize;
      const endIndex = Math.min(startIndex + this.pageSize, this.totalRecords);

      // 1. Detach & re-append sorted rows according to pagination slice
      const frag = document.createDocumentFragment();
      this.rows.forEach((row, idx) => {
        if (idx >= startIndex && idx < endIndex) {
          row.style.display = '';
          frag.appendChild(row);
        } else {
          row.style.display = 'none';
          frag.appendChild(row);
        }
      });
      this.tbody.appendChild(frag);

      // 2. Update Footer info text & pagination controls
      const displayStart = this.totalRecords === 0 ? 0 : startIndex + 1;
      const displayEnd = endIndex;
      const summaryText = t.summary
        .replace('{start}', displayStart)
        .replace('{end}', displayEnd)
        .replace('{total}', this.totalRecords);

      let paginationHtml = '';
      if (totalPages > 1) {
        paginationHtml = `
          <nav aria-label="Table pagination" class="table-pagination-nav">
            <ul class="pagination pagination-sm mb-0">
              <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
                <button type="button" class="page-link table-btn-prev" aria-label="${t.prev}">
                  <span aria-hidden="true">&laquo;</span> ${t.prev}
                </button>
              </li>
        `;

        // Calculate page window (at most 5 page numbers)
        let startPage = Math.max(1, this.currentPage - 2);
        let endPage = Math.min(totalPages, startPage + 4);
        if (endPage - startPage < 4) {
          startPage = Math.max(1, endPage - 4);
        }

        if (startPage > 1) {
          paginationHtml += `
            <li class="page-item"><button type="button" class="page-link table-btn-page" data-page="1">1</button></li>
          `;
          if (startPage > 2) {
            paginationHtml += `<li class="page-item disabled"><span class="page-link">&hellip;</span></li>`;
          }
        }

        for (let p = startPage; p <= endPage; p++) {
          paginationHtml += `
            <li class="page-item ${p === this.currentPage ? 'active' : ''}">
              <button type="button" class="page-link table-btn-page" data-page="${p}">${p}</button>
            </li>
          `;
        }

        if (endPage < totalPages) {
          if (endPage < totalPages - 1) {
            paginationHtml += `<li class="page-item disabled"><span class="page-link">&hellip;</span></li>`;
          }
          paginationHtml += `
            <li class="page-item"><button type="button" class="page-link table-btn-page" data-page="${totalPages}">${totalPages}</button></li>
          `;
        }

        paginationHtml += `
              <li class="page-item ${this.currentPage === totalPages ? 'disabled' : ''}">
                <button type="button" class="page-link table-btn-next" aria-label="${t.next}">
                  ${t.next} <span aria-hidden="true">&raquo;</span>
                </button>
              </li>
            </ul>
          </nav>
        `;
      }

      this.footer.innerHTML = `
        <div class="table-info-text fw-medium">
          ${summaryText}
        </div>
        ${paginationHtml}
      `;

      // 3. Attach Footer Pagination Click Handlers
      const prevBtn = this.footer.querySelector('.table-btn-prev');
      if (prevBtn) {
        prevBtn.addEventListener('click', (e) => {
          e.preventDefault();
          if (this.currentPage > 1) {
            this.currentPage--;
            this.render();
          }
        });
      }

      const nextBtn = this.footer.querySelector('.table-btn-next');
      if (nextBtn) {
        nextBtn.addEventListener('click', (e) => {
          e.preventDefault();
          if (this.currentPage < totalPages) {
            this.currentPage++;
            this.render();
          }
        });
      }

      this.footer.querySelectorAll('.table-btn-page').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          const targetPage = parseInt(btn.getAttribute('data-page'), 10);
          if (targetPage && targetPage !== this.currentPage) {
            this.currentPage = targetPage;
            this.render();
          }
        });
      });
    }
  }

  /**
   * Global Click Delegator for Clickable Rows
   * Isolates buttons, inputs, links, forms, and drag-selection.
   */
  document.addEventListener('click', function (e) {
    // If clicked inside an interactive action element, ignore row click
    if (e.target.closest('a, button, input, select, textarea, form, label, .btn, [onclick], [data-bs-toggle], [data-bs-dismiss]')) {
      return;
    }

    // If user made a text selection (e.g. copying a code), ignore row click
    const sel = window.getSelection();
    if (sel && sel.toString().trim().length > 0) {
      return;
    }

    const row = e.target.closest('tr.clickable-row[data-href]');
    if (row) {
      const url = row.getAttribute('data-href');
      if (url) {
        if (e.ctrlKey || e.metaKey) {
          window.open(url, '_blank');
        } else {
          window.location.href = url;
        }
      }
    }
  });

  // Global Keyboard Navigation for Clickable Rows
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' || e.key === ' ') {
      if (e.target && e.target.matches('tr.clickable-row[data-href]')) {
        e.preventDefault();
        const url = e.target.getAttribute('data-href');
        if (url) window.location.href = url;
      }
    }
  });

  /**
   * Automatic Data Table Discovery & Enhancement
   */
  function initAllDataTables() {
    // Look for all tables inside card / table-responsive
    const tables = document.querySelectorAll('table.table');
    tables.forEach(table => {
      // Don't enhance twice
      if (table.dataset.enhancedDataTable === 'true') return;
      if (table.closest('.no-datatable') || table.dataset.noDatatable === 'true') return;

      table.dataset.enhancedDataTable = 'true';
      new EnhancedDataTable(table);
    });
  }

  // Initialize once DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAllDataTables);
  } else {
    initAllDataTables();
  }

  window.initAllDataTables = initAllDataTables;
})();
