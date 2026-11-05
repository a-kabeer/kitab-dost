/**
 * Kitaab Bank - Zero-FOUC Theme Management Engine
 * Supports: Light, Dark, System Default
 * Fully offline, zero dependencies. Coordinated with Bootstrap 5.3 data-bs-theme.
 */

(function () {
  'use strict';

  const STORAGE_KEY = 'kb_theme';
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

  function getSavedPreference() {
    return localStorage.getItem(STORAGE_KEY) || 'system';
  }

  function resolveTheme(preference) {
    if (preference === 'system') {
      return mediaQuery.matches ? 'dark' : 'light';
    }
    return preference;
  }

  function applyTheme(preference) {
    const activeTheme = resolveTheme(preference);
    document.documentElement.setAttribute('data-theme', activeTheme);
    document.documentElement.setAttribute('data-bs-theme', activeTheme);
    document.documentElement.setAttribute('data-theme-preference', preference);
    localStorage.setItem(STORAGE_KEY, preference);
    updateUI(preference, activeTheme);
  }

  function updateUI(preference, activeTheme) {
    const labelEls = document.querySelectorAll('[data-theme-label]');
    const iconEls = document.querySelectorAll('[data-theme-icon]');

    const icons = {
      light: '<i class="fa-solid fa-sun text-warning" aria-hidden="true"></i>',
      dark: '<i class="fa-solid fa-moon text-info" aria-hidden="true"></i>',
      system: '<i class="fa-solid fa-desktop text-secondary" aria-hidden="true"></i>'
    };

    const labels = {
      light: 'Light',
      dark: 'Dark',
      system: 'System'
    };

    iconEls.forEach(el => {
      el.innerHTML = icons[preference] || icons.light;
    });

    labelEls.forEach(el => {
      el.textContent = labels[preference] || 'Theme';
    });

    // Mark active option in dropdowns
    document.querySelectorAll('[data-theme-set]').forEach(btn => {
      const target = btn.getAttribute('data-theme-set');
      if (target === preference) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });
  }

  // Setup DOM listeners once loaded
  document.addEventListener('DOMContentLoaded', () => {
    const currentPref = getSavedPreference();
    applyTheme(currentPref);

    // Theme selection buttons (delegated for dynamically created or offcanvas buttons)
    document.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-theme-set]');
      if (!btn) return;
      e.preventDefault();
      const targetTheme = btn.getAttribute('data-theme-set');
      applyTheme(targetTheme);

      // Close legacy menus if open
      document.querySelectorAll('.theme-dropdown-menu.show').forEach(menu => {
        menu.classList.remove('show');
      });
    });

    // Legacy theme toggle support if present
    document.querySelectorAll('[data-theme-toggle]').forEach(toggleBtn => {
      toggleBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const wrap = toggleBtn.closest('.theme-selector-wrap');
        if (wrap) {
          const menu = wrap.querySelector('.theme-dropdown-menu');
          if (menu) menu.classList.toggle('show');
        }
      });
    });

    document.addEventListener('click', () => {
      document.querySelectorAll('.theme-dropdown-menu.show').forEach(menu => {
        menu.classList.remove('show');
      });
    });

    // React to OS changes when set to system default
    mediaQuery.addEventListener('change', () => {
      if (getSavedPreference() === 'system') {
        applyTheme('system');
      }
    });
  });

  // Expose global helper
  window.KitaabTheme = {
    setTheme: applyTheme,
    getPreference: getSavedPreference
  };
})();
